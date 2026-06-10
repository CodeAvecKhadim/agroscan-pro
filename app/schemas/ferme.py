"""
Schémas Pydantic V2 — Module GESTION DE FERME.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

from app.models.ferme import (
    TypeActivite, StatutActivite,
    TypePreuve, SourcePreuve,
    CategorieCoût, TypeMainOeuvre, TypeJournal,
)


# ── ACTIVITÉ ────────────────────────────────────────────────────────────────────

class ActiviteCreate(BaseModel):
    type: TypeActivite
    titre: str = Field(..., min_length=1, max_length=200)
    parcelle_id: Optional[int] = None
    culture_id: Optional[int] = None
    consultation_id: Optional[int] = None
    description: Optional[str] = None
    date_prevue: Optional[date] = None
    stade_culture: Optional[str] = None
    surface_traitee_ha: Optional[float] = Field(None, gt=0)
    details: Dict[str, Any] = Field(default_factory=dict)
    note: Optional[str] = None


class ActiviteUpdate(BaseModel):
    titre: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    date_prevue: Optional[date] = None
    stade_culture: Optional[str] = None
    surface_traitee_ha: Optional[float] = Field(None, gt=0)
    details: Optional[Dict[str, Any]] = None
    note: Optional[str] = None


class DemarrerActivite(BaseModel):
    conditions_meteo: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="{temp_air, humidite_rel, pluie_24h, vent}"
    )
    localisation_debut: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="{lat, lon, precision_m}"
    )


class TerminerActivite(BaseModel):
    date_fin: Optional[datetime] = None
    duree_minutes: Optional[int] = Field(None, gt=0)
    note: Optional[str] = None
    details_complementaires: Optional[Dict[str, Any]] = None


class ActiviteOut(BaseModel):
    id: int
    org_id: int
    parcelle_id: Optional[int] = None
    culture_id: Optional[int] = None
    consultation_id: Optional[int] = None
    type: TypeActivite
    statut: StatutActivite
    titre: str
    description: Optional[str] = None
    date_prevue: Optional[date] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    duree_minutes: Optional[int] = None
    stade_culture: Optional[str] = None
    surface_traitee_ha: Optional[float] = None
    conditions_meteo: Dict[str, Any]
    localisation_debut: Dict[str, Any]
    details: Dict[str, Any]
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Calculé à la volée
    cout_total_fcfa: Optional[int] = None
    nb_preuves: Optional[int] = None

    model_config = {"from_attributes": True}


class ActiviteDetail(ActiviteOut):
    preuves: List[PreuveOut] = []
    couts: List[CoutOut] = []
    main_oeuvre: List[MainOeuvreOut] = []
    journal: List[JournalOut] = []


# ── PREUVE ──────────────────────────────────────────────────────────────────────

class PreuveOut(BaseModel):
    id: int
    activite_id: int
    type: TypePreuve
    filename: str
    url: str
    thumbnail_url: Optional[str] = None
    duree_secondes: Optional[int] = None
    taille_ko: Optional[int] = None
    source: Optional[SourcePreuve] = None
    localisation: Dict[str, Any]
    horodatage_terrain: Optional[datetime] = None
    photo_meta: Dict[str, Any]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ── COÛT ────────────────────────────────────────────────────────────────────────

class CoutCreate(BaseModel):
    categorie: CategorieCoût
    sous_categorie: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=300)
    quantite: Optional[float] = Field(None, gt=0)
    unite: Optional[str] = Field(None, max_length=30)
    prix_unitaire_fcfa: Optional[int] = Field(None, ge=0)
    montant_total_fcfa: Optional[int] = Field(None, ge=0)
    fournisseur: Optional[str] = Field(None, max_length=200)
    date_achat: Optional[date] = None
    recu: bool = False
    note: Optional[str] = None

    @model_validator(mode="after")
    def calculer_montant(self):
        if self.montant_total_fcfa is None:
            if self.prix_unitaire_fcfa is not None and self.quantite is not None:
                self.montant_total_fcfa = int(self.prix_unitaire_fcfa * self.quantite)
            else:
                raise ValueError("montant_total_fcfa requis si prix_unitaire ou quantite absent.")
        return self


class CoutUpdate(BaseModel):
    categorie: Optional[CategorieCoût] = None
    sous_categorie: Optional[str] = None
    description: Optional[str] = None
    quantite: Optional[float] = None
    unite: Optional[str] = None
    prix_unitaire_fcfa: Optional[int] = None
    montant_total_fcfa: Optional[int] = None
    fournisseur: Optional[str] = None
    date_achat: Optional[date] = None
    recu: Optional[bool] = None
    note: Optional[str] = None


class CoutOut(BaseModel):
    id: int
    activite_id: int
    categorie: CategorieCoût
    sous_categorie: Optional[str] = None
    description: str
    quantite: Optional[float] = None
    unite: Optional[str] = None
    prix_unitaire_fcfa: Optional[int] = None
    montant_total_fcfa: int
    fournisseur: Optional[str] = None
    date_achat: Optional[date] = None
    recu: bool
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── MAIN-D'ŒUVRE ────────────────────────────────────────────────────────────────

class MainOeuvreCreate(BaseModel):
    type: TypeMainOeuvre
    description: Optional[str] = Field(None, max_length=200)
    nb_personnes: int = Field(1, ge=1)
    duree_jours: float = Field(..., gt=0)
    taux_journalier_fcfa: int = Field(0, ge=0)
    note: Optional[str] = None

    @model_validator(mode="after")
    def calculer_montant(self):
        self._montant = int(self.taux_journalier_fcfa * self.duree_jours * self.nb_personnes)
        return self


class MainOeuvreOut(BaseModel):
    id: int
    activite_id: int
    type: TypeMainOeuvre
    description: Optional[str] = None
    nb_personnes: int
    duree_jours: float
    taux_journalier_fcfa: int
    montant_total_fcfa: int
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── JOURNAL ──────────────────────────────────────────────────────────────────────

class JournalCreate(BaseModel):
    date_entree: date
    type: TypeJournal = TypeJournal.NOTE_TERRAIN
    titre: Optional[str] = Field(None, max_length=200)
    contenu: str = Field(..., min_length=1)
    parcelle_id: Optional[int] = None
    activite_id: Optional[int] = None


class JournalOut(BaseModel):
    id: int
    org_id: int
    parcelle_id: Optional[int] = None
    activite_id: Optional[int] = None
    date_entree: date
    type: TypeJournal
    titre: Optional[str] = None
    contenu: str
    created_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── BILANS ───────────────────────────────────────────────────────────────────────

class LigneActiviteBilan(BaseModel):
    id: int
    type: TypeActivite
    titre: str
    statut: StatutActivite
    date_prevue: Optional[date] = None
    date_fin: Optional[datetime] = None
    cout_total_fcfa: int
    nb_preuves: int


class BilanParcelle(BaseModel):
    parcelle_id: int
    parcelle_nom: Optional[str] = None
    culture_nom: Optional[str] = None
    surface_ha: Optional[float] = None
    periode_debut: Optional[date] = None
    periode_fin: Optional[date] = None
    nb_activites: int
    activites: List[LigneActiviteBilan]
    cout_intrants_fcfa: int
    cout_materiel_fcfa: int
    cout_main_oeuvre_fcfa: int
    cout_transport_fcfa: int
    cout_autre_fcfa: int
    cout_total_fcfa: int
    cout_par_ha_fcfa: Optional[int] = None
    rendement_kg_ha: Optional[float] = None       # depuis activité récolte
    rendement_reference_kg_ha: Optional[float] = None
    ecart_rendement_pct: Optional[float] = None
    genere_le: datetime


class StatsActivites(BaseModel):
    total_activites: int
    par_type: Dict[str, int]
    par_statut: Dict[str, int]
    cout_total_fcfa: int
    cout_moyen_par_activite_fcfa: int
    nb_parcelles_actives: int
    nb_preuves_total: int


# Résoudre références forward
ActiviteDetail.model_rebuild()
