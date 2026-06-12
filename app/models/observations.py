"""
Modèle SQLAlchemy — Table observations.
Stocke photos + diagnostic Kindwise + message simple producteur.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class ObservationDiagnostic(Base):
    __tablename__ = "observations"

    id                    = Column(Integer, primary_key=True)
    org_id                = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    parcelle_id           = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="CASCADE"), nullable=True)
    user_id               = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    type                  = Column(String(20), nullable=False, default="photo")
    chemin                = Column(Text)
    diagnostic            = Column(JSONB)
    etat_simple           = Column(Text)
    anomalie              = Column(Boolean, default=False)
    validation_conseiller = Column(Text)
    created_at            = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_obs_org",      "org_id"),
        Index("ix_obs_parcelle", "parcelle_id"),
        Index("ix_obs_anomalie", "anomalie"),
    )
