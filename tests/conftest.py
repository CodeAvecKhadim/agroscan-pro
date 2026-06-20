"""
Fixtures partagées pour la suite de tests AgroScan Pro.
Crée les utilisateurs de test une seule fois par session pytest.
"""
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _register(phone: str, password: str = "test1234") -> str | None:
    """Inscrit un utilisateur et retourne le token. Ignore si déjà inscrit."""
    r = client.post("/api/auth/register", json={
        "full_name": f"Test {phone}",
        "phone": phone,
        "password": password,
        "profil": "producteur",
    })
    if r.status_code not in (201, 409):
        return None
    tok = client.post("/api/auth/login", data={"username": phone, "password": password})
    return tok.json().get("access_token") if tok.status_code == 200 else None


@pytest.fixture(scope="session")
def token_user_a():
    """Utilisateur A — propriétaire de parcelles de test."""
    time.sleep(0.5)  # évite le rate limit si tests précédents ont consommé le quota
    return _register("770000001")


@pytest.fixture(scope="session")
def token_user_b():
    """Utilisateur B — organisation différente de A."""
    time.sleep(0.5)
    return _register("770000002")


@pytest.fixture(scope="session")
def token_user_c():
    """Utilisateur C — pour tests restauration."""
    time.sleep(0.5)
    return _register("770000003")
