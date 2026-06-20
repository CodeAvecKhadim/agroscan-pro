"""
Router Observations Terrain — /api/observations-terrain
Stocke les observations déclaratives producteur (irrigation, pluie, feuilles, ravageurs, maladies).
Alimentent le contexte IA Polélé pour croisement satellite + météo + terrain.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.models.observations_terrain import ObservationTerrain

router = APIRouter(prefix="/api/observations-terrain", tags=["Observations Terrain"])


# ── Schémas ──────────────────────────────────────────────────────────────────

class ObservationTerrainCreate(BaseModel):
    parcelle_id:           Optional[int]  = None
    date_observation:      Optional[date] = None
    irrigation_effectuee:  Optional[bool] = None
    pluie_observee:        Optional[bool] = None
    etat_feuilles:         Optional[str]  = Field(None, max_length=30)
    ravageurs_observes:    Optional[bool] = None
    maladie_observee:      Optional[bool] = None
    confiance_observation: Optional[str]  = Field("moyen", pattern="^(faible|moyen|élevé|eleve)$")
    notes:                 Optional[str]  = Field(None, max_length=1000)


class ObservationTerrainOut(BaseModel):
    id:                    int
    parcelle_id:           Optional[int]
    date_observation:      date
    irrigation_effectuee:  Optional[bool]
    pluie_observee:        Optional[bool]
    etat_feuilles:         Optional[str]
    ravageurs_observes:    Optional[bool]
    maladie_observee:      Optional[bool]
    confiance_observation: Optional[str]
    notes:                 Optional[str]
    created_at:            datetime

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ObservationTerrainOut, status_code=201,
             summary="Créer une observation terrain")
def creer_observation(
    body: ObservationTerrainCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    obs = ObservationTerrain(
        org_id               = user.org_id,
        user_id              = user.id,
        parcelle_id          = body.parcelle_id,
        date_observation     = body.date_observation or date.today(),
        irrigation_effectuee = body.irrigation_effectuee,
        pluie_observee       = body.pluie_observee,
        etat_feuilles        = body.etat_feuilles,
        ravageurs_observes   = body.ravageurs_observes,
        maladie_observee     = body.maladie_observee,
        confiance_observation= body.confiance_observation or "moyen",
        notes                = body.notes,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.get("", response_model=list[ObservationTerrainOut],
            summary="Lister les observations terrain (7 derniers jours)")
def lister_observations(
    parcelle_id: Optional[int] = Query(None),
    jours:       int           = Query(7, ge=1, le=90),
    db:          Session       = Depends(get_db),
    user:        User          = Depends(current_user),
):
    depuis = date.today() - timedelta(days=jours)
    q = (db.query(ObservationTerrain)
         .filter(ObservationTerrain.org_id == user.org_id,
                 ObservationTerrain.date_observation >= depuis)
         .order_by(ObservationTerrain.date_observation.desc()))
    if parcelle_id:
        q = q.filter(ObservationTerrain.parcelle_id == parcelle_id)
    return q.limit(50).all()
