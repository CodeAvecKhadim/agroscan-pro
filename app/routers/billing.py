"""
Routeur des abonnements et de la facturation AgroScan Pro.

Nouveau modèle tarifaire (juin 2026) :
  GRATUIT     : 0 FCFA — quotas daily IA + weekly satellite + max parcelles
  PREMIUM     : 14 900 FCFA / campagne agricole (90 jours)
  COOPERATIVE : 25 000 FCFA/mois ou 250 000 FCFA/an

Endpoints :
  GET  /api/billing/plans            — grille tarifaire (public)
  GET  /api/billing/me               — abonnement courant + jours restants
  GET  /api/billing/usage            — consommation IA/satellite du jour/semaine
  POST /api/billing/change           — changer de plan
  POST /api/billing/checkout         — initier un paiement (Wave / Orange Money / PayDunya)
  GET  /api/billing/checkout/{id}    — statut d'un paiement
  POST /api/billing/webhook          — confirmation PSP générique
  POST /api/billing/webhook-paydunya — IPN PayDunya
  POST /api/billing/webhook-wave     — Wave Money (HMAC-SHA256)
  POST /api/billing/webhook-orange-money — Orange Money (HMAC-SHA256)
"""
import hashlib
import hmac
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import (current_user, current_subscription, require_role,
                            get_usage, _today_str, _current_week_str)
from app.models import User, Subscription, Payment, PlanType, SubStatus, UserRole
from app.schemas import SubscriptionOut, ChangePlanIn, UsageOut
from app.services.plans import PLAN_FEATURES, price_ttc, features_for, COOP_HA_EXTENSIONS
from app.services.subscription import (change_plan, confirm_payment,
                                        remaining_campaign_days)

router = APIRouter(prefix="/api/billing", tags=["Abonnements"])


@router.get("/plans")
def list_plans():
    """Grille des offres avec prix TTC — pour la page tarifs."""
    out = []
    for plan, feats in PLAN_FEATURES.items():
        entry = {
            "plan": plan.value,
            "label": feats["label"],
            "pricing_monthly": price_ttc(plan, billing="monthly"),
            "pricing_annual": price_ttc(plan, billing="annual") if feats.get("price_ht_annual") else None,
            # Limites
            "max_parcelles": feats["max_parcelles"],
            "max_ha_per_parcelle": feats["max_ha_per_parcelle"],
            "daily_ai_analyses": feats["daily_ai_analyses"],
            "weekly_satellite": feats["weekly_satellite"],
            "max_seats": feats["max_seats"],
            # Fonctionnalités
            "features": {
                "precision_agriculture": feats["precision_agriculture"],
                "ndvi_satellite": feats["ndvi_satellite"],
                "ai_assistant": feats["ai_assistant"],
                "soil_analysis": feats["soil_analysis"],
                "crop_health_advanced": feats["crop_health_advanced"],
                "pdf_reports": feats["pdf_reports"],
                "historical_data": feats["historical_data"],
                "activities_management": feats["activities_management"],
                "farm_management": feats["farm_management"],
                "advisor_dashboard": feats["advisor_dashboard"],
                "multi_farmer": feats["multi_farmer"],
                "consolidated_reports": feats["consolidated_reports"],
                "alerts": feats["alerts"],
            },
        }
        if plan == PlanType.COOPERATIVE:
            entry["ha_extensions"] = COOP_HA_EXTENSIONS
            entry["included_ha"] = feats.get("included_ha", 25)
        out.append(entry)
    return {
        "currency": settings.CURRENCY,
        "vat_rate": settings.VAT_RATE,
        "marketing": {
            "premium_tagline": "14 900 FCFA par campagne agricole (3 mois)",
            "premium_daily": "Soit moins de 170 FCFA par jour",
        },
        "plans": out,
    }


@router.get("/me")
def my_subscription(
    sub: Subscription = Depends(current_subscription),
):
    """Abonnement courant + jours de campagne restants."""
    remaining = remaining_campaign_days(sub)
    is_trial = sub.status == SubStatus.TRIAL
    trial_expired = sub.status == SubStatus.EXPIRED and sub.plan == PlanType.GRATUIT
    return {
        "plan": sub.plan.value,
        "status": sub.status.value,
        "seats": sub.seats,
        "current_period_end": sub.current_period_end,
        "auto_renew": sub.auto_renew,
        "campaign_billing": sub.campaign_billing or "monthly",
        "remaining_days": remaining,
        "is_active": sub.status in (SubStatus.ACTIVE, SubStatus.TRIAL),
        "is_trial": is_trial,
        "trial_days_remaining": remaining if is_trial else None,
        "trial_expired": trial_expired,
    }


@router.get("/usage", response_model=UsageOut)
def my_usage(user: User = Depends(current_user),
             sub: Subscription = Depends(current_subscription),
             db: Session = Depends(get_db)):
    """Consommation IA (jour) et satellite (semaine) + limites du plan."""
    uc = get_usage(db, user.org_id)
    feats = features_for(sub.plan)

    # Reset si nouveau jour / nouvelle semaine
    today = _today_str()
    week = _current_week_str()
    changed = False
    if uc.daily_ai_date != today:
        uc.daily_ai_count = 0
        uc.daily_ai_date = today
        changed = True
    if uc.weekly_period != week:
        uc.weekly_satellite_count = 0
        uc.weekly_period = week
        changed = True
    if changed:
        db.commit()

    daily_ai_count = uc.daily_ai_count or 0
    weekly_sat_count = uc.weekly_satellite_count or 0

    return UsageOut(
        period=uc.period,
        daily_ai_used=daily_ai_count,
        daily_ai_limit=feats["daily_ai_analyses"],
        weekly_satellite_used=weekly_sat_count,
        weekly_satellite_limit=feats["weekly_satellite"],
        analyses_used=uc.analyses_count,
        analyses_limit=feats["monthly_analyses"],
        history_days=feats["history_days"],
        plan=sub.plan,
    )


@router.post("/change")
def change_subscription(
    data: ChangePlanIn,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """Change de plan. Renvoie l'instruction de paiement pour les plans payants."""
    return change_plan(db, sub, data.plan, data.seats, billing=data.billing)


# ── CHECKOUT INITIATION ──────────────────────────────────────────────────────

class CheckoutIn(BaseModel):
    plan: PlanType
    billing: str = "monthly"
    provider: str = "wave"
    seats: int = 1
    phone: Optional[str] = None


@router.post("/checkout")
def initiate_checkout(
    data: CheckoutIn,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """
    Initie un paiement auprès du PSP choisi et retourne le lien/code de paiement.

    - Wave       : retourne `checkout_url` (lien Wave) + `wave_launch_url`
    - Orange Money: retourne `ussd_code` + instructions
    - PayDunya   : retourne `checkout_url` (page de paiement PayDunya)
    - Manuel     : retourne instructions de virement
    """
    if data.plan == PlanType.GRATUIT:
        return change_plan(db, sub, PlanType.GRATUIT)

    from app.services.plans import price_ttc, features_for
    feats = features_for(data.plan)
    seats = max(1, min(data.seats, feats["max_seats"]))
    pricing = price_ttc(data.plan, billing=data.billing)
    amount_ttc = pricing["ttc"]

    # Créer le paiement en attente
    payment = Payment(
        subscription_id=sub.id,
        provider=data.provider,
        amount_ht=pricing["ht"],
        vat=pricing["vat"],
        amount_ttc=amount_ttc,
        status="pending",
    )
    sub.plan = data.plan
    sub.seats = seats
    sub.status = SubStatus.PAST_DUE
    sub.campaign_billing = data.billing  # monthly | annual — conservé pour PREMIUM et COOPERATIVE
    db.add(payment)
    db.commit()
    db.refresh(payment)

    result = {
        "payment_id": payment.id,
        "plan": data.plan.value,
        "amount_ttc": amount_ttc,
        "currency": settings.CURRENCY,
        "provider": data.provider,
        "billing": data.billing,
    }

    if data.provider == "wave":
        result.update(_initiate_wave(payment, amount_ttc))
    elif data.provider == "orange_money":
        result.update(_initiate_orange_money(payment, amount_ttc, data.phone))
    elif data.provider == "paydunya":
        result.update(_initiate_paydunya(payment, amount_ttc, data.plan, data.billing))
    else:
        result.update({
            "type": "manuel",
            "instruction": (
                f"Envoyez {amount_ttc:,} FCFA à Social Technologie "
                f"({settings.CONTACT_PHONE}) via Wave ou Orange Money "
                f"en indiquant votre email {user.email} en référence. "
                f"L'activation est manuelle sous 24h."
            ),
        })

    return result


@router.get("/checkout/{payment_id}")
def checkout_status(
    payment_id: int,
    user: User = Depends(current_user),
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """Statut d'un paiement en cours."""
    payment = db.query(Payment).filter_by(
        id=payment_id, subscription_id=sub.id
    ).first()
    if not payment:
        raise HTTPException(404, "Paiement introuvable.")
    return {
        "payment_id": payment.id,
        "status": payment.status,
        "provider": payment.provider,
        "amount_ttc": payment.amount_ttc,
        "provider_ref": payment.provider_ref,
        "created_at": payment.created_at,
    }


# ── Helpers PSP ───────────────────────────────────────────────────────────────

def _initiate_wave(payment: Payment, amount_ttc: int) -> dict:
    """Crée une session Wave Checkout et retourne le lien de paiement."""
    if not settings.WAVE_API_KEY:
        return {
            "type": "wave_manual",
            "instruction": (
                f"Payez {amount_ttc:,} FCFA via Wave Money. "
                f"Envoyez au marchand AgroScan Pro. "
                f"Référence : AGRO-{payment.id:06d}."
            ),
            "wave_merchant": settings.CONTACT_PHONE,
        }
    try:
        resp = httpx.post(
            settings.WAVE_CHECKOUT_URL,
            headers={
                "Authorization": f"Bearer {settings.WAVE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "amount": str(amount_ttc),
                "currency": "XOF",
                "client_reference": str(payment.id),
                "success_url": settings.PAYMENT_SUCCESS_URL + f"&ref={payment.id}",
                "error_url": settings.PAYMENT_ERROR_URL + f"&ref={payment.id}",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "type": "wave_checkout",
            "checkout_url": data.get("wave_launch_url", ""),
            "wave_session_id": data.get("id", ""),
        }
    except httpx.HTTPError as e:
        return {
            "type": "wave_error",
            "error": f"Wave API indisponible : {str(e)[:100]}",
            "fallback": f"Payez {amount_ttc:,} FCFA via Wave au {settings.CONTACT_PHONE}, réf AGRO-{payment.id:06d}.",
        }


def _initiate_orange_money(payment: Payment, amount_ttc: int, phone: Optional[str]) -> dict:
    """Initie un paiement Orange Money (Orange Money Webpayment API Sénégal)."""
    if not settings.ORANGE_API_KEY or not settings.ORANGE_AUTH_HEADER:
        ussd = f"*144*{amount_ttc}#"
        return {
            "type": "orange_manual",
            "ussd_code": ussd,
            "instruction": (
                f"Composez {ussd} sur votre téléphone Orange Money, "
                f"envoyez {amount_ttc:,} FCFA au numéro {settings.CONTACT_PHONE} "
                f"et indiquez la référence AGRO-{payment.id:06d}."
            ),
        }
    try:
        resp = httpx.post(
            settings.ORANGE_CHECKOUT_URL,
            headers={
                "Authorization": settings.ORANGE_AUTH_HEADER,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "merchant_key": settings.ORANGE_API_KEY,
                "currency": "OUV",
                "order_id": f"AGRO-{payment.id:06d}",
                "amount": amount_ttc,
                "return_url": settings.PAYMENT_SUCCESS_URL,
                "cancel_url": settings.PAYMENT_ERROR_URL,
                "notif_url": f"{settings.PAYMENT_SUCCESS_URL.rsplit('/', 1)[0]}/api/billing/webhook-orange-money",
                "lang": "fr",
                "reference": str(payment.id),
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "type": "orange_checkout",
            "checkout_url": data.get("payment_url", ""),
            "notif_token": data.get("notif_token", ""),
        }
    except httpx.HTTPError as e:
        return {
            "type": "orange_error",
            "error": f"Orange Money API indisponible : {str(e)[:100]}",
            "fallback": (
                f"Composez *144# sur votre téléphone Orange et payez "
                f"{amount_ttc:,} FCFA, réf AGRO-{payment.id:06d}."
            ),
        }


def _initiate_paydunya(payment: Payment, amount_ttc: int,
                        plan: PlanType, billing: str) -> dict:
    """Crée une facture PayDunya et retourne l'URL de paiement."""
    mode = settings.PAYDUNYA_MODE
    if mode == "live":
        base_url = "https://app.paydunya.com/api/v1"
    else:
        base_url = "https://app.paydunya.com/sandbox-api/v1"

    if not settings.PAYDUNYA_MASTER_KEY:
        return {
            "type": "paydunya_manual",
            "instruction": (
                f"Payez {amount_ttc:,} FCFA via PayDunya. "
                f"Contactez {settings.CONTACT_PHONE} pour recevoir le lien de paiement. "
                f"Référence : AGRO-{payment.id:06d}."
            ),
        }

    label = {
        PlanType.PREMIUM: f"AgroScan Pro — Campagne agricole 3 mois",
        PlanType.COOPERATIVE: f"AgroScan Pro — Coopérative {billing}",
    }.get(plan, "AgroScan Pro — Abonnement")

    try:
        resp = httpx.post(
            f"{base_url}/checkout-invoice/create",
            headers={
                "PAYDUNYA-MASTER-KEY": settings.PAYDUNYA_MASTER_KEY,
                "PAYDUNYA-PRIVATE-KEY": settings.PAYDUNYA_PRIVATE_KEY,
                "PAYDUNYA-TOKEN": settings.PAYDUNYA_TOKEN,
                "PAYDUNYA-PUBLIC-KEY": settings.PAYDUNYA_PUBLIC_KEY,
                "Content-Type": "application/json",
            },
            json={
                "invoice": {
                    "total_amount": amount_ttc,
                    "description": label,
                },
                "store": {
                    "name": settings.PAYDUNYA_STORE_NAME,
                },
                "actions": {
                    "cancel_url": settings.PAYMENT_ERROR_URL,
                    "return_url": settings.PAYMENT_SUCCESS_URL + f"&ref={payment.id}",
                    "callback_url": f"{settings.PAYMENT_SUCCESS_URL.rsplit('/', 1)[0]}/api/billing/webhook-paydunya",
                },
                "custom_data": {
                    "payment_id": str(payment.id),
                },
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("response_code") == "00":
            token = data.get("token", "")
            return {
                "type": "paydunya_checkout",
                "checkout_url": f"https://app.paydunya.com/sandbox/checkout-invoice/confirm/{token}" if mode == "test" else f"https://app.paydunya.com/checkout-invoice/confirm/{token}",
                "paydunya_token": token,
            }
        return {
            "type": "paydunya_error",
            "error": data.get("response_text", "Erreur PayDunya"),
        }
    except httpx.HTTPError as e:
        return {
            "type": "paydunya_error",
            "error": f"PayDunya indisponible : {str(e)[:100]}",
            "fallback": f"Payez {amount_ttc:,} FCFA via PayDunya, réf AGRO-{payment.id:06d}.",
        }


@router.post("/webhook")
def payment_webhook(
    payload: dict,
    x_webhook_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Confirmation de paiement PSP générique."""
    if settings.PAYMENT_WEBHOOK_SECRET and x_webhook_secret != settings.PAYMENT_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Signature webhook invalide.")

    payment = db.query(Payment).filter(Payment.id == payload.get("payment_id")).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    if payload.get("status") == "paid":
        confirm_payment(db, payment, payload.get("provider_ref", ""))
        return {"ok": True, "message": "Abonnement activé."}
    payment.status = "failed"
    db.commit()
    return {"ok": False, "message": "Paiement échoué."}


@router.post("/webhook-paydunya")
def paydunya_webhook(
    payload: dict,
    x_webhook_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Confirmation IPN PayDunya (appelé par le serveur Node.js)."""
    if not settings.PAYMENT_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook non configuré.")
    if x_webhook_secret != settings.PAYMENT_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Signature webhook invalide.")

    try:
        user_id = int(payload.get("user_id", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="user_id invalide.")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id manquant.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    sub = db.query(Subscription).filter(Subscription.org_id == user.org_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Abonnement introuvable.")

    payment = (
        db.query(Payment)
        .filter(Payment.subscription_id == sub.id, Payment.status == "pending")
        .order_by(Payment.created_at.desc())
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Aucun paiement en attente.")

    confirm_payment(db, payment, payload.get("provider_ref", ""))
    return {"ok": True, "message": f"Abonnement activé pour l'utilisateur {user_id}."}


# ── Wave Money ──────────────────────────────────────────────────────────────────

@router.post("/webhook-wave")
async def wave_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Callback Wave Money — HMAC-SHA256 dans 'Wave-Signature'."""
    body = await request.body()
    wave_sig = request.headers.get("Wave-Signature", "")

    if settings.PAYMENT_WEBHOOK_SECRET:
        expected = hmac.new(
            settings.PAYMENT_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, wave_sig):
            raise HTTPException(status_code=401, detail="Signature Wave invalide.")

    import json
    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Corps JSON invalide.")

    if payload.get("type") != "checkout.completed":
        return {"ok": True, "ignored": True}

    data = payload.get("data", {})
    try:
        payment_id = int(data.get("client_reference", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="client_reference invalide.")

    payment = db.query(Payment).filter_by(id=payment_id, status="pending").first()
    if not payment:
        return {"ok": False, "detail": "Paiement déjà traité ou introuvable."}

    confirm_payment(db, payment, f"WAVE-{data.get('checkout_id', '')}")
    return {"ok": True, "message": "Paiement Wave confirmé."}


# ── Orange Money ─────────────────────────────────────────────────────────────────

@router.post("/webhook-orange-money")
async def orange_money_webhook(
    request: Request,
    x_orange_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Callback Orange Money — HMAC-SHA256 dans 'X-Orange-Signature'."""
    body = await request.body()

    if settings.PAYMENT_WEBHOOK_SECRET and x_orange_signature:
        expected = hmac.new(
            settings.PAYMENT_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, x_orange_signature):
            raise HTTPException(status_code=401, detail="Signature Orange Money invalide.")

    import json
    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Corps JSON invalide.")

    st = payload.get("status", "")
    notif_code = payload.get("notifCode", "")
    if not (st == "SUCCESSFULL" or notif_code == "60019001"):
        return {"ok": False, "status": st, "notifCode": notif_code}

    try:
        payment_id = int(payload.get("payToken", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="payToken invalide.")

    payment = db.query(Payment).filter_by(id=payment_id, status="pending").first()
    if not payment:
        return {"ok": False, "detail": "Paiement déjà traité ou introuvable."}

    confirm_payment(db, payment, f"OM-{payload.get('txnid', '')}")
    return {"ok": True, "message": "Paiement Orange Money confirmé."}
