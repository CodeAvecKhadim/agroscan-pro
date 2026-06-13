"""
Modèles SQLAlchemy — Santé des Cultures + Agriculture de Précision.
Tables : sc_analyses, sc_indices_satellitaires, sc_cartes_precision,
         sc_previsions_rendement, sc_analyse_economique
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, Float, Boolean,
    DateTime, Date, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


# ── Énumérations ────────────────────────────────────────────────────────────

class StatutAnalyse(str, enum.Enum):
    EN_COURS  = "en_cours"
    TERMINE   = "termine"
    ERREUR    = "erreur"


class EtatGeneral(str, enum.Enum):
    EXCELLENT = "excellent"
    BON       = "bon"
    MOYEN     = "moyen"
    FAIBLE    = "faible"


class NiveauDonnees(int, enum.Enum):
    SATELLITE = 1   # Satellite + Météo + Rules Engine
    CAPTEUR   = 2   # + Capteur 8-en-1
    LABO      = 3   # + Analyse sol laboratoire


class TypeCarte(str, enum.Enum):
    SANTE      = "sante"
    HYDRIQUE   = "hydrique"
    FERTILITE  = "fertilite"
    RISQUES    = "risques"


# ── Tables ──────────────────────────────────────────────────────────────────

class ScAnalyse(Base):
    """Résultat global d'une analyse Santé des Cultures."""
    __tablename__ = "sc_analyses"

    id              = Column(Integer, primary_key=True, index=True)
    parcelle_id     = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="CASCADE"), nullable=False, index=True)
    culture_id      = Column(Integer, ForeignKey("agro_cultures.id"), nullable=True)
    org_id          = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Statut
    statut          = Column(String(20), nullable=False, default=StatutAnalyse.EN_COURS.value, index=True)
    analyse_le      = Column(DateTime(timezone=True), default=_now, nullable=False)
    duree_ms        = Column(Integer)
    erreur_message  = Column(Text)

    # Niveau de données utilisé
    niveau_donnees  = Column(SmallInteger, nullable=False, default=1)  # 1|2|3

    # Scores (0–100)
    score_sante     = Column(Float)
    score_vigueur   = Column(Float)
    score_hydrique  = Column(Float)
    score_fertilite = Column(Float)
    score_maladie   = Column(Float)
    score_ravageur  = Column(Float)

    etat_general    = Column(String(20))    # excellent|bon|moyen|faible

    # Données brutes stockées pour réanalyse
    contexte_entree = Column(JSONB)
    resultat        = Column(JSONB)         # réponse API complète en cache

    # Relations
    indices         = relationship("ScIndicesSatellitaires", back_populates="analyse",
                                   uselist=False, cascade="all, delete-orphan")
    cartes          = relationship("ScCartePrecision", back_populates="analyse",
                                   cascade="all, delete-orphan")
    prevision       = relationship("ScPrevisionRendement", back_populates="analyse",
                                   uselist=False, cascade="all, delete-orphan")
    economie        = relationship("ScAnalyseEconomique", back_populates="analyse",
                                   uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sc_analyses_parcelle_date", "parcelle_id", "analyse_le"),
    )


class ScIndicesSatellitaires(Base):
    """Indices calculés depuis Sentinel-1/2 via Sentinel Hub Process API.
    Cache de 10 jours (cadence revisit Sentinel-2).
    """
    __tablename__ = "sc_indices_satellitaires"

    id                    = Column(Integer, primary_key=True, index=True)
    parcelle_id           = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="CASCADE"), nullable=False, index=True)
    analyse_id            = Column(Integer, ForeignKey("sc_analyses.id", ondelete="CASCADE"), nullable=True)

    date_image            = Column(Date, nullable=False)
    date_calcul           = Column(DateTime(timezone=True), default=_now)
    satellite             = Column(String(20), default="sentinel-2")  # sentinel-1|sentinel-2

    # Indices végétation (Sentinel-2)
    ndvi                  = Column(Float)   # Vigueur générale
    ndre                  = Column(Float)   # Teneur chlorophylle (RedEdge)
    savi                  = Column(Float)   # Végétation sols nus (L=0.5)
    evi                   = Column(Float)   # Végétation résistant à l'atmosphère
    msavi                 = Column(Float)   # SAVI amélioré (sols très nus)

    # Indice hydrique
    ndwi                  = Column(Float)   # Eau en surface (B3-B8)/(B3+B8)
    ndmi                  = Column(Float)   # Humidité végétation (B8A-B11)/(B8A+B11)

    # Biomasse & température
    biomasse              = Column(Float)   # t MS/ha — estimée depuis EVI/NDVI
    temperature_canopee   = Column(Float)   # °C — LST Sentinel-3 ou estimation

    # Qualité image
    couverture_nuages     = Column(Float)   # 0–100 %

    # Labels traduits (jamais retournés bruts en API)
    ndvi_label            = Column(String(15))  # Excellent|Bon|Moyen|Faible
    ndre_label            = Column(String(15))
    savi_label            = Column(String(15))
    evi_label             = Column(String(15))
    msavi_label           = Column(String(15))
    ndwi_label            = Column(String(15))
    ndmi_label            = Column(String(15))
    biomasse_label        = Column(String(15))

    # Metadata Sentinel Hub
    sentinelhub_request_id = Column(String(100))
    bbox                   = Column(JSONB)   # {min_lon, min_lat, max_lon, max_lat}

    # Cache TTL
    expire_le              = Column(DateTime(timezone=True))

    # Relations
    analyse = relationship("ScAnalyse", back_populates="indices")

    __table_args__ = (
        Index("ix_sc_indices_parcelle_date", "parcelle_id", "date_image"),
    )


class ScCartePrecision(Base):
    """Carte de précision GeoJSON (grille 10m/20m/60m selon superficie).
    4 types : sante, hydrique, fertilite, risques.
    """
    __tablename__ = "sc_cartes_precision"

    id             = Column(Integer, primary_key=True, index=True)
    analyse_id     = Column(Integer, ForeignKey("sc_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    parcelle_id    = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="CASCADE"), nullable=False, index=True)

    type_carte     = Column(String(20), nullable=False)  # sante|hydrique|fertilite|risques
    donnees        = Column(JSONB, nullable=False)        # GeoJSON FeatureCollection
    resolution_m   = Column(Integer, default=10)         # 10|20|60
    nb_cellules    = Column(Integer)
    created_at     = Column(DateTime(timezone=True), default=_now)

    # Relations
    analyse = relationship("ScAnalyse", back_populates="cartes")

    __table_args__ = (
        Index("ix_sc_cartes_analyse_type", "analyse_id", "type_carte"),
    )


class ScPrevisionRendement(Base):
    """Prévision de rendement basée sur indices satellitaires + Rules Engine."""
    __tablename__ = "sc_previsions_rendement"

    id                          = Column(Integer, primary_key=True, index=True)
    analyse_id                  = Column(Integer, ForeignKey("sc_analyses.id", ondelete="CASCADE"), nullable=False, unique=True)
    culture_id                  = Column(Integer, ForeignKey("agro_cultures.id"), nullable=True)

    rendement_estime            = Column(Float)   # T/ha
    rendement_potentiel         = Column(Float)   # T/ha (référence zone agro)
    ecart_performance           = Column(Float)   # %  ((estime - potentiel) / potentiel * 100)

    facteurs_limitants          = Column(JSONB)   # [{facteur, impact_pct, source}]
    confiance                   = Column(Float, default=0.70)  # 0–1
    methode                     = Column(String(50), default="rules_satellite")

    created_at                  = Column(DateTime(timezone=True), default=_now)

    # Relations
    analyse = relationship("ScAnalyse", back_populates="prevision")


class ScAnalyseEconomique(Base):
    """Analyse économique : perte potentielle, gain, ROI."""
    __tablename__ = "sc_analyse_economique"

    id                              = Column(Integer, primary_key=True, index=True)
    analyse_id                      = Column(Integer, ForeignKey("sc_analyses.id", ondelete="CASCADE"), nullable=False, unique=True)

    superficie_ha                   = Column(Float)

    # Rendement
    rendement_actuel_estime_t_ha    = Column(Float)
    rendement_potentiel_t_ha        = Column(Float)
    perte_volume_t_ha               = Column(Float)

    # Prix marché (FCFA/kg — configurable par culture/zone)
    prix_marche_fcfa_kg             = Column(Float)

    # Résultats économiques (FCFA/ha)
    perte_potentielle_fcfa_ha       = Column(Float)
    cout_correction_estime_fcfa_ha  = Column(Float)
    gain_potentiel_fcfa_ha          = Column(Float)
    roi_estime                      = Column(Float)   # %

    created_at                      = Column(DateTime(timezone=True), default=_now)

    # Relations
    analyse = relationship("ScAnalyse", back_populates="economie")
