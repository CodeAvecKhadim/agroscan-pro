"""
Modèles Satellite — Sentinel Hub integration.

Tables :
  sc_satellite_products  -> Métadonnées produits Sentinel Hub (S2, S1)
  sc_satellite_jobs      -> Orchestration des jobs (search, process)
  sc_satellite_config    -> Configuration Sentinel Hub (API keys, env)

Architecture :
  - Un product = une image Sentinel acquise à une date donnée
  - Un job = une requête utilisateur (search ou process)
  - Config = stockage des credentials et paramètres Sentinel Hub
"""
import enum
from datetime import datetime, timezone, date
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text, JSON, Date, Index
)
from sqlalchemy.orm import relationship
from app.core.config import settings

# Use JSONB for PostgreSQL, fallback to JSON for SQLite/testing
if settings.DATABASE_URL.startswith("postgres"):
    from sqlalchemy.dialects.postgresql import JSONB as JSONType
else:
    JSONType = JSON

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


# --------- Énumérations ---------

class SensorType(str, enum.Enum):
    """Types de capteurs Sentinel."""
    SENTINEL_2 = "sentinel-2"      # Multispectral (10–60 m resolution)
    SENTINEL_1 = "sentinel-1"      # SAR (10–40 m resolution)


class JobStatus(str, enum.Enum):
    """Statuts job Sentinel Hub."""
    QUEUED = "queued"              # En attente d'exécution
    RUNNING = "running"            # En cours d'exécution
    DONE = "done"                  # Terminé avec succès
    ERROR = "error"                # Erreur lors du traitement
    CANCELED = "canceled"          # Annulé par l'utilisateur


class JobType(str, enum.Enum):
    """Types de jobs Sentinel Hub."""
    SEARCH = "search"              # Recherche dans le catalogue
    PROCESS = "process"            # Traitement avec Process API
    FETCH = "fetch"                # Récupération des données


# --------- Tables ---------

class SatelliteProduct(Base):
    """Métadonnées produit Sentinel Hub (une image acquise à une date donnée)."""
    __tablename__ = "sc_satellite_products"

    id                  = Column(Integer, primary_key=True, index=True)
    parcelle_id         = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="CASCADE"), 
                                nullable=False, index=True)
    org_id              = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), 
                                nullable=False, index=True)

    # Identifiants Sentinel Hub
    product_id          = Column(String(200), nullable=False, unique=True, index=True)
    tile_id             = Column(String(50))  # ex: 31NDD (UTM tile pour S2)
    
    # Capteur et date d'acquisition
    sensor              = Column(String(20), nullable=False)  # sentinel-2|sentinel-1
    date_acquisition    = Column(Date, nullable=False, index=True)
    date_product_date   = Column(DateTime(timezone=True), nullable=False)  # Timestamp exact Sentinel Hub
    
    # Qualité image
    cloud_cover         = Column(Float, default=0.0)  # 0–100 %
    snow_cover          = Column(Float, default=0.0)
    
    # Géométrie
    footprint           = Column(JSONType)  # GeoJSON Polygon de la coverage
    
    # URLs
    product_url         = Column(String(500))  # URL Sentinel Hub
    
    # Statut dans notre pipeline
    is_cached           = Column(Boolean, default=False)  # Stocké en local
    cached_at           = Column(DateTime(timezone=True))
    
    # Timestamps
    discovered_at       = Column(DateTime(timezone=True), default=_now)
    created_at          = Column(DateTime(timezone=True), default=_now)

    # Relations
    jobs                = relationship("SatelliteJob", back_populates="product", 
                                      cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sc_satellite_products_parcelle_date", "parcelle_id", "date_acquisition"),
        Index("ix_sc_satellite_products_sensor", "sensor"),
    )

    def __repr__(self):
        return f"<SatelliteProduct {self.product_id} {self.sensor} {self.date_acquisition}>"


class SatelliteJob(Base):
    """Orchestration des jobs Sentinel Hub (search, process, fetch)."""
    __tablename__ = "sc_satellite_jobs"

    id                  = Column(Integer, primary_key=True, index=True)
    parcelle_id         = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="CASCADE"), 
                                nullable=False, index=True)
    product_id          = Column(Integer, ForeignKey("sc_satellite_products.id", ondelete="SET NULL"), 
                                nullable=True)
    org_id              = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), 
                                nullable=False, index=True)
    
    # Type et statut
    job_type            = Column(String(20), nullable=False)  # search|process|fetch
    status              = Column(String(20), nullable=False, default=JobStatus.QUEUED.value, index=True)
    
    # Paramètres d'entrée
    params              = Column(JSONType)  # {bbox, date_range, sensor, cloud_cover_max, ...}
    
    # Résultats / Erreurs
    result              = Column(JSONType)  # Résultat du job (si succès)
    error_message       = Column(Text)   # Message d'erreur (si erreur)
    error_code          = Column(String(50))  # Code erreur Sentinel Hub (si applicable)
    
    # Sentinel Hub job ID (pour polling)
    sentinelhub_job_id  = Column(String(100))
    
    # Timings
    started_at          = Column(DateTime(timezone=True))
    completed_at        = Column(DateTime(timezone=True))
    created_at          = Column(DateTime(timezone=True), default=_now)
    
    # Retry logic
    retry_count         = Column(Integer, default=0)
    max_retries         = Column(Integer, default=3)
    next_retry_at       = Column(DateTime(timezone=True))

    # Relations
    product             = relationship("SatelliteProduct", back_populates="jobs")

    __table_args__ = (
        Index("ix_sc_satellite_jobs_parcelle_status", "parcelle_id", "status"),
        Index("ix_sc_satellite_jobs_sentinelhub_id", "sentinelhub_job_id"),
    )

    def __repr__(self):
        return f"<SatelliteJob {self.id} {self.job_type} {self.status}>"


class SatelliteConfig(Base):
    """Configuration Sentinel Hub (API keys, environment, quotas)."""
    __tablename__ = "sc_satellite_config"

    id                  = Column(Integer, primary_key=True, index=True)
    
    # Clé de configuration unique
    key                 = Column(String(100), nullable=False, unique=True, index=True)
    
    # Valeur (peut être JSON, texte, booléen, nombre)
    value               = Column(JSONType, nullable=False)
    
    # Description
    description         = Column(Text)
    
    # Visibilité (pour logs / audit)
    is_secret           = Column(Boolean, default=False)  # Ne pas logguer la valeur
    
    # Timestamps
    updated_at          = Column(DateTime(timezone=True), default=_now, onupdate=_now)
    created_at          = Column(DateTime(timezone=True), default=_now)

    def __repr__(self):
        return f"<SatelliteConfig {self.key}>"


class SatelliteMetrics(Base):
    """Indices calculés depuis Sentinel Hub (optionnel : peut être dans sc_indices_satellitaires)."""
    __tablename__ = "sc_satellite_metrics"

    id                  = Column(Integer, primary_key=True, index=True)
    parcelle_id         = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="CASCADE"), 
                                nullable=False, index=True)
    product_id          = Column(Integer, ForeignKey("sc_satellite_products.id", ondelete="SET NULL"), 
                                nullable=True)
    
    # Date de l'image
    metric_date         = Column(Date, nullable=False, index=True)
    
    # Indices de végétation
    ndvi                = Column(Float)   # Normalized Difference Vegetation Index
    ndre                = Column(Float)   # Red Edge NDVI (chlorophylle)
    ndmi                = Column(Float)   # Normalized Difference Moisture Index
    savi                = Column(Float)   # Soil Adjusted Vegetation Index
    evi                 = Column(Float)   # Enhanced Vegetation Index
    
    # Indices proxy (calcul) - optionnels pour MVP Phase 1
    humidity_proxy      = Column(Float)   # Calculé depuis NDMI
    temperature_proxy   = Column(Float)   # Calculé depuis TIR si disponible (S3)
    biomass_proxy       = Column(Float)   # Calculé depuis NDVI
    
    # Cloud cover
    cloud_cover         = Column(Float, default=0.0)
    
    # Timestamps
    created_at          = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_sc_satellite_metrics_parcelle_date", "parcelle_id", "metric_date"),
    )

    def __repr__(self):
        return f"<SatelliteMetrics {self.parcelle_id} {self.metric_date}>"
