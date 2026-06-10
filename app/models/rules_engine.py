"""
Modèles SQLAlchemy — Rules Engine AgroScan Pro.
6 tables : re_regles, re_regles_cultures, re_regles_entites,
           re_parametres, re_declenchements, re_sessions_evaluation
"""
from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, Boolean, Float,
    DateTime, ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RegleMoteur(Base):
    __tablename__ = "re_regles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    categorie = Column(String(30), nullable=False, index=True)
    sous_categorie = Column(String(50))
    nom = Column(String(250), nullable=False)
    description = Column(Text)

    # Applicability filters (null = all)
    zones_applicables = Column(JSONB)
    stades_applicables = Column(JSONB)
    mois_applicables = Column(JSONB)

    # Rule logic
    conditions = Column(JSONB, nullable=False)
    actions = Column(JSONB, nullable=False)

    # Metadata
    gravite = Column(String(20), index=True)   # faible | moyenne | elevee | critique
    priorite = Column(SmallInteger, default=5) # 1-10
    confiance = Column(Float, default=0.80)    # 0.0-1.0

    plan_requis = Column(String(20), default="gratuit")  # gratuit | premium | cooperative
    active = Column(Boolean, default=True, index=True)
    source = Column(Text)
    version = Column(String(10), default="1.0")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cultures = relationship("RegleCulture", back_populates="regle", cascade="all, delete-orphan")
    entites = relationship("RegleEntite", back_populates="regle", cascade="all, delete-orphan")
    declenchements = relationship("RegleDeclenchement", back_populates="regle")

    __table_args__ = (
        Index("ix_re_regles_categorie_active", "categorie", "active"),
        Index("ix_re_regles_gravite_prio", "gravite", "priorite"),
    )


class RegleCulture(Base):
    __tablename__ = "re_regles_cultures"
    __table_args__ = (UniqueConstraint("regle_id", "culture_id"),)

    id = Column(Integer, primary_key=True)
    regle_id = Column(Integer, ForeignKey("re_regles.id", ondelete="CASCADE"), nullable=False, index=True)
    culture_id = Column(Integer, ForeignKey("agro_cultures.id"), nullable=False, index=True)
    notes = Column(Text)

    regle = relationship("RegleMoteur", back_populates="cultures")
    culture = relationship("Culture")


class RegleEntite(Base):
    """Liaison règle ↔ maladie ou ravageur de la bibliothèque."""
    __tablename__ = "re_regles_entites"

    id = Column(Integer, primary_key=True)
    regle_id = Column(Integer, ForeignKey("re_regles.id", ondelete="CASCADE"), nullable=False, index=True)
    entite_type = Column(String(20), nullable=False)  # "maladie" | "ravageur"
    entite_id = Column(Integer, nullable=False)

    regle = relationship("RegleMoteur", back_populates="entites")


class RegleParametre(Base):
    """Seuils calibrables — modifiables sans redéploiement."""
    __tablename__ = "re_parametres"

    id = Column(Integer, primary_key=True)
    cle = Column(String(100), unique=True, nullable=False, index=True)
    valeur = Column(JSONB, nullable=False)
    categorie = Column(String(50))
    description = Column(Text)
    modifiable_admin = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RegleDeclenchement(Base):
    """Journal immuable : chaque déclenchement de règle pour un org."""
    __tablename__ = "re_declenchements"

    id = Column(Integer, primary_key=True)
    regle_id = Column(Integer, ForeignKey("re_regles.id"), nullable=False, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    parcelle_id = Column(Integer, nullable=True)
    analyse_id = Column(Integer, nullable=True)

    contexte_entree = Column(JSONB)
    resultat = Column(JSONB)
    score_confiance = Column(Float)

    declenche_le = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    acquitte = Column(Boolean, default=False, index=True)
    acquitte_le = Column(DateTime(timezone=True))

    regle = relationship("RegleMoteur", back_populates="declenchements")

    __table_args__ = (
        Index("ix_re_decl_org_date", "org_id", "declenche_le"),
    )


class RegleSession(Base):
    """Cache léger d'une session d'évaluation."""
    __tablename__ = "re_sessions_evaluation"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, nullable=False, index=True)
    parcelle_id = Column(Integer, nullable=True)
    contexte = Column(JSONB)
    regles_evaluees = Column(Integer)
    regles_declenchees = Column(Integer)
    duree_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
