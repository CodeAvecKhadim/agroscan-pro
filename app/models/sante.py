"""
Modèles SQLAlchemy — Module SANTÉ DES CULTURES.
Tables : sc_consultations, sc_observations, sc_photos,
         sc_diagnostics, sc_traitements, sc_suivis, sc_rapports
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, Float, Boolean,
    DateTime, Date, ForeignKey, Enum, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


# ── Énumérations ───────────────────────────────────────────────────────────────

class TypeConsultation(str, enum.Enum):
    MALADIE       = "maladie"
    RAVAGEUR      = "ravageur"
    FERTILISATION = "fertilisation"


class StatutConsultation(str, enum.Enum):
    EN_COURS  = "en_cours"
    ANALYSE   = "analyse"
    CONFIRME  = "confirme"
    ARCHIVE   = "archive"


class TypeObservation(str, enum.Enum):
    SYMPTOME          = "symptome"
    RAVAGEUR_OBSERVE  = "ravageur_observe"
    SOL               = "sol"
    METEO             = "meteo"
    AUTRE             = "autre"


class PartiePlante(str, enum.Enum):
    FEUILLE        = "feuille"
    TIGE           = "tige"
    RACINE         = "racine"
    FRUIT          = "fruit"
    GRAINE         = "graine"
    PLANTE_ENTIERE = "plante_entiere"
    SOL            = "sol"


class SourcePhoto(str, enum.Enum):
    TERRAIN      = "terrain"
    LABORATOIRE  = "laboratoire"
    DRONE        = "drone"
    SMARTPHONE   = "smartphone"
    AUTRE        = "autre"


class TypeEntite(str, enum.Enum):
    MALADIE  = "maladie"
    RAVAGEUR = "ravageur"
    CARENCE  = "carence"


class MethodeDiagnostic(str, enum.Enum):
    RULES_ENGINE = "rules_engine"
    BIBLIOTHEQUE = "bibliotheque"
    SYMPTOMES    = "symptomes"
    COMBINEE     = "combinee"


class StatutDiagnostic(str, enum.Enum):
    PROBABLE = "probable"
    CONFIRME = "confirme"
    EXCLU    = "exclu"


class TypeTraitement(str, enum.Enum):
    TRAITEMENT_PHYTO = "traitement_phyto"
    FERTILISATION    = "fertilisation"
    IRRIGATION       = "irrigation"
    MESURE_CULTURALE = "mesure_culturale"
    RECOLTE          = "recolte"
    SURVEILLANCE     = "surveillance"


class StatutTraitement(str, enum.Enum):
    PLANIFIE = "planifie"
    APPLIQUE = "applique"
    SKIP     = "skip"


class EvolutionSuivi(str, enum.Enum):
    AMELIORATION = "amelioration"
    STABLE       = "stable"
    AGGRAVATION  = "aggravation"


class TypeRapport(str, enum.Enum):
    DIAGNOSTIC_MALADIE   = "diagnostic_maladie"
    DIAGNOSTIC_RAVAGEUR  = "diagnostic_ravageur"
    PLAN_FERTILISATION   = "plan_fertilisation"
    SUIVI                = "suivi"


# ── Modèles ────────────────────────────────────────────────────────────────────

class Consultation(Base):
    """Session de diagnostic ouverte par un agriculteur."""
    __tablename__ = "sc_consultations"

    id          = Column(Integer, primary_key=True)
    org_id      = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    parcelle_id = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="SET NULL"), nullable=True)
    culture_id  = Column(Integer, ForeignKey("agro_cultures.id",  ondelete="SET NULL"), nullable=True)
    type        = Column(Enum(TypeConsultation), nullable=False)
    statut      = Column(Enum(StatutConsultation), default=StatutConsultation.EN_COURS, nullable=False)
    # Snapshot contexte au moment de l'analyse
    contexte    = Column(JSONB, default=dict)   # {zone_agro, stade, mois, sol, meteo…}
    resume      = Column(Text)                  # synthèse auto post-analyse
    nb_photos   = Column(SmallInteger, default=0)
    created_by  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime, default=_now)
    updated_at  = Column(DateTime, default=_now, onupdate=_now)

    # Relations
    observations = relationship("Observation",     back_populates="consultation", cascade="all, delete-orphan")
    photos       = relationship("PhotoConsultation", back_populates="consultation", cascade="all, delete-orphan")
    diagnostics  = relationship("Diagnostic",      back_populates="consultation", cascade="all, delete-orphan",
                                order_by="Diagnostic.rang")
    traitements  = relationship("Traitement",      back_populates="consultation", cascade="all, delete-orphan",
                                order_by="Traitement.priorite")
    suivis       = relationship("Suivi",           back_populates="consultation", cascade="all, delete-orphan",
                                order_by="Suivi.date_suivi")
    rapports     = relationship("RapportSante",    back_populates="consultation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sc_consultations_org", "org_id"),
        Index("ix_sc_consultations_parcelle", "parcelle_id"),
    )


class Observation(Base):
    """Saisie terrain : symptôme, ravageur observé, données sol/météo."""
    __tablename__ = "sc_observations"

    id              = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey("sc_consultations.id", ondelete="CASCADE"), nullable=False)
    type            = Column(Enum(TypeObservation), nullable=False)
    partie_plante   = Column(Enum(PartiePlante), nullable=True)
    valeur          = Column(JSONB, nullable=False)  # contenu flexible par type
    note_terrain    = Column(Text)
    created_at      = Column(DateTime, default=_now)

    consultation = relationship("Consultation", back_populates="observations")
    photos       = relationship("PhotoConsultation", back_populates="observation")

    __table_args__ = (
        Index("ix_sc_obs_consultation", "consultation_id"),
    )


class PhotoConsultation(Base):
    """Photo liée à une consultation (stockage local, migration S3 future)."""
    __tablename__ = "sc_photos"

    id              = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey("sc_consultations.id", ondelete="CASCADE"), nullable=False)
    observation_id  = Column(Integer, ForeignKey("sc_observations.id",  ondelete="SET NULL"), nullable=True)
    source_photo    = Column(Enum(SourcePhoto), default=SourcePhoto.SMARTPHONE)
    filename        = Column(String(255), nullable=False)
    url             = Column(Text, nullable=False)        # /uploads/{type}/uuid.jpg
    thumbnail_url   = Column(Text)
    taille_ko       = Column(Integer)
    photo_meta      = Column(JSONB, default=dict)         # {width, height, hash_sha256, mime}
    uploaded_at     = Column(DateTime, default=_now)

    consultation = relationship("Consultation", back_populates="photos")
    observation  = relationship("Observation",  back_populates="photos")

    __table_args__ = (
        Index("ix_sc_photos_consultation", "consultation_id"),
    )


class Diagnostic(Base):
    """Résultat classé — maladie, ravageur ou carence probable."""
    __tablename__ = "sc_diagnostics"

    id              = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey("sc_consultations.id", ondelete="CASCADE"), nullable=False)
    rang            = Column(SmallInteger, nullable=False)  # 1 = plus probable
    entite_type     = Column(Enum(TypeEntite), nullable=False)
    entite_id       = Column(Integer, nullable=False)       # FK polymorphe agro_maladies|agro_ravageurs
    entite_nom      = Column(String(200))                   # dénormalisé pour affichage rapide
    score_confiance = Column(Float, default=0.0)            # 0.0–1.0
    score_rules     = Column(Float, default=0.0)
    score_symptomes = Column(Float, default=0.0)
    regles_matches  = Column(JSONB, default=list)           # ["MAL-RIZ-001",…]
    methode         = Column(Enum(MethodeDiagnostic), default=MethodeDiagnostic.COMBINEE)
    statut          = Column(Enum(StatutDiagnostic), default=StatutDiagnostic.PROBABLE)
    confirme_par    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirme_le     = Column(DateTime, nullable=True)
    note_expert     = Column(Text)
    created_at      = Column(DateTime, default=_now)

    consultation = relationship("Consultation", back_populates="diagnostics")
    traitements  = relationship("Traitement",   back_populates="diagnostic")

    __table_args__ = (
        Index("ix_sc_diag_consultation", "consultation_id"),
    )


class Traitement(Base):
    """Plan de traitement : action à entreprendre suite à un diagnostic."""
    __tablename__ = "sc_traitements"

    id              = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey("sc_consultations.id", ondelete="CASCADE"), nullable=False)
    diagnostic_id   = Column(Integer, ForeignKey("sc_diagnostics.id",  ondelete="SET NULL"), nullable=True)
    priorite        = Column(SmallInteger, default=5)   # 1 = urgent
    type            = Column(Enum(TypeTraitement), nullable=False)
    titre           = Column(String(300), nullable=False)
    produit         = Column(String(200))
    dose            = Column(String(100))
    frequence       = Column(String(100))
    delai_carence_jours = Column(SmallInteger)
    urgence_jours   = Column(SmallInteger)
    detail          = Column(Text)
    date_application = Column(Date)
    statut          = Column(Enum(StatutTraitement), default=StatutTraitement.PLANIFIE)
    applique_le     = Column(Date)
    note            = Column(Text)

    consultation = relationship("Consultation", back_populates="traitements")
    diagnostic   = relationship("Diagnostic",   back_populates="traitements")

    __table_args__ = (
        Index("ix_sc_trait_consultation", "consultation_id"),
    )


class Suivi(Base):
    """Suivi post-traitement : évolution de l'état de la culture."""
    __tablename__ = "sc_suivis"

    id              = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey("sc_consultations.id", ondelete="CASCADE"), nullable=False)
    date_suivi      = Column(Date, nullable=False)
    evolution       = Column(Enum(EvolutionSuivi))
    efficacite      = Column(SmallInteger)   # 1–5
    note            = Column(Text)
    photo_url       = Column(Text)
    created_at      = Column(DateTime, default=_now)

    consultation = relationship("Consultation", back_populates="suivis")

    __table_args__ = (
        Index("ix_sc_suivis_consultation", "consultation_id"),
    )


class RapportSante(Base):
    """Rapport PDF archivé (diagnostic ou plan fertilisation)."""
    __tablename__ = "sc_rapports"

    id              = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey("sc_consultations.id", ondelete="CASCADE"), nullable=False)
    org_id          = Column(Integer, ForeignKey("organizations.id",    ondelete="CASCADE"), nullable=False)
    type            = Column(Enum(TypeRapport), nullable=False)
    titre           = Column(String(300), nullable=False)
    url             = Column(Text, nullable=False)    # /uploads/rapports/uuid.pdf
    taille_ko       = Column(Integer)
    genere_par      = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    genere_le       = Column(DateTime, default=_now)
    telechargements = Column(SmallInteger, default=0)

    consultation = relationship("Consultation", back_populates="rapports")

    __table_args__ = (
        Index("ix_sc_rapports_org", "org_id"),
        Index("ix_sc_rapports_consultation", "consultation_id"),
    )
