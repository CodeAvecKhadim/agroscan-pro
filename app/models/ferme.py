"""
Modèles SQLAlchemy — Module GESTION DE FERME.
Tables : gf_activites, gf_preuves, gf_couts, gf_main_oeuvre, gf_journal
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, Float, Boolean,
    DateTime, Date, ForeignKey, Enum, Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


# ── Énumérations ───────────────────────────────────────────────────────────────

class TypeActivite(str, enum.Enum):
    SEMIS          = "semis"
    PLANTATION     = "plantation"
    FERTILISATION  = "fertilisation"
    TRAITEMENT     = "traitement"
    IRRIGATION     = "irrigation"
    DESHERBAGE     = "desherbage"
    RECOLTE        = "recolte"
    AUTRE          = "autre"


class StatutActivite(str, enum.Enum):
    PLANIFIE  = "planifie"
    EN_COURS  = "en_cours"
    TERMINE   = "termine"
    ANNULE    = "annule"


class TypePreuve(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"


class SourcePreuve(str, enum.Enum):
    SMARTPHONE = "smartphone"
    DRONE      = "drone"
    TABLETTE   = "tablette"
    AUTRE      = "autre"


class CategorieCoût(str, enum.Enum):
    INTRANT    = "intrant"
    MATERIEL   = "materiel"
    TRANSPORT  = "transport"
    PRESTATION = "prestation"
    AUTRE      = "autre"


class TypeMainOeuvre(str, enum.Enum):
    FAMILIALE   = "familiale"
    SALARIALE   = "salariale"
    ENTRAIDE    = "entraide"
    PRESTATAIRE = "prestataire"


class TypeJournal(str, enum.Enum):
    OBSERVATION  = "observation"
    DECISION     = "decision"
    ALERTE       = "alerte"
    NOTE_TERRAIN = "note_terrain"
    METEO        = "meteo"


# ── Modèles ────────────────────────────────────────────────────────────────────

class Activite(Base):
    """Activité agricole — pivot central du module."""
    __tablename__ = "gf_activites"

    id                 = Column(Integer, primary_key=True)
    org_id             = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    parcelle_id        = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="SET NULL"), nullable=True)
    culture_id         = Column(Integer, ForeignKey("agro_cultures.id",   ondelete="SET NULL"), nullable=True)
    consultation_id    = Column(Integer, ForeignKey("sc_consultations.id", ondelete="SET NULL"), nullable=True)
    type               = Column(Enum(TypeActivite), nullable=False)
    statut             = Column(Enum(StatutActivite), default=StatutActivite.PLANIFIE, nullable=False)
    titre              = Column(String(200), nullable=False)
    description        = Column(Text)
    date_prevue        = Column(Date)
    date_debut         = Column(DateTime)
    date_fin           = Column(DateTime)
    duree_minutes      = Column(Integer)
    stade_culture      = Column(String(100))
    surface_traitee_ha = Column(Float)
    conditions_meteo   = Column(JSONB, default=dict)   # {temp_air, humidite_rel, pluie_24h, vent}
    localisation_debut = Column(JSONB, default=dict)   # {lat, lon, precision_m}
    details            = Column(JSONB, default=dict)   # contenu spécifique par type
    note               = Column(Text)
    created_by         = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at         = Column(DateTime, default=_now)
    updated_at         = Column(DateTime, default=_now, onupdate=_now)

    # Relations
    preuves     = relationship("Preuve",       back_populates="activite", cascade="all, delete-orphan")
    couts       = relationship("Cout",         back_populates="activite", cascade="all, delete-orphan")
    main_oeuvre = relationship("MainOeuvre",   back_populates="activite", cascade="all, delete-orphan")
    journal     = relationship("JournalEntree", back_populates="activite")

    __table_args__ = (
        Index("ix_gf_activites_org",      "org_id"),
        Index("ix_gf_activites_parcelle", "parcelle_id"),
        Index("ix_gf_activites_type",     "type"),
        Index("ix_gf_activites_statut",   "statut"),
        Index("ix_gf_activites_date",     "date_prevue"),
    )


class Preuve(Base):
    """Photo ou vidéo comme preuve d'une activité."""
    __tablename__ = "gf_preuves"

    id                 = Column(Integer, primary_key=True)
    activite_id        = Column(Integer, ForeignKey("gf_activites.id", ondelete="CASCADE"), nullable=False)
    org_id             = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    type               = Column(Enum(TypePreuve), nullable=False)
    filename           = Column(String(255), nullable=False)
    url                = Column(Text, nullable=False)
    thumbnail_url      = Column(Text)
    duree_secondes     = Column(SmallInteger)        # vidéo uniquement, max 180
    taille_ko          = Column(Integer)
    source             = Column(Enum(SourcePreuve), default=SourcePreuve.SMARTPHONE)
    localisation       = Column(JSONB, default=dict) # {lat, lon, precision_m}
    horodatage_terrain = Column(DateTime)            # EXIF ou saisi
    photo_meta         = Column(JSONB, default=dict) # {width, height, hash_sha256, mime}
    uploaded_at        = Column(DateTime, default=_now)

    activite = relationship("Activite", back_populates="preuves")

    __table_args__ = (
        Index("ix_gf_preuves_activite", "activite_id"),
    )


class Cout(Base):
    """Dépense liée à une activité (intrant, matériel, transport…)."""
    __tablename__ = "gf_couts"

    id                  = Column(Integer, primary_key=True)
    activite_id         = Column(Integer, ForeignKey("gf_activites.id", ondelete="CASCADE"), nullable=False)
    org_id              = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    categorie           = Column(Enum(CategorieCoût), nullable=False)
    sous_categorie      = Column(String(100))          # semence, engrais, pesticide, carburant…
    description         = Column(String(300), nullable=False)
    quantite            = Column(Float)
    unite               = Column(String(30))           # kg, L, sac, heure, km…
    prix_unitaire_fcfa  = Column(Integer)
    montant_total_fcfa  = Column(Integer, nullable=False)
    fournisseur         = Column(String(200))
    date_achat          = Column(Date)
    recu                = Column(Boolean, default=False)
    note                = Column(Text)
    created_at          = Column(DateTime, default=_now)

    activite = relationship("Activite", back_populates="couts")

    __table_args__ = (
        Index("ix_gf_couts_activite", "activite_id"),
        Index("ix_gf_couts_org",      "org_id"),
    )


class MainOeuvre(Base):
    """Main-d'œuvre engagée pour une activité."""
    __tablename__ = "gf_main_oeuvre"

    id                   = Column(Integer, primary_key=True)
    activite_id          = Column(Integer, ForeignKey("gf_activites.id", ondelete="CASCADE"), nullable=False)
    org_id               = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    type                 = Column(Enum(TypeMainOeuvre), nullable=False)
    description          = Column(String(200))
    nb_personnes         = Column(SmallInteger, nullable=False, default=1)
    duree_jours          = Column(Float, nullable=False)
    taux_journalier_fcfa = Column(Integer, default=0)   # 0 si familiale/entraide
    montant_total_fcfa   = Column(Integer, default=0)   # calculé : taux × jours × personnes
    note                 = Column(Text)
    created_at           = Column(DateTime, default=_now)

    activite = relationship("Activite", back_populates="main_oeuvre")

    __table_args__ = (
        Index("ix_gf_mo_activite", "activite_id"),
    )


class JournalEntree(Base):
    """Entrée libre du journal numérique."""
    __tablename__ = "gf_journal"

    id          = Column(Integer, primary_key=True)
    org_id      = Column(Integer, ForeignKey("organizations.id",   ondelete="CASCADE"), nullable=False)
    parcelle_id = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="SET NULL"), nullable=True)
    activite_id = Column(Integer, ForeignKey("gf_activites.id",   ondelete="SET NULL"), nullable=True)
    date_entree = Column(Date, nullable=False)
    type        = Column(Enum(TypeJournal), nullable=False, default=TypeJournal.NOTE_TERRAIN)
    titre       = Column(String(200))
    contenu     = Column(Text, nullable=False)
    created_by  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime, default=_now)

    activite = relationship("Activite", back_populates="journal")

    __table_args__ = (
        Index("ix_gf_journal_org",      "org_id"),
        Index("ix_gf_journal_parcelle", "parcelle_id"),
        Index("ix_gf_journal_date",     "date_entree"),
    )
