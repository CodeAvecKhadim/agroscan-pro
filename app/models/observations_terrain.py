"""
Modèle SQLAlchemy — Table observations_terrain.
Observations déclaratives producteur : irrigation, pluie, état feuilles, ravageurs, maladies.
Injectées dans le contexte IA Polélé pour croisement satellite + météo.
"""
from datetime import date as date_t, datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Index

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class ObservationTerrain(Base):
    __tablename__ = "observations_terrain"

    id                    = Column(Integer, primary_key=True)
    org_id                = Column(Integer, ForeignKey("organizations.id",     ondelete="CASCADE"), nullable=False)
    parcelle_id           = Column(Integer, ForeignKey("champ_parcelles.id",   ondelete="CASCADE"), nullable=True)
    user_id               = Column(Integer, ForeignKey("users.id",             ondelete="SET NULL"), nullable=True)
    date_observation      = Column(Date, nullable=False, default=date_t.today)
    irrigation_effectuee  = Column(Boolean, nullable=True)
    pluie_observee        = Column(Boolean, nullable=True)
    etat_feuilles         = Column(String(30), nullable=True)   # bon|moyen|mauvais|jauni|fleuri|chute
    ravageurs_observes    = Column(Boolean, nullable=True)
    maladie_observee      = Column(Boolean, nullable=True)
    confiance_observation = Column(String(10), nullable=True, default="moyen")  # faible|moyen|élevé
    notes                 = Column(Text, nullable=True)
    created_at            = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_obs_terrain_org",      "org_id"),
        Index("ix_obs_terrain_parcelle", "parcelle_id"),
        Index("ix_obs_terrain_date",     "date_observation"),
    )
