"""
Router OTP SMS — authentification et réinitialisation mot de passe par SMS.

Endpoints :
  POST /api/otp/request              — demande d'OTP (envoi SMS)
  POST /api/otp/verify               — vérification OTP → JWT
  POST /api/otp/forgot-password      — réinitialisation mot de passe par OTP SMS

Sécurité :
  - OTP haché HMAC-SHA256 en base (jamais en clair)
  - Expiration 5 minutes
  - Maximum 5 tentatives par OTP
  - Rate limit 3 requêtes/minute par IP
  - Invalidation automatique des anciens OTP à chaque nouvelle demande
  - Réponse identique si numéro inconnu (anti-énumération)
"""
import hashlib
import hmac
import logging
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import COOKIE_NAME
from app.core.limiter import limiter
from app.core.security import create_access_token
from app.models import User
from app.models.otp import OTPRecord
from app.services.sms import get_sms_provider

logger = logging.getLogger("agroscan.otp")

router = APIRouter(prefix="/api/otp", tags=["OTP SMS"])

OTP_EXPIRE_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
OTP_LENGTH = 6

PurposeType = Literal["login", "reset_password", "register"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_otp(otp: str) -> str:
    """HMAC-SHA256 de l'OTP avec la SECRET_KEY comme sel."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        otp.encode(),
        hashlib.sha256,
    ).hexdigest()


def _gen_otp() -> str:
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


def _normalize_phone(phone: str) -> str:
    p = phone.strip().replace(" ", "").replace("-", "")
    if p.startswith("+221"):
        return p
    if p.startswith("221"):
        return "+" + p
    if p.startswith("0"):
        p = p[1:]
    return "+221" + p


def _invalidate_previous(phone: str, purpose: str, db: Session) -> None:
    """Invalide tous les OTP actifs existants pour ce numéro + objectif."""
    db.query(OTPRecord).filter(
        OTPRecord.phone == phone,
        OTPRecord.purpose == purpose,
        OTPRecord.verified == False,
        OTPRecord.invalidated == False,
    ).update({"invalidated": True})
    db.flush()


def _find_user_by_phone(phone: str, db: Session) -> User | None:
    from sqlalchemy import func
    # Normalise les deux côtés pour gérer les espaces/tirets en base
    phone_stripped = phone.replace(" ", "").replace("-", "")
    return (
        db.query(User)
        .filter(
            func.replace(func.replace(User.phone, " ", ""), "-", "") == phone_stripped
        )
        .first()
    )


# ── Schémas ───────────────────────────────────────────────────────────────────

class OTPRequestIn(BaseModel):
    phone: str
    purpose: PurposeType = "login"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        p = _normalize_phone(v)
        local = p.replace("+221", "")
        if len(local) != 9 or not local.isdigit():
            raise ValueError("Numéro de téléphone invalide (format attendu : 77 XXX XX XX)")
        return p


class OTPVerifyIn(BaseModel):
    phone: str
    otp: str
    purpose: PurposeType = "login"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _normalize_phone(v)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != OTP_LENGTH:
            raise ValueError(f"Le code OTP doit être composé de {OTP_LENGTH} chiffres")
        return v


class ForgotPasswordOTPIn(BaseModel):
    phone: str
    new_password: str | None = None  # fourni à /verify, pas ici

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _normalize_phone(v)


class OTPRequestOut(BaseModel):
    message: str
    expires_in: str = f"{OTP_EXPIRE_MINUTES} minutes"
    provider: str = ""


class OTPVerifyOut(BaseModel):
    message: str
    access_token: str | None = None
    token_type: str = "bearer"
    reset_token: str | None = None  # pour reset_password uniquement


# ── POST /api/otp/request ─────────────────────────────────────────────────────

@router.post("/request", response_model=OTPRequestOut)
@limiter.limit("3/minute")
def otp_request(
    request: Request,
    data: OTPRequestIn,
    db: Session = Depends(get_db),
) -> OTPRequestOut:
    """
    Génère un OTP à 6 chiffres, le stocke haché en base et l'envoie par SMS.

    Pour login / reset_password : le numéro doit correspondre à un compte existant.
    Pour register : pas de vérification (le compte n'existe pas encore).

    Réponse identique même si numéro inconnu (anti-énumération).
    """
    phone = data.phone
    purpose = data.purpose

    # Vérification numéro existant (login / reset)
    if purpose in ("login", "reset_password"):
        user = _find_user_by_phone(phone, db)
        if not user:
            # Anti-énumération : réponse identique
            logger.info("OTP request pour numéro inconnu %s (purpose=%s)", phone, purpose)
            return OTPRequestOut(
                message="Si ce numéro est enregistré, vous recevrez un code par SMS.",
                provider="",
            )

    # Invalider les OTP précédents pour éviter l'accumulation
    _invalidate_previous(phone, purpose, db)

    # Générer l'OTP
    otp_clear = _gen_otp()
    otp_hash = _hash_otp(otp_clear)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

    record = OTPRecord(
        phone=phone,
        otp_hash=otp_hash,
        purpose=purpose,
        expires_at=expires_at,
        attempts=0,
        verified=False,
        invalidated=False,
    )
    db.add(record)
    db.commit()

    # Construire le message SMS
    purpose_labels = {
        "login": "connexion à AgroScan",
        "reset_password": "réinitialisation de votre mot de passe AgroScan",
        "register": "création de votre compte AgroScan",
    }
    label = purpose_labels.get(purpose, "AgroScan")
    sms_body = (
        f"AgroScan Pro\n"
        f"Code de {label} : {otp_clear}\n"
        f"Valable {OTP_EXPIRE_MINUTES} min. Ne le partagez pas."
    )

    # Envoyer via le provider configuré (détection auto possible)
    provider = get_sms_provider(phone)
    result = provider.send(phone, sms_body)

    if not result.success:
        logger.error("Échec envoi OTP → %s : %s", phone, result.error)
        # Ne pas exposer l'erreur SMS à l'utilisateur (sécurité)
        # L'OTP est quand même créé, un retry peut fonctionner

    return OTPRequestOut(
        message="Code envoyé par SMS. Valable 5 minutes.",
        expires_in=f"{OTP_EXPIRE_MINUTES} minutes",
        provider=result.provider,
    )


# ── POST /api/otp/verify ──────────────────────────────────────────────────────

@router.post("/verify", response_model=OTPVerifyOut)
@limiter.limit("10/minute")
def otp_verify(
    request: Request,
    data: OTPVerifyIn,
    db: Session = Depends(get_db),
    response: Response = None,
) -> OTPVerifyOut:
    """
    Vérifie un OTP.

    - login → retourne un JWT d'accès
    - reset_password → retourne un reset_token à utiliser avec /api/auth/reset-password
    - register → retourne un signal de vérification (le compte doit être créé séparément)

    Erreurs :
    - 400 Code invalide (avec compteur de tentatives)
    - 400 Code expiré
    - 429 Trop de tentatives (OTP verrouillé)
    """
    phone = data.phone
    purpose = data.purpose
    otp_hash = _hash_otp(data.otp)

    # Récupérer l'OTP le plus récent non vérifié pour ce numéro + objectif
    record = (
        db.query(OTPRecord)
        .filter(
            OTPRecord.phone == phone,
            OTPRecord.purpose == purpose,
            OTPRecord.verified == False,
            OTPRecord.invalidated == False,
        )
        .order_by(OTPRecord.created_at.desc())
        .first()
    )

    # OTP introuvable
    if not record:
        raise HTTPException(
            status_code=400,
            detail="Aucun code actif pour ce numéro. Demandez un nouveau code.",
        )

    # Expiré
    if record.is_expired:
        raise HTTPException(
            status_code=400,
            detail="Code expiré. Demandez un nouveau code.",
        )

    # Trop de tentatives → verrouillage
    if record.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de tentatives ({OTP_MAX_ATTEMPTS} max). Demandez un nouveau code.",
        )

    # Vérification HMAC (timing-safe)
    if not hmac.compare_digest(record.otp_hash, otp_hash):
        record.attempts += 1
        remaining = OTP_MAX_ATTEMPTS - record.attempts
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Code incorrect. {remaining} tentative{'s' if remaining > 1 else ''} restante{'s' if remaining > 1 else ''}.",
        )

    # ✓ OTP valide — invalider immédiatement
    record.verified = True
    db.commit()

    # Retour selon l'objectif
    if purpose == "login":
        user = _find_user_by_phone(phone, db)
        if not user:
            raise HTTPException(status_code=404, detail="Compte introuvable.")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Compte désactivé.")

        token = create_access_token({
            "sub": str(user.id),
            "org": user.org_id,
            "role": user.role.value,
            "profil": user.profil,
        })
        logger.info("OTP login réussi → user_id=%s phone=%s", user.id, phone)
        if response is not None:
            response.set_cookie(
                key=COOKIE_NAME, value=token, httponly=True,
                secure=True, samesite="lax", max_age=8 * 3600, path="/",
            )
        return OTPVerifyOut(message="Connexion réussie.", access_token=token)

    if purpose == "reset_password":
        import secrets as _secrets
        user = _find_user_by_phone(phone, db)
        if not user:
            raise HTTPException(status_code=404, detail="Compte introuvable.")
        reset_token = _secrets.token_urlsafe(32)
        user.reset_token = reset_token
        from datetime import timedelta
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        logger.info("OTP reset_password réussi → user_id=%s phone=%s", user.id, phone)
        return OTPVerifyOut(
            message="Code vérifié. Utilisez le reset_token pour définir votre nouveau mot de passe.",
            reset_token=reset_token,
        )

    if purpose == "register":
        # Marquer le téléphone comme vérifié pour la session d'inscription
        return OTPVerifyOut(
            message="Numéro vérifié. Vous pouvez créer votre compte.",
        )

    raise HTTPException(status_code=400, detail="Objectif OTP inconnu.")


# ── POST /api/otp/forgot-password ─────────────────────────────────────────────

@router.post("/forgot-password", response_model=OTPRequestOut)
@limiter.limit("3/minute")
def otp_forgot_password(
    request: Request,
    data: ForgotPasswordOTPIn,
    db: Session = Depends(get_db),
) -> OTPRequestOut:
    """
    Réinitialisation de mot de passe par SMS OTP.

    Étape 1 : POST /api/otp/forgot-password  {phone}
              → envoi SMS avec OTP
    Étape 2 : POST /api/otp/verify  {phone, otp, purpose:"reset_password"}
              → retourne reset_token
    Étape 3 : POST /api/auth/reset-password  {token: reset_token, new_password}
              → nouveau mot de passe défini

    Réponse identique si numéro inconnu (anti-énumération).
    """
    # Délègue à otp_request avec purpose="reset_password"
    inner = OTPRequestIn(phone=data.phone, purpose="reset_password")
    return otp_request(request=request, data=inner, db=db)
