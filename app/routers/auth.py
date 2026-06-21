"""
Routeur d'authentification : inscription et connexion.
À l'inscription, on crée d'un coup : l'organisation (tenant), l'utilisateur propriétaire,
et un abonnement gratuit. C'est le parcours d'onboarding SaaS standard.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import COOKIE_NAME
from app.core.security import hash_password, verify_password, create_access_token
from app.models import User, Organization, UserRole
from app.schemas import RegisterIn, TokenOut, UserOut
from app.services.subscription import create_default_subscription

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


def _set_auth_cookie(response: Response, token: str) -> None:
    """Pose le cookie httpOnly sécurisé en complément du JSON token."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=8 * 3600,
        path="/",
    )


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
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
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    create_default_subscription(db, org)
    return user


@router.post("/login", response_model=TokenOut)
def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Connexion : renvoie un jeton JWT + pose un cookie httpOnly sécurisé."""
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    token = create_access_token({"sub": str(user.id), "org": user.org_id, "role": user.role.value})
    _set_auth_cookie(response, token)
    return TokenOut(access_token=token)


@router.post("/logout", status_code=200)
def logout(response: Response):
    """Révoque le cookie httpOnly côté serveur."""
    response.delete_cookie(key=COOKIE_NAME, path="/", secure=True, httponly=True, samesite="lax")
    return {"message": "Déconnecté."}
