"""
Contrôle d'accès — dépendances FastAPI réutilisables.

Trois niveaux :
  1) Authentification    : qui est l'utilisateur ? (JWT valide)
  2) Droits / quotas     : son plan autorise-t-il cette action ? (matrice PLAN_FEATURES)
  3) Rôles               : a-t-il le rôle requis ? (owner/admin/member/viewer)

Modèle de quotas (juin 2026) :
  - Plan GRATUIT : 3 analyses IA/JOUR, 1 satellite/SEMAINE, 2 parcelles max, 3 ha/parcelle
  - Plan PREMIUM : illimité (campagne 90 jours)
  - Plan COOPERATIVE : illimité
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
    """Récupère l'utilisateur connecté à partir du jeton JWT."""
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
    # Rétrogradation automatique si période échue
    end = sub.current_period_end
    if end is not None and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if (end and sub.plan != PlanType.GRATUIT and end < datetime.now(timezone.utc)):
        sub.status = SubStatus.EXPIRED
        db.commit()
    return sub


def effective_plan(sub: Subscription) -> PlanType:
    """Plan réellement actif : EXPIRED/PAST_DUE → GRATUIT pour les feature checks."""
    if sub.status in (SubStatus.ACTIVE, SubStatus.TRIAL):
        return sub.plan
    return PlanType.GRATUIT


def _current_period() -> str:
    """Clé du mois courant, ex : '2026-05'."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _today_str() -> str:
    """Date du jour, ex : '2026-06-12'."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _current_week_str() -> str:
    """Semaine ISO courante, ex : '2026-W24'."""
    d = datetime.now(timezone.utc)
    return f"{d.year}-W{d.isocalendar()[1]:02d}"


def get_usage(db: Session, org_id: int) -> UsageCounter:
    """Récupère (ou crée) le compteur de consommation du mois courant."""
    period = _current_period()
    uc = (db.query(UsageCounter)
            .filter(UsageCounter.org_id == org_id, UsageCounter.period == period)
            .first())
    if not uc:
        uc = UsageCounter(org_id=org_id, period=period, analyses_count=0,
                          daily_ai_count=0, weekly_satellite_count=0)
        db.add(uc)
        db.commit()
        db.refresh(uc)
    return uc


def enforce_analysis_quota(user: User = Depends(current_user),
                           sub: Subscription = Depends(current_subscription),
                           db: Session = Depends(get_db)) -> User:
    """
    Garde-fou quota IA : plan GRATUIT limité à 3 analyses/JOUR.
    Plans payants actifs : illimité.
    """
    plan = effective_plan(sub)
    feats = features_for(plan)
    limit = feats["daily_ai_analyses"]

    if limit is None:
        return user  # illimité (plan payant actif)

    uc = get_usage(db, user.org_id)
    today = _today_str()

    # Reset si nouveau jour
    if uc.daily_ai_date != today:
        uc.daily_ai_count = 0
        uc.daily_ai_date = today
        db.commit()

    if uc.daily_ai_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(f"Limite atteinte : {limit} analyses IA/jour sur le plan gratuit. "
                    f"Passez au plan Premium pour des analyses illimitées."),
        )
    return user


def enforce_satellite_quota(user: User = Depends(current_user),
                             sub: Subscription = Depends(current_subscription),
                             db: Session = Depends(get_db)) -> User:
    """
    Garde-fou satellite : plan GRATUIT limité à 1 analyse satellite/SEMAINE.
    Plans payants actifs : illimité.
    """
    plan = effective_plan(sub)
    feats = features_for(plan)
    limit = feats["weekly_satellite"]

    if limit is None:
        return user  # illimité

    uc = get_usage(db, user.org_id)
    week = _current_week_str()

    if uc.weekly_period != week:
        uc.weekly_satellite_count = 0
        uc.weekly_period = week
        db.commit()

    if uc.weekly_satellite_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(f"Limite atteinte : {limit} analyse satellite/semaine sur le plan gratuit. "
                    f"Passez au plan Premium pour des analyses illimitées."),
        )
    return user


def enforce_parcelle_limit(user: User = Depends(current_user),
                            sub: Subscription = Depends(current_subscription),
                            db: Session = Depends(get_db)) -> User:
    """
    Vérifie que la limite de parcelles du plan n'est pas dépassée avant création.
    """
    plan = effective_plan(sub)
    feats = features_for(plan)
    max_p = feats["max_parcelles"]

    if max_p is None:
        return user  # illimité

    from app.models.champ import Parcelle
    count = db.query(Parcelle).filter_by(org_id=user.org_id).count()
    if count >= max_p:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(f"Limite atteinte : {max_p} parcelle(s) sur le plan gratuit. "
                    f"Passez au plan Premium pour créer plus de parcelles."),
        )
    return user


def increment_daily_ai(db: Session, org_id: int):
    """Incrémente le compteur IA journalier après une analyse réussie."""
    uc = get_usage(db, org_id)
    today = _today_str()
    if uc.daily_ai_date != today:
        uc.daily_ai_count = 0
        uc.daily_ai_date = today
    uc.daily_ai_count += 1
    uc.analyses_count += 1   # legacy compat
    db.commit()


def increment_weekly_satellite(db: Session, org_id: int):
    """Incrémente le compteur satellite hebdomadaire après une analyse réussie."""
    uc = get_usage(db, org_id)
    week = _current_week_str()
    if uc.weekly_period != week:
        uc.weekly_satellite_count = 0
        uc.weekly_period = week
    uc.weekly_satellite_count += 1
    db.commit()


def require_feature(feature_key: str):
    """Fabrique de dépendance : exige qu'une fonctionnalité soit incluse dans le plan."""
    def checker(sub: Subscription = Depends(current_subscription)) -> Subscription:
        plan = effective_plan(sub)
        feats = features_for(plan)
        if not feats.get(feature_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Fonctionnalité réservée à un plan supérieur ({feature_key}).",
            )
        return sub
    return checker


def require_role(*roles: UserRole):
    """Exige que l'utilisateur ait l'un des rôles indiqués."""
    def checker(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Droits insuffisants.")
        return user
    return checker


def require_profil(*profils: str):
    """Exige que l'utilisateur ait l'un des profils indiqués."""
    def checker(user: User = Depends(current_user)) -> User:
        user_profil = getattr(user, "profil", "producteur")
        if user_profil not in profils:
            raise HTTPException(
                status_code=403,
                detail=f"Accès réservé au profil : {', '.join(profils)}.",
            )
        return user
    return checker
