"""
Modèles SQLAlchemy — Module MÉTÉO & ALERTES INTELLIGENTES.
Tables préfixe mt_ : conditions cache, prévisions cache, alertes, config, planificateur.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, SmallInteger, String, Float, Boolean,
    DateTime, Date, Time, ForeignKey, Enum, Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


# ── Enums ─────────────────────────────────────────────────────────────────────

class SourceMeteo(str, enum.Enum):
    OPEN_METEO = "open_meteo"
    CAPTEUR    = "capteur"
    MANUEL     = "manuel"


class TypeAlerte(str, enum.Enum):
    METEO         = "meteo"
    MALADIE       = "maladie"
    RAVAGEUR      = "ravageur"
    FERTILISATION = "fertilisation"
    IRRIGATION    = "irrigation"
    CALENDRIER    = "calendrier"
    PLANIFICATEUR = "planificateur"


class NiveauAlerte(str, enum.Enum):
    INFO          = "info"
    AVERTISSEMENT = "avertissement"
    CRITIQUE      = "critique"


class StatutPlanificateur(str, enum.Enum):
    RECOMMANDE = "recommande"
    PLANIFIE   = "planifie"
    IGNORE     = "ignore"
    FAIT       = "fait"


class SourcePlanificateur(str, enum.Enum):
    RULES_ENGINE = "rules_engine"
    METEO        = "meteo"
    GF_ACTIVITE  = "gf_activite"
    MANUEL       = "manuel"


class SousTypeMeteo(str, enum.Enum):
    PLUIE_FORTE   = "pluie_forte"
    PLUIE_EXTREME = "pluie_extreme"
    CHALEUR       = "chaleur"
    CHALEUR_EXTREME = "chaleur_extreme"
    VENT_FORT     = "vent_fort"
    VENT_EXTREME  = "vent_extreme"
    SECHERESSE    = "secheresse"
    ETP_ELEVEE    = "etp_elevee"


# ── Modèles ───────────────────────────────────────────────────────────────────

class ConditionMeteo(Base):
    """Cache conditions météo actuelles (TTL 1h). 1 ligne par parcelle ou zone."""
    __tablename__ = "mt_conditions"

    id            = Column(Integer, primary_key=True)
    org_id        = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    parcelle_id   = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=True, index=True)
    lat           = Column(Float, nullable=False)
    lon           = Column(Float, nullable=False)
    zone_agro     = Column(String(40))
    source        = Column(Enum(SourceMeteo), default=SourceMeteo.OPEN_METEO)

    temp_actuelle = Column(Float)
    temp_min      = Column(Float)
    temp_max      = Column(Float)
    humidite_rel  = Column(SmallInteger)
    pluie_mm      = Column(Float)
    vent_kmh      = Column(Float)
    direction_vent = Column(SmallInteger)
    etp_mm        = Column(Float)
    code_meteo    = Column(SmallInteger)
    description_fr = Column(String(100))

    date_releve   = Column(Date)
    heure_releve  = Column(DateTime)
    expire_le     = Column(DateTime)
    created_at    = Column(DateTime, default=_now)

    parcelle      = relationship("Parcelle", foreign_keys=[parcelle_id])


class Prevision(Base):
    """Cache prévisions météo N jours (TTL 6h). donnees = liste de jours JSON."""
    __tablename__ = "mt_previsions"

    id            = Column(Integer, primary_key=True)
    org_id        = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    parcelle_id   = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=True, index=True)
    lat           = Column(Float, nullable=False)
    lon           = Column(Float, nullable=False)
    zone_agro     = Column(String(40))
    source        = Column(String(30), default="open_meteo")
    horizon_jours = Column(SmallInteger, nullable=False)
    donnees       = Column(JSONB, nullable=False)
    genere_le     = Column(DateTime, default=_now)
    expire_le     = Column(DateTime)

    parcelle      = relationship("Parcelle", foreign_keys=[parcelle_id])


class Alerte(Base):
    """Alertes unifiées : météo, maladie, ravageur, fertilisation, irrigation, planificateur."""
    __tablename__ = "mt_alertes"

    id            = Column(Integer, primary_key=True)
    org_id        = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    parcelle_id   = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=True, index=True)
    culture_id    = Column(Integer, ForeignKey("agro_cultures.id"), nullable=True)
    type_alerte   = Column(Enum(TypeAlerte), nullable=False, index=True)
    sous_type     = Column(String(80))
    niveau        = Column(Enum(NiveauAlerte), nullable=False, default=NiveauAlerte.INFO, index=True)
    titre         = Column(String(200), nullable=False)
    message       = Column(Text, nullable=False)
    details       = Column(JSONB)
    regle_code    = Column(String(20))
    valable_du    = Column(DateTime, default=_now)
    valable_au    = Column(DateTime)
    lu            = Column(Boolean, default=False)
    lu_le         = Column(DateTime)
    action_prise  = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=_now)

    parcelle      = relationship("Parcelle", foreign_keys=[parcelle_id])
    culture       = relationship("Culture", foreign_keys=[culture_id])


class ConfigAlertes(Base):
    """Configuration alertes par organisation (1 ligne par org)."""
    __tablename__ = "mt_config_alertes"

    id            = Column(Integer, primary_key=True)
    org_id        = Column(Integer, ForeignKey("organizations.id"), unique=True, nullable=False)
    seuils        = Column(JSONB, default=lambda: {
        "pluie_forte_mm": 30,
        "pluie_extreme_mm": 60,
        "chaleur_max_c": 38,
        "chaleur_extreme_c": 42,
        "vent_fort_kmh": 40,
        "vent_extreme_kmh": 70,
        "secheresse_jours": 7,
        "secheresse_critique_jours": 14,
        "etp_elevee_mm": 8,
    })
    alertes_meteo_actives         = Column(Boolean, default=True)
    alertes_maladies_actives      = Column(Boolean, default=True)
    alertes_ravageurs_actives     = Column(Boolean, default=True)
    alertes_fertilisation_actives = Column(Boolean, default=True)
    alertes_irrigation_actives    = Column(Boolean, default=True)
    alertes_planificateur_actives = Column(Boolean, default=True)
    heure_envoi_alertes           = Column(Time)
    updated_at                    = Column(DateTime, default=_now, onupdate=_now)


class RecommandationPlan(Base):
    """Planificateur intelligent : fenêtres météo optimales pour activités agricoles."""
    __tablename__ = "mt_planificateur"

    id                  = Column(Integer, primary_key=True)
    org_id              = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    parcelle_id         = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=True, index=True)
    culture_id          = Column(Integer, ForeignKey("agro_cultures.id"), nullable=True)
    activite_id         = Column(Integer, ForeignKey("gf_activites.id"), nullable=True)
    date_recommandee    = Column(Date, nullable=False)
    type_activite       = Column(String(50))
    titre               = Column(String(200), nullable=False)
    priorite            = Column(SmallInteger, default=3)
    raison              = Column(Text)
    fenetre_debut       = Column(Date)
    fenetre_fin         = Column(Date)
    conditions_ok       = Column(Boolean)
    detail_conditions   = Column(JSONB)
    statut              = Column(Enum(StatutPlanificateur), default=StatutPlanificateur.RECOMMANDE)
    source              = Column(Enum(SourcePlanificateur), default=SourcePlanificateur.METEO)
    genere_le           = Column(DateTime, default=_now)
    expire_le           = Column(Date)

    parcelle  = relationship("Parcelle", foreign_keys=[parcelle_id])
    culture   = relationship("Culture", foreign_keys=[culture_id])
