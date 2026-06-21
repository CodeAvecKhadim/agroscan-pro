"""
Routeur Coopérative : fonctionnalités multi-utilisateurs et multi-exploitations.
Chaque endpoint est protégé par require_feature(...) : il renvoie 403 si le plan
de l'organisation n'inclut pas la fonctionnalité (ex : un compte gratuit ou premium
ne peut pas inviter de membres).
"""
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import current_user, current_subscription, require_feature, require_role
from app.core.security import hash_password
from app.models import (User, Farm, Analysis, Subscription, UserRole)
from app.schemas import FarmIn, FarmOut, InviteMemberIn, UserOut
from app.services.plans import features_for

router = APIRouter(prefix="/api/coop", tags=["Coopérative"])


# ---------- Multi-utilisateurs ----------
@router.post("/members", response_model=UserOut, status_code=201,
             dependencies=[Depends(require_feature("multi_user"))])
def invite_member(
    data: InviteMemberIn,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """Ajoute un membre à la coopérative, dans la limite des sièges payés."""
    count = db.query(func.count(User.id)).filter(User.org_id == user.org_id).scalar()
    if count >= sub.seats:
        raise HTTPException(
            status_code=402,
            detail=f"Limite de {sub.seats} membre(s) atteinte. Ajoutez des sièges à votre abonnement.",
        )
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé.")

    member = User(
        org_id=user.org_id, full_name=data.full_name, email=data.email,
        phone=data.phone, hashed_password=hash_password(data.password), role=data.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/members", response_model=List[UserOut],
            dependencies=[Depends(require_feature("multi_user"))])
def list_members(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Liste les membres de la coopérative."""
    return db.query(User).filter(User.org_id == user.org_id).all()


# ---------- Multi-exploitations ----------
@router.post("/farms", response_model=FarmOut, status_code=201,
             dependencies=[Depends(require_feature("multi_farm"))])
def create_farm(data: FarmIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Enregistre une exploitation / parcelle."""
    farm = Farm(org_id=user.org_id, **data.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/farms", response_model=List[FarmOut],
            dependencies=[Depends(require_feature("multi_farm"))])
def list_farms(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Liste les exploitations de l'organisation."""
    return db.query(Farm).filter(Farm.org_id == user.org_id).all()


# ---------- Tableau de bord collaboratif ----------
@router.get("/dashboard", dependencies=[Depends(require_feature("collab_dashboard"))])
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """
    Vue d'ensemble pour coopératives/ONG : nombre de membres, d'exploitations,
    total d'analyses, score moyen des sols, et répartition par culture et région.
    """
    org_id = user.org_id
    n_members = db.query(func.count(User.id)).filter(User.org_id == org_id).scalar()
    n_farms = db.query(func.count(Farm.id)).filter(Farm.org_id == org_id).scalar()
    n_analyses = db.query(func.count(Analysis.id)).filter(Analysis.org_id == org_id).scalar()
    avg_score = db.query(func.avg(Analysis.score)).filter(Analysis.org_id == org_id).scalar()

    by_culture = dict(
        db.query(Analysis.culture, func.count(Analysis.id))
          .filter(Analysis.org_id == org_id).group_by(Analysis.culture).all()
    )
    by_region = dict(
        db.query(Analysis.region, func.count(Analysis.id))
          .filter(Analysis.org_id == org_id).group_by(Analysis.region).all()
    )
    ready = db.query(func.count(Analysis.id)).filter(
        Analysis.org_id == org_id, Analysis.score >= 6).scalar()

    return {
        "members": n_members,
        "farms": n_farms,
        "analyses": n_analyses,
        "avg_score": round(avg_score, 1) if avg_score else 0,
        "soils_ready": ready,
        "by_culture": by_culture,
        "by_region": by_region,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
