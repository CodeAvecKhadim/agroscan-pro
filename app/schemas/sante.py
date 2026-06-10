"""
Schémas Pydantic V2 — Module SANTÉ DES CULTURES.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

from app.models.sante import (
    TypeConsultation, StatutConsultation,
    TypeObservation, PartiePlante, SourcePhoto,
    TypeEntite, MethodeDiagnostic, StatutDiagnostic,
    TypeTraitement, StatutTraitement, EvolutionSuivi, TypeRapport,
)


# ── CONSULTATION ────────────────────────────────────────────────────────────────

class ConsultationCreate(BaseModel):
    type: TypeConsultation
    parcelle_id: Optional[int] = None
    culture_id: Optional[int] = None
    stade_actuel: Optional[str] = None   # "floraison", "végétatif", …
    mois: Optional[int] = Field(None, ge=1, le=12)
    zone_agro: Optional[str] = None


class ConsultationUpdate(BaseModel):
    statut: Optional[StatutConsultation] = None
    resume: Optional[str] = None


class ConsultationOut(BaseModel):
    id: int
    org_id: int
    parcelle_id: Optional[int] = None
    culture_id: Optional[int] = None
    type: TypeConsultation
    statut: StatutConsultation
    contexte: Dict[str, Any]
    resume: Optional[str] = None
    nb_photos: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConsultationDetail(ConsultationOut):
    observations: List[ObservationOut] = []
    photos: List[PhotoOut] = []
    diagnostics: List[DiagnosticOut] = []
    traitements: List[TraitementOut] = []
    suivis: List[SuiviOut] = []


# ── OBSERVATION ─────────────────────────────────────────────────────────────────

class ObservationCreate(BaseModel):
    type: TypeObservation
    partie_plante: Optional[PartiePlante] = None
    valeur: Dict[str, Any] = Field(..., description=(
        "symptome: {code, intensite} | "
        "ravageur_observe: {nom, densite, stade} | "
        "sol: {pH, humidite, azote, phosphore, potassium} | "
        "meteo: {temp_air, humidite_rel, pluie_24h, pluie_7j}"
    ))
    note_terrain: Optional[str] = None


class ObservationOut(BaseModel):
    id: int
    consultation_id: int
    type: TypeObservation
    partie_plante: Optional[PartiePlante] = None
    valeur: Dict[str, Any]
    note_terrain: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── PHOTO ───────────────────────────────────────────────────────────────────────

class PhotoOut(BaseModel):
    id: int
    consultation_id: int
    observation_id: Optional[int] = None
    source_photo: Optional[SourcePhoto] = None
    filename: str
    url: str
    thumbnail_url: Optional[str] = None
    taille_ko: Optional[int] = None
    photo_meta: Dict[str, Any]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ── DIAGNOSTIC ──────────────────────────────────────────────────────────────────

class DiagnosticOut(BaseModel):
    id: int
    consultation_id: int
    rang: int
    entite_type: TypeEntite
    entite_id: int
    entite_nom: Optional[str] = None
    score_confiance: float
    score_rules: float
    score_symptomes: float
    regles_matches: List[str]
    methode: MethodeDiagnostic
    statut: StatutDiagnostic
    confirme_par: Optional[int] = None
    confirme_le: Optional[datetime] = None
    note_expert: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DiagnosticConfirm(BaseModel):
    statut: StatutDiagnostic   # confirme | exclu
    note_expert: Optional[str] = None

    @model_validator(mode="after")
    def statut_must_be_terminal(self):
        if self.statut == StatutDiagnostic.PROBABLE:
            raise ValueError("statut doit être 'confirme' ou 'exclu'.")
        return self


# ── TRAITEMENT ──────────────────────────────────────────────────────────────────

class TraitementOut(BaseModel):
    id: int
    consultation_id: int
    diagnostic_id: Optional[int] = None
    priorite: int
    type: TypeTraitement
    titre: str
    produit: Optional[str] = None
    dose: Optional[str] = None
    frequence: Optional[str] = None
    delai_carence_jours: Optional[int] = None
    urgence_jours: Optional[int] = None
    detail: Optional[str] = None
    date_application: Optional[date] = None
    statut: StatutTraitement
    applique_le: Optional[date] = None
    note: Optional[str] = None

    model_config = {"from_attributes": True}


class TraitementAppliquer(BaseModel):
    applique_le: Optional[date] = None
    note: Optional[str] = None


class TraitementSkip(BaseModel):
    note: Optional[str] = None


# ── SUIVI ───────────────────────────────────────────────────────────────────────

class SuiviCreate(BaseModel):
    date_suivi: date
    evolution: Optional[EvolutionSuivi] = None
    efficacite: Optional[int] = Field(None, ge=1, le=5)
    note: Optional[str] = None
    photo_url: Optional[str] = None


class SuiviOut(BaseModel):
    id: int
    consultation_id: int
    date_suivi: date
    evolution: Optional[EvolutionSuivi] = None
    efficacite: Optional[int] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── RAPPORT ─────────────────────────────────────────────────────────────────────

class RapportOut(BaseModel):
    id: int
    consultation_id: int
    org_id: int
    type: TypeRapport
    titre: str
    url: str
    taille_ko: Optional[int] = None
    genere_par: Optional[int] = None
    genere_le: datetime
    telechargements: int

    model_config = {"from_attributes": True}


# ── RÉSULTAT ANALYSE ────────────────────────────────────────────────────────────

class AnalyseResult(BaseModel):
    """Retour du endpoint POST /analyser."""
    consultation_id: int
    type: TypeConsultation
    diagnostics: List[DiagnosticOut]
    traitements: List[TraitementOut]
    resume: str
    duree_ms: int


# ── FICHES RÉFÉRENTIELLES ────────────────────────────────────────────────────────

class FicheMaladie(BaseModel):
    id: int
    nom: str
    nom_scientifique: Optional[str] = None
    pathogene_type: Optional[str] = None
    symptomes: str
    conditions_favorables: Optional[str] = None
    # Données issue de agro_culture_maladies pour la culture sélectionnée
    gravite: Optional[str] = None
    frequence: Optional[str] = None
    stade_sensible: Optional[str] = None
    pertes_estimees: Optional[str] = None
    prevention: Optional[str] = None
    traitement: Optional[str] = None


class FicheRavageur(BaseModel):
    id: int
    nom: str
    nom_scientifique: Optional[str] = None
    type_ravageur: Optional[str] = None
    description: Optional[str] = None
    symptomes_degats: str
    # Données issue de agro_culture_ravageurs
    gravite: Optional[str] = None
    frequence: Optional[str] = None
    stade_sensible: Optional[str] = None
    pertes_estimees: Optional[str] = None
    prevention: Optional[str] = None
    lutte: Optional[str] = None


# ── STATS ────────────────────────────────────────────────────────────────────────

class StatEntite(BaseModel):
    nom: str
    nb_consultations: int
    taux_confirmation_pct: float


class StatsConsultations(BaseModel):
    total_consultations: int
    maladies: int
    ravageurs: int
    fertilisations: int
    top_maladies: List[StatEntite]
    top_ravageurs: List[StatEntite]
    taux_confirmation_global_pct: float


# Résoudre les références forward
ConsultationDetail.model_rebuild()
