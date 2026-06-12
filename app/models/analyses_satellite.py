"""
Modèle SQLAlchemy — Table analyses_satellite.
Stocke l'analyse NDVI + message simple pour le producteur.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class AnalyseSatellite(Base):
    __tablename__ = "analyses_satellite"

    id             = Column(Integer, primary_key=True)
    org_id         = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    parcelle_id    = Column(Integer, ForeignKey("champ_parcelles.id", ondelete="CASCADE"), nullable=True)
    date           = Column(Date, nullable=False)
    ndvi_moyen     = Column(Numeric(5, 3))
    ndre           = Column(Numeric(5, 3))
    ndwi           = Column(Numeric(5, 3))
    zones          = Column(JSONB)
    message_simple = Column(Text)
    couleur        = Column(String(10), default="vert")  # vert | orange | rouge
    source         = Column(String(50), default="sentinel-2")
    created_at     = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_as_org",      "org_id"),
        Index("ix_as_parcelle", "parcelle_id"),
        Index("ix_as_date",     "date"),
    )
