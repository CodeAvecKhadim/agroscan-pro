"""
Modèles SQLAlchemy — Base Agronomique AgroScan Pro.

Architecture : 11 tables couvrant 20 cultures prioritaires du Sénégal.
Zones agro-écologiques : vallée_fleuve, niayes, bassin_arachidier,
                         senegal_oriental, casamance, zone_sylvopastorale
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Text, DateTime,
    ForeignKey, CheckConstraint, UniqueConstraint, Index, ARRAY
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def now_utc():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────
#  Énumérations
# ─────────────────────────────────────────────

class CategorieCulture(str, enum.Enum):
    GRANDES_CULTURES = "grandes_cultures"
    MARAICHAGE       = "maraichage"
    ARBORICULTURE    = "arboriculture"

class Frequence(str, enum.Enum):
    TRES_FREQUENTE = "tres_frequente"
    FREQUENTE      = "frequente"
    OCCASIONNELLE  = "occasionnelle"

class Pratique(str, enum.Enum):
    SUBSISTANCE = "subsistance"
    AMELIOREE   = "amelioree"
    INTENSIVE   = "intensive"

class Saison(str, enum.Enum):
    HIVERNAGE      = "hivernage"
    SAISON_SECHE   = "saison_seche"
    CONTRE_SAISON  = "contre_saison"

ZONES_AGRO = [
    "vallee_fleuve",        # Saint-Louis, Matam, Podor — irrigué
    "niayes",               # Côte Dakar→Saint-Louis — maraîchage
    "bassin_arachidier",    # Kaolack, Thiès, Diourbel, Kaffrine
    "senegal_oriental",     # Tambacounda, Kédougou — humid
    "casamance",            # Ziguinchor, Sédhiou, Kolda — humid
    "zone_sylvopastorale",  # Louga, Matam — aride/semi-aride
]


# ─────────────────────────────────────────────
#  1. CULTURES
# ─────────────────────────────────────────────

class Culture(Base):
    __tablename__ = "agro_cultures"

    id              = Column(Integer, primary_key=True)
    nom             = Column(String(100), nullable=False, unique=True)
    nom_scientifique = Column(String(200))
    nom_local       = Column(String(200))          # wolof / diola / pulaar
    famille         = Column(String(100))          # Poaceae, Solanaceae…
    categorie       = Column(String(30), nullable=False)
    icone           = Column(String(10), default="🌱")
    description     = Column(Text)
    actif           = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=now_utc)

    __table_args__ = (
        CheckConstraint(
            "categorie IN ('grandes_cultures','maraichage','arboriculture')",
            name="ck_culture_categorie"
        ),
        Index("ix_agro_cultures_categorie", "categorie"),
    )

    # Relations
    varietes               = relationship("Variete",              back_populates="culture", cascade="all, delete-orphan")
    parametres_climatiques = relationship("ParametreClimatique",  back_populates="culture", uselist=False, cascade="all, delete-orphan")
    besoins_eau            = relationship("BesoinEau",            back_populates="culture", cascade="all, delete-orphan")
    besoins_nutritionnels  = relationship("BesoinNutritionnel",   back_populates="culture", cascade="all, delete-orphan")
    stades                 = relationship("StadePhenologique",    back_populates="culture", cascade="all, delete-orphan", order_by="StadePhenologique.ordre")
    calendriers            = relationship("CalendrierCultural",   back_populates="culture", cascade="all, delete-orphan")
    rendements             = relationship("RendementReference",   back_populates="culture", cascade="all, delete-orphan")
    culture_maladies       = relationship("CultureMaladie",       back_populates="culture", cascade="all, delete-orphan")
    culture_ravageurs      = relationship("CultureRavageur",      back_populates="culture", cascade="all, delete-orphan")
    recommandations        = relationship("RecommandationCulture", back_populates="culture", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
#  2. VARIÉTÉS
# ─────────────────────────────────────────────

class Variete(Base):
    __tablename__ = "agro_varietes"

    id                   = Column(Integer, primary_key=True)
    culture_id           = Column(Integer, ForeignKey("agro_cultures.id", ondelete="CASCADE"), nullable=False)
    nom                  = Column(String(150), nullable=False)
    origine              = Column(String(100))          # ISRA, CGIAR, local, importé
    cycle_min_jours      = Column(Integer)
    cycle_max_jours      = Column(Integer)
    precocite            = Column(String(20))            # hative | semi-tardive | tardive
    tolerance_secheresse = Column(Boolean, default=False)
    tolerance_salinite   = Column(Boolean, default=False)
    zones_adaptees       = Column(JSONB, default=list)   # ["niayes","bassin_arachidier"]
    rendement_potentiel_t_ha = Column(Numeric(5, 2))
    notes                = Column(Text)

    culture = relationship("Culture", back_populates="varietes")

    __table_args__ = (
        Index("ix_agro_varietes_culture", "culture_id"),
    )


# ─────────────────────────────────────────────
#  3. PARAMÈTRES CLIMATIQUES
# ─────────────────────────────────────────────

class ParametreClimatique(Base):
    __tablename__ = "agro_parametres_climatiques"

    id              = Column(Integer, primary_key=True)
    culture_id      = Column(Integer, ForeignKey("agro_cultures.id", ondelete="CASCADE"), nullable=False, unique=True)
    temp_min_c      = Column(Numeric(4, 1))    # minimum absolu (dommages)
    temp_opt_min_c  = Column(Numeric(4, 1))    # optimum bas
    temp_opt_max_c  = Column(Numeric(4, 1))    # optimum haut
    temp_max_c      = Column(Numeric(4, 1))    # maximum absolu (stress sévère)
    pluvio_min_mm   = Column(Integer)          # besoins eau totaux min (mm/cycle)
    pluvio_opt_mm   = Column(Integer)          # optimum
    pluvio_max_mm   = Column(Integer)          # maximum toléré
    altitude_max_m  = Column(Integer, default=1500)
    ensoleillement_h = Column(Numeric(3, 1))   # heures/jour
    ph_min          = Column(Numeric(3, 1))
    ph_opt_min      = Column(Numeric(3, 1))
    ph_opt_max      = Column(Numeric(3, 1))
    ph_max          = Column(Numeric(3, 1))
    texture_preferee = Column(String(100))     # ex: "limon-sableux, bien drainé"

    culture = relationship("Culture", back_populates="parametres_climatiques")


# ─────────────────────────────────────────────
#  4. BESOINS EN EAU
# ─────────────────────────────────────────────

class BesoinEau(Base):
    __tablename__ = "agro_besoins_eau"

    id                  = Column(Integer, primary_key=True)
    culture_id          = Column(Integer, ForeignKey("agro_cultures.id", ondelete="CASCADE"), nullable=False)
    stade               = Column(String(80), nullable=False)
    besoin_mm_semaine   = Column(Numeric(5, 1))    # mm/semaine
    sensibilite         = Column(String(20))        # critique | elevee | moyenne | faible
    frequence_irrigation = Column(String(100))      # ex: "tous les 3 jours"
    notes               = Column(Text)

    culture = relationship("Culture", back_populates="besoins_eau")

    __table_args__ = (
        Index("ix_agro_besoins_eau_culture", "culture_id"),
    )


# ─────────────────────────────────────────────
#  5. BESOINS NUTRITIONNELS (NPK)
# ─────────────────────────────────────────────

class BesoinNutritionnel(Base):
    __tablename__ = "agro_besoins_nutritionnels"

    id                  = Column(Integer, primary_key=True)
    culture_id          = Column(Integer, ForeignKey("agro_cultures.id", ondelete="CASCADE"), nullable=False)
    stade               = Column(String(80), nullable=False)   # 'total' | stade spécifique
    azote_kg_ha         = Column(Numeric(6, 1))
    phosphore_kg_ha     = Column(Numeric(6, 1))
    potassium_kg_ha     = Column(Numeric(6, 1))
    calcium_kg_ha       = Column(Numeric(6, 1))
    magnesium_kg_ha     = Column(Numeric(6, 1))
    engrais_recommandes = Column(Text)     # engrais disponibles au Sénégal
    moment_application  = Column(Text)     # quand appliquer
    notes               = Column(Text)

    culture = relationship("Culture", back_populates="besoins_nutritionnels")


# ─────────────────────────────────────────────
#  6. STADES PHÉNOLOGIQUES
# ─────────────────────────────────────────────

class StadePhenologique(Base):
    __tablename__ = "agro_stades_phenologiques"

    id                   = Column(Integer, primary_key=True)
    culture_id           = Column(Integer, ForeignKey("agro_cultures.id", ondelete="CASCADE"), nullable=False)
    variete_id           = Column(Integer, ForeignKey("agro_varietes.id", ondelete="SET NULL"), nullable=True)
    ordre                = Column(Integer, nullable=False)
    nom_stade            = Column(String(100), nullable=False)
    jours_debut          = Column(Integer)     # jours depuis semis
    jours_fin            = Column(Integer)
    description          = Column(Text)
    actions_cles         = Column(JSONB, default=list)   # ["Irrigation","Fertilisation N"]
    indicateurs_visuels  = Column(Text)        # ce que le producteur observe

    culture = relationship("Culture", back_populates="stades")

    __table_args__ = (
        Index("ix_agro_stades_culture", "culture_id"),
    )


# ─────────────────────────────────────────────
#  7. CALENDRIERS CULTURAUX
# ─────────────────────────────────────────────

class CalendrierCultural(Base):
    __tablename__ = "agro_calendriers_culturaux"

    id                  = Column(Integer, primary_key=True)
    culture_id          = Column(Integer, ForeignKey("agro_cultures.id", ondelete="CASCADE"), nullable=False)
    zone_agro           = Column(String(40), nullable=False)
    saison              = Column(String(20), nullable=False)
    mois_semis_debut    = Column(Integer)      # 1-12
    mois_semis_fin      = Column(Integer)
    mois_recolte_debut  = Column(Integer)
    mois_recolte_fin    = Column(Integer)
    remarques           = Column(Text)

    culture = relationship("Culture", back_populates="calendriers")

    __table_args__ = (
        UniqueConstraint("culture_id", "zone_agro", "saison", name="uq_calendrier_culture_zone_saison"),
        Index("ix_agro_cal_culture_zone", "culture_id", "zone_agro"),
    )


# ─────────────────────────────────────────────
#  8. RENDEMENTS DE RÉFÉRENCE
# ─────────────────────────────────────────────

class RendementReference(Base):
    __tablename__ = "agro_rendements_reference"

    id                   = Column(Integer, primary_key=True)
    culture_id           = Column(Integer, ForeignKey("agro_cultures.id", ondelete="CASCADE"), nullable=False)
    variete_id           = Column(Integer, ForeignKey("agro_varietes.id", ondelete="SET NULL"), nullable=True)
    zone_agro            = Column(String(40))   # NULL = moyenne nationale
    pratique             = Column(String(20), nullable=False)
    rendement_min_t_ha   = Column(Numeric(5, 2))
    rendement_max_t_ha   = Column(Numeric(5, 2))
    rendement_moyen_t_ha = Column(Numeric(5, 2))
    unite                = Column(String(20), default="t/ha")
    source               = Column(String(100))  # ISRA, FAO, ANSD
    annee_reference      = Column(Integer)

    culture = relationship("Culture", back_populates="rendements")

    __table_args__ = (
        Index("ix_agro_rendements_culture_zone", "culture_id", "zone_agro", "pratique"),
    )


# ─────────────────────────────────────────────
#  9. MALADIES
# ─────────────────────────────────────────────

class Maladie(Base):
    __tablename__ = "agro_maladies"

    id               = Column(Integer, primary_key=True)
    nom              = Column(String(150), nullable=False)
    nom_scientifique = Column(String(200))
    pathogene_type   = Column(String(20))  # fongique|bacterien|viral|parasitaire|physiologique
    symptomes        = Column(Text, nullable=False)
    conditions_favorables = Column(Text)
    created_at       = Column(DateTime, default=now_utc)

    culture_maladies = relationship("CultureMaladie", back_populates="maladie")

    __table_args__ = (
        CheckConstraint(
            "pathogene_type IN ('fongique','bacterien','viral','parasitaire','physiologique','nematode')",
            name="ck_maladie_type"
        ),
    )


class CultureMaladie(Base):
    __tablename__ = "agro_culture_maladies"

    id              = Column(Integer, primary_key=True)
    culture_id      = Column(Integer, ForeignKey("agro_cultures.id",  ondelete="CASCADE"), nullable=False)
    maladie_id      = Column(Integer, ForeignKey("agro_maladies.id",  ondelete="CASCADE"), nullable=False)
    frequence       = Column(String(20))     # tres_frequente | frequente | occasionnelle
    gravite         = Column(String(20))     # elevee | moyenne | faible
    stade_sensible  = Column(String(100))
    pertes_estimees = Column(String(100))    # ex: "20-40% en cas d'épidémie"
    prevention      = Column(Text)
    traitement      = Column(Text, nullable=False)

    culture = relationship("Culture",  back_populates="culture_maladies")
    maladie = relationship("Maladie",  back_populates="culture_maladies")

    __table_args__ = (
        UniqueConstraint("culture_id", "maladie_id", name="uq_culture_maladie"),
        Index("ix_agro_cm_culture", "culture_id"),
    )


# ─────────────────────────────────────────────
#  10. RAVAGEURS
# ─────────────────────────────────────────────

class Ravageur(Base):
    __tablename__ = "agro_ravageurs"

    id               = Column(Integer, primary_key=True)
    nom              = Column(String(150), nullable=False)
    nom_scientifique = Column(String(200))
    type_ravageur    = Column(String(20))    # insecte|acarien|nematode|rongeur|oiseau|mollusque
    description      = Column(Text)
    symptomes_degats = Column(Text, nullable=False)
    created_at       = Column(DateTime, default=now_utc)

    culture_ravageurs = relationship("CultureRavageur", back_populates="ravageur")


class CultureRavageur(Base):
    __tablename__ = "agro_culture_ravageurs"

    id              = Column(Integer, primary_key=True)
    culture_id      = Column(Integer, ForeignKey("agro_cultures.id",   ondelete="CASCADE"), nullable=False)
    ravageur_id     = Column(Integer, ForeignKey("agro_ravageurs.id",  ondelete="CASCADE"), nullable=False)
    frequence       = Column(String(20))
    gravite         = Column(String(20))
    stade_sensible  = Column(String(100))
    pertes_estimees = Column(String(100))
    prevention      = Column(Text)
    lutte           = Column(Text, nullable=False)

    culture  = relationship("Culture",  back_populates="culture_ravageurs")
    ravageur = relationship("Ravageur", back_populates="culture_ravageurs")

    __table_args__ = (
        UniqueConstraint("culture_id", "ravageur_id", name="uq_culture_ravageur"),
        Index("ix_agro_cr_culture", "culture_id"),
    )


# ─────────────────────────────────────────────
#  11. RECOMMANDATIONS AGROSCAN
# ─────────────────────────────────────────────

class RecommandationCulture(Base):
    """
    Recommandations pratiques AgroScan par culture.
    Sert au Rules Engine et à l'IA de conseil.
    """
    __tablename__ = "agro_recommandations"

    id              = Column(Integer, primary_key=True)
    culture_id      = Column(Integer, ForeignKey("agro_cultures.id", ondelete="CASCADE"), nullable=False)
    zone_agro       = Column(String(40))     # NULL = valable toutes zones
    categorie_reco  = Column(String(50), nullable=False)
    # preparation_terrain | semis_plantation | irrigation | fertilisation |
    # protection_phyto | recolte | post_recolte | alerte_saisonniere
    titre           = Column(String(200), nullable=False)
    contenu         = Column(Text, nullable=False)
    priorite        = Column(Integer, default=1)   # 1=haute, 2=moyenne, 3=faible
    mois_applicable = Column(JSONB, default=list)  # [6,7,8] → juin-juil-août
    created_at      = Column(DateTime, default=now_utc)

    culture = relationship("Culture", back_populates="recommandations")

    __table_args__ = (
        Index("ix_agro_reco_culture_zone", "culture_id", "zone_agro"),
        Index("ix_agro_reco_categorie", "categorie_reco"),
    )
