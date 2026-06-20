"""
Router Photo — envoi photo(s) + diagnostic Kindwise + stockage observation.
Préfixe : /api/app

Endpoints :
  POST /photo                      → Upload 1–5 photos + diagnostic + enregistrement
  GET  /observations               → Liste observations de l'org
  GET  /observations/{id}          → Détail diagnostic (avec maladies/certitudes)
  PATCH /observations/{id}/valider → Validation conseiller
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user, require_profil
from app.models import User
from app.models.champ import Parcelle, StatutParcelle, Cartographie
from app.models.observations import ObservationDiagnostic as Observation
from app.services.crop_health import identifier_maladie, CropHealthError
from app.services.sante.upload import save_photo
from app.services.diagnostic_simple import phrase_etat
from app.core.config import settings

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/app", tags=["Photo & Observations"])


def _get_parcelle_gps(
    db: Session,
    parcelle_id: int,
    org_id: int,
) -> tuple[Optional[float], Optional[float]]:
    """
    Retourne (centre_lat, centre_lon) d'une parcelle active.

    Priorité :
      1. Champs centre_lat / centre_lon déjà calculés sur la parcelle.
      2. Fallback : centroïde calculé depuis la cartographie active.
      3. (None, None) si la parcelle n'a pas de données GPS ou est archivée.
    """
    try:
        p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=org_id).first()
        if not p or p.statut == StatutParcelle.ARCHIVE:
            return None, None

        if p.centre_lat is not None and p.centre_lon is not None:
            return float(p.centre_lat), float(p.centre_lon)

        # Fallback : calculer depuis le polygone
        carto = (
            db.query(Cartographie)
            .filter_by(parcelle_id=parcelle_id, actif=True)
            .first()
        )
        if carto and carto.coordonnees and len(carto.coordonnees) >= 3:
            from app.services.geo import centroide
            lat, lon = centroide(carto.coordonnees)
            return float(lat), float(lon)

    except Exception as e:
        log.warning("GPS parcelle %s indisponible : %s", parcelle_id, e)

    return None, None


class ObservationOut(BaseModel):
    id: int
    parcelle_id: Optional[int] = None
    parcelle_nom: Optional[str] = None
    type: str
    chemin: Optional[str] = None
    etat_simple: Optional[str] = None
    anomalie: bool
    validation_conseiller: Optional[str] = None
    diagnostic: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ValiderRequest(BaseModel):
    commentaire: str


def _obs_to_out(obs: Observation, parcelle_nom: Optional[str] = None) -> ObservationOut:
    return ObservationOut(
        id=obs.id,
        parcelle_id=obs.parcelle_id,
        parcelle_nom=parcelle_nom,
        type=obs.type,
        chemin=obs.chemin,
        etat_simple=obs.etat_simple,
        anomalie=obs.anomalie,
        validation_conseiller=obs.validation_conseiller,
        diagnostic=obs.diagnostic,
        created_at=obs.created_at,
    )


@router.post("/photo", response_model=ObservationOut, status_code=201)
async def envoyer_photo(
    # Accepte 1 photo (rétrocompatibilité) ou plusieurs (multi-image)
    photo: Optional[UploadFile] = File(None),
    photos: List[UploadFile] = File(default=[]),
    parcelle_id: Optional[int] = Form(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Upload 1–5 photos, diagnostic Kindwise, enregistrement observation.
    Champ 'photo' (single) ou 'photos' (liste) — les deux sont acceptés.
    """
    # Construire la liste unifiée
    all_photos: List[UploadFile] = []
    if photo:
        all_photos.append(photo)
    if photos:
        all_photos.extend(photos)
    if not all_photos:
        raise HTTPException(status_code=422, detail="Aucune photo fournie.")
    if len(all_photos) > 5:
        raise HTTPException(status_code=422, detail="Maximum 5 photos par envoi.")

    # Vérifier parcelle (si fournie) — exclure les parcelles archivées
    parcelle_nom = None
    centre_lat: Optional[float] = None
    centre_lon: Optional[float] = None
    if parcelle_id:
        p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
        if not p or p.statut == StatutParcelle.ARCHIVE:
            raise HTTPException(status_code=404, detail="Parcelle introuvable.")
        parcelle_nom = p.nom
        centre_lat, centre_lon = _get_parcelle_gps(db, parcelle_id, user.org_id)

    # Sauvegarder la première photo (référence principale de l'observation)
    try:
        upload = await save_photo(all_photos[0], "observation")
    except HTTPException:
        raise

    # Lire les bytes de toutes les photos pour Kindwise
    contenu_photos: List[bytes] = []
    upload_dir = Path("/opt/agroscan/uploads/observations")
    contenu_principal = (upload_dir / upload["filename"]).read_bytes()
    contenu_photos.append(contenu_principal)

    for extra_photo in all_photos[1:]:
        extra_bytes = await extra_photo.read()
        if extra_bytes:
            contenu_photos.append(extra_bytes)

    # Diagnostic Kindwise
    diagnostic = None
    if settings.CROP_HEALTH_API_KEY:
        try:
            diagnostic = identifier_maladie(
                images_bytes=contenu_photos,
                langue="fr",
                latitude=centre_lat,
                longitude=centre_lon,
            )
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

    return _obs_to_out(obs, parcelle_nom)


@router.get("/observations", response_model=List[ObservationOut])
def lister_observations(
    parcelle_id: Optional[int] = None,
    anomalie_seulement: bool = False,
    skip: int = 0,
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

    obs_list = q.order_by(Observation.created_at.desc()).offset(skip).limit(limit).all()

    ids = {o.parcelle_id for o in obs_list if o.parcelle_id}
    noms = {}
    if ids:
        rows = db.query(Parcelle.id, Parcelle.nom).filter(Parcelle.id.in_(ids)).all()
        noms = {r.id: r.nom for r in rows}

    return [_obs_to_out(o, noms.get(o.parcelle_id)) for o in obs_list]


@router.get("/observations/{obs_id}", response_model=ObservationOut)
def detail_observation(
    obs_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Détail complet d'une observation avec diagnostic (maladies, certitudes, traitements)."""
    obs = db.query(Observation).filter_by(id=obs_id, org_id=user.org_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation introuvable.")

    parcelle_nom = None
    if obs.parcelle_id:
        p = db.query(Parcelle).filter_by(id=obs.parcelle_id).first()
        parcelle_nom = p.nom if p else None

    return _obs_to_out(obs, parcelle_nom)


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

    return _obs_to_out(obs, parcelle_nom)
