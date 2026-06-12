"""
Router Activités — vue simplifiée producteur.
Préfixe : /api/app/activites

Endpoints :
  GET  /                        → Liste activités (statut simplifié)
  POST /{id}/realiser            → Marquer réalisé
  POST /generer/{parcelle_id}    → Générer depuis calendrier
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.models.champ import Parcelle
from app.models.ferme import Activite, StatutActivite
from app.services.activites import generer_activites_calendrier, statut_simple

router = APIRouter(prefix="/api/app/activites", tags=["Activités producteur"])


class ActiviteSimple(BaseModel):
    id: int
    titre: str
    type: str
    date_prevue: Optional[date]
    statut_simple: str
    parcelle_nom: Optional[str] = None
    parcelle_id: Optional[int] = None
    icone: str

    model_config = {"from_attributes": True}


class RealiserRequest(BaseModel):
    note: Optional[str] = None


def _icone(statut: str) -> str:
    return {"realise": "✅", "en_retard": "🔴", "prevu": "🟡"}.get(statut, "🟡")


@router.get("", response_model=list[ActiviteSimple])
def lister_activites(
    parcelle_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Liste les activités du producteur avec statut simplifié."""
    q = db.query(Activite).filter(
        Activite.org_id == user.org_id,
        Activite.statut != StatutActivite.ANNULE,
    )
    if parcelle_id:
        q = q.filter(Activite.parcelle_id == parcelle_id)

    activites = q.order_by(Activite.date_prevue.asc()).limit(limit).all()

    # Récupérer noms parcelles en une requête
    parcel_ids = {a.parcelle_id for a in activites if a.parcelle_id}
    parcelles = {}
    if parcel_ids:
        rows = db.query(Parcelle.id, Parcelle.nom).filter(Parcelle.id.in_(parcel_ids)).all()
        parcelles = {r.id: r.nom for r in rows}

    result = []
    for a in activites:
        s = statut_simple(a)
        result.append(ActiviteSimple(
            id=a.id,
            titre=a.titre,
            type=a.type.value,
            date_prevue=a.date_prevue,
            statut_simple=s,
            parcelle_nom=parcelles.get(a.parcelle_id),
            parcelle_id=a.parcelle_id,
            icone=_icone(s),
        ))
    return result


@router.post("/{activite_id}/realiser", response_model=ActiviteSimple)
def marquer_realise(
    activite_id: int,
    req: RealiserRequest = RealiserRequest(),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Marque une activité comme réalisée."""
    a = db.query(Activite).filter_by(id=activite_id, org_id=user.org_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Activité introuvable.")

    a.statut = StatutActivite.TERMINE
    a.date_fin = datetime.now(timezone.utc)
    if req.note:
        a.note = req.note
    a.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(a)

    parcelle_nom = None
    if a.parcelle_id:
        p = db.query(Parcelle).filter_by(id=a.parcelle_id).first()
        parcelle_nom = p.nom if p else None

    s = statut_simple(a)
    return ActiviteSimple(
        id=a.id, titre=a.titre, type=a.type.value,
        date_prevue=a.date_prevue, statut_simple=s,
        parcelle_nom=parcelle_nom, parcelle_id=a.parcelle_id,
        icone=_icone(s),
    )


@router.post("/generer/{parcelle_id}")
def generer_activites(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Génère les activités depuis le calendrier cultural de la parcelle."""
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    if not p.type_culture or not p.date_semis:
        raise HTTPException(status_code=400, detail="Culture et date de semis requis.")

    creees = generer_activites_calendrier(
        db=db, parcelle_id=p.id, org_id=user.org_id,
        culture=p.type_culture, date_semis=p.date_semis,
        created_by_id=user.id,
    )
    return {"message": f"{len(creees)} activité(s) générée(s).", "count": len(creees)}
