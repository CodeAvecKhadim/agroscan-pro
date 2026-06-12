"""
Tests E2E — Export PDF et Excel.
Vérifie que les endpoints retournent le bon type MIME et un contenu non vide.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.database import SessionLocal
from app.models import User, Organization, UserRole
from app.core.security import hash_password
import uuid


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def test_user_token():
    """Crée un user+org, retourne token + ids, cleanup après."""
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:8]
    org = Organization(name=f"PDF Test Org {suffix}")
    db.add(org)
    db.flush()
    user = User(
        org_id=org.id,
        full_name=f"PDF User {suffix}",
        email=f"pdf_{suffix}@test.agroscan",
        hashed_password=hash_password("Test123!"),
        role=UserRole.OWNER,
        profil="producteur",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)

    token = create_access_token({
        "sub": str(user.id), "org": org.id,
        "role": user.role.value, "profil": user.profil,
    })
    yield {"token": token, "user_id": user.id, "org_id": org.id}

    db.delete(user)
    db.delete(org)
    db.commit()
    db.close()


class TestExportPDF:
    """Tests endpoint GET /api/app/parcelles/{id}/export-pdf."""

    def test_sans_token_retourne_401(self, client):
        r = client.get("/api/app/parcelles/1/export-pdf")
        assert r.status_code == 401

    def test_parcelle_inexistante_retourne_404(self, client, test_user_token):
        headers = {"Authorization": f"Bearer {test_user_token['token']}"}
        r = client.get("/api/app/parcelles/999999/export-pdf", headers=headers)
        assert r.status_code == 404

    def test_pdf_genere_contenu_binaire(self, client, test_user_token):
        """Crée une vraie parcelle, génère le PDF, vérifie le contenu."""
        from app.models.champ import Parcelle
        db = SessionLocal()
        p = Parcelle(
            org_id=test_user_token["org_id"],
            nom="Parcelle Test PDF",
            type_culture="Riz",
            superficie_ha=2.5,
            code_parcelle=f"TEST-PDF-{uuid.uuid4().hex[:6].upper()}",
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        pid = p.id

        headers = {"Authorization": f"Bearer {test_user_token['token']}"}
        r = client.get(f"/api/app/parcelles/{pid}/export-pdf", headers=headers)

        db.delete(p)
        db.commit()
        db.close()

        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF", "Contenu ne commence pas par %PDF"
        assert len(r.content) > 1000

    def test_pdf_header_content_disposition(self, client, test_user_token):
        from app.models.champ import Parcelle
        db = SessionLocal()
        p = Parcelle(
            org_id=test_user_token["org_id"],
            nom="Test Disposition",
            type_culture="Maïs",
            code_parcelle=f"TEST-PDF-{uuid.uuid4().hex[:6].upper()}",
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        pid = p.id

        headers = {"Authorization": f"Bearer {test_user_token['token']}"}
        r = client.get(f"/api/app/parcelles/{pid}/export-pdf", headers=headers)

        db.delete(p)
        db.commit()
        db.close()

        assert r.status_code == 200
        assert "attachment" in r.headers.get("content-disposition", "")
        assert ".pdf" in r.headers.get("content-disposition", "")


class TestExportExcel:
    """Tests endpoints export Excel activités."""

    def test_sans_token_retourne_401(self, client):
        r = client.get("/api/app/activites/export-excel")
        assert r.status_code == 401

    def test_export_retourne_xlsx(self, client, test_user_token):
        headers = {"Authorization": f"Bearer {test_user_token['token']}"}
        r = client.get("/api/app/activites/export-excel", headers=headers)
        assert r.status_code == 200
        # Magic bytes XLSX = PK (ZIP)
        assert r.content[:2] == b"PK", "Contenu ne commence pas par PK (XLSX invalide)"
        assert "spreadsheetml" in r.headers.get("content-type", "")

    def test_export_parcelle_inexistante_404(self, client, test_user_token):
        headers = {"Authorization": f"Bearer {test_user_token['token']}"}
        r = client.get("/api/app/parcelles/999999/activites/export-excel", headers=headers)
        assert r.status_code == 404

    def test_export_parcelle_xlsx(self, client, test_user_token):
        from app.models.champ import Parcelle
        db = SessionLocal()
        p = Parcelle(
            org_id=test_user_token["org_id"],
            nom="Parcelle Excel Test",
            code_parcelle=f"TEST-XLS-{uuid.uuid4().hex[:6].upper()}",
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        pid = p.id

        headers = {"Authorization": f"Bearer {test_user_token['token']}"}
        r = client.get(f"/api/app/parcelles/{pid}/activites/export-excel", headers=headers)

        db.delete(p)
        db.commit()
        db.close()

        assert r.status_code == 200
        assert r.content[:2] == b"PK"
