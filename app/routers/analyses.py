"""
Routeur des analyses de sol.
- POST /api/analyses        : crée une analyse (protégé par le quota du plan gratuit).
- GET  /api/analyses        : historique (fenêtre limitée à 30 j sur le plan gratuit).
Le diagnostic est SIMPLIFIÉ en gratuit, AVANCÉ en premium/coopérative.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user, current_subscription, enforce_analysis_quota, get_usage
from app.models import Analysis, User, Subscription
from app.schemas import AnalysisIn, AnalysisOut
from app.services.diagnostic import diagnose
from app.services.plans import features_for
from app.services.subscription import history_cutoff

router = APIRouter(prefix="/api/analyses", tags=["Analyses de sol"])


@router.post("", response_model=AnalysisOut, status_code=201)
def create_analysis(
    data: AnalysisIn,
    user: User = Depends(enforce_analysis_quota),       # ← bloque si quota gratuit dépassé
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """Lance un diagnostic, l'enregistre, et incrémente le compteur du mois."""
    feats = features_for(sub.plan)
    advanced = feats["advanced_reco"]                   # recommandations avancées = premium+

    result = diagnose(data.culture, data.measurements, advanced=advanced)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    analysis = Analysis(
        org_id=user.org_id, user_id=user.id, farm_id=data.farm_id,
        culture=data.culture, region=data.region,
        measurements=data.measurements,
        score=result["score"], verdict=result["verdict"], advanced=advanced,
    )
    db.add(analysis)

    # Incrément du compteur de consommation mensuel (pour les quotas).
    uc = get_usage(db, user.org_id)
    uc.analyses_count += 1
    db.commit()
    db.refresh(analysis)

    out = AnalysisOut.model_validate(analysis)
    out.diagnostic = result["detail"]                   # détail calculé (non stocké tel quel)
    return out


@router.get("", response_model=List[AnalysisOut])
def list_analyses(
    user: User = Depends(current_user),
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """
    Historique des analyses de l'organisation.
    Sur le plan gratuit, on ne renvoie que les 30 derniers jours.
    """
    q = db.query(Analysis).filter(Analysis.org_id == user.org_id)
    cutoff = history_cutoff(sub.plan)
    if cutoff is not None:
        q = q.filter(Analysis.created_at >= cutoff)
    return q.order_by(Analysis.created_at.desc()).all()
