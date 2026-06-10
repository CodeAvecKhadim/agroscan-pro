"""
Extraction de recommandations structurées depuis une réponse IA.
Plan premium : extraction via Claude (haiku).
Plan gratuit  : extraction par regex/marqueurs simples.
"""
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ia import CategorieReco, RecommandationIA, StatutReco
from app.schemas.ia import ContexteAgro
from app.services.ia import llm_provider
from app.services.ia.system_prompt import build_prompt_extraction

log = logging.getLogger(__name__)

_MOTS_URGENT = ["urgence", "urgent", "immédiat", "sans délai", "aujourd'hui", "maintenant"]
_CATEGORIES_MOTS = {
    CategorieReco.MALADIE:       ["maladie", "pathogène", "champignon", "bactér", "virus", "pyriculariose", "cercosporiose", "traitement", "fongicide"],
    CategorieReco.RAVAGEUR:      ["ravageur", "insecte", "parasite", "puceron", "criquet", "foreur", "aleurode", "nématode"],
    CategorieReco.FERTILISATION: ["fertilisa", "engrais", "azote", "phosphore", "potassium", "urée", "npk", "carence", "amendement"],
    CategorieReco.IRRIGATION:    ["irrigation", "arrosage", "eau", "irrigu", "sécheresse", "stress hydrique"],
    CategorieReco.SOL:           ["sol", "ph", "texture", "structure", "labour", "amendement organique", "compost"],
    CategorieReco.CALENDRIER:    ["semis", "plantation", "récolte", "date", "période", "calendrier", "stade"],
    CategorieReco.RECOLTE:       ["récolte", "rendement", "maturité", "battre", "stocker"],
}


def extraire_recommandations(
    db: Session,
    conversation_id: int,
    message_id: int,
    org_id: int,
    texte_reponse: str,
    ctx: ContexteAgro,
    plan: str,
    parcelle_id: Optional[int] = None,
    culture_id: Optional[int] = None,
) -> list[RecommandationIA]:
    """
    Extrait les recommandations structurées d'une réponse IA.
    Premium : via Claude haiku
    Gratuit  : regex sur marqueurs RECOMMANDATION:/ACTION:/POURQUOI:
    """
    recs = []

    if plan != "gratuit" and llm_provider.disponible():
        recs = _extraire_via_llm(db, conversation_id, message_id, org_id,
                                  texte_reponse, parcelle_id, culture_id)
    else:
        recs = _extraire_via_regex(db, conversation_id, message_id, org_id,
                                    texte_reponse, parcelle_id, culture_id)

    return recs


def _extraire_via_llm(
    db: Session,
    conversation_id: int,
    message_id: int,
    org_id: int,
    texte: str,
    parcelle_id: Optional[int],
    culture_id: Optional[int],
) -> list[RecommandationIA]:
    """Extraction LLM — retourne list[RecommandationIA] persistées."""
    system = build_prompt_extraction()
    raw = llm_provider.chat_extraction(texte, system)
    if not raw or not isinstance(raw, list):
        return []

    recs = []
    for item in raw[:8]:  # max 8 recommandations par réponse
        if not isinstance(item, dict):
            continue
        titre = (item.get("titre") or "")[:200]
        action = item.get("action") or ""
        if not titre or not action:
            continue

        categorie_str = item.get("categorie", "general")
        try:
            categorie = CategorieReco(categorie_str)
        except ValueError:
            categorie = CategorieReco.GENERAL

        priorite = int(item.get("priorite") or 3)
        priorite = max(1, min(5, priorite))
        confiance = float(item.get("confiance") or 0.7)
        confiance = max(0.0, min(1.0, confiance))

        rec = RecommandationIA(
            org_id=org_id,
            conversation_id=conversation_id,
            message_id=message_id,
            parcelle_id=parcelle_id,
            culture_id=culture_id,
            categorie=categorie,
            priorite=priorite,
            titre=titre,
            action=action,
            justification=item.get("justification"),
            echeance_jours=item.get("echeance_jours"),
            confiance=confiance,
            statut=StatutReco.NOUVELLE,
        )
        db.add(rec)
        recs.append(rec)

    if recs:
        db.commit()
        for r in recs:
            db.refresh(r)

    return recs


def _extraire_via_regex(
    db: Session,
    conversation_id: int,
    message_id: int,
    org_id: int,
    texte: str,
    parcelle_id: Optional[int],
    culture_id: Optional[int],
) -> list[RecommandationIA]:
    """
    Extraction légère basée sur le format structuré du prompt :
    RECOMMANDATION : ...
    ACTION : ...
    POURQUOI : ...
    DÉLAI : ...
    """
    pattern = re.compile(
        r"RECOMMANDATION\s*:\s*(?P<titre>[^\n]+)\n"
        r"ACTION\s*:\s*(?P<action>[^\n]+(?:\n(?!POURQUOI|DÉLAI|RECOMMANDATION)[^\n]+)*)\n?"
        r"(?:POURQUOI\s*:\s*(?P<justification>[^\n]+(?:\n(?!DÉLAI|RECOMMANDATION)[^\n]+)*)\n?)?"
        r"(?:DÉLAI\s*:\s*(?P<delai>[^\n]+))?",
        re.IGNORECASE,
    )

    recs = []
    for m in pattern.finditer(texte):
        titre = (m.group("titre") or "").strip()[:200]
        action = (m.group("action") or "").strip()
        if not titre:
            continue

        justification = (m.group("justification") or "").strip() or None
        delai_str = (m.group("delai") or "").strip()
        echeance = _parse_delai(delai_str)
        categorie = _detecter_categorie(titre + " " + action)
        priorite = 1 if any(u in (titre + action).lower() for u in _MOTS_URGENT) else 3

        rec = RecommandationIA(
            org_id=org_id,
            conversation_id=conversation_id,
            message_id=message_id,
            parcelle_id=parcelle_id,
            culture_id=culture_id,
            categorie=categorie,
            priorite=priorite,
            titre=titre,
            action=action,
            justification=justification,
            echeance_jours=echeance,
            confiance=0.6,
            statut=StatutReco.NOUVELLE,
        )
        db.add(rec)
        recs.append(rec)

    if recs:
        db.commit()
        for r in recs:
            db.refresh(r)

    return recs


def _detecter_categorie(texte: str) -> CategorieReco:
    texte_lower = texte.lower()
    for cat, mots in _CATEGORIES_MOTS.items():
        if any(m in texte_lower for m in mots):
            return cat
    return CategorieReco.GENERAL


def _parse_delai(delai_str: str) -> Optional[int]:
    if not delai_str:
        return None
    nombres = re.findall(r"\d+", delai_str)
    if nombres:
        return int(nombres[0])
    mots = delai_str.lower()
    if "aujourd" in mots or "immédiat" in mots:
        return 0
    if "demain" in mots:
        return 1
    if "semaine" in mots:
        return 7
    if "mois" in mots:
        return 30
    return None
