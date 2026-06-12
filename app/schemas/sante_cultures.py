"""
Schémas Pydantic — Santé des Cultures + Agriculture de Précision.
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ── Requête d'analyse ────────────────────────────────────────────────────────

class CapteurData(BaseModel):
    """Données optionnelles capteur 8-en-1 (Niveau 2)."""
    sol_pH:              Optional[float] = Field(None, ge=0, le=14)
    sol_conductivite:    Optional[float] = Field(None, ge=0, description="dS/m")
    sol_azote:           Optional[float] = Field(None, ge=0, description="mg/kg")
    sol_phosphore:       Optional[float] = Field(None, ge=0, description="mg/kg")
    sol_potassium:       Optional[float] = Field(None, ge=0, description="mg/kg")
    sol_humidite:        Optional[float] = Field(None, ge=0, le=100, description="%")
    sol_temperature:     Optional[float] = Field(None, description="°C")
    sol_matiere_organique: Optional[float] = Field(None, ge=0, description="%")


class AnalyseSanteRequest(BaseModel):
    """Requête d'analyse Santé des Cultures. Le reste est automatique."""
    culture_nom:   str   = Field(..., description="Nom exact de la culture (ex: 'Riz')")
    parcelle_id:   int   = Field(..., description="ID de la parcelle à analyser")
    stade_actuel:  Optional[str]  = Field(None, description="Stade phénologique (ex: tallage)")
    mois:          Optional[int]  = Field(None, ge=1, le=12)
    zone_agro:     Optional[str]  = Field(None)
    capteur:       Optional[CapteurData] = Field(None, description="Données capteur 8-en-1 (niveau 2)")
    photo_base64:  Optional[str]  = Field(None, description="Photo base64 pour analyse visuelle (optionnel)")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "culture_nom": "Riz",
            "parcelle_id": 1,
            "stade_actuel": "tallage",
            "mois": 8,
            "capteur": {
                "sol_pH": 6.2,
                "sol_humidite": 65.0,
            }
        }
    })


# ── Résultats indices ────────────────────────────────────────────────────────

class IndicesResult(BaseModel):
    """Indices satellitaires traduits. Valeurs brutes jamais exposées."""
    date_image:     Optional[date]  = None
    vigueur:        Optional[str]   = Field(None, description="Excellent|Bon|Moyen|Faible (NDVI)")
    chlorophylle:   Optional[str]   = Field(None, description="Excellent|Bon|Moyen|Faible (NDRE)")
    stress_hydrique: Optional[str]  = Field(None, description="Excellent|Bon|Moyen|Faible (NDWI inversé)")
    vigueur_detail: Optional[str]   = Field(None, description="EVI label")
    couverture_nuages: Optional[float] = None


# ── Scores détaillés ─────────────────────────────────────────────────────────

class ScoresDetail(BaseModel):
    vigueur:    Optional[float] = Field(None, ge=0, le=100, description="Score vigueur végétale")
    hydrique:   Optional[float] = Field(None, ge=0, le=100, description="Score stress hydrique")
    fertilite:  Optional[float] = Field(None, ge=0, le=100, description="Score fertilité estimée")
    maladie:    Optional[float] = Field(None, ge=0, le=100, description="Score risque maladies (100=aucun risque)")
    ravageur:   Optional[float] = Field(None, ge=0, le=100, description="Score risque ravageurs (100=aucun risque)")


# ── Facteurs limitants ───────────────────────────────────────────────────────

class FacteurLimitant(BaseModel):
    facteur:     str
    impact_pct:  float = Field(..., description="Impact négatif sur rendement (%)")
    source:      str   = Field(..., description="satellite|rules_engine|capteur")


# ── Prévision rendement ──────────────────────────────────────────────────────

class PrevisionRendementResult(BaseModel):
    rendement_estime:    Optional[float] = Field(None, description="T/ha estimé")
    rendement_potentiel: Optional[float] = Field(None, description="T/ha potentiel de la zone")
    ecart_performance:   Optional[float] = Field(None, description="% d'écart vs potentiel")
    facteurs_limitants:  List[FacteurLimitant] = []
    confiance:           Optional[float] = Field(None, ge=0, le=1)


# ── Analyse économique ───────────────────────────────────────────────────────

class AnalyseEconomiqueResult(BaseModel):
    superficie_ha:                  Optional[float] = None
    perte_potentielle_fcfa_ha:      Optional[float] = None
    cout_correction_estime_fcfa_ha: Optional[float] = None
    gain_potentiel_fcfa_ha:         Optional[float] = None
    roi_estime:                     Optional[float] = Field(None, description="%")


# ── Réponse principale ───────────────────────────────────────────────────────

class AnalyseSanteResponse(BaseModel):
    """Réponse complète d'une analyse Santé des Cultures."""
    analyse_id:      int
    statut:          str    = Field(..., description="en_cours|termine|erreur")
    culture_evaluee: Optional[str] = None
    parcelle_id:     int
    niveau_donnees:  int    = Field(..., description="1=satellite|2=capteur|3=labo")
    duree_ms:        Optional[int] = None
    erreur_message:  Optional[str] = None

    # Score global
    score_sante:    Optional[float] = Field(None, ge=0, le=100)
    etat_general:   Optional[str]   = Field(None, description="Excellent|Bon|Moyen|Faible")

    # Détails
    scores:         Optional[ScoresDetail] = None
    indices:        Optional[IndicesResult] = None

    # Alertes et recommandations Rules Engine
    alertes:            List[Dict[str, Any]] = []
    recommandations:    List[Dict[str, Any]] = []
    regles_declenchees: int = 0

    # Prévisions et économie
    prevision_rendement:  Optional[PrevisionRendementResult] = None
    analyse_economique:   Optional[AnalyseEconomiqueResult]  = None

    # Timestamps
    analyse_le:      Optional[datetime] = None


class AnalyseSanteResume(BaseModel):
    """Résumé pour la liste historique."""
    analyse_id:     int
    statut:         str
    culture_nom:    Optional[str] = None
    score_sante:    Optional[float] = None
    etat_general:   Optional[str] = None
    niveau_donnees: int
    analyse_le:     datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyseDemarreeResponse(BaseModel):
    """Retourné immédiatement par POST /analyser (202 Accepted)."""
    analyse_id:        int
    statut:            str = "en_cours"
    message:           str = "Analyse démarrée. Utilisez GET /analyse/{id} pour le résultat."
    estimated_seconds: int = Field(15, description="Durée estimée en secondes")


# ── Niveaux données disponibles ──────────────────────────────────────────────

class NiveauxDisponibles(BaseModel):
    parcelle_id:          int
    niveau_max:           int   = Field(..., description="Niveau de données disponible (1|2|3)")
    capteur_disponible:   bool  = False
    labo_disponible:      bool  = False
    satellite_cache:      bool  = False   # indices récents en cache (<10j)
    description_niveau:   str   = ""


# ── Cartes ───────────────────────────────────────────────────────────────────

class CarteInfo(BaseModel):
    type_carte:   str
    resolution_m: int
    nb_cellules:  int
    created_at:   datetime

    model_config = ConfigDict(from_attributes=True)


# ── Série temporelle indices ─────────────────────────────────────────────────

class IndicesHistorique(BaseModel):
    date_image:   date
    satellite:    str
    ndvi_label:   Optional[str] = None
    ndre_label:   Optional[str] = None
    ndwi_label:   Optional[str] = None
    couverture_nuages: Optional[float] = None
    analyse_id:   Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
