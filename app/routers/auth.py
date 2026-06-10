"""
Routeur d'authentification : inscription et connexion.
À l'inscription, on crée d'un coup : l'organisation (tenant), l'utilisateur propriétaire,
et un abonnement gratuit. C'est le parcours d'onboarding SaaS standard.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user
from app.core.limiter import limiter
from app.core.security import hash_password, verify_password, create_access_token
from app.models import User, Organization, UserRole
from app.schemas import RegisterIn, TokenOut, UserOut
from app.services.subscription import create_default_subscription

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit("3/minute")
def register(request: Request, data: RegisterIn, db: Session = Depends(get_db)):
    """Crée une organisation + un utilisateur propriétaire + un abonnement gratuit."""
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé.")

    org = Organization(
        name=data.org_name or f"Compte de {data.full_name}",
        is_cooperative=data.is_cooperative,
    )
    db.add(org)
    db.flush()  # pour obtenir org.id avant le commit

    user = User(
        org_id=org.id,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.password),
        role=UserRole.OWNER,
        profil=data.profil or "producteur",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    create_default_subscription(db, org)
    return user


@router.post("/login", response_model=TokenOut)
@limiter.limit("5/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Connexion : renvoie un jeton JWT. (champ 'username' = email)"""
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    token = create_access_token({"sub": str(user.id), "org": user.org_id, "role": user.role.value, "profil": user.profil})
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut, tags=["Utilisateurs"])
def me(user: User = Depends(current_user)):
    """Retourne le profil de l'utilisateur connecté."""
    return user
