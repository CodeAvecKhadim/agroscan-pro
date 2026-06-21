"""
Router Satellite — Sentinel Hub endpoints.
Préfixe : /api/sante/precision/satellite

Endpoints :
  POST /search                     → Rechercher produits dans le catalogue
  GET  /products                   → Lister produits trouvés
  GET  /jobs/{job_id}              → Statut d'un job
  GET  /jobs/parcelle/{parcelle_id} → Lister jobs d'une parcelle
  POST /config                     → Mettre à jour configuration (admin)
  GET  /config/{key}               → Lire une config (admin)
"""
import logging
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user, require_role
from app.models import User, UserRole
from app.models.champ import Parcelle
from app.models.champ import Cartographie
from app.models.satellite import SatelliteProduct, SatelliteJob, SatelliteConfig, SensorType, JobStatus
from app.schemas.satellite import (
    SatelliteSearchRequest, SatelliteSearchResponse, SatelliteProductResponse,
    SatelliteJobResponse, SatelliteConfigRequest, SatelliteConfigResponse,
    BulkStatusResponse,
)
from app.services.satellite import (
    SentinelHubClient, SentinelHubConfig, SentinelHubException,
    coordonnees_to_bbox,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sante/precision/satellite", tags=["Satellite Sentinel Hub"])


def _get_sentinel_hub_config(db: Session) -> SentinelHubConfig:
    """Récupère la configuration Sentinel Hub depuis la DB."""
    api_key_cfg = db.query(SatelliteConfig).filter_by(key="sentinel_hub_api_key").first()
    api_secret_cfg = db.query(SatelliteConfig).filter_by(key="sentinel_hub_api_secret").first()
    
    if not api_key_cfg or not api_secret_cfg:
        raise HTTPException(
            status_code=500,
            detail="Sentinel Hub configuration not found. Contact administrator."
        )
    
    return SentinelHubConfig(
        api_key=api_key_cfg.value.get("value") if isinstance(api_key_cfg.value, dict) else api_key_cfg.value,
        api_secret=api_secret_cfg.value.get("value") if isinstance(api_secret_cfg.value, dict) else api_secret_cfg.value,
    )


def _check_parcelle(parcelle_id: int, user: User, db: Session) -> Parcelle:
    """Vérifie que la parcelle existe et appartient à l'org."""
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.org_id == user.org_id,
    ).first()
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle not found")
    return parcelle


# ── POST /search ─────────────────────────────────────────────────────────────

@router.post("/search", response_model=SatelliteSearchResponse, status_code=201)
def search_satellite_products(
    req: SatelliteSearchRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Recherche des produits Sentinel Hub (S2 ou S1) pour une parcelle.
    
    Enregistre les produits trouvés dans sc_satellite_products.
    """
    log.info(f"[{user.org_id}] Searching satellite products for parcelle {req.parcelle_id}")
    
    # Vérifier la parcelle
    parcelle = _check_parcelle(req.parcelle_id, user, db)
    
    # Obtenir la géométrie de la parcelle — contour réel en priorité
    if not parcelle.centre_lat or not parcelle.centre_lon:
        raise HTTPException(
            status_code=400,
            detail="Parcelle must have coordinates (centre_lat, centre_lon)"
        )

    # Chercher le contour cartographié le plus récent
    carto = (
        db.query(Cartographie)
        .filter_by(parcelle_id=parcelle.id)
        .order_by(Cartographie.created_at.desc())
        .first()
    )

    if carto and carto.coordonnees:
        try:
            min_lon, min_lat, max_lon, max_lat = coordonnees_to_bbox(carto.coordonnees)
            bbox = {
                "min_lon": min_lon, "min_lat": min_lat,
                "max_lon": max_lon, "max_lat": max_lat,
            }
            log.info(f"Bbox from parcel contour ({len(carto.coordonnees)} pts): {bbox}")
        except (ValueError, KeyError) as exc:
            log.warning(f"Contour invalide pour parcelle {parcelle.id}: {exc} — fallback centre")
            delta = 0.001
            bbox = {
                "min_lon": parcelle.centre_lon - delta,
                "min_lat": parcelle.centre_lat - delta,
                "max_lon": parcelle.centre_lon + delta,
                "max_lat": parcelle.centre_lat + delta,
            }
    else:
        # Pas de contour : approximation ~110 m autour du centre
        delta = 0.001
        bbox = {
            "min_lon": parcelle.centre_lon - delta,
            "min_lat": parcelle.centre_lat - delta,
            "max_lon": parcelle.centre_lon + delta,
            "max_lat": parcelle.centre_lat + delta,
        }
        log.info(f"Bbox from centre±{delta}° (no contour): {bbox}")
    
    # Récupérer config Sentinel Hub
    try:
        sentinel_config = _get_sentinel_hub_config(db)
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to load Sentinel Hub config: {e}")
        raise HTTPException(status_code=500, detail="Configuration error")
    
    # Créer client et rechercher
    try:
        client = SentinelHubClient(sentinel_config)
        stac_result = client.search_catalog(
            bbox=bbox,
            date_from=req.date_from,
            date_to=req.date_to,
            sensor=req.sensor,
            cloud_cover_max=req.cloud_cover_max,
            limit=req.limit,
        )
    except SentinelHubException as e:
        log.error(f"Sentinel Hub search failed: {e}")
        raise HTTPException(status_code=502, detail=f"Sentinel Hub error: {e}")
    
    # Parser les résultats STAC et enregistrer les produits
    features = stac_result.get("features", [])
    products = []
    
    for feature in features:
        product_id = feature.get("id")
        properties = feature.get("properties", {})
        
        # Vérifier si le produit existe déjà
        existing = db.query(SatelliteProduct).filter_by(product_id=product_id).first()
        if existing:
            log.info(f"Product {product_id} already exists, skipping")
            products.append(existing)
            continue
        
        # Parser les propriétés
        datetime_str = properties.get("datetime", "")
        try:
            date_acq = datetime.fromisoformat(datetime_str.replace("Z", "+00:00")).date()
        except (ValueError, AttributeError):
            date_acq = req.date_from
        
        cloud_cover = properties.get("eo:cloud_cover", 0.0)
        snow_cover = properties.get("eo:snow_cover", 0.0)
        tile_id = properties.get("sentinel:utm_zone")
        
        # Créer le produit
        product = SatelliteProduct(
            parcelle_id=req.parcelle_id,
            org_id=user.org_id,
            product_id=product_id,
            tile_id=tile_id,
            sensor=req.sensor,
            date_acquisition=date_acq,
            date_product_date=datetime.fromisoformat(datetime_str.replace("Z", "+00:00")),
            cloud_cover=cloud_cover,
            snow_cover=snow_cover,
            footprint=feature.get("geometry"),
            product_url=None,  # URL à récupérer si disponible
        )
        
        db.add(product)
        db.flush()  # Pour avoir l'ID
        products.append(product)
        log.info(f"Registered product {product_id}")
    
    db.commit()
    
    # Construire la réponse
    product_responses = [
        SatelliteProductResponse.model_validate(p) for p in products
    ]
    
    return SatelliteSearchResponse(
        parcelle_id=req.parcelle_id,
        sensor=req.sensor,
        products=product_responses,
        total_count=len(product_responses),
        searched_at=datetime.now(timezone.utc),
    )


# ── GET /products ────────────────────────────────────────────────────────────

@router.get("/products", response_model=list[SatelliteProductResponse])
def list_satellite_products(
    parcelle_id: int = Query(..., description="Filter by parcelle_id"),
    sensor: Optional[str] = Query(None, description="Filter by sensor"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Liste les produits Sentinel Hub d'une parcelle.
    """
    # Vérifier la parcelle
    _check_parcelle(parcelle_id, user, db)
    
    query = db.query(SatelliteProduct).filter_by(
        parcelle_id=parcelle_id,
        org_id=user.org_id,
    )
    
    if sensor:
        query = query.filter_by(sensor=sensor)
    
    products = query.order_by(SatelliteProduct.date_acquisition.desc()).all()
    
    return [SatelliteProductResponse.model_validate(p) for p in products]


# ── GET /jobs/{job_id} ───────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=SatelliteJobResponse)
def get_satellite_job(
    job_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Récupère le statut d'un job Sentinel Hub.
    """
    job = db.query(SatelliteJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Vérifier que le job appartient à l'org
    if job.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return SatelliteJobResponse.model_validate(job)


# ── GET /jobs/parcelle/{parcelle_id} ────────────────────────────────────────

@router.get("/jobs/parcelle/{parcelle_id}", response_model=BulkStatusResponse)
def list_satellite_jobs(
    parcelle_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Liste tous les jobs d'une parcelle avec résumé du statut.
    """
    # Vérifier la parcelle
    _check_parcelle(parcelle_id, user, db)
    
    query = db.query(SatelliteJob).filter_by(
        parcelle_id=parcelle_id,
        org_id=user.org_id,
    )
    
    if status:
        query = query.filter_by(status=status)
    
    jobs = query.order_by(SatelliteJob.created_at.desc()).all()
    job_responses = [SatelliteJobResponse.model_validate(j) for j in jobs]
    
    # Résumé
    pending = len([j for j in jobs if j.status == JobStatus.QUEUED.value])
    running = len([j for j in jobs if j.status == JobStatus.RUNNING.value])
    done = len([j for j in jobs if j.status == JobStatus.DONE.value])
    error = len([j for j in jobs if j.status == JobStatus.ERROR.value])
    
    return BulkStatusResponse(
        parcelle_id=parcelle_id,
        jobs=job_responses,
        pending_count=pending,
        running_count=running,
        done_count=done,
        error_count=error,
    )


# ── POST /config ─────────────────────────────────────────────────────────────

@router.post("/config", response_model=SatelliteConfigResponse)
def update_satellite_config(
    req: SatelliteConfigRequest,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """
    Met à jour la configuration Sentinel Hub (owner/admin uniquement).
    """
    log.info(f"[{user.org_id}] Updating config: {req.key}")
    
    # Chercher ou créer la config
    config = db.query(SatelliteConfig).filter_by(key=req.key).first()
    
    if not config:
        config = SatelliteConfig(
            key=req.key,
            value=req.value,
            description=req.description,
        )
        db.add(config)
    else:
        config.value = req.value
        if req.description:
            config.description = req.description
        config.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(config)
    
    return SatelliteConfigResponse(
        success=True,
        message=f"Config '{req.key}' updated",
        config=None,  # Ne pas retourner les secrets
    )


# ── GET /config/{key} ────────────────────────────────────────────────────────

@router.get("/config/{key}", response_model=Dict[str, Any])
def get_satellite_config(
    key: str,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """
    Récupère une configuration (non-secrets seulement, owner/admin uniquement).
    """
    config = db.query(SatelliteConfig).filter_by(key=key).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"Config '{key}' not found")
    
    if config.is_secret:
        raise HTTPException(status_code=403, detail="Cannot read secret config")
    
    return {
        "key": config.key,
        "value": config.value,
        "description": config.description,
        "updated_at": config.updated_at.isoformat(),
    }


# ── Health check ─────────────────────────────────────────────────────────────

@router.get("/health", response_model=Dict[str, str])
def health_check(db: Session = Depends(get_db)):
    """Vérifie la santé du service satellite."""
    try:
        # Vérifier la DB
        db.execute(text("SELECT 1"))
        
        # Vérifier la config Sentinel Hub
        _get_sentinel_hub_config(db)
        
        return {
            "status": "ok",
            "service": "satellite",
        }
    except Exception as e:
        log.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
