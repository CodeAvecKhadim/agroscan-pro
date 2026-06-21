"""
Service de gestion des abonnements.
Centralise la logique métier : changer de plan, enregistrer un paiement (TVA 18 %),
calculer la fenêtre d'historique consultable selon le plan.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import (Subscription, Payment, PlanType, SubStatus, Organization)
from app.services.plans import features_for, price_ttc
from app.core.config import settings


def create_default_subscription(db: Session, org: Organization) -> Subscription:
    """À l'inscription, toute organisation démarre sur le plan GRATUIT actif."""
    sub = Subscription(org_id=org.id, plan=PlanType.GRATUIT,
                       status=SubStatus.ACTIVE, seats=1, auto_renew=False)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def change_plan(db: Session, sub: Subscription, plan: PlanType, seats: int = 1) -> dict:
    """
    Change le plan d'une organisation.
    - Vers GRATUIT : effet immédiat, pas de paiement.
    - Vers un plan payant : crée un paiement en attente (à confirmer par le PSP),
      puis active l'abonnement une fois le paiement confirmé via le webhook.
    Renvoie les infos de paiement à présenter à l'utilisateur.
    """
    feats = features_for(plan)
    seats = max(1, min(seats, feats["max_seats"]))

    if plan == PlanType.GRATUIT:
        sub.plan = PlanType.GRATUIT
        sub.status = SubStatus.ACTIVE
        sub.seats = 1
        sub.current_period_end = None
        sub.auto_renew = False
        db.commit()
        return {"plan": plan.value, "status": "active", "payment": None}

    pricing = price_ttc(plan)
    # Pour la coopérative, on facture par siège supplémentaire au-delà du 1er.
    total_ht = pricing["ht"] * (seats if plan == PlanType.COOPERATIVE else 1)
    vat = round(total_ht * settings.VAT_RATE)
    total_ttc = total_ht + vat

    payment = Payment(
        subscription_id=sub.id,
        provider=settings.PAYMENT_PROVIDER,
        amount_ht=total_ht, vat=vat, amount_ttc=total_ttc,
        status="pending",
    )
    sub.plan = plan
    sub.seats = seats
    sub.status = SubStatus.PAST_DUE   # devient ACTIVE après confirmation du paiement
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "plan": plan.value,
        "status": sub.status.value,
        "payment": {
            "id": payment.id,
            "amount_ht": total_ht,
            "vat": vat,
            "amount_ttc": total_ttc,
            "currency": settings.CURRENCY,
            "provider": settings.PAYMENT_PROVIDER,
            "instruction": _payment_instruction(total_ttc),
        },
    }


def confirm_payment(db: Session, payment: Payment, provider_ref: str = "") -> Subscription:
    """
    Confirme un paiement (appelé par le webhook du PSP).
    Active l'abonnement et prolonge la période d'un mois.
    """
    payment.status = "paid"
    payment.provider_ref = provider_ref
    sub = payment.subscription
    sub.status = SubStatus.ACTIVE
    base = sub.current_period_end or datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    if base < datetime.now(timezone.utc):
        base = datetime.now(timezone.utc)
    sub.current_period_end = base + timedelta(days=30)
    db.commit()
    db.refresh(sub)
    return sub


def history_cutoff(plan: PlanType):
    """
    Date la plus ancienne consultable selon le plan.
    Plan gratuit : 30 derniers jours. Plans payants : None (tout l'historique).
    """
    days = features_for(plan)["history_days"]
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


def _payment_instruction(ttc: int) -> str:
    """Message d'instruction de paiement selon le fournisseur configuré."""
    prov = settings.PAYMENT_PROVIDER
    if prov == "wave":
        return f"Payez {ttc} FCFA via Wave puis confirmez. La validation est automatique."
    if prov == "orange_money":
        return f"Composez le code Orange Money et payez {ttc} FCFA."
    if prov == "paydunya":
        return f"Vous allez être redirigé vers PayDunya pour régler {ttc} FCFA."
    return (f"Paiement manuel : envoyez {ttc} FCFA puis contactez Social Technologie "
            f"({settings.CONTACT_PHONE}) pour activation.")
