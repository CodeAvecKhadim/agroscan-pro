"""
Logique métier activités agricoles.
Gère démarrage, clôture, calcul durée, validation rendement.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ferme import Activite, StatutActivite, TypeActivite, Cout, MainOeuvre


def demarrer_activite(
    db: Session,
    activite: Activite,
    conditions_meteo: dict,
    localisation_debut: dict,
) -> Activite:
    """Passe en EN_COURS, enregistre GPS + météo au démarrage."""
    if activite.statut == StatutActivite.ANNULE:
        from fastapi import HTTPException
        raise HTTPException(400, "Activité annulée, impossible de démarrer.")
    if activite.statut == StatutActivite.TERMINE:
        from fastapi import HTTPException
        raise HTTPException(400, "Activité déjà terminée.")

    activite.statut            = StatutActivite.EN_COURS
    activite.date_debut        = datetime.now(timezone.utc)
    activite.conditions_meteo  = conditions_meteo or {}
    activite.localisation_debut = localisation_debut or {}
    activite.updated_at        = datetime.now(timezone.utc)
    db.commit()
    db.refresh(activite)
    return activite


def terminer_activite(
    db: Session,
    activite: Activite,
    date_fin: datetime | None,
    duree_minutes: int | None,
    note: str | None,
    details_complementaires: dict | None,
) -> Activite:
    """Clôture l'activité, calcule la durée si non fournie."""
    now = datetime.now(timezone.utc)
    fin = date_fin or now

    activite.statut     = StatutActivite.TERMINE
    activite.date_fin   = fin
    activite.updated_at = now

    if duree_minutes:
        activite.duree_minutes = duree_minutes
    elif activite.date_debut:
        debut = activite.date_debut
        if debut.tzinfo is None:
            debut = debut.replace(tzinfo=timezone.utc)
        delta = fin.replace(tzinfo=timezone.utc) - debut
        activite.duree_minutes = max(1, int(delta.total_seconds() / 60))

    if note:
        activite.note = note

    if details_complementaires:
        merged = dict(activite.details or {})
        merged.update(details_complementaires)
        activite.details = merged

    db.commit()
    db.refresh(activite)
    return activite


def cout_total(db: Session, activite_id: int) -> int:
    """Somme coûts + main-d'œuvre pour une activité."""
    couts = db.query(Cout).filter_by(activite_id=activite_id).all()
    mo    = db.query(MainOeuvre).filter_by(activite_id=activite_id).all()
    return (
        sum(c.montant_total_fcfa or 0 for c in couts)
        + sum(m.montant_total_fcfa or 0 for m in mo)
    )


def ecart_rendement(rendement_reel: float, rendement_ref: float | None) -> float | None:
    """Écart rendement réel vs référence en %."""
    if rendement_ref and rendement_ref > 0:
        return round((rendement_reel - rendement_ref) / rendement_ref * 100, 1)
    return None
