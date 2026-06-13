"""
Routeur authentification — inscription, connexion, reset mot de passe,
vérification email/téléphone, gestion profil.
"""
import random
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user
from app.core.limiter import limiter
from app.core.security import hash_password, verify_password, create_access_token
from app.models import User, Organization, UserRole
from app.schemas import RegisterIn, TokenOut, UserOut
from app.services.subscription import create_default_subscription

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


def _gen_token(n: int = 64) -> str:
    return secrets.token_urlsafe(n)


def _gen_otp(n: int = 6) -> str:
    return "".join(random.choices(string.digits, k=n))


def _normalize_phone(phone: str) -> str:
    p = phone.strip().replace(" ", "").replace("-", "")
    if p.startswith("+221"):
        return p
    if p.startswith("221"):
        return "+" + p
    if p.startswith("0"):
        p = p[1:]
    return "+221" + p


def _find_user_by_phone(raw: str, db: Session) -> User | None:
    from sqlalchemy import func
    # Normalise l'input en E.164 puis compare en strippant espaces/tirets en base
    try:
        normalized = _normalize_phone(raw)
    except Exception:
        normalized = raw.strip()
    stripped = normalized.replace(" ", "").replace("-", "")
    return (
        db.query(User)
        .filter(func.replace(func.replace(User.phone, " ", ""), "-", "") == stripped)
        .first()
    )


# ── INSCRIPTION ───────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit("3/minute")
def register(request: Request, data: RegisterIn, db: Session = Depends(get_db)):
    """Crée organisation + utilisateur propriétaire + abonnement gratuit."""
    # Normalisation et validation téléphone
    phone_norm = _normalize_phone(data.phone)
    local = phone_norm.replace("+221", "")
    if len(local) != 9 or not local.isdigit():
        raise HTTPException(400, "Numéro de téléphone invalide (format attendu : 77 XXX XX XX).")

    # Unicité téléphone
    if _find_user_by_phone(phone_norm, db):
        raise HTTPException(409, "Ce numéro de téléphone est déjà utilisé.")

    # Unicité email (seulement si fourni)
    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Cet email est déjà utilisé.")

    org = Organization(
        name=data.org_name or f"Compte de {data.full_name}",
        is_cooperative=data.is_cooperative,
    )
    db.add(org)
    db.flush()

    role_map = {
        "conseiller": UserRole.CONSEILLER,
        "technicien": UserRole.TECHNICIEN,
        "laboratoire": UserRole.LABORATOIRE,
        "producteur": UserRole.PRODUCTEUR,
    }
    role = role_map.get(data.profil or "producteur", UserRole.OWNER)
    if data.is_cooperative:
        role = UserRole.OWNER

    verif_token = _gen_token(32) if data.email else None
    user = User(
        org_id=org.id,
        full_name=data.full_name,
        email=data.email or None,
        phone=phone_norm,
        hashed_password=hash_password(data.password),
        role=role,
        profil=data.profil or "producteur",
        email_verification_token=verif_token,
        email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    create_default_subscription(db, org)
    return user


# ── CONNEXION ─────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenOut)
@limiter.limit("5/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Connexion → JWT. Le champ 'username' accepte email OU numéro de téléphone."""
    username = form.username.strip()

    if "@" in username:
        user = db.query(User).filter(User.email == username.lower()).first()
    else:
        user = _find_user_by_phone(username, db)

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiant ou mot de passe incorrect.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé.")
    token = create_access_token({
        "sub": str(user.id),
        "org": user.org_id,
        "role": user.role.value,
        "profil": user.profil,
    })
    return TokenOut(access_token=token)


# ── PROFIL ────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_profile(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Mettre à jour full_name, phone, profil."""
    allowed = {"full_name", "phone", "profil"}
    for k, v in data.items():
        if k in allowed and v is not None:
            setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


# ── CHANGEMENT MOT DE PASSE (connecté) ───────────────────────────────────────

@router.post("/change-password")
def change_password(
    data: dict,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Changer son mot de passe (requiert l'ancien)."""
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")
    if not verify_password(old_pw, user.hashed_password):
        raise HTTPException(400, "Ancien mot de passe incorrect.")
    if len(new_pw) < 6:
        raise HTTPException(400, "Nouveau mot de passe trop court (min 6 caractères).")
    user.hashed_password = hash_password(new_pw)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return {"message": "Mot de passe changé avec succès."}


# ── RESET MOT DE PASSE (oublié) ───────────────────────────────────────────────

@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, data: dict, db: Session = Depends(get_db)):
    """
    Génère un token de reset valable 1h.
    Retourne le token (à envoyer par WhatsApp/SMS via le frontend).
    En production, brancher un service SMS/email ici.
    """
    email = data.get("email", "").strip().lower()
    user = db.query(User).filter(User.email == email).first()
    # Répondre OK même si email inconnu (sécurité : pas d'énumération)
    if not user:
        return {"message": "Si cet email existe, un code de réinitialisation a été envoyé."}

    token = _gen_token(32)
    user.reset_token = token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    # TODO: envoyer via WhatsApp/SMS quand service configuré
    # Pour l'instant le token est retourné (dev/test)
    return {
        "message": "Code de réinitialisation généré.",
        "reset_token": token,          # à supprimer en prod quand SMS actif
        "expires_in": "1 heure",
    }


@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    """Réinitialise le mot de passe avec le token reçu."""
    token = data.get("token", "")
    new_pw = data.get("new_password", "")
    if len(new_pw) < 6:
        raise HTTPException(400, "Mot de passe trop court (min 6 caractères).")

    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        raise HTTPException(400, "Token invalide ou expiré.")
    if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(400, "Token expiré. Demandez un nouveau code.")

    user.hashed_password = hash_password(new_pw)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return {"message": "Mot de passe réinitialisé avec succès."}


# ── VÉRIFICATION EMAIL ────────────────────────────────────────────────────────

@router.post("/send-verification-email")
@limiter.limit("2/minute")
def send_verification_email(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Génère/renouvelle le token de vérification email."""
    if user.email_verified:
        return {"message": "Email déjà vérifié."}
    token = _gen_token(32)
    user.email_verification_token = token
    db.commit()
    # TODO: envoyer email quand SMTP configuré
    return {
        "message": "Lien de vérification généré.",
        "verification_token": token,   # à supprimer en prod
    }


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Valide l'email depuis le lien de vérification."""
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        raise HTTPException(400, "Token de vérification invalide.")
    user.email_verified = True
    user.email_verification_token = None
    db.commit()
    return {"message": "Email vérifié avec succès. Vous pouvez vous connecter."}


# ── VÉRIFICATION TÉLÉPHONE OTP ────────────────────────────────────────────────

@router.post("/send-phone-otp")
@limiter.limit("3/minute")
def send_phone_otp(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Génère un OTP 6 chiffres valable 10 min pour vérifier le numéro de téléphone."""
    if not user.phone:
        raise HTTPException(400, "Aucun numéro de téléphone enregistré.")
    if user.phone_verified:
        return {"message": "Téléphone déjà vérifié."}

    otp = _gen_otp(6)
    user.phone_otp = otp
    user.phone_otp_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()
    # TODO: envoyer via WhatsApp Business API ou Orange SMS Gateway
    return {
        "message": f"OTP envoyé au {user.phone}.",
        "otp": otp,           # à supprimer en prod quand SMS actif
        "expires_in": "10 minutes",
    }


@router.post("/verify-phone-otp")
def verify_phone_otp(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Vérifie le code OTP reçu par SMS/WhatsApp."""
    otp = data.get("otp", "").strip()
    if not user.phone_otp or user.phone_otp != otp:
        raise HTTPException(400, "Code OTP incorrect.")
    if user.phone_otp_expires and user.phone_otp_expires < datetime.now(timezone.utc):
        raise HTTPException(400, "Code OTP expiré. Demandez un nouveau code.")

    user.phone_verified = True
    user.phone_otp = None
    user.phone_otp_expires = None
    db.commit()
    return {"message": "Téléphone vérifié avec succès."}
