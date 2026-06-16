"""
Modèles SQLAlchemy — Module MON CHAMP.
Tables : champ_parcelles, champ_cartographies, champ_sols,
         champ_infrastructures, champ_sources_eau
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, Float, Boolean,
    DateTime, Date, ForeignKey, Enum, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


# ── Énumérations ───────────────────────────────────────────────────────────────

class StatutParcelle(str, enum.Enum):
    ACTIVE = "active"
    EN_CULTURE = "en_culture"
    EN_REPOS = "en_repos"
    EN_PREPARATION = "en_preparation"
    ARCHIVE = "archive"


class TypeGeometrie(str, enum.Enum):
    POLYGON = "polygon"
    POINT = "point"
    LINESTRING = "linestring"


class SourceMesure(str, enum.Enum):
    GPS_TERRAIN = "gps_terrain"
    DESSIN_CARTE = "dessin_carte"
    IMPORT_FICHIER = "import_fichier"
    ESTIMATION = "estimation"


class TextureSol(str, enum.Enum):
    SABLEUX = "sableux"
    LIMONEUX = "limoneux"
    ARGILEUX = "argileux"
    ARGILO_LIMONEUX = "argilo_limoneux"
    SABLO_LIMONEUX = "sablo_limoneux"
    LIMON_ARGILEUX = "limon_argileux"


class ErosionSol(str, enum.Enum):
    NULLE = "nulle"
    FAIBLE = "faible"
    MODEREE = "moderee"
    FORTE = "forte"
    TRES_FORTE = "tres_forte"


class EtatInfrastructure(str, enum.Enum):
    BON = "bon"
    MOYEN = "moyen"
    MAUVAIS = "mauvais"
    A_REPARER = "a_reparer"
    HORS_SERVICE = "hors_service"


class TypeSourceEau(str, enum.Enum):
    FORAGE = "forage"
    PUITS_TRADITIONNEL = "puits_traditionnel"
    COURS_EAU = "cours_eau"
    MARE_PERMANENTE = "mare_permanente"
    MARE_TEMPORAIRE = "mare_temporaire"
    RESERVOIR = "reservoir"
    EAU_DE_PLUIE = "eau_de_pluie"
    CANAL_IRRIGATION = "canal_irrigation"
    RIVIERE = "riviere"
    FLEUVE = "fleuve"
    CHATEAU_EAU = "chateau_eau"


class QualiteEau(str, enum.Enum):
    BONNE = "bonne"
    ACCEPTABLE = "acceptable"
    TRAITEE_REQUISE = "traitee_requise"
    IMPROPRE = "impropre"


class DisponibiliteEau(str, enum.Enum):
    PERMANENTE = "permanente"
    SAISONNIERE = "saisonniere"
    IRREGULIERE = "irreguliere"


# ── Modèles ────────────────────────────────────────────────────────────────────

class Parcelle(Base):
    __tablename__ = "champ_parcelles"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    nom = Column(String(200), nullable=False)
    code_parcelle = Column(String(50), unique=True, index=True)

    # Culture
    type_culture = Column(String(100))
    culture_id = Column(Integer, ForeignKey("agro_cultures.id"), nullable=True)

    # Localisation
    zone_agro = Column(String(50))
    region = Column(String(100))
    localite = Column(String(200))

    statut = Column(Enum(StatutParcelle), default=StatutParcelle.ACTIVE, nullable=False)
    description = Column(Text)

    # Calculés — mis à jour après chaque modif cartographie
    superficie_m2 = Column(Float)
    superficie_ha = Column(Float)
    perimetre_m = Column(Float)
    centre_lat = Column(Float)
    centre_lon = Column(Float)

    # Agronomie
    date_semis = Column(Date, nullable=True)
    date_recolte_prevue = Column(Date, nullable=True)
    variete = Column(String(200), nullable=True)
    stade_culture = Column(String(200), nullable=True)

    # Eau & irrigation (saisies étape 1 du wizard)
    source_eau_principale = Column(String(100), nullable=True)
    type_irrigation = Column(String(100), nullable=True)

    # Score complétude
    score_completude = Column(SmallInteger, default=0)
    score_detail = Column(JSONB)

    # Wizard de création
    etape_wizard = Column(SmallInteger, default=1)
    wizard_complet = Column(Boolean, default=False)
    date_activation = Column(DateTime(timezone=True), nullable=True)

    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relations
    cartographies = relationship("Cartographie", back_populates="parcelle",
                                 cascade="all, delete-orphan",
                                 order_by="Cartographie.created_at.desc()")
    sols = relationship("AnalyseSol", back_populates="parcelle",
                        cascade="all, delete-orphan",
                        order_by="AnalyseSol.date_analyse.desc()")
    infrastructures = relationship("Infrastructure", back_populates="parcelle",
                                   cascade="all, delete-orphan")
    sources_eau = relationship("SourceEau", back_populates="parcelle",
                               cascade="all, delete-orphan")


class Cartographie(Base):
    __tablename__ = "champ_cartographies"

    id = Column(Integer, primary_key=True, index=True)
    parcelle_id = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=False, index=True)

    type_geometrie = Column(Enum(TypeGeometrie), default=TypeGeometrie.POLYGON, nullable=False)
    coordonnees = Column(JSONB, nullable=False)   # [{lat, lon}, ...]
    projection = Column(String(20), default="WGS84")
    source_mesure = Column(Enum(SourceMesure))
    precision_m = Column(Float)
    date_mesure = Column(Date)
    actif = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=_now)

    parcelle = relationship("Parcelle", back_populates="cartographies")


class AnalyseSol(Base):
    __tablename__ = "champ_sols"

    id = Column(Integer, primary_key=True, index=True)
    parcelle_id = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=False, index=True)
    date_analyse = Column(Date)

    # Source : "satellite" | "capteur_8en1" | "laboratoire"
    source_analyse = Column(String(50), nullable=True)

    # Physique
    texture = Column(Enum(TextureSol))
    profondeur_labour_cm = Column(SmallInteger)
    pierrosite_pct = Column(Float)
    erosion = Column(Enum(ErosionSol))

    # Chimique
    pH_eau = Column(Float)
    pH_kcl = Column(Float)
    matiere_organique = Column(Float)    # %
    azote_total = Column(Float)          # g/kg
    phosphore_assim = Column(Float)      # mg/kg
    potassium_echang = Column(Float)     # cmol+/kg
    calcium = Column(Float)              # cmol+/kg
    magnesium = Column(Float)            # cmol+/kg
    sodium = Column(Float)               # cmol+/kg
    cec = Column(Float)                  # cmol+/kg
    conductivite_ds_m = Column(Float)    # dS/m

    # Capteur 8-en-1
    temperature_sol = Column(Float)      # °C
    humidite_sol = Column(Float)         # %
    salinite = Column(Float)             # mg/L ou ppm

    # Méta
    methode_analyse = Column(String(100))
    laboratoire = Column(String(200))
    reference_labo = Column(String(100))
    observations = Column(Text)

    # Analyse satellite complète (JSONB : géographie, admin, topo, hydro, risques, historique, profil)
    analyse_satellite = Column(JSONB)

    created_at = Column(DateTime(timezone=True), default=_now)

    parcelle = relationship("Parcelle", back_populates="sols")


class Infrastructure(Base):
    __tablename__ = "champ_infrastructures"

    id = Column(Integer, primary_key=True, index=True)
    parcelle_id = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=False, index=True)

    # type est désormais VARCHAR libre (migration b2c3d4e5f6g7)
    type = Column(String(100), nullable=False)
    categorie = Column(String(100))        # Eau | Irrigation | Production végétale | etc.
    nom = Column(String(200))
    description = Column(Text)
    longueur_m = Column(Float)
    superficie_m2 = Column(Float)
    capacite = Column(Float)
    unite_capacite = Column(String(20))
    etat = Column(Enum(EtatInfrastructure))
    annee_construction = Column(SmallInteger)
    localisation = Column(JSONB)           # {lat, lon}
    photo_url = Column(String(500))

    created_at = Column(DateTime(timezone=True), default=_now)

    parcelle = relationship("Parcelle", back_populates="infrastructures")


class SourceEau(Base):
    __tablename__ = "champ_sources_eau"

    id = Column(Integer, primary_key=True, index=True)
    parcelle_id = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=False, index=True)

    type = Column(Enum(TypeSourceEau), nullable=False)
    nom = Column(String(200))
    debit_m3h = Column(Float)
    profondeur_m = Column(Float)
    pH_eau = Column(Float)
    conductivite_ds_m = Column(Float)
    qualite = Column(Enum(QualiteEau))
    disponibilite = Column(Enum(DisponibiliteEau))
    partage = Column(Boolean, default=False)
    superficie_m2 = Column(Float)
    localisation = Column(JSONB)           # {lat, lon}
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), default=_now)

    parcelle = relationship("Parcelle", back_populates="sources_eau")
