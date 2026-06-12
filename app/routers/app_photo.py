"""
Router Photo — envoi photo + diagnostic Kindwise + stockage observation.
Préfixe : /api/app

Endpoints :
  POST /photo                      → Upload photo + diagnostic + enregistrement
  GET  /observations               → Liste observations de l'org
  PATCH /observations/{id}/valider → Validation conseiller
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user, require_profil
from app.models import User
from app.models.champ import Parcelle
from app.models.observations import ObservationDiagnostic as Observation
from app.services.crop_health import identifier_maladie, CropHealthError
from app.services.sante.upload import save_photo
from app.services.diagnostic_simple import phrase_etat
from app.core.config import settings

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/app", tags=["Photo & Observations"])


class ObservationOut(BaseModel):
    id: int
    parcelle_id: Optional[int] = None
    parcelle_nom: Optional[str] = None
    type: str
    chemin: Optional[str] = None
    etat_simple: Optional[str] = None
    anomalie: bool
    validation_conseiller: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ValiderRequest(BaseModel):
    commentaire: str


@router.post("/photo", response_model=ObservationOut, status_code=201)
async def envoyer_photo(
    photo: UploadFile = File(...),
    parcelle_id: Optional[int] = Form(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Envoie une photo, effectue le diagnostic Kindwise, enregistre l'observation."""
    # Vérifier parcelle si fournie
    parcelle_nom = None
    if parcelle_id:
        p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Parcelle introuvable.")
        parcelle_nom = p.nom

    # Sauvegarder la photo
    try:
        upload = await save_photo(photo, "observation")
    except HTTPException:
        raise

    # Diagnostic Kindwise (facultatif — fallback si clé absente)
    diagnostic = None
    if settings.CROP_HEALTH_API_KEY:
        try:
            import httpx
            # Relire le fichier depuis le disque pour Kindwise
            from pathlib import Path
            chemin_fichier = Path("/opt/agroscan/uploads/observations") / upload["filename"]
            contenu = chemin_fichier.read_bytes()
            diagnostic = identifier_maladie(contenu, langue="fr")
        except CropHealthError as e:
            log.warning("Kindwise error: %s", e)
        except Exception as e:
            log.error("Photo diagnostic error: %s", e)

    etat_simple, anomalie = phrase_etat(diagnostic)

    obs = Observation(
        org_id=user.org_id,
        parcelle_id=parcelle_id,
        user_id=user.id,
        type="photo",
        chemin=upload["url"],
        diagnostic=diagnostic,
        etat_simple=etat_simple,
        anomalie=anomalie,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)

    return ObservationOut(
        id=obs.id,
        parcelle_id=obs.parcelle_id,
        parcelle_nom=parcelle_nom,
        type=obs.type,
        chemin=obs.chemin,
        etat_simple=obs.etat_simple,
        anomalie=obs.anomalie,
        validation_conseiller=obs.validation_conseiller,
        created_at=obs.created_at,
    )


@router.get("/observations", response_model=list[ObservationOut])
def lister_observations(
    parcelle_id: Optional[int] = None,
    anomalie_seulement: bool = False,
    limit: int = 50,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Liste les observations de l'organisation."""
    q = db.query(Observation).filter(Observation.org_id == user.org_id)
    if parcelle_id:
        q = q.filter(Observation.parcelle_id == parcelle_id)
    if anomalie_seulement:
        q = q.filter(Observation.anomalie == True)  # noqa: E712

    obs_list = q.order_by(Observation.created_at.desc()).limit(limit).all()

    # Noms parcelles
    ids = {o.parcelle_id for o in obs_list if o.parcelle_id}
    noms = {}
    if ids:
        rows = db.query(Parcelle.id, Parcelle.nom).filter(Parcelle.id.in_(ids)).all()
        noms = {r.id: r.nom for r in rows}

    return [
        ObservationOut(
            id=o.id,
            parcelle_id=o.parcelle_id,
            parcelle_nom=noms.get(o.parcelle_id),
            type=o.type,
            chemin=o.chemin,
            etat_simple=o.etat_simple,
            anomalie=o.anomalie,
            validation_conseiller=o.validation_conseiller,
            created_at=o.created_at,
        )
        for o in obs_list
    ]


@router.patch("/observations/{obs_id}/valider", response_model=ObservationOut)
def valider_observation(
    obs_id: int,
    req: ValiderRequest,
    user: User = Depends(require_profil("conseiller", "admin")),
    db: Session = Depends(get_db),
):
    """Conseiller/admin valide ou commente une observation."""
    obs = db.query(Observation).filter_by(id=obs_id, org_id=user.org_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation introuvable.")

    obs.validation_conseiller = req.commentaire
    db.commit()
    db.refresh(obs)

    parcelle_nom = None
    if obs.parcelle_id:
        p = db.query(Parcelle).filter_by(id=obs.parcelle_id).first()
        parcelle_nom = p.nom if p else None

    return ObservationOut(
        id=obs.id,
        parcelle_id=obs.parcelle_id,
        parcelle_nom=parcelle_nom,
        type=obs.type,
        chemin=obs.chemin,
        etat_simple=obs.etat_simple,
        anomalie=obs.anomalie,
        validation_conseiller=obs.validation_conseiller,
        created_at=obs.created_at,
    )
