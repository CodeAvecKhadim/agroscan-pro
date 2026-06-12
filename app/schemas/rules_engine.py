"""
Schémas Pydantic — Rules Engine AgroScan Pro.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Contexte d'entrée ────────────────────────────────────────────────────────

class RulesContext(BaseModel):
    """Contexte complet fourni au moteur d'évaluation."""

    # Culture (requis)
    culture_nom: str = Field(..., description="Nom exact de la culture (ex : 'Riz')")

    # Parcelle / org (optionnels — pour persistance du journal)
    org_id: Optional[int] = None
    parcelle_id: Optional[int] = None

    # Localisation
    zone_agro: Optional[str] = Field(None, description="vallee_fleuve | niayes | bassin_arachidier | …")

    # Stade phénologique
    stade_actuel: Optional[str] = Field(None, description="Ex : tallage, floraison, fructification")
    mois: Optional[int] = Field(None, ge=1, le=12, description="Mois en cours (1–12)")
    jours_semis: Optional[int] = Field(None, ge=0, description="Jours depuis le semis")

    # Sol (depuis analyses)
    sol_pH: Optional[float] = Field(None, ge=0, le=14)
    sol_azote: Optional[float] = Field(None, ge=0, description="mg/kg")
    sol_phosphore: Optional[float] = Field(None, ge=0, description="mg/kg")
    sol_potassium: Optional[float] = Field(None, ge=0, description="mg/kg")
    sol_humidite: Optional[float] = Field(None, ge=0, le=100, description="%")
    sol_temperature: Optional[float] = Field(None, description="°C")
    sol_matiere_organique: Optional[float] = Field(None, ge=0, description="%")
    sol_conductivite: Optional[float] = Field(None, ge=0, description="dS/m — ex: 1.0=normal, 4.0=salin, 8.0=très salin")

    # Météo
    meteo_temp_air: Optional[float] = Field(None, description="°C")
    meteo_humidite_rel: Optional[float] = Field(None, ge=0, le=100, description="%")
    meteo_pluie_24h: Optional[float] = Field(None, ge=0, description="mm")
    meteo_pluie_7j: Optional[float] = Field(None, ge=0, description="mm")
    meteo_vent: Optional[float] = Field(None, ge=0, description="km/h")
    meteo_etp: Optional[float] = Field(None, ge=0, description="mm/j")

    # Observations terrain
    obs_symptomes: List[str] = Field(default_factory=list, description="Symptômes observés")
    obs_ravageurs: List[str] = Field(default_factory=list, description="Ravageurs observés")
    obs_densite_ravageur: Optional[str] = Field(None, description="faible | moyenne | elevee")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "culture_nom": "Riz",
            "zone_agro": "vallee_fleuve",
            "stade_actuel": "tallage",
            "mois": 8,
            "meteo_temp_air": 27.0,
            "meteo_humidite_rel": 92.0,
            "meteo_pluie_24h": 18.0,
            "meteo_pluie_7j": 68.0,
        }
    })


# ── Résultats d'évaluation ───────────────────────────────────────────────────

class AlerteResult(BaseModel):
    niveau: str
    titre: str
    message: str


class RecommandationResult(BaseModel):
    priorite: int
    type: str
    titre: str
    detail: Optional[str] = None
    produit: Optional[str] = None
    dose: Optional[str] = None
    delai_carence_jours: Optional[int] = None
    urgence_jours: Optional[int] = None


class RisqueResult(BaseModel):
    score: float
    libelle: str


class RegleDeclencheeResult(BaseModel):
    code: str
    nom: str
    categorie: str
    sous_categorie: Optional[str] = None
    gravite: str
    priorite: int
    confiance: float
    alertes: List[AlerteResult] = []
    recommandations: List[RecommandationResult] = []
    risque: Optional[RisqueResult] = None


class EvaluationResponse(BaseModel):
    culture_evaluee: str
    zone: Optional[str] = None
    stade: Optional[str] = None
    regles_evaluees: int
    regles_declenchees: int
    duree_ms: int
    alertes_critiques: int
    alertes_elevees: int
    resultats: List[RegleDeclencheeResult]


# ── Admin ────────────────────────────────────────────────────────────────────

class RegleListItem(BaseModel):
    id: int
    code: str
    categorie: str
    sous_categorie: Optional[str] = None
    nom: str
    gravite: str
    priorite: int
    confiance: float
    plan_requis: str
    active: bool
    nb_cultures: int = 0

    model_config = ConfigDict(from_attributes=True)


class RegleDetail(RegleListItem):
    description: Optional[str] = None
    zones_applicables: Optional[Any] = None
    stades_applicables: Optional[Any] = None
    mois_applicables: Optional[Any] = None
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    source: Optional[str] = None
    version: str
