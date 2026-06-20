"""
Journalisation des actions des bêta-testeurs AgroScan Pro.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class BetaLog(Base):
    __tablename__ = "beta_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    method = Column(String(10))          # GET, POST, PATCH, DELETE
    path = Column(String(256))           # /api/champ/parcelles
    status_code = Column(Integer)        # 200, 201, 400…
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, index=True)
