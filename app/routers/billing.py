"""
Routeur des abonnements et de la facturation.
- GET  /api/billing/plans   : grille tarifaire (prix TTC, TVA 18 %).
- GET  /api/billing/me      : abonnement + consommation courante.
- POST /api/billing/change  : changer de plan (renvoie l'instruction de paiement).
- POST /api/billing/webhook : confirmation de paiement par le PSP (Wave/OM/PayDunya).
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import current_user, current_subscription, require_role, get_usage
from app.models import User, Subscription, Payment, PlanType, UserRole
from app.schemas import SubscriptionOut, ChangePlanIn, UsageOut
from app.services.plans import PLAN_FEATURES, price_ttc, features_for
from app.services.subscription import change_plan, confirm_payment

router = APIRouter(prefix="/api/billing", tags=["Abonnements"])


@router.get("/plans")
def list_plans():
    """Grille des offres avec prix TTC en FCFA — pour la page tarifs."""
    out = []
    for plan, feats in PLAN_FEATURES.items():
        out.append({
            "plan": plan.value,
            "label": feats["label"],
            "pricing": price_ttc(plan),
            "monthly_analyses": feats["monthly_analyses"],
            "history_days": feats["history_days"],
            "pdf_reports": feats["pdf_reports"],
            "advanced_reco": feats["advanced_reco"],
            "whatsapp_support": feats["whatsapp_support"],
            "multi_user": feats["multi_user"],
            "max_seats": feats["max_seats"],
        })
    return {"currency": settings.CURRENCY, "vat_rate": settings.VAT_RATE, "plans": out}


@router.get("/me", response_model=SubscriptionOut)
def my_subscription(sub: Subscription = Depends(current_subscription)):
    """Abonnement courant de l'organisation."""
    return sub


@router.get("/usage", response_model=UsageOut)
def my_usage(user: User = Depends(current_user),
             sub: Subscription = Depends(current_subscription),
             db: Session = Depends(get_db)):
    """Consommation du mois + limites du plan (pour afficher '2/3 analyses utilisées')."""
    uc = get_usage(db, user.org_id)
    feats = features_for(sub.plan)
    return UsageOut(
        period=uc.period,
        analyses_used=uc.analyses_count,
        analyses_limit=feats["monthly_analyses"],
        history_days=feats["history_days"],
        plan=sub.plan,
    )


@router.post("/change")
def change_subscription(
    data: ChangePlanIn,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),  # seuls owner/admin
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """Change de plan. Renvoie l'instruction de paiement pour les plans payants."""
    return change_plan(db, sub, data.plan, data.seats)


@router.post("/webhook")
def payment_webhook(
    payload: dict,
    x_webhook_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """
    Endpoint appelé par le fournisseur de paiement après un règlement réussi.
    Sécurisé par un secret partagé. Corps attendu :
      {"payment_id": 12, "provider_ref": "WAVE-XYZ", "status": "paid"}
    """
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
