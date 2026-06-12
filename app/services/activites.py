"""
Génération automatique d'activités depuis le calendrier cultural.
Crée des entrées dans gf_activites à partir de culture + date_semis.
"""
from datetime import date, datetime, timezone
import logging

from sqlalchemy.orm import Session

from app.models.ferme import Activite, TypeActivite, StatutActivite
from app.services.calendrier import generer_calendrier

log = logging.getLogger(__name__)

# Correspondance titre étape → type d'activité
_TITRE_TYPE: dict[str, TypeActivite] = {
    "Semis direct":              TypeActivite.SEMIS,
    "Semis en pépinière":        TypeActivite.SEMIS,
    "Repiquage au champ":        TypeActivite.PLANTATION,
    "Levée & démariage":         TypeActivite.DESHERBAGE,
    "Apport d'engrais":          TypeActivite.FERTILISATION,
    "Surveillance sanitaire":    TypeActivite.TRAITEMENT,
    "Phase critique en eau":     TypeActivite.IRRIGATION,
    "Début de récolte possible": TypeActivite.RECOLTE,
    "Fin de récolte estimée":    TypeActivite.RECOLTE,
    "Plantation":                TypeActivite.PLANTATION,
    "Reprise & arrosage":        TypeActivite.IRRIGATION,
    "Premier entretien":         TypeActivite.DESHERBAGE,
    "Suivi sanitaire":           TypeActivite.TRAITEMENT,
    "Entrée en production":      TypeActivite.RECOLTE,
}


def statut_simple(activite: Activite) -> str:
    """Statut simplifié pour le producteur : prevu | realise | en_retard."""
    if activite.statut == StatutActivite.TERMINE:
        return "realise"
    if activite.date_prevue and activite.date_prevue < date.today():
        return "en_retard"
    return "prevu"


def generer_activites_calendrier(
    db: Session,
    parcelle_id: int,
    org_id: int,
    culture: str,
    date_semis: date,
    created_by_id: int | None = None,
) -> list[Activite]:
    """Crée les activités d'une saison depuis le calendrier cultural.

    Idempotent : ne crée pas de doublon si activité même type + même date existe déjà.
    """
    cal = generer_calendrier(culture, date_semis)
    if "error" in cal:
        log.warning("Calendrier introuvable pour culture=%s", culture)
        return []

    # Activités existantes pour cette parcelle (pour éviter doublons)
    existantes = db.query(Activite).filter_by(
        parcelle_id=parcelle_id, org_id=org_id
    ).all()
    cles_existantes = {
        (a.type, a.date_prevue) for a in existantes
    }

    creees: list[Activite] = []
    for etape in cal.get("etapes", []):
        titre = etape["titre"]
        type_act = _TITRE_TYPE.get(titre, TypeActivite.AUTRE)
        date_prevue = date.fromisoformat(etape["date"])

        if (type_act, date_prevue) in cles_existantes:
            continue

        statut = StatutActivite.PLANIFIE
        activite = Activite(
            org_id=org_id,
            parcelle_id=parcelle_id,
            type=type_act,
            statut=statut,
            titre=f"{etape['icone']} {titre}",
            description=etape.get("detail"),
            date_prevue=date_prevue,
            created_by=created_by_id,
        )
        db.add(activite)
        creees.append(activite)
        cles_existantes.add((type_act, date_prevue))

    if creees:
        db.commit()
        log.info("Générées %d activités pour parcelle %d culture=%s", len(creees), parcelle_id, culture)

    return creees
