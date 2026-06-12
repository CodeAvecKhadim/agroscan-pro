"""
Router Admin — tableau de bord multi-organisations.
Accès : profil 'admin' uniquement.
Préfixe : /api/admin
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_profil
from app.models import User, Organization, Subscription, PlanType, SubStatus
from app.models.champ import Parcelle
from app.models.analyses_satellite import AnalyseSatellite

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Schémas de sortie ─────────────────────────────────────────────────────────

class OrgStats(BaseModel):
    org_id: int
    org_name: str
    plan: str
    nb_users: int
    nb_parcelles: int
    nb_analyses_satellite: int
    derniere_activite: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=False)


class PlatformStats(BaseModel):
    total_orgs: int
    total_users: int
    total_parcelles: int
    total_analyses_satellite: int
    orgs_par_plan: dict
    nouveaux_7j: int


class UserInfo(BaseModel):
    id: int
    full_name: str
    email: str
    profil: str
    role: str
    org_id: int
    org_name: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=False)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=PlatformStats)
def stats_plateforme(
    admin: User = Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Statistiques globales de la plateforme."""
    total_orgs = db.query(func.count(Organization.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    total_parcelles = db.query(func.count(Parcelle.id)).scalar()
    total_sat = db.query(func.count(AnalyseSatellite.id)).scalar()

    # Répartition par plan
    subs = db.query(Subscription.plan, func.count(Subscription.id)).group_by(Subscription.plan).all()
    orgs_par_plan = {str(s.plan.value if hasattr(s.plan, "value") else s.plan): s[1] for s in subs}

    # Nouvelles orgs 7 derniers jours
    seuil = datetime.now(timezone.utc) - timedelta(days=7)
    nouveaux = db.query(func.count(Organization.id)).filter(Organization.created_at >= seuil).scalar() if hasattr(Organization, "created_at") else 0

    return PlatformStats(
        total_orgs=total_orgs or 0,
        total_users=total_users or 0,
        total_parcelles=total_parcelles or 0,
        total_analyses_satellite=total_sat or 0,
        orgs_par_plan=orgs_par_plan,
        nouveaux_7j=nouveaux or 0,
    )


@router.get("/organisations", response_model=list[OrgStats])
def lister_organisations(
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin: User = Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Liste toutes les organisations avec statistiques."""
    orgs = db.query(Organization).offset(offset).limit(limit).all()

    result = []
    for org in orgs:
        nb_users = db.query(func.count(User.id)).filter(User.org_id == org.id).scalar() or 0
        nb_parcelles = db.query(func.count(Parcelle.id)).filter(Parcelle.org_id == org.id).scalar() or 0
        nb_sat = db.query(func.count(AnalyseSatellite.id)).filter(AnalyseSatellite.org_id == org.id).scalar() or 0

        sub = db.query(Subscription).filter_by(org_id=org.id).first()
        plan_label = sub.plan.value if sub and sub.plan else "gratuit"

        derniere_sat = (
            db.query(AnalyseSatellite.created_at)
            .filter(AnalyseSatellite.org_id == org.id)
            .order_by(AnalyseSatellite.created_at.desc())
            .first()
        )

        result.append(OrgStats(
            org_id=org.id,
            org_name=org.name,
            plan=plan_label,
            nb_users=nb_users,
            nb_parcelles=nb_parcelles,
            nb_analyses_satellite=nb_sat,
            derniere_activite=derniere_sat[0] if derniere_sat else None,
        ))

    return result


@router.get("/utilisateurs", response_model=list[UserInfo])
def lister_utilisateurs(
    org_id: Optional[int] = None,
    profil: Optional[str] = None,
    limit: int = Query(100, le=500),
    admin: User = Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Liste tous les utilisateurs (filtrable par org ou profil)."""
    q = db.query(User, Organization.name).join(Organization, User.org_id == Organization.id)
    if org_id:
        q = q.filter(User.org_id == org_id)
    if profil:
        q = q.filter(User.profil == profil)
    rows = q.limit(limit).all()

    return [
        UserInfo(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            profil=u.profil,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            org_id=u.org_id,
            org_name=org_name,
            created_at=getattr(u, "created_at", None),
        )
        for u, org_name in rows
    ]


@router.get("/organisation/{org_id}", response_model=OrgStats)
def detail_organisation(
    org_id: int,
    admin: User = Depends(require_profil("admin")),
    db: Session = Depends(get_db),
):
    """Détail d'une organisation."""
    org = db.query(Organization).filter_by(id=org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable.")

    nb_users = db.query(func.count(User.id)).filter(User.org_id == org_id).scalar() or 0
    nb_parcelles = db.query(func.count(Parcelle.id)).filter(Parcelle.org_id == org_id).scalar() or 0
    nb_sat = db.query(func.count(AnalyseSatellite.id)).filter(AnalyseSatellite.org_id == org_id).scalar() or 0
    sub = db.query(Subscription).filter_by(org_id=org_id).first()
    plan_label = sub.plan.value if sub and sub.plan else "gratuit"

    return OrgStats(
        org_id=org.id,
        org_name=org.name,
        plan=plan_label,
        nb_users=nb_users,
        nb_parcelles=nb_parcelles,
        nb_analyses_satellite=nb_sat,
    )
