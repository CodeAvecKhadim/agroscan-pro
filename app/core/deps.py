"""
Contrôle d'accès — dépendances FastAPI réutilisables.

Trois niveaux :
  1) Authentification    : qui est l'utilisateur ? (JWT valide)
  2) Droits / quotas     : son plan autorise-t-il cette action ? (matrice PLAN_FEATURES)
  3) Rôles               : a-t-il le rôle requis ? (owner/admin/member/viewer)

Bonne pratique : on ne fait JAMAIS confiance au client. Chaque endpoint sensible
dépend d'une de ces fonctions ; impossible de contourner un quota côté front.
"""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, Subscription, UsageCounter, SubStatus, UserRole, PlanType
from app.services.plans import features_for

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Récupère l'utilisateur connecté à partir du jeton JWT, ou refuse l'accès."""
    cred_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou session expirée.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise cred_error
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise cred_error
    return user


def current_subscription(user: User = Depends(current_user),
                         db: Session = Depends(get_db)) -> Subscription:
    """Renvoie l'abonnement de l'organisation de l'utilisateur."""
    sub = db.query(Subscription).filter(Subscription.org_id == user.org_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Aucun abonnement trouvé.")
    # Si la période payée est échue, on rétrograde proprement vers le plan gratuit.
    end = sub.current_period_end
    if end is not None and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)   # SQLite stocke sans fuseau
    if (end and sub.plan != PlanType.GRATUIT and end < datetime.now(timezone.utc)):
        sub.status = SubStatus.EXPIRED
        db.commit()
    return sub


def _current_period() -> str:
    """Clé du mois courant, ex : '2026-05'."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_usage(db: Session, org_id: int) -> UsageCounter:
    """Récupère (ou crée) le compteur de consommation du mois courant."""
    period = _current_period()
    uc = (db.query(UsageCounter)
            .filter(UsageCounter.org_id == org_id, UsageCounter.period == period)
            .first())
    if not uc:
        uc = UsageCounter(org_id=org_id, period=period, analyses_count=0)
        db.add(uc)
        db.commit()
        db.refresh(uc)
    return uc


def enforce_analysis_quota(user: User = Depends(current_user),
                           sub: Subscription = Depends(current_subscription),
                           db: Session = Depends(get_db)) -> User:
    """
    Garde-fou de quota : bloque une nouvelle analyse si le plan gratuit a atteint
    sa limite mensuelle. Les plans payants actifs sont illimités.
    """
    feats = features_for(sub.plan)
    limit = feats["monthly_analyses"]

    # Un plan payant échu/résilié est traité comme gratuit (sécurité).
    plan_actif = sub.status in (SubStatus.ACTIVE, SubStatus.TRIAL)
    if limit is None and plan_actif:
        return user  # illimité

    effective_limit = limit if (limit is not None) else features_for(PlanType.GRATUIT)["monthly_analyses"]
    uc = get_usage(db, user.org_id)
    if uc.analyses_count >= effective_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(f"Limite atteinte : {effective_limit} analyses/mois sur le plan gratuit. "
                    f"Passez au plan Premium pour des analyses illimitées."),
        )
    return user


def require_feature(feature_key: str):
    """
    Fabrique de dépendance : exige qu'une fonctionnalité soit incluse dans le plan.
    Ex : Depends(require_feature('pdf_reports'))
    """
    def checker(sub: Subscription = Depends(current_subscription)) -> Subscription:
        feats = features_for(sub.plan)
        if not feats.get(feature_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Fonctionnalité réservée à un plan supérieur ({feature_key}).",
            )
        return sub
    return checker


def require_role(*roles: UserRole):
    """Exige que l'utilisateur ait l'un des rôles indiqués (ex : owner/admin)."""
    def checker(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Droits insuffisants.")
        return user
    return checker
