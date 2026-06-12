"""
Schémas Pydantic V2 — Module MON CHAMP.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

from app.models.champ import (
    StatutParcelle, TypeGeometrie, SourceMesure, TextureSol, ErosionSol,
    TypeInfrastructure, EtatInfrastructure, TypeSourceEau, QualiteEau, DisponibiliteEau,
)


# ── Coordonnée GPS ──────────────────────────────────────────────────────────────

class CoordGPS(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


# ── PARCELLE ────────────────────────────────────────────────────────────────────

class ParcelleCreate(BaseModel):
    nom: str = Field(..., min_length=1, max_length=200)
    code_parcelle: Optional[str] = Field(None, max_length=50)
    type_culture: Optional[str] = None
    culture_id: Optional[int] = None
    zone_agro: Optional[str] = None
    region: Optional[str] = None
    localite: Optional[str] = None
    statut: StatutParcelle = StatutParcelle.ACTIVE
    description: Optional[str] = None
    date_semis: Optional[date] = None
    variete: Optional[str] = Field(None, max_length=200)
    stade_culture: Optional[str] = Field(None, max_length=200)


class ParcelleUpdate(BaseModel):
    nom: Optional[str] = Field(None, max_length=200)
    type_culture: Optional[str] = None
    culture_id: Optional[int] = None
    zone_agro: Optional[str] = None
    region: Optional[str] = None
    localite: Optional[str] = None
    statut: Optional[StatutParcelle] = None
    description: Optional[str] = None
    date_semis: Optional[date] = None
    variete: Optional[str] = Field(None, max_length=200)
    stade_culture: Optional[str] = Field(None, max_length=200)


class ParcelleSummary(BaseModel):
    id: int
    nom: str
    code_parcelle: Optional[str] = None
    type_culture: Optional[str] = None
    zone_agro: Optional[str] = None
    region: Optional[str] = None
    statut: StatutParcelle
    superficie_ha: Optional[float] = None
    score_completude: int
    date_semis: Optional[date] = None
    stade_culture: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ParcelleOut(BaseModel):
    id: int
    org_id: int
    nom: str
    code_parcelle: Optional[str] = None
    type_culture: Optional[str] = None
    culture_id: Optional[int] = None
    zone_agro: Optional[str] = None
    region: Optional[str] = None
    localite: Optional[str] = None
    statut: StatutParcelle
    description: Optional[str] = None
    superficie_m2: Optional[float] = None
    superficie_ha: Optional[float] = None
    perimetre_m: Optional[float] = None
    centre_lat: Optional[float] = None
    centre_lon: Optional[float] = None
    score_completude: int
    score_detail: Optional[Dict[str, Any]] = None
    date_semis: Optional[date] = None
    variete: Optional[str] = None
    stade_culture: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ParcelleDetail(ParcelleOut):
    cartographie_active: Optional[CartographieOut] = None
    sol_recent: Optional[AnalyseSolOut] = None
    infrastructures: List[InfrastructureOut] = []
    sources_eau: List[SourceEauOut] = []


# ── CARTOGRAPHIE ────────────────────────────────────────────────────────────────

class CartographieCreate(BaseModel):
    type_geometrie: TypeGeometrie = TypeGeometrie.POLYGON
    coordonnees: List[CoordGPS] = Field(..., min_length=3)
    projection: str = "WGS84"
    source_mesure: Optional[SourceMesure] = None
    precision_m: Optional[float] = None
    date_mesure: Optional[date] = None

    @model_validator(mode="after")
    def polygon_needs_3_points(self):
        if self.type_geometrie == TypeGeometrie.POLYGON and len(self.coordonnees) < 3:
            raise ValueError("Un polygon nécessite au moins 3 points.")
        return self


class CartographieOut(BaseModel):
    id: int
    parcelle_id: int
    type_geometrie: TypeGeometrie
    coordonnees: List[Dict[str, float]]
    projection: str
    source_mesure: Optional[SourceMesure] = None
    precision_m: Optional[float] = None
    date_mesure: Optional[date] = None
    actif: bool
    # Métriques calculées (depuis la parcelle)
    superficie_m2: Optional[float] = None
    superficie_ha: Optional[float] = None
    perimetre_m: Optional[float] = None
    centre_lat: Optional[float] = None
    centre_lon: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── ANALYSE SOL ─────────────────────────────────────────────────────────────────

class AnalyseSolCreate(BaseModel):
    date_analyse: Optional[date] = None
    texture: Optional[TextureSol] = None
    profondeur_labour_cm: Optional[int] = Field(None, ge=0, le=200)
    pierrosite_pct: Optional[float] = Field(None, ge=0, le=100)
    erosion: Optional[ErosionSol] = None
    pH_eau: Optional[float] = Field(None, ge=0, le=14)
    pH_kcl: Optional[float] = Field(None, ge=0, le=14)
    matiere_organique: Optional[float] = Field(None, ge=0, le=100)
    azote_total: Optional[float] = Field(None, ge=0)
    phosphore_assim: Optional[float] = Field(None, ge=0)
    potassium_echang: Optional[float] = Field(None, ge=0)
    calcium: Optional[float] = Field(None, ge=0)
    magnesium: Optional[float] = Field(None, ge=0)
    sodium: Optional[float] = Field(None, ge=0)
    cec: Optional[float] = Field(None, ge=0)
    conductivite_ds_m: Optional[float] = Field(None, ge=0)
    methode_analyse: Optional[str] = None
    laboratoire: Optional[str] = None
    reference_labo: Optional[str] = None
    observations: Optional[str] = None


class AnalyseSolOut(AnalyseSolCreate):
    id: int
    parcelle_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── INFRASTRUCTURE ──────────────────────────────────────────────────────────────

class InfrastructureCreate(BaseModel):
    type: TypeInfrastructure
    nom: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    longueur_m: Optional[float] = Field(None, ge=0)
    superficie_m2: Optional[float] = Field(None, ge=0)
    capacite: Optional[float] = Field(None, ge=0)
    unite_capacite: Optional[str] = None
    etat: Optional[EtatInfrastructure] = None
    annee_construction: Optional[int] = Field(None, ge=1900, le=2100)
    localisation: Optional[CoordGPS] = None


class InfrastructureUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    longueur_m: Optional[float] = None
    superficie_m2: Optional[float] = None
    capacite: Optional[float] = None
    unite_capacite: Optional[str] = None
    etat: Optional[EtatInfrastructure] = None
    annee_construction: Optional[int] = None
    localisation: Optional[CoordGPS] = None


class InfrastructureOut(BaseModel):
    id: int
    parcelle_id: int
    type: TypeInfrastructure
    nom: Optional[str] = None
    description: Optional[str] = None
    longueur_m: Optional[float] = None
    superficie_m2: Optional[float] = None
    capacite: Optional[float] = None
    unite_capacite: Optional[str] = None
    etat: Optional[EtatInfrastructure] = None
    annee_construction: Optional[int] = None
    localisation: Optional[Dict[str, float]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── SOURCE EAU ──────────────────────────────────────────────────────────────────

class SourceEauCreate(BaseModel):
    type: TypeSourceEau
    nom: Optional[str] = Field(None, max_length=200)
    debit_m3h: Optional[float] = Field(None, ge=0)
    profondeur_m: Optional[float] = Field(None, ge=0)
    pH_eau: Optional[float] = Field(None, ge=0, le=14)
    conductivite_ds_m: Optional[float] = Field(None, ge=0)
    qualite: Optional[QualiteEau] = None
    disponibilite: Optional[DisponibiliteEau] = None
    partage: bool = False
    superficie_m2: Optional[float] = Field(None, ge=0)
    localisation: Optional[CoordGPS] = None


class SourceEauUpdate(BaseModel):
    nom: Optional[str] = None
    debit_m3h: Optional[float] = None
    profondeur_m: Optional[float] = None
    pH_eau: Optional[float] = None
    conductivite_ds_m: Optional[float] = None
    qualite: Optional[QualiteEau] = None
    disponibilite: Optional[DisponibiliteEau] = None
    partage: Optional[bool] = None
    superficie_m2: Optional[float] = None
    localisation: Optional[CoordGPS] = None


class SourceEauOut(BaseModel):
    id: int
    parcelle_id: int
    type: TypeSourceEau
    nom: Optional[str] = None
    debit_m3h: Optional[float] = None
    profondeur_m: Optional[float] = None
    pH_eau: Optional[float] = None
    conductivite_ds_m: Optional[float] = None
    qualite: Optional[QualiteEau] = None
    disponibilite: Optional[DisponibiliteEau] = None
    partage: bool
    superficie_m2: Optional[float] = None
    localisation: Optional[Dict[str, float]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── SCORE COMPLÉTUDE ────────────────────────────────────────────────────────────

class DimensionScore(BaseModel):
    score: int        # 0 ou valeur partielle
    max: int
    pct: float
    complete: bool
    manquant: Optional[str] = None


class ScoreCompletude(BaseModel):
    total: int        # 0-100
    cartographie: DimensionScore
    sol: DimensionScore
    culture_zone: DimensionScore
    sources_eau: DimensionScore
    infrastructures: DimensionScore
    localisation: DimensionScore
    manquants: List[str]


# ── RAPPORT INITIAL ─────────────────────────────────────────────────────────────

class RapportInitial(BaseModel):
    parcelle: ParcelleOut
    cartographie: Optional[CartographieOut] = None
    sol: Optional[AnalyseSolOut] = None
    infrastructures: List[InfrastructureOut] = []
    sources_eau: List[SourceEauOut] = []
    score: ScoreCompletude
    genere_le: datetime


# Résoudre les références forward
ParcelleDetail.model_rebuild()
