"""
Schémas Pydantic — Base Agronomique AgroScan Pro.
Séparation lecture/écriture ; from_attributes=True pour SQLAlchemy.
"""
from typing import Optional, List, Any
from pydantic import BaseModel


# ─────────────────────────────────────────────
#  Sous-entités (lecture)
# ─────────────────────────────────────────────

class VarieteOut(BaseModel):
    id: int
    nom: str
    origine: Optional[str]
    cycle_min_jours: Optional[int]
    cycle_max_jours: Optional[int]
    precocite: Optional[str]
    tolerance_secheresse: bool
    tolerance_salinite: bool
    zones_adaptees: Optional[Any]
    rendement_potentiel_t_ha: Optional[float]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ParametreClimatiqueOut(BaseModel):
    temp_min_c: Optional[float]
    temp_opt_min_c: Optional[float]
    temp_opt_max_c: Optional[float]
    temp_max_c: Optional[float]
    pluvio_min_mm: Optional[int]
    pluvio_opt_mm: Optional[int]
    pluvio_max_mm: Optional[int]
    ph_min: Optional[float]
    ph_opt_min: Optional[float]
    ph_opt_max: Optional[float]
    ph_max: Optional[float]
    texture_preferee: Optional[str]
    ensoleillement_h: Optional[float]

    class Config:
        from_attributes = True


class BesoinEauOut(BaseModel):
    stade: str
    besoin_mm_semaine: Optional[float]
    sensibilite: Optional[str]
    frequence_irrigation: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class BesoinNutritionnelOut(BaseModel):
    stade: str
    azote_kg_ha: Optional[float]
    phosphore_kg_ha: Optional[float]
    potassium_kg_ha: Optional[float]
    calcium_kg_ha: Optional[float]
    magnesium_kg_ha: Optional[float]
    engrais_recommandes: Optional[str]
    moment_application: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class StadeOut(BaseModel):
    ordre: int
    nom_stade: str
    jours_debut: Optional[int]
    jours_fin: Optional[int]
    description: Optional[str]
    actions_cles: Optional[Any]
    indicateurs_visuels: Optional[str]

    class Config:
        from_attributes = True


class CalendrierOut(BaseModel):
    zone_agro: str
    saison: str
    mois_semis_debut: Optional[int]
    mois_semis_fin: Optional[int]
    mois_recolte_debut: Optional[int]
    mois_recolte_fin: Optional[int]
    remarques: Optional[str]

    class Config:
        from_attributes = True


class RendementOut(BaseModel):
    zone_agro: Optional[str]
    pratique: str
    rendement_min_t_ha: Optional[float]
    rendement_max_t_ha: Optional[float]
    rendement_moyen_t_ha: Optional[float]
    unite: Optional[str]
    source: Optional[str]

    class Config:
        from_attributes = True


class MaladieOut(BaseModel):
    id: int
    nom: str
    nom_scientifique: Optional[str]
    pathogene_type: Optional[str]
    symptomes: str
    conditions_favorables: Optional[str]

    class Config:
        from_attributes = True


class CultureMaladieOut(BaseModel):
    maladie: MaladieOut
    frequence: Optional[str]
    gravite: Optional[str]
    stade_sensible: Optional[str]
    pertes_estimees: Optional[str]
    prevention: Optional[str]
    traitement: str

    class Config:
        from_attributes = True


class RavageurOut(BaseModel):
    id: int
    nom: str
    nom_scientifique: Optional[str]
    type_ravageur: Optional[str]
    description: Optional[str]
    symptomes_degats: str

    class Config:
        from_attributes = True


class CultureRavageurOut(BaseModel):
    ravageur: RavageurOut
    frequence: Optional[str]
    gravite: Optional[str]
    stade_sensible: Optional[str]
    pertes_estimees: Optional[str]
    prevention: Optional[str]
    lutte: str

    class Config:
        from_attributes = True


class RecommandationOut(BaseModel):
    categorie_reco: str
    titre: str
    contenu: str
    priorite: int
    zone_agro: Optional[str]
    mois_applicable: Optional[Any]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Culture — résumé (liste)
# ─────────────────────────────────────────────

class CultureResume(BaseModel):
    id: int
    nom: str
    nom_scientifique: Optional[str]
    nom_local: Optional[str]
    famille: Optional[str]
    categorie: str
    icone: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Culture — fiche complète
# ─────────────────────────────────────────────

class CultureDetail(CultureResume):
    varietes: List[VarieteOut] = []
    parametres_climatiques: Optional[ParametreClimatiqueOut] = None
    besoins_eau: List[BesoinEauOut] = []
    besoins_nutritionnels: List[BesoinNutritionnelOut] = []
    stades: List[StadeOut] = []
    calendriers: List[CalendrierOut] = []
    rendements: List[RendementOut] = []
    culture_maladies: List[CultureMaladieOut] = []
    culture_ravageurs: List[CultureRavageurOut] = []
    recommandations: List[RecommandationOut] = []

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
#  Réponse stade actuel (OAD)
# ─────────────────────────────────────────────

class StadeActuelOut(BaseModel):
    culture: str
    date_semis: str
    jours_depuis_semis: int
    stade_actuel: Optional[str]
    stade_suivant: Optional[str]
    jours_restants_stade: Optional[int]
    actions_urgentes: List[str] = []
    message_producteur: str         # phrase simple sans jargon


# ─────────────────────────────────────────────
#  Recommandation cultures adaptées (OAD)
# ─────────────────────────────────────────────

class CultureAdapteeOut(BaseModel):
    culture: CultureResume
    score_adaptation: int           # 0-100
    raisons: List[str]
    periode_semis: Optional[str]
    rendement_attendu: Optional[str]
