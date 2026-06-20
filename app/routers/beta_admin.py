"""
Router Administration Bêta — tableau de bord des bêta-testeurs terrain.
Accès : profil 'admin' uniquement.
Préfixe : /api/admin/beta
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_profil
from app.models import User, Analysis
from app.models.beta import BetaLog
from app.models.champ import Parcelle, StatutParcelle

router = APIRouter(prefix="/api/admin/beta", tags=["Admin Bêta"])

BETA_PERMISSIONS = [
    "Mon Champ",
    "Cartographie GPS",
    "Santé des Cultures Pro",
    "Diagnostic Maladies",
    "Météo Agricole",
    "Polélé",
    "Rapports PDF",
]


# ── Schémas ───────────────────────────────────────────────────────────────────

class BetaTesteurStats(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    badge: Optional[str] = None
    permissions: Optional[list] = None
    max_parcelles: int = 1
    nb_connexions: int = 0
    nb_parcelles: int = 0
    nb_analyses: int = 0
    derniere_activite: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=False)


class BetaGlobalStats(BaseModel):
    total_testeurs: int
    total_connexions: int
    total_parcelles: int
    total_analyses: int
    testeurs_actifs_7j: int


class BetaLogEntry(BaseModel):
    id: int
    user_id: int
    username: str
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    details: Optional[dict] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _beta_users(db: Session) -> list[User]:
    return db.query(User).filter(User.is_beta == True).all()  # noqa: E712


def _stats_for(user: User, db: Session) -> BetaTesteurStats:
    nb_connexions = (
        db.query(func.count(BetaLog.id))
        .filter(BetaLog.user_id == user.id, BetaLog.path == "/api/auth/login")
        .scalar() or 0
    )
    nb_parcelles = (
        db.query(func.count(Parcelle.id))
        .filter(
            Parcelle.org_id == user.org_id,
            Parcelle.statut != StatutParcelle.ARCHIVE,
        )
        .scalar() or 0
    )
    nb_analyses = (
        db.query(func.count(Analysis.id))
        .filter(Analysis.user_id == user.id)
        .scalar() or 0
    )
    last_log = (
        db.query(BetaLog.created_at)
        .filter(BetaLog.user_id == user.id)
        .order_by(BetaLog.created_at.desc())
        .first()
    )
    return BetaTesteurStats(
        user_id=user.id,
        username=user.full_name,
        email=user.email,
        phone=user.phone,
        badge=user.beta_badge,
        permissions=user.beta_permissions,
        max_parcelles=user.beta_max_parcelles or 1,
        nb_connexions=nb_connexions,
        nb_parcelles=nb_parcelles,
        nb_analyses=nb_analyses,
        derniere_activite=last_log[0] if last_log else None,
        created_at=user.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/testeurs", response_model=list[BetaTesteurStats])
def lister_testeurs(
    admin=Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Liste tous les bêta-testeurs avec leurs statistiques."""
    return [_stats_for(u, db) for u in _beta_users(db)]


@router.get("/testeur/{user_id}", response_model=BetaTesteurStats)
def detail_testeur(
    user_id: int,
    admin=Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Statistiques détaillées d'un bêta-testeur."""
    from fastapi import HTTPException
    user = db.query(User).filter(User.id == user_id, User.is_beta == True).first()  # noqa: E712
    if not user:
        raise HTTPException(404, "Bêta-testeur introuvable.")
    return _stats_for(user, db)


@router.get("/stats", response_model=BetaGlobalStats)
def stats_globales(
    admin=Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Statistiques globales de la phase bêta."""
    from datetime import timedelta
    users = _beta_users(db)
    user_ids = [u.id for u in users]
    org_ids = [u.org_id for u in users]

    total_connexions = (
        db.query(func.count(BetaLog.id))
        .filter(BetaLog.user_id.in_(user_ids), BetaLog.path == "/api/auth/login")
        .scalar() or 0
    ) if user_ids else 0

    total_parcelles = (
        db.query(func.count(Parcelle.id))
        .filter(
            Parcelle.org_id.in_(org_ids),
            Parcelle.statut != StatutParcelle.ARCHIVE,
        )
        .scalar() or 0
    ) if org_ids else 0

    total_analyses = (
        db.query(func.count(Analysis.id))
        .filter(Analysis.user_id.in_(user_ids))
        .scalar() or 0
    ) if user_ids else 0

    seuil = datetime.now(timezone.utc) - timedelta(days=7)
    actifs_7j = (
        db.query(func.count(func.distinct(BetaLog.user_id)))
        .filter(
            BetaLog.user_id.in_(user_ids),
            BetaLog.created_at >= seuil,
        )
        .scalar() or 0
    ) if user_ids else 0

    return BetaGlobalStats(
        total_testeurs=len(users),
        total_connexions=total_connexions,
        total_parcelles=total_parcelles,
        total_analyses=total_analyses,
        testeurs_actifs_7j=actifs_7j,
    )


@router.get("/logs", response_model=list[BetaLogEntry])
def logs_beta(
    user_id: Optional[int] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    admin=Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Journal des actions des bêta-testeurs (filtrable par testeur)."""
    q = (
        db.query(BetaLog, User.full_name)
        .join(User, BetaLog.user_id == User.id)
        .filter(User.is_beta == True)  # noqa: E712
    )
    if user_id:
        q = q.filter(BetaLog.user_id == user_id)
    rows = q.order_by(BetaLog.created_at.desc()).offset(offset).limit(limit).all()
    return [
        BetaLogEntry(
            id=log.id,
            user_id=log.user_id,
            username=name,
            method=log.method,
            path=log.path,
            status_code=log.status_code,
            details=log.details,
            created_at=log.created_at,
        )
        for log, name in rows
    ]


@router.get("/rapport")
def rapport_beta(
    admin=Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Rapport final de la phase bêta — tous les testeurs + statistiques globales."""
    users = _beta_users(db)
    testeurs = [_stats_for(u, db) for u in users]
    user_ids = [u.id for u in users]
    org_ids = [u.org_id for u in users]

    total_connexions = sum(t.nb_connexions for t in testeurs)
    total_parcelles = sum(t.nb_parcelles for t in testeurs)
    total_analyses = sum(t.nb_analyses for t in testeurs)

    return {
        "rapport": "Phase Bêta Terrain AgroScan Pro",
        "date_rapport": datetime.now(timezone.utc).isoformat(),
        "global": {
            "total_testeurs": len(users),
            "total_connexions": total_connexions,
            "total_parcelles": total_parcelles,
            "total_analyses": total_analyses,
        },
        "testeurs": [t.model_dump() for t in testeurs],
        "permissions_beta": BETA_PERMISSIONS,
    }
