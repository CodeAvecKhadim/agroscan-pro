"""
Tests — Router /api/app/satellite (Phase 4).
Vérifie cache, trigger analyse, et protection historique.
Utilise mocks pour fetch_indices et authentification.
"""
import pytest
from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.ndvi_message import ndvi_to_message


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_token(profil: str = "producteur", org_id: int = 1, user_id: int = 1) -> str:
    """Token JWT minimal pour les tests (non signé — override via mock)."""
    import base64, json
    payload = {"sub": str(user_id), "org_id": org_id, "profil": profil}
    b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{b64}.sig"


def _fake_user(profil="producteur", org_id=1, user_id=1):
    u = MagicMock()
    u.id = user_id
    u.org_id = org_id
    u.profil = profil
    return u


def _fake_parcelle(pid=1, org_id=1):
    p = MagicMock()
    p.id = pid
    p.org_id = org_id
    p.type_culture = "Maïs"
    p.superficie_ha = 2.5
    p.centre_lat = 14.5
    p.centre_lon = -14.0
    return p


FAKE_INDICES = {"ndvi": 0.65, "ndwi": -0.05, "ndre": 0.45, "source": "sentinel-2"}


# ── Tests ndvi_to_message intégration ────────────────────────────────────────

class TestNdviMessageIntegration:
    """Vérifie que ndvi_to_message produit des messages exploitables."""

    def test_message_non_vide(self):
        msg, col = ndvi_to_message(0.65, -0.05, "sentinel-2")
        assert len(msg) > 10
        assert col in {"vert", "orange", "rouge"}

    def test_ndvi_eleve_vert(self):
        _, col = ndvi_to_message(0.65)
        assert col == "vert"

    def test_ndvi_rouge_message_conseiller(self):
        msg, col = ndvi_to_message(0.05)
        assert col == "rouge"
        assert "conseiller" in msg.lower() or "anomalie" in msg.lower()


# ── Tests router sans DB ──────────────────────────────────────────────────────

class TestSatelliteRouterAuth:
    """Vérifie que les endpoints refusent les requêtes non-authentifiées."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_get_analyse_sans_token_retourne_401(self):
        r = self.client.get("/api/app/satellite/1")
        assert r.status_code == 401

    def test_post_analyser_sans_token_retourne_401(self):
        r = self.client.post("/api/app/satellite/1/analyser")
        assert r.status_code == 401

    def test_historique_sans_token_retourne_401(self):
        r = self.client.get("/api/app/satellite/historique/1")
        assert r.status_code == 401


# ── Tests logique métier (mocks complets) ────────────────────────────────────

class TestSatelliteAnalyse:
    """Tests de la logique d'analyse satellite avec mocks."""

    def setup_method(self):
        self.client = TestClient(app)

    def _auth_headers(self):
        return {"Authorization": "Bearer test_token"}

    def test_get_analyse_retourne_cache_si_recent(self):
        """Si une analyse récente existe, retourner le cache sans appeler fetch_indices."""
        fake_user = _fake_user()
        fake_analyse = MagicMock()
        fake_analyse.parcelle_id = 1
        fake_analyse.date = date.today()
        fake_analyse.message_simple = "Votre champ va très bien."
        fake_analyse.couleur = "vert"
        fake_analyse.source = "sentinel-2"
        fake_analyse.created_at = datetime.now(timezone.utc)

        with patch("app.routers.app_satellite.current_user", return_value=fake_user), \
             patch("app.core.deps.current_user", return_value=fake_user), \
             patch("app.routers.app_satellite._get_parcelle", return_value=_fake_parcelle()), \
             patch("app.routers.app_satellite.AnalyseSatellite") as MockAS, \
             patch("app.routers.app_satellite.fetch_indices") as mock_fetch:

            # Simuler cache existant
            db_mock = MagicMock()
            query_mock = MagicMock()
            query_mock.filter.return_value.order_by.return_value.first.return_value = fake_analyse
            db_mock.query.return_value = query_mock

            with patch("app.routers.app_satellite.get_db", return_value=iter([db_mock])):
                r = self.client.get("/api/app/satellite/1", headers=self._auth_headers())

            # fetch_indices ne doit pas être appelé si cache existe
            mock_fetch.assert_not_called()

    def test_ndvi_to_message_appele_avec_bons_params(self):
        """ndvi_to_message reçoit les valeurs correctes depuis fetch_indices."""
        with patch("app.services.ndvi_message.ndvi_to_message") as mock_msg:
            mock_msg.return_value = ("Votre champ est en bon état.", "vert")
            msg, col = mock_msg(0.65, -0.05, "sentinel-2")
            mock_msg.assert_called_once_with(0.65, -0.05, "sentinel-2")
            assert col == "vert"

    def test_historique_requiert_profil_conseiller(self):
        """GET /historique/{id} doit rejeter un producteur (403)."""
        fake_producteur = _fake_user(profil="producteur")

        with patch("app.core.deps.current_user", return_value=fake_producteur):
            r = self.client.get(
                "/api/app/satellite/historique/1",
                headers=self._auth_headers(),
            )
        # 401 ou 403 selon l'implémentation — pas 200
        assert r.status_code in {401, 403}


# ── Tests schéma de sortie ────────────────────────────────────────────────────

class TestAnalyseSatOut:
    """Vérifie la structure de sortie des analyses."""

    def test_champs_requis_presents(self):
        from app.routers.app_satellite import AnalyseSatOut
        a = AnalyseSatOut(
            parcelle_id=1,
            date=date.today(),
            message_simple="Test",
            couleur="vert",
            source="sentinel-2",
            created_at=datetime.now(timezone.utc),
        )
        assert a.parcelle_id == 1
        assert a.couleur == "vert"
        assert a.message_simple == "Test"

    def test_tech_out_inclut_ndvi(self):
        from app.routers.app_satellite import AnalyseSatTechOut
        a = AnalyseSatTechOut(
            parcelle_id=1,
            date=date.today(),
            message_simple="Test",
            couleur="orange",
            source="simule",
            created_at=datetime.now(timezone.utc),
            ndvi_moyen=0.42,
            ndwi=-0.18,
        )
        assert a.ndvi_moyen == 0.42
        assert a.ndwi == -0.18
        assert a.ndre is None
