"""
Sécurité : hachage des mots de passe (bcrypt) et jetons d'accès JWT.
Bonnes pratiques : mots de passe jamais stockés en clair, jetons signés et expirables.
On utilise la librairie bcrypt directement (robuste, sans dépendance fragile).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt, JWTError

from app.core.config import settings


def hash_password(plain: str) -> str:
    """Transforme un mot de passe en empreinte irréversible (bcrypt)."""
    pw = plain.encode("utf-8")[:72]  # bcrypt limite l'entrée à 72 octets
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond à son empreinte stockée."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """Génère un jeton JWT signé contenant l'identité de l'utilisateur."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Décode et valide un jeton. Renvoie None si invalide ou expiré."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
