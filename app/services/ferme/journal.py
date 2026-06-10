"""
Journal numérique — timeline mixte activités + notes libres.
"""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.models.ferme import Activite, JournalEntree


def journal_parcelle(
    db: Session,
    org_id: int,
    parcelle_id: Optional[int] = None,
    type_filtre: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[JournalEntree]:
    """Timeline notes libres d'une parcelle ou de toute l'org."""
    q = db.query(JournalEntree).filter_by(org_id=org_id)
    if parcelle_id:
        q = q.filter(JournalEntree.parcelle_id == parcelle_id)
    if type_filtre:
        q = q.filter(JournalEntree.type == type_filtre)
    return q.order_by(JournalEntree.date_entree.desc()).offset(offset).limit(limit).all()


def activites_journal(
    db: Session,
    org_id: int,
    parcelle_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Activite]:
    """Activités triées chronologiquement pour le journal."""
    q = (db.query(Activite)
         .options(
             selectinload(Activite.preuves),
             selectinload(Activite.couts),
             selectinload(Activite.main_oeuvre),
         )
         .filter_by(org_id=org_id))
    if parcelle_id:
        q = q.filter(Activite.parcelle_id == parcelle_id)
    return q.order_by(Activite.date_prevue.desc()).offset(offset).limit(limit).all()
