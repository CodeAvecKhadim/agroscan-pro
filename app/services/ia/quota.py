"""
Gestion des quotas IA par plan.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ia import Conversation, StatutConversation
from app.schemas.ia import QuotaIA

LIMITES_PLAN: dict[str, dict] = {
    "gratuit": {
        "conv_mois":   3,
        "msg_conv":    10,
        "tokens_max":  1200,
        "modele":      "claude-haiku-4-5-20251001",
        "extraction":  False,
        "history_msgs": 6,
    },
    "premium": {
        "conv_mois":   None,
        "msg_conv":    50,
        "tokens_max":  2500,
        "modele":      "claude-sonnet-4-6",
        "extraction":  True,
        "history_msgs": 20,
    },
    "cooperative": {
        "conv_mois":   None,
        "msg_conv":    50,
        "tokens_max":  2500,
        "modele":      "claude-sonnet-4-6",
        "extraction":  True,
        "history_msgs": 20,
    },
}


def limites(plan: str) -> dict:
    return LIMITES_PLAN.get(plan, LIMITES_PLAN["gratuit"])


def mois_courant() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def nb_conversations_mois(db: Session, org_id: int, mois: Optional[str] = None) -> int:
    m = mois or mois_courant()
    return (db.query(Conversation)
            .filter_by(org_id=org_id, mois_periode=m)
            .filter(Conversation.statut != StatutConversation.ARCHIVEE)
            .count())


def verifier_quota_conversation(db: Session, org_id: int, plan: str) -> tuple[bool, str]:
    """Retourne (ok, raison)."""
    lim = limites(plan)
    if lim["conv_mois"] is None:
        return True, ""
    nb = nb_conversations_mois(db, org_id)
    if nb >= lim["conv_mois"]:
        return False, f"Quota atteint : {nb}/{lim['conv_mois']} conversations ce mois (plan {plan})"
    return True, ""


def verifier_quota_message(conv: Conversation, plan: str) -> tuple[bool, str]:
    """Retourne (ok, raison)."""
    lim = limites(plan)
    if conv.nb_messages >= lim["msg_conv"]:
        return False, f"Quota atteint : {conv.nb_messages}/{lim['msg_conv']} messages (plan {plan})"
    return True, ""


def quota_ia(db: Session, org_id: int, plan: str) -> QuotaIA:
    lim = limites(plan)
    nb  = nb_conversations_mois(db, org_id)
    limite = lim["conv_mois"]
    return QuotaIA(
        plan=plan,
        conv_mois_utilisees=nb,
        conv_mois_limite=limite,
        conv_restantes=(limite - nb) if limite is not None else None,
        modele=lim["modele"],
    )
