"""
Gestion du cache météo avec TTL.
ConditionMeteo : TTL 1h
Prevision      : TTL 6h
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.meteo import ConditionMeteo, Prevision, SourceMeteo
from app.services.meteo.provider import OpenMeteoProvider, get_provider

log = logging.getLogger(__name__)

_TTL_CONDITIONS_H = 1
_TTL_PREVISIONS_H = 6


def get_conditions(
    db: Session,
    org_id: int,
    lat: float,
    lon: float,
    parcelle_id: Optional[int] = None,
    zone_agro: Optional[str] = None,
    force_refresh: bool = False,
) -> ConditionMeteo:
    """Retourne conditions actuelles depuis cache ou API."""
    now = datetime.now(timezone.utc)

    if not force_refresh:
        existing = _find_condition(db, org_id, parcelle_id, lat, lon)
        if existing and existing.expire_le and existing.expire_le.replace(tzinfo=timezone.utc) > now:
            return existing

    provider = get_provider()
    try:
        data = provider.conditions_actuelles(lat, lon)
    except RuntimeError as e:
        log.warning("Cache conditions fallback: %s", e)
        existing = _find_condition(db, org_id, parcelle_id, lat, lon)
        if existing:
            return existing
        raise

    expire = now + timedelta(hours=_TTL_CONDITIONS_H)

    if not force_refresh:
        existing = _find_condition(db, org_id, parcelle_id, lat, lon)
    else:
        existing = None

    if existing:
        for k, v in data.items():
            if v is not None:
                setattr(existing, k, v)
        existing.expire_le    = expire
        existing.heure_releve = now
        existing.date_releve  = now.date()
        existing.source       = SourceMeteo.OPEN_METEO
    else:
        existing = ConditionMeteo(
            org_id=org_id,
            parcelle_id=parcelle_id,
            lat=lat,
            lon=lon,
            zone_agro=zone_agro,
            source=SourceMeteo.OPEN_METEO,
            expire_le=expire,
            heure_releve=now,
            date_releve=now.date(),
            **{k: v for k, v in data.items() if v is not None},
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return existing


def get_previsions(
    db: Session,
    org_id: int,
    lat: float,
    lon: float,
    jours: int = 16,
    parcelle_id: Optional[int] = None,
    zone_agro: Optional[str] = None,
    force_refresh: bool = False,
) -> Prevision:
    """Retourne prévisions depuis cache ou API."""
    now = datetime.now(timezone.utc)

    if not force_refresh:
        existing = _find_prevision(db, org_id, parcelle_id, lat, lon, jours)
        if existing and existing.expire_le and existing.expire_le.replace(tzinfo=timezone.utc) > now:
            return existing

    provider = get_provider()
    try:
        donnees = provider.previsions(lat, lon, jours)
    except RuntimeError as e:
        log.warning("Cache prévisions fallback: %s", e)
        existing = _find_prevision(db, org_id, parcelle_id, lat, lon, jours)
        if existing:
            return existing
        raise

    expire = now + timedelta(hours=_TTL_PREVISIONS_H)

    if not force_refresh:
        existing = _find_prevision(db, org_id, parcelle_id, lat, lon, jours)
    else:
        existing = None

    if existing:
        existing.donnees    = donnees
        existing.expire_le  = expire
        existing.genere_le  = now
    else:
        existing = Prevision(
            org_id=org_id,
            parcelle_id=parcelle_id,
            lat=lat,
            lon=lon,
            zone_agro=zone_agro,
            horizon_jours=jours,
            donnees=donnees,
            expire_le=expire,
            genere_le=now,
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return existing


def invalider_cache(db: Session, org_id: int, parcelle_id: Optional[int] = None):
    """Force refresh : expire immédiatement les entrées cache."""
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    q_c = db.query(ConditionMeteo).filter_by(org_id=org_id)
    q_p = db.query(Prevision).filter_by(org_id=org_id)
    if parcelle_id is not None:
        q_c = q_c.filter_by(parcelle_id=parcelle_id)
        q_p = q_p.filter_by(parcelle_id=parcelle_id)
    q_c.update({"expire_le": past})
    q_p.update({"expire_le": past})
    db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_condition(db: Session, org_id: int, parcelle_id, lat, lon) -> Optional[ConditionMeteo]:
    q = db.query(ConditionMeteo).filter_by(org_id=org_id)
    if parcelle_id is not None:
        q = q.filter_by(parcelle_id=parcelle_id)
    else:
        q = q.filter(ConditionMeteo.parcelle_id.is_(None))
    return q.order_by(ConditionMeteo.id.desc()).first()


def _find_prevision(db: Session, org_id: int, parcelle_id, lat, lon, jours) -> Optional[Prevision]:
    q = db.query(Prevision).filter_by(org_id=org_id, horizon_jours=jours)
    if parcelle_id is not None:
        q = q.filter_by(parcelle_id=parcelle_id)
    else:
        q = q.filter(Prevision.parcelle_id.is_(None))
    return q.order_by(Prevision.id.desc()).first()
