"""
Tests GPS + Kindwise — Étape 4.

Couvre :
  - Unitaires : resize, normalisation, _get_parcelle_gps
  - Intégration API : payload Kindwise avec/sans GPS, cas d'erreur
"""
import io
import json
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.crop_health import _resize, _normaliser, identifier_maladie, CropHealthError

client = TestClient(app)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _fake_image(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color=(80, 120, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _kindwise_success_response() -> dict:
    """Réponse Kindwise simulée avec une maladie à 85%."""
    return {
        "result": {
            "disease": {
                "suggestions": [
                    {
                        "name": "Mildiou du mil",
                        "probability": 0.85,
                        "details": {
                            "description": "Taches jaunes sur feuilles.",
                            "treatment": {"biological": ["Extrait de neem"], "chemical": []},
                        },
                    }
                ]
            }
        }
    }


# ── Unitaires : resize ────────────────────────────────────────────────────────

class TestResize:
    def test_grande_image_reduite_a_1024(self):
        original = _fake_image(2000, 1500)
        resized = _resize(original)
        img = Image.open(io.BytesIO(resized))
        assert max(img.size) <= 1024

    def test_petite_image_non_modifiee(self):
        original = _fake_image(400, 300)
        resized = _resize(original)
        img = Image.open(io.BytesIO(resized))
        assert img.size == (400, 300)

    def test_image_carree_reduite(self):
        original = _fake_image(2048, 2048)
        resized = _resize(original)
        img = Image.open(io.BytesIO(resized))
        assert img.size == (1024, 1024)

    def test_bytes_invalides_retournes_tels_quels(self):
        mauvais = b"ce_nest_pas_une_image"
        result = _resize(mauvais)
        assert result == mauvais


# ── Unitaires : normalisation réponse Kindwise ───────────────────────────────

class TestNormaliser:
    def test_suggestions_vides(self):
        result = _normaliser({"result": {"disease": {"suggestions": []}}})
        assert result == {"disponible": False, "maladies": []}

    def test_trois_maladies_max(self):
        suggestions = [
            {"name": f"Maladie {i}", "probability": 0.9 - i * 0.1, "details": {}}
            for i in range(5)
        ]
        result = _normaliser({"result": {"disease": {"suggestions": suggestions}}})
        assert len(result["maladies"]) == 3

    def test_certitude_arrondie_en_pourcent(self):
        result = _normaliser({
            "result": {"disease": {"suggestions": [
                {"name": "Test", "probability": 0.856, "details": {}}
            ]}}
        })
        assert result["maladies"][0]["certitude"] == 86

    def test_structure_manquante_ne_crashe_pas(self):
        result = _normaliser({})
        assert result["disponible"] is False

    def test_traitement_dict_concatene(self):
        result = _normaliser({
            "result": {"disease": {"suggestions": [
                {"name": "X", "probability": 0.7, "details": {
                    "treatment": {
                        "prevention": ["Rotation des cultures"],
                        "biological": ["Neem"],
                        "chemical": [],
                    }
                }}
            ]}}
        })
        assert "Neem" in result["maladies"][0]["traitement"]
        assert "Rotation" in result["maladies"][0]["traitement"]


# ── Unitaires : identifier_maladie — signature List[bytes] ───────────────────

class TestIdentifierMaladie:
    def test_accepte_liste_images(self):
        """identifier_maladie doit accepter List[bytes], pas bytes seul."""
        import inspect
        sig = inspect.signature(identifier_maladie)
        param = sig.parameters["images_bytes"]
        # Le type annoté doit être List ou contenir list
        annotation = str(param.annotation)
        assert "List" in annotation or "list" in annotation

    def test_cle_absente_leve_erreur(self):
        with patch("app.services.crop_health.settings") as mock_s:
            mock_s.CROP_HEALTH_API_KEY = ""
            with pytest.raises(CropHealthError, match="absente"):
                identifier_maladie([_fake_image()])

    def test_reponse_json_invalide_leve_erreur(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("bad json")

        with patch("app.services.crop_health.settings") as mock_s, \
             patch("app.services.crop_health.requests.post", return_value=mock_resp), \
             patch("app.services.crop_health.get_remaining_credits", return_value=100):
            mock_s.CROP_HEALTH_API_KEY = "test_key"
            with pytest.raises(CropHealthError, match="illisible"):
                identifier_maladie([_fake_image()])

    def test_erreur_401_leve_erreur_cle(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("app.services.crop_health.settings") as mock_s, \
             patch("app.services.crop_health.requests.post", return_value=mock_resp), \
             patch("app.services.crop_health.get_remaining_credits", return_value=100):
            mock_s.CROP_HEALTH_API_KEY = "bad_key"
            with pytest.raises(CropHealthError, match="invalide"):
                identifier_maladie([_fake_image()])

    def test_gps_present_dans_payload_si_fourni(self):
        """latitude/longitude doivent apparaître dans le payload JSON envoyé à Kindwise."""
        payloads_capturés = []

        def fake_post(url, *, params, json, headers, timeout):
            payloads_capturés.append(json)
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = _kindwise_success_response()
            return mock_resp

        with patch("app.services.crop_health.settings") as mock_s, \
             patch("app.services.crop_health.requests.post", side_effect=fake_post), \
             patch("app.services.crop_health.get_remaining_credits", return_value=200):
            mock_s.CROP_HEALTH_API_KEY = "test_key"
            identifier_maladie([_fake_image()], latitude=14.6928, longitude=-17.4467)

        assert len(payloads_capturés) == 1
        payload = payloads_capturés[0]
        assert "latitude" in payload
        assert "longitude" in payload
        assert payload["latitude"] == pytest.approx(14.6928)
        assert payload["longitude"] == pytest.approx(-17.4467)

    def test_gps_absent_si_non_fourni(self):
        """Sans lat/lon, le payload ne doit pas contenir latitude/longitude."""
        payloads_capturés = []

        def fake_post(url, *, params, json, headers, timeout):
            payloads_capturés.append(json)
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = _kindwise_success_response()
            return mock_resp

        with patch("app.services.crop_health.settings") as mock_s, \
             patch("app.services.crop_health.requests.post", side_effect=fake_post), \
             patch("app.services.crop_health.get_remaining_credits", return_value=200):
            mock_s.CROP_HEALTH_API_KEY = "test_key"
            identifier_maladie([_fake_image()])

        payload = payloads_capturés[0]
        assert "latitude" not in payload
        assert "longitude" not in payload

    def test_multi_images_dans_payload(self):
        """Plusieurs images doivent toutes apparaître dans le tableau 'images'."""
        payloads_capturés = []

        def fake_post(url, *, params, json, headers, timeout):
            payloads_capturés.append(json)
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = _kindwise_success_response()
            return mock_resp

        with patch("app.services.crop_health.settings") as mock_s, \
             patch("app.services.crop_health.requests.post", side_effect=fake_post), \
             patch("app.services.crop_health.get_remaining_credits", return_value=200):
            mock_s.CROP_HEALTH_API_KEY = "test_key"
            identifier_maladie([_fake_image(), _fake_image(200, 200), _fake_image(300, 300)])

        assert len(payloads_capturés[0]["images"]) == 3


# ── Intégration : _get_parcelle_gps ──────────────────────────────────────────

class TestGetParcelleGPS:
    """Tests unitaires de la fonction _get_parcelle_gps avec DB mockée."""

    def _make_parcelle(self, centre_lat=None, centre_lon=None, statut="active"):
        from app.models.champ import StatutParcelle
        p = MagicMock()
        p.centre_lat = centre_lat
        p.centre_lon = centre_lon
        p.statut = StatutParcelle.ARCHIVE if statut == "archive" else StatutParcelle.ACTIVE
        return p

    def _make_db(self, parcelle=None, carto=None):
        db = MagicMock(spec=Session)
        q_parcelle = MagicMock()
        q_parcelle.filter_by.return_value.first.return_value = parcelle
        q_carto = MagicMock()
        q_carto.filter_by.return_value.first.return_value = carto
        db.query.side_effect = lambda model: (
            q_carto if "Cartographie" in str(model) else q_parcelle
        )
        return db

    def test_gps_depuis_centre_parcelle(self):
        from app.routers.app_photo import _get_parcelle_gps
        p = self._make_parcelle(centre_lat=14.6928, centre_lon=-17.4467)
        db = self._make_db(parcelle=p)
        lat, lon = _get_parcelle_gps(db, 1, 1)
        assert lat == pytest.approx(14.6928)
        assert lon == pytest.approx(-17.4467)

    def test_gps_none_si_parcelle_archivee(self):
        from app.routers.app_photo import _get_parcelle_gps
        p = self._make_parcelle(centre_lat=14.0, centre_lon=-17.0, statut="archive")
        db = self._make_db(parcelle=p)
        lat, lon = _get_parcelle_gps(db, 1, 1)
        assert lat is None
        assert lon is None

    def test_gps_none_si_parcelle_introuvable(self):
        from app.routers.app_photo import _get_parcelle_gps
        db = self._make_db(parcelle=None)
        lat, lon = _get_parcelle_gps(db, 999, 1)
        assert lat is None
        assert lon is None

    def test_gps_fallback_depuis_cartographie(self):
        """Si centre_lat null, calcule depuis le polygone de la cartographie."""
        from app.routers.app_photo import _get_parcelle_gps
        p = self._make_parcelle(centre_lat=None, centre_lon=None)

        # Polygone carré autour de Dakar (~14.69°N, ~-17.44°E)
        carto = MagicMock()
        carto.coordonnees = [
            {"lat": 14.69, "lon": -17.44},
            {"lat": 14.70, "lon": -17.44},
            {"lat": 14.70, "lon": -17.43},
            {"lat": 14.69, "lon": -17.43},
        ]

        db = self._make_db(parcelle=p, carto=carto)
        lat, lon = _get_parcelle_gps(db, 1, 1)
        assert lat is not None
        assert lon is not None
        # Centroïde doit être proche du centre du carré
        assert 14.69 < lat < 14.70
        assert -17.44 < lon < -17.43

    def test_gps_none_si_polygon_invalide(self):
        """Polygone avec moins de 3 points → (None, None) sans crash."""
        from app.routers.app_photo import _get_parcelle_gps
        p = self._make_parcelle(centre_lat=None, centre_lon=None)

        carto = MagicMock()
        carto.coordonnees = [{"lat": 14.69, "lon": -17.44}]  # 1 seul point

        db = self._make_db(parcelle=p, carto=carto)
        lat, lon = _get_parcelle_gps(db, 1, 1)
        assert lat is None
        assert lon is None

    def test_gps_none_si_coordonnees_vides(self):
        from app.routers.app_photo import _get_parcelle_gps
        p = self._make_parcelle(centre_lat=None, centre_lon=None)

        carto = MagicMock()
        carto.coordonnees = []

        db = self._make_db(parcelle=p, carto=carto)
        lat, lon = _get_parcelle_gps(db, 1, 1)
        assert lat is None
        assert lon is None

    def test_gps_none_si_exception_db(self):
        """Exception DB → (None, None) sans propager."""
        from app.routers.app_photo import _get_parcelle_gps
        db = MagicMock(spec=Session)
        db.query.side_effect = Exception("DB timeout")
        lat, lon = _get_parcelle_gps(db, 1, 1)
        assert lat is None
        assert lon is None


# ── Intégration API : POST /api/app/photo ────────────────────────────────────

class TestEndpointPhoto:
    """Tests d'intégration via TestClient avec Kindwise mocké."""

    def _post_photo(self, token: str, parcelle_id: Optional[int] = None) -> dict:
        files = {"photo": ("test.jpg", _fake_image(), "image/jpeg")}
        data = {}
        if parcelle_id is not None:
            data["parcelle_id"] = str(parcelle_id)
        return client.post(
            "/api/app/photo",
            files=files,
            data=data,
            headers=_auth(token),
        )

    def test_photo_sans_parcelle_201(self, token_user_a):
        """Upload sans parcelle → 201, pas de GPS dans observation."""
        with patch("app.routers.app_photo.identifier_maladie") as mock_id:
            mock_id.return_value = {"disponible": False, "maladies": [], "credits_restants": 100}
            r = self._post_photo(token_user_a)
        assert r.status_code == 201
        mock_id.assert_called_once()
        # lat/lon doivent être None quand pas de parcelle
        _, kwargs = mock_id.call_args
        assert kwargs.get("latitude") is None
        assert kwargs.get("longitude") is None

    def test_photo_parcelle_archivee_404(self, token_user_a):
        """Parcelle archivée → 404."""
        # Créer puis supprimer une parcelle
        r = client.post("/api/champ/parcelles", json={
            "nom": "GPS Test", "type_culture": "Mil", "statut": "active"
        }, headers=_auth(token_user_a))
        assert r.status_code == 201
        pid = r.json()["id"]
        client.delete(f"/api/champ/parcelles/{pid}", headers=_auth(token_user_a))

        with patch("app.routers.app_photo.identifier_maladie"):
            r = self._post_photo(token_user_a, parcelle_id=pid)
        assert r.status_code == 404

    def test_aucune_photo_422(self, token_user_a):
        """Appel sans fichier → 422."""
        r = client.post(
            "/api/app/photo",
            data={},
            headers=_auth(token_user_a),
        )
        assert r.status_code in (422, 400)

    def test_trop_de_photos_422(self, token_user_a):
        """Plus de 5 photos → 422."""
        files = [
            ("photos", (f"img{i}.jpg", _fake_image(), "image/jpeg"))
            for i in range(6)
        ]
        r = client.post(
            "/api/app/photo",
            files=files,
            headers=_auth(token_user_a),
        )
        assert r.status_code == 422

    def test_diagnostic_stocke_en_base(self, token_user_a):
        """Le diagnostic Kindwise est stocké dans observation.diagnostic."""
        fake_diag = {
            "disponible": True,
            "maladies": [{"nom": "Rouille", "certitude": 80, "symptomes": None,
                          "cause": None, "traitement": None}],
            "credits_restants": 150,
        }
        with patch("app.routers.app_photo.identifier_maladie", return_value=fake_diag):
            r = self._post_photo(token_user_a)
        assert r.status_code == 201
        obs_id = r.json()["id"]

        # Vérifier via GET /observations/{id}
        r2 = client.get(f"/api/app/observations/{obs_id}", headers=_auth(token_user_a))
        assert r2.status_code == 200
        data = r2.json()
        assert data["diagnostic"]["disponible"] is True
        assert data["diagnostic"]["maladies"][0]["nom"] == "Rouille"

    def test_scan_maladie_legacy_list_bytes(self):
        """POST /api/scan-maladie doit passer List[bytes] à identifier_maladie."""
        captured = []

        def fake_id(images_bytes, *, langue="fr", latitude=None, longitude=None):
            captured.append(images_bytes)
            return {"disponible": False, "maladies": [], "credits_restants": -1}

        with patch("app.main.identifier_maladie", side_effect=fake_id), \
             patch("app.main.settings") as mock_s:
            mock_s.CROP_HEALTH_API_KEY = "test_key"
            r = client.post(
                "/api/scan-maladie",
                files={"photo": ("leaf.jpg", _fake_image(), "image/jpeg")},
            )
        assert r.status_code == 200
        # identifier_maladie doit recevoir une liste, pas des bytes bruts
        assert isinstance(captured[0], list)
        assert len(captured[0]) == 1
        assert isinstance(captured[0][0], bytes)
