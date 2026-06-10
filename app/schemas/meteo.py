"""
Schémas Pydantic v2 — Module MÉTÉO & ALERTES INTELLIGENTES.
"""
from datetime import date, datetime, time
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.meteo import (
    NiveauAlerte, SourceMeteo, SourcePlanificateur,
    StatutPlanificateur, TypeAlerte,
)


# ── Conditions ────────────────────────────────────────────────────────────────

class ConditionManuelle(BaseModel):
    """Injecter données capteur terrain."""
    parcelle_id:   Optional[int]   = None
    lat:           float
    lon:           float
    zone_agro:     Optional[str]   = None
    temp_actuelle: Optional[float] = None
    temp_min:      Optional[float] = None
    temp_max:      Optional[float] = None
    humidite_rel:  Optional[int]   = None
    pluie_mm:      Optional[float] = None
    vent_kmh:      Optional[float] = None
    direction_vent: Optional[int]  = None
    etp_mm:        Optional[float] = None
    code_meteo:    Optional[int]   = None


class ConditionOut(BaseModel):
    id:             int
    parcelle_id:    Optional[int]   = None
    zone_agro:      Optional[str]   = None
    source:         SourceMeteo
    temp_actuelle:  Optional[float] = None
    temp_min:       Optional[float] = None
    temp_max:       Optional[float] = None
    humidite_rel:   Optional[int]   = None
    pluie_mm:       Optional[float] = None
    vent_kmh:       Optional[float] = None
    etp_mm:         Optional[float] = None
    code_meteo:     Optional[int]   = None
    description_fr: Optional[str]   = None
    date_releve:    Optional[date]  = None
    heure_releve:   Optional[datetime] = None
    expire_le:      Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Prévisions ────────────────────────────────────────────────────────────────

class PrevisionJour(BaseModel):
    date:               date
    temp_min:           Optional[float] = None
    temp_max:           Optional[float] = None
    pluie_mm:           Optional[float] = None
    pluie_proba_pct:    Optional[int]   = None
    vent_kmh:           Optional[float] = None
    humidite_pct:       Optional[int]   = None
    etp_mm:             Optional[float] = None
    code_meteo:         Optional[int]   = None
    description_fr:     Optional[str]   = None


class PrevisionOut(BaseModel):
    id:             int
    parcelle_id:    Optional[int]    = None
    zone_agro:      Optional[str]    = None
    horizon_jours:  int
    jours:          list[PrevisionJour]
    pluie_totale_mm: float           = 0.0
    temp_moy_max:   Optional[float]  = None
    genere_le:      datetime
    expire_le:      Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Alertes ───────────────────────────────────────────────────────────────────

class AlerteResume(BaseModel):
    id:           int
    type_alerte:  TypeAlerte
    sous_type:    Optional[str]     = None
    niveau:       NiveauAlerte
    titre:        str
    parcelle_id:  Optional[int]     = None
    parcelle_nom: Optional[str]     = None
    lu:           bool
    created_at:   datetime

    model_config = {"from_attributes": True}


class AlerteOut(BaseModel):
    id:           int
    org_id:       int
    parcelle_id:  Optional[int]     = None
    parcelle_nom: Optional[str]     = None
    culture_id:   Optional[int]     = None
    culture_nom:  Optional[str]     = None
    type_alerte:  TypeAlerte
    sous_type:    Optional[str]     = None
    niveau:       NiveauAlerte
    titre:        str
    message:      str
    details:      Optional[dict]    = None
    regle_code:   Optional[str]     = None
    valable_du:   Optional[datetime] = None
    valable_au:   Optional[datetime] = None
    lu:           bool
    lu_le:        Optional[datetime] = None
    action_prise: bool
    created_at:   datetime

    model_config = {"from_attributes": True}


# ── Config alertes ────────────────────────────────────────────────────────────

class ConfigAlertesUpdate(BaseModel):
    seuils:                        Optional[dict]  = None
    alertes_meteo_actives:         Optional[bool]  = None
    alertes_maladies_actives:      Optional[bool]  = None
    alertes_ravageurs_actives:     Optional[bool]  = None
    alertes_fertilisation_actives: Optional[bool]  = None
    alertes_irrigation_actives:    Optional[bool]  = None
    alertes_planificateur_actives: Optional[bool]  = None
    heure_envoi_alertes:           Optional[time]  = None


class ConfigAlertesOut(BaseModel):
    id:                            int
    org_id:                        int
    seuils:                        dict
    alertes_meteo_actives:         bool
    alertes_maladies_actives:      bool
    alertes_ravageurs_actives:     bool
    alertes_fertilisation_actives: bool
    alertes_irrigation_actives:    bool
    alertes_planificateur_actives: bool
    heure_envoi_alertes:           Optional[time]  = None

    model_config = {"from_attributes": True}


# ── Planificateur ─────────────────────────────────────────────────────────────

class PlanStatutUpdate(BaseModel):
    statut: StatutPlanificateur


class RecommandationOut(BaseModel):
    id:                 int
    parcelle_id:        Optional[int]     = None
    parcelle_nom:       Optional[str]     = None
    culture_id:         Optional[int]     = None
    culture_nom:        Optional[str]     = None
    activite_id:        Optional[int]     = None
    date_recommandee:   date
    type_activite:      Optional[str]     = None
    titre:              str
    priorite:           int
    raison:             Optional[str]     = None
    fenetre_debut:      Optional[date]    = None
    fenetre_fin:        Optional[date]    = None
    conditions_ok:      Optional[bool]   = None
    detail_conditions:  Optional[dict]   = None
    statut:             StatutPlanificateur
    source:             SourcePlanificateur
    genere_le:          datetime

    model_config = {"from_attributes": True}


# ── Analyse risque ────────────────────────────────────────────────────────────

class RisqueDetail(BaseModel):
    type:         str
    niveau:       str
    description:  str
    recommandation: Optional[str] = None


class AnalyseRisque(BaseModel):
    parcelle_id:    int
    parcelle_nom:   Optional[str]     = None
    culture_nom:    Optional[str]     = None
    score_risque:   int               = Field(ge=0, le=100)
    risques:        list[RisqueDetail]
    recommandations: list[str]
    conditions:     Optional[dict]    = None
    genere_le:      datetime


# ── Stats alertes ─────────────────────────────────────────────────────────────

class StatsAlertes(BaseModel):
    nb_total:       int
    nb_critique:    int
    nb_avertissement: int
    nb_info:        int
    nb_non_lues:    int
    taux_lecture_pct: float
    par_type:       dict[str, int]


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardMeteo(BaseModel):
    conditions_parcelles:  list[ConditionOut]
    nb_alertes_actives:    int
    nb_alertes_critiques:  int
    alertes_recentes:      list[AlerteResume]
    recommandations_top:   list[RecommandationOut]
    stats:                 StatsAlertes


# ── Résultat génération ───────────────────────────────────────────────────────

class ResultatGeneration(BaseModel):
    nb_alertes_meteo:       int = 0
    nb_alertes_agrono:      int = 0
    nb_recommandations:     int = 0
    nb_alertes_total:       int = 0
    parcelles_analysees:    int = 0
    duree_ms:               int = 0
