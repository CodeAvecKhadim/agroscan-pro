"""
Schémas Pydantic — Satellite Sentinel Hub.

Requêtes/Réponses pour les endpoints de recherche et orchestration Sentinel Hub.
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Requête de recherche catalogue ───────────────────────────────────────────

class SatelliteSearchRequest(BaseModel):
    """Requête de recherche dans le catalogue Sentinel Hub."""
    parcelle_id:        int             = Field(..., description="ID de la parcelle")
    sensor:             str             = Field("sentinel-2", description="sentinel-2 ou sentinel-1")
    date_from:          date            = Field(..., description="Date de début (incluse)")
    date_to:            date            = Field(..., description="Date de fin (incluse)")
    cloud_cover_max:    Optional[float] = Field(50.0, ge=0, le=100, description="Cloud cover max %")
    limit:              Optional[int]   = Field(10, ge=1, le=100, description="Nb max résultats")

    class Config:
        json_schema_extra = {
            "example": {
                "parcelle_id": 1,
                "sensor": "sentinel-2",
                "date_from": "2026-05-01",
                "date_to": "2026-06-11",
                "cloud_cover_max": 30.0,
                "limit": 10,
            }
        }


# ── Produit Sentinel Hub ─────────────────────────────────────────────────────

class SatelliteProductResponse(BaseModel):
    """Réponse : un produit (image) trouvé dans le catalogue."""
    id:                 int                 = Field(..., description="ID local AgroScan")
    product_id:         str                 = Field(..., description="Identifiant Sentinel Hub")
    tile_id:            Optional[str]       = None
    sensor:             str                 = Field(..., description="sentinel-2 ou sentinel-1")
    date_acquisition:   date
    cloud_cover:        float               = Field(..., ge=0, le=100)
    snow_cover:         Optional[float]     = None
    discovered_at:      datetime
    product_url:        Optional[str]       = None

    class Config:
        from_attributes = True


# ── Réponse de recherche ─────────────────────────────────────────────────────

class SatelliteSearchResponse(BaseModel):
    """Réponse : liste des produits trouvés."""
    parcelle_id:    int
    sensor:         str
    products:       List[SatelliteProductResponse]
    total_count:    int = Field(..., description="Nombre total de produits trouvés")
    searched_at:    datetime

    class Config:
        json_schema_extra = {
            "example": {
                "parcelle_id": 1,
                "sensor": "sentinel-2",
                "products": [
                    {
                        "id": 42,
                        "product_id": "S2A_MSIL2A_20260530T104031_N0510_R117_T31NDD_20260530T122534",
                        "tile_id": "31NDD",
                        "sensor": "sentinel-2",
                        "date_acquisition": "2026-05-30",
                        "cloud_cover": 12.5,
                        "discovered_at": "2026-06-11T10:00:00Z",
                    }
                ],
                "total_count": 5,
                "searched_at": "2026-06-11T10:05:00Z",
            }
        }


# ── Requête de traitement (Process API) ──────────────────────────────────────

class ProcessRequest(BaseModel):
    """Paramètres pour une requête Process API."""
    product_id:         int             = Field(..., description="ID du produit à traiter")
    evalscript:         Optional[str]   = Field(None, description="Script d'évaluation custom")
    data_fusion:        Optional[bool]  = Field(False, description="Fusionner S1 + S2")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 42,
                "evalscript": None,
                "data_fusion": False,
            }
        }


# ── Job Satellite ────────────────────────────────────────────────────────────

class SatelliteJobResponse(BaseModel):
    """Réponse : statut d'un job Sentinel Hub."""
    id:                 int
    job_type:           str             = Field(..., description="search|process|fetch")
    status:             str             = Field(..., description="queued|running|done|error")
    sentinelhub_job_id: Optional[str]   = None
    started_at:         Optional[datetime] = None
    completed_at:       Optional[datetime] = None
    error_message:      Optional[str]   = None
    result:             Optional[Dict[str, Any]] = None
    retry_count:        int             = 0

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "job_type": "process",
                "status": "done",
                "sentinelhub_job_id": "abc123def456",
                "started_at": "2026-06-11T10:10:00Z",
                "completed_at": "2026-06-11T10:15:30Z",
                "error_message": None,
                "result": {
                    "ndvi": 0.65,
                    "ndre": 0.48,
                    "ndmi": 0.32,
                },
                "retry_count": 0,
            }
        }


# ── Indices satellitaires ────────────────────────────────────────────────────

class SatelliteMetricsResponse(BaseModel):
    """Réponse : indices calculés."""
    id:                 int
    parcelle_id:        int
    metric_date:        date
    ndvi:               Optional[float] = None
    ndre:               Optional[float] = None
    ndmi:               Optional[float] = None
    savi:               Optional[float] = None
    evi:                Optional[float] = None
    humidity_proxy:     Optional[float] = None
    temperature_proxy:  Optional[float] = None
    biomass_proxy:      Optional[float] = None
    cloud_cover:        float = 0.0
    created_at:         datetime

    class Config:
        from_attributes = True


# ── Configuration Sentinel Hub (Expert mode) ─────────────────────────────────

class SatelliteConfigItem(BaseModel):
    """Item de configuration (clé-valeur)."""
    key:                str
    value:              Any
    is_secret:          bool = False
    description:        Optional[str] = None
    updated_at:         datetime

    class Config:
        from_attributes = True


class SatelliteConfigRequest(BaseModel):
    """Requête pour mise à jour config."""
    key:                str             = Field(..., description="Clé unique")
    value:              Any             = Field(..., description="Nouvelle valeur")
    description:        Optional[str]   = None


class SatelliteConfigResponse(BaseModel):
    """Réponse : config mise à jour."""
    success:            bool
    message:            str
    config:             Optional[SatelliteConfigItem] = None


# ── Erreurs ──────────────────────────────────────────────────────────────────

class SatelliteErrorDetail(BaseModel):
    """Détail d'erreur Sentinel Hub."""
    error_code:         str
    error_message:      str
    timestamp:          datetime
    job_id:             Optional[int] = None


# ── Bulk response ────────────────────────────────────────────────────────────

class BulkStatusResponse(BaseModel):
    """Statut de multiples jobs."""
    parcelle_id:        int
    jobs:               List[SatelliteJobResponse]
    pending_count:      int
    running_count:      int
    done_count:         int
    error_count:        int
