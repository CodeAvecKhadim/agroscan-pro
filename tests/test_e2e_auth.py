"""
Tests E2E — Authentification JWT et flux principal.
Flux réel : inscription → connexion → token JWT → endpoints protégés.
Pas de mocks : utilise la DB de test via HTTPX TestClient + vraie logique JWT.
Login utilise OAuth2PasswordRequestForm : form-data avec champ 'username' (= email).
"""
import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token, decode_token, hash_password
from app.core.database import SessionLocal
from app.models import User, Organization, UserRole


# ── Helpers ───────────────────────────────────────────────────────────────────

def _login(client: TestClient, email: str, password: str):
    """Effectue un login via form-data (OAuth2PasswordRequestForm)."""
    return client.post("/api/auth/login", data={"username": email, "password": password})


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def unique_suffix():
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="module")
def test_org_and_user(unique_suffix):
    """Crée une org + user de test réel en DB et les supprime après."""
    db = SessionLocal()
    suffix = unique_suffix
    org = Organization(name=f"E2E Test Org {suffix}")
    db.add(org)
    db.flush()

    password = "TestPass123!"
    user = User(
        org_id=org.id,
        full_name=f"E2E User {suffix}",
        email=f"e2e_{suffix}@test.agroscan",
        hashed_password=hash_password(password),
        role=UserRole.OWNER,
        profil="producteur",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)

    yield {"user": user, "org": org, "email": user.email, "password": password}

    db.delete(user)
    db.delete(org)
    db.commit()
    db.close()


@pytest.fixture(scope="module")
def auth_token(client, test_org_and_user):
    """Token JWT réel obtenu par un seul login (rate limit)."""
    r = _login(client, test_org_and_user["email"], test_org_and_user["password"])
    assert r.status_code == 200, f"Login échoué: {r.json()}"
    return r.json()["access_token"]


# ── Tests JWT unitaires ───────────────────────────────────────────────────────

class TestJWT:
    """Vérifie create_access_token et decode_token sans HTTP."""

    def test_token_encode_decode(self):
        payload = {"sub": "42", "org": 1, "role": "owner", "profil": "producteur"}
        token = create_access_token(payload)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "42"
        assert decoded["org"] == 1
        assert decoded["profil"] == "producteur"

    def test_token_invalide_retourne_none(self):
        assert decode_token("token.invalide.bidon") is None

    def test_token_expire(self):
        token = create_access_token({"sub": "99"}, expires_minutes=-1)
        assert decode_token(token) is None

    def test_token_contient_exp(self):
        token = create_access_token({"sub": "1"})
        decoded = decode_token(token)
        assert "exp" in decoded

    def test_hash_password_non_reversible(self):
        h = hash_password("monMotDePasse")
        assert h != "monMotDePasse"
        assert len(h) > 20

    def test_verify_password_ok(self):
        from app.core.security import verify_password
        h = hash_password("secret123")
        assert verify_password("secret123", h) is True

    def test_verify_password_faux(self):
        from app.core.security import verify_password
        h = hash_password("secret123")
        assert verify_password("mauvais", h) is False


# ── Tests E2E login → endpoints ───────────────────────────────────────────────

class TestE2EFlux:
    """Flux complet : login → token JWT → accès endpoints."""

    def test_login_retourne_token(self, auth_token):
        assert auth_token is not None
        assert len(auth_token) > 20

    def test_token_valide_decodable(self, auth_token, test_org_and_user):
        decoded = decode_token(auth_token)
        assert decoded is not None
        assert decoded["sub"] == str(test_org_and_user["user"].id)

    def test_me_avec_token_valide(self, client, auth_token, test_org_and_user):
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
        assert r.status_code == 200
        me = r.json()
        assert me["email"] == test_org_and_user["email"]

    def test_me_sans_token_retourne_401(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_token_invalide_retourne_401(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer faux.token.bidon"})
        assert r.status_code == 401

    def test_login_mauvais_mdp_retourne_401(self, client, test_org_and_user):
        r = _login(client, test_org_and_user["email"], "mauvais_mot_de_passe")
        assert r.status_code == 401

    def test_login_email_inconnu_retourne_401(self, client):
        r = _login(client, "inexistant@nowhere.test", "quelconque")
        assert r.status_code == 401

    def test_parcelles_avec_token_valide(self, client, auth_token):
        r = client.get("/api/champ/parcelles", headers={"Authorization": f"Bearer {auth_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_parcelles_sans_token_retourne_401(self, client):
        r = client.get("/api/champ/parcelles")
        assert r.status_code == 401

    def test_satellite_analyse_sans_token_retourne_401(self, client):
        r = client.get("/api/app/satellite/1")
        assert r.status_code == 401

    def test_export_pdf_sans_token_retourne_401(self, client):
        r = client.get("/api/app/parcelles/1/export-pdf")
        assert r.status_code == 401


# ── Tests E2E profils ─────────────────────────────────────────────────────────

class TestE2EProfilAcces:
    """Vérifie que les profils sont bien encodés dans le token."""

    def test_profil_producteur_dans_token(self, auth_token):
        decoded = decode_token(auth_token)
        assert decoded.get("profil") == "producteur"

    def test_token_contient_org_id(self, auth_token, test_org_and_user):
        decoded = decode_token(auth_token)
        assert decoded.get("org") == test_org_and_user["user"].org_id
