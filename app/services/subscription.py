"""
Service de gestion des abonnements AgroScan Pro.

Modèle économique :
  GRATUIT     : plan permanent, pas d'expiration
  PREMIUM     : campagne 90 jours (14 900 FCFA)
  COOPERATIVE : mensuel (25 000 FCFA) ou annuel (250 000 FCFA)
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Subscription, Payment, PlanType, SubStatus, Organization
from app.services.plans import features_for, price_ttc
from app.core.config import settings


def create_default_subscription(db: Session, org: Organization) -> Subscription:
    """À l'inscription, toute organisation démarre sur le plan GRATUIT actif."""
    sub = Subscription(
        org_id=org.id,
        plan=PlanType.GRATUIT,
        status=SubStatus.ACTIVE,
        seats=1,
        auto_renew=False,
        campaign_billing="monthly",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def change_plan(db: Session, sub: Subscription, plan: PlanType,
                seats: int = 1, billing: str = "monthly") -> dict:
    """
    Change le plan d'une organisation.
    - Vers GRATUIT : effet immédiat.
    - PREMIUM : campagne 90 jours, paiement unique 14 900 FCFA.
    - COOPERATIVE : mensuel ou annuel selon `billing`.
    """
    feats = features_for(plan)
    seats = max(1, min(seats, feats["max_seats"]))

    if plan == PlanType.GRATUIT:
        sub.plan = PlanType.GRATUIT
        sub.status = SubStatus.ACTIVE
        sub.seats = 1
        sub.current_period_end = None
        sub.auto_renew = False
        sub.campaign_billing = "monthly"
        db.commit()
        return {"plan": plan.value, "status": "active", "payment": None}

    pricing = price_ttc(plan, billing=billing)
    total_ht = pricing["ht"]
    vat = pricing["vat"]
    total_ttc = pricing["ttc"]

    payment = Payment(
        subscription_id=sub.id,
        provider=settings.PAYMENT_PROVIDER,
        amount_ht=total_ht,
        vat=vat,
        amount_ttc=total_ttc,
        status="pending",
    )
    sub.plan = plan
    sub.seats = seats
    sub.status = SubStatus.PAST_DUE
    sub.campaign_billing = billing if plan == PlanType.COOPERATIVE else "campaign"
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
            "billing": pricing["billing"],
            "instruction": _payment_instruction(plan, total_ttc, billing),
        },
    }


def confirm_payment(db: Session, payment: Payment, provider_ref: str = "") -> Subscription:
    """
    Confirme un paiement (webhook PSP).
    Active l'abonnement et calcule la date d'expiration selon le plan :
      - PREMIUM     : +90 jours (campagne agricole)
      - COOPERATIVE mensuel : +30 jours
      - COOPERATIVE annuel  : +365 jours
    """
    payment.status = "paid"
    payment.provider_ref = provider_ref
    sub = payment.subscription
    sub.status = SubStatus.ACTIVE

    now = datetime.now(timezone.utc)
    base = sub.current_period_end or now
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    if base < now:
        base = now

    if sub.plan == PlanType.PREMIUM:
        duration = settings.PRICE_PREMIUM_DURATION_DAYS  # 90 jours
    elif sub.plan == PlanType.COOPERATIVE and sub.campaign_billing == "annual":
        duration = 365
    else:
        duration = 30  # coopérative mensuelle

    sub.current_period_end = base + timedelta(days=duration)
    db.commit()
    db.refresh(sub)
    return sub


def remaining_campaign_days(sub: Subscription) -> int | None:
    """Jours restants sur la campagne / période payée. None pour GRATUIT."""
    if sub.plan == PlanType.GRATUIT:
        return None
    end = sub.current_period_end
    if end is None:
        return None
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    delta = end - datetime.now(timezone.utc)
    return max(0, delta.days)


def history_cutoff(plan: PlanType):
    """Date la plus ancienne consultable selon le plan."""
    from datetime import timedelta
    days = features_for(plan)["history_days"]
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


def _payment_instruction(plan: PlanType, ttc: int, billing: str = "monthly") -> str:
    """Message d'instruction de paiement."""
    prov = settings.PAYMENT_PROVIDER
    if plan == PlanType.PREMIUM:
        label = f"{ttc:,} FCFA pour votre campagne agricole (3 mois)"
    elif billing == "annual":
        label = f"{ttc:,} FCFA pour 1 an"
    else:
        label = f"{ttc:,} FCFA/mois"

    if prov == "wave":
        return f"Payez {label} via Wave. La validation est automatique."
    if prov == "orange_money":
        return f"Composez le code Orange Money et payez {label}."
    if prov == "paydunya":
        return f"Vous allez être redirigé vers PayDunya pour régler {label}."
    return (f"Paiement manuel : envoyez {label} puis contactez Social Technologie "
            f"({settings.CONTACT_PHONE}) pour activation.")
