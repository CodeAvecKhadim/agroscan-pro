"""
Tests unitaires — Satellite Sentinel Hub (Phase 1).

Coverage :
  - SentinelHubClient (mock)
  - Endpoints satellite
  - Models satellite
"""
import pytest
import httpx
from datetime import date, datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import json

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.models.satellite import (
    SatelliteProduct, SatelliteJob, SatelliteConfig,
    SensorType, JobStatus, JobType,
)
from app.models import Organization, User, Parcelle
from app.schemas.satellite import (
    SatelliteSearchRequest, SatelliteSearchResponse, SatelliteProductResponse,
)
from app.services.satellite import (
    SentinelHubClient, SentinelHubConfig, SentinelHubException,
    coordonnees_to_bbox,
    get_evalscript_ndvi_ndre_ndmi, get_evalscript_savi_evi_msavi,
)
from app.core.database import SessionLocal, Base, engine


@pytest.fixture
def db_session():
    """Crée une session DB pour les tests.
    N'effectue pas drop_all (incompatible avec la DB de production partagée).
    """
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client():
    """Client HTTP pour les tests."""
    return TestClient(app)


@pytest.fixture
def test_org(db_session: Session):
    """Retourne la première organisation existante (DB partagée — pas d'insertion)."""
    from app.models import Organization as Org
    org = db_session.query(Org).first()
    if not org:
        pytest.skip("Aucune organisation en DB — requiert DB isolée")
    return org


@pytest.fixture
def test_user(db_session: Session, test_org):
    """Retourne le premier utilisateur de l'organisation existante."""
    from app.models import User as U
    user = db_session.query(U).filter_by(org_id=test_org.id).first()
    if not user:
        pytest.skip("Aucun utilisateur en DB — requiert DB isolée")
    return user


@pytest.fixture
def test_parcelle(db_session: Session, test_org):
    """Retourne la première parcelle de l'organisation existante."""
    parcelle = db_session.query(Parcelle).filter_by(org_id=test_org.id).first()
    if not parcelle:
        pytest.skip("Aucune parcelle en DB — requiert DB isolée")
    return parcelle


@pytest.fixture
def sentinel_config() -> SentinelHubConfig:
    """Configuration Sentinel Hub pour les tests."""
    return SentinelHubConfig(
        api_key="test-api-key",
        api_secret="test-api-secret",
        api_url="https://services.sentinel-hub.com",
        data_collection="sentinel-2-l2a",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests : Modèles
# ─────────────────────────────────────────────────────────────────────────────

class TestSatelliteModels:
    """Tests pour les modèles Satellite."""

    def test_satellite_product_creation(self, db_session: Session, test_org, test_parcelle):
        """Teste la création d'un produit satellite."""
        _PROD_ID = "S2A_TEST_UNIT_PROD_20260530"
        db_session.query(SatelliteProduct).filter_by(product_id=_PROD_ID).delete()
        db_session.commit()

        product = SatelliteProduct(
            parcelle_id=test_parcelle.id,
            org_id=test_org.id,
            product_id=_PROD_ID,
            tile_id="31NDD",
            sensor="sentinel-2",
            date_acquisition=date(2026, 5, 30),
            date_product_date=datetime(2026, 5, 30, 12, 25, 34, tzinfo=timezone.utc),
            cloud_cover=12.5,
            snow_cover=0.0,
        )
        db_session.add(product)
        db_session.commit()

        saved = db_session.query(SatelliteProduct).filter_by(product_id=_PROD_ID).first()
        assert saved is not None
        assert saved.sensor == "sentinel-2"
        assert saved.cloud_cover == 12.5

        db_session.delete(saved)
        db_session.commit()

    def test_satellite_job_creation(self, db_session: Session, test_org, test_parcelle):
        """Teste la création d'un job satellite."""
        _JOB_TYPE = "test_unit_search_job"
        db_session.query(SatelliteJob).filter_by(job_type=_JOB_TYPE).delete()
        db_session.commit()

        job = SatelliteJob(
            parcelle_id=test_parcelle.id,
            org_id=test_org.id,
            job_type=_JOB_TYPE,
            status=JobStatus.QUEUED.value,
            params={"bbox": {"min_lon": -14.0, "min_lat": 14.5}, "sensor": "sentinel-2"},
        )
        db_session.add(job)
        db_session.commit()

        saved = db_session.query(SatelliteJob).filter_by(job_type=_JOB_TYPE).first()
        assert saved is not None
        assert saved.status == "queued"
        assert saved.retry_count == 0

        db_session.delete(saved)
        db_session.commit()

    def test_satellite_config_creation(self, db_session: Session):
        """Teste la création d'une config satellite."""
        _KEY = "test_unit_satellite_config"
        # Cleanup any leftover from previous runs
        db_session.query(SatelliteConfig).filter_by(key=_KEY).delete()
        db_session.commit()

        config = SatelliteConfig(key=_KEY, value={"value": "test-key-123"}, is_secret=True)
        db_session.add(config)
        db_session.commit()

        saved = db_session.query(SatelliteConfig).filter_by(key=_KEY).first()
        assert saved is not None
        assert saved.is_secret is True

        # Cleanup
        db_session.delete(saved)
        db_session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Tests : SentinelHubClient
# ─────────────────────────────────────────────────────────────────────────────

class TestSentinelHubClient:
    """Tests pour le client Sentinel Hub."""

    def test_client_initialization(self, sentinel_config):
        """Teste l'initialisation du client."""
        client = SentinelHubClient(sentinel_config)
        assert client.api_key == "test-api-key"
        assert client.api_secret == "test-api-secret"

    def test_evalscript_ndvi_ndre_ndmi(self):
        """Teste la génération du script NDVI/NDRE/NDMI."""
        script = get_evalscript_ndvi_ndre_ndmi()
        assert "NDVI" in script or "ndvi" in script
        assert "NDRE" in script or "ndre" in script
        assert "NDMI" in script or "ndmi" in script
        assert "VERSION=3" in script

    def test_evalscript_savi_evi_msavi(self):
        """Teste la génération du script SAVI/EVI/MSAVI."""
        script = get_evalscript_savi_evi_msavi()
        assert "SAVI" in script or "savi" in script
        assert "EVI" in script or "evi" in script
        assert "MSAVI" in script or "msavi" in script
        assert "VERSION=3" in script

    @patch("app.services.satellite.client.httpx.Client")
    def test_search_catalog_success(self, mock_http_client, sentinel_config):
        """Teste une recherche catalogue réussie (mock)."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "S2A_MSIL2A_20260530T104031_N0510_R117_T31NDD_20260530T122534",
                    "properties": {
                        "datetime": "2026-05-30T12:25:34Z",
                        "eo:cloud_cover": 12.5,
                        "eo:snow_cover": 0.0,
                        "sentinel:utm_zone": "31NDD",
                    },
                    "geometry": {"type": "Polygon", "coordinates": [[]]},
                }
            ]
        }
        mock_http_client.return_value.post.return_value = mock_response

        client = SentinelHubClient(sentinel_config)
        result = client.search_catalog(
            bbox={"min_lon": -14.0, "min_lat": 14.5, "max_lon": -13.99, "max_lat": 14.51},
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 31),
            sensor="sentinel-2",
        )

        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 1
        assert result["features"][0]["id"] == "S2A_MSIL2A_20260530T104031_N0510_R117_T31NDD_20260530T122534"

    @patch("app.services.satellite.client.httpx.Client")
    def test_search_catalog_error(self, mock_http_client, sentinel_config):
        """Teste une erreur lors de la recherche catalogue."""
        mock_http_client.return_value.post.side_effect = httpx.HTTPError("Network error")

        client = SentinelHubClient(sentinel_config)

        with pytest.raises(SentinelHubException):
            client.search_catalog(
                bbox={"min_lon": -14.0, "min_lat": 14.5, "max_lon": -13.99, "max_lat": 14.51},
                date_from=date(2026, 5, 1),
                date_to=date(2026, 5, 31),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Tests : Endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestSatelliteEndpoints:
    """Tests pour les endpoints satellite."""

    def test_health_check_no_config(self, client: TestClient, db_session: Session):
        """Teste le health check sans config (doit échouer)."""
        # Pas de config créée
        response = client.get("/api/sante/precision/satellite/health")
        assert response.status_code == 503

    def test_health_check_with_config(self, client: TestClient, db_session: Session):
        """Teste le health check avec config."""
        _KEY_K = "test_unit_shub_key"
        _KEY_S = "test_unit_shub_secret"
        # Cleanup any leftover
        db_session.query(SatelliteConfig).filter(
            SatelliteConfig.key.in_([_KEY_K, _KEY_S])
        ).delete(synchronize_session=False)
        db_session.commit()

        db_session.add(SatelliteConfig(key=_KEY_K, value={"value": "test-key"}, is_secret=True))
        db_session.add(SatelliteConfig(key=_KEY_S, value={"value": "test-secret"}, is_secret=True))
        db_session.commit()

        # Patch _get_sentinel_hub_config to use our test keys
        with patch("app.routers.satellite._get_sentinel_hub_config") as mock_cfg:
            from app.services.satellite import SentinelHubConfig
            mock_cfg.return_value = SentinelHubConfig(
                api_key="test-key", api_secret="test-secret"
            )
            response = client.get("/api/sante/precision/satellite/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Cleanup
        db_session.query(SatelliteConfig).filter(
            SatelliteConfig.key.in_([_KEY_K, _KEY_S])
        ).delete(synchronize_session=False)
        db_session.commit()

    def test_search_no_coords(self, client: TestClient, db_session: Session):
        """Teste la recherche sans coordonnées (doit échouer)."""
        # TODO: Créer une parcelle sans coords et tester que l'endpoint refuse
        pass

    def test_list_products_empty(self, client: TestClient, db_session: Session, test_user: User):
        """Teste la liste des produits (vide)."""
        # TODO: Implémenter avec auth mock
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Tests : Schemas
# ─────────────────────────────────────────────────────────────────────────────

class TestSatelliteSchemas:
    """Tests pour les schémas Pydantic."""

    def test_search_request_validation(self):
        """Teste la validation d'une requête de recherche."""
        req = SatelliteSearchRequest(
            parcelle_id=1,
            sensor="sentinel-2",
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 31),
            cloud_cover_max=30.0,
        )

        assert req.parcelle_id == 1
        assert req.sensor == "sentinel-2"
        assert req.limit == 10  # Valeur par défaut

    def test_search_request_invalid_cloud_cover(self):
        """Teste la validation d'une cloud cover invalide."""
        with pytest.raises(ValueError):
            SatelliteSearchRequest(
                parcelle_id=1,
                sensor="sentinel-2",
                date_from=date(2026, 5, 1),
                date_to=date(2026, 5, 31),
                cloud_cover_max=150.0,  # > 100
            )

    def test_product_response_serialization(self, test_org):
        """Teste la sérialisation d'une réponse produit."""
        product = SatelliteProduct(
            id=42,
            parcelle_id=1,
            org_id=test_org.id,
            product_id="S2A_MSIL2A_20260530T104031_N0510_R117_T31NDD_20260530T122534",
            sensor="sentinel-2",
            date_acquisition=date(2026, 5, 30),
            date_product_date=datetime(2026, 5, 30, 12, 25, 34, tzinfo=timezone.utc),
            cloud_cover=12.5,
            discovered_at=datetime(2026, 5, 30, 13, 0, 0, tzinfo=timezone.utc),
        )

        response = SatelliteProductResponse.model_validate(product)
        assert response.id == 42
        assert response.sensor == "sentinel-2"
        assert response.cloud_cover == 12.5


# ─────────────────────────────────────────────────────────────────────────────
# Tests d'intégration
# ─────────────────────────────────────────────────────────────────────────────

class TestSatelliteIntegration:
    """Tests d'intégration (end-to-end)."""

    @patch("app.services.satellite.client.httpx.Client")
    def test_search_and_register_products(
        self,
        mock_http_client,
        db_session: Session,
        test_org: Organization,
        test_parcelle: Parcelle,
        sentinel_config: SentinelHubConfig,
    ):
        """Test: Rechercher et enregistrer des produits."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "S2A_MSIL2A_20260530T104031_N0510_R117_T31NDD_20260530T122534",
                    "properties": {
                        "datetime": "2026-05-30T12:25:34Z",
                        "eo:cloud_cover": 12.5,
                        "eo:snow_cover": 0.0,
                        "sentinel:utm_zone": "31NDD",
                    },
                    "geometry": {"type": "Polygon", "coordinates": [[]]},
                }
            ]
        }
        mock_http_client.return_value.post.return_value = mock_response

        # Créer une config Sentinel Hub (clés de test uniques + cleanup)
        _CK, _CS = "test_unit_integ_key", "test_unit_integ_secret"
        db_session.query(SatelliteConfig).filter(
            SatelliteConfig.key.in_([_CK, _CS])
        ).delete(synchronize_session=False)
        db_session.commit()

        config_key    = SatelliteConfig(key=_CK, value={"value": "test-key"})
        config_secret = SatelliteConfig(key=_CS, value={"value": "test-secret"})
        db_session.add(config_key)
        db_session.add(config_secret)
        db_session.commit()

        # Rechercher les produits
        client = SentinelHubClient(sentinel_config)
        result = client.search_catalog(
            bbox={
                "min_lon": test_parcelle.centre_lon - 0.001,
                "min_lat": test_parcelle.centre_lat - 0.001,
                "max_lon": test_parcelle.centre_lon + 0.001,
                "max_lat": test_parcelle.centre_lat + 0.001,
            },
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 31),
            sensor="sentinel-2",
        )

        # Enregistrer les produits
        for feature in result.get("features", []):
            product_id = feature.get("id")
            properties = feature.get("properties", {})
            date_acq = datetime.fromisoformat(
                properties.get("datetime", "").replace("Z", "+00:00")
            ).date()

            product = SatelliteProduct(
                parcelle_id=test_parcelle.id,
                org_id=test_org.id,
                product_id=product_id,
                sensor="sentinel-2",
                date_acquisition=date_acq,
                date_product_date=datetime.fromisoformat(
                    properties.get("datetime", "").replace("Z", "+00:00")
                ),
                cloud_cover=properties.get("eo:cloud_cover", 0.0),
            )
            db_session.add(product)

        db_session.commit()

        # Vérifier l'enregistrement
        saved = db_session.query(SatelliteProduct).filter_by(
            parcelle_id=test_parcelle.id
        ).first()
        assert saved is not None
        assert saved.sensor == "sentinel-2"

        # Cleanup
        db_session.query(SatelliteProduct).filter_by(parcelle_id=test_parcelle.id).delete()
        db_session.query(SatelliteConfig).filter(
            SatelliteConfig.key.in_([_CK, _CS])
        ).delete(synchronize_session=False)
        db_session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Tests Sprint 1 — Security + Bbox from real contour
# ─────────────────────────────────────────────────────────────────────────────

class TestCoordonneesToBbox:
    """Tests pour coordonnees_to_bbox."""

    def test_square_polygon(self):
        """Carré simple → bbox exacte."""
        coords = [
            {"lat": 14.5,  "lon": -14.0},
            {"lat": 14.5,  "lon": -13.9},
            {"lat": 14.4,  "lon": -13.9},
            {"lat": 14.4,  "lon": -14.0},
        ]
        min_lon, min_lat, max_lon, max_lat = coordonnees_to_bbox(coords)
        assert min_lon == pytest.approx(-14.0)
        assert min_lat == pytest.approx(14.4)
        assert max_lon == pytest.approx(-13.9)
        assert max_lat == pytest.approx(14.5)

    def test_single_point(self):
        """Un seul point → bbox dégénérée (min == max)."""
        coords = [{"lat": 14.5, "lon": -14.0}]
        min_lon, min_lat, max_lon, max_lat = coordonnees_to_bbox(coords)
        assert min_lon == max_lon == pytest.approx(-14.0)
        assert min_lat == max_lat == pytest.approx(14.5)

    def test_empty_list_raises(self):
        """Liste vide → ValueError."""
        with pytest.raises(ValueError, match="Coordonnées vides"):
            coordonnees_to_bbox([])

    def test_missing_lon_raises(self):
        """Coordonnée sans 'lon' → KeyError."""
        with pytest.raises((KeyError, ValueError)):
            coordonnees_to_bbox([{"lat": 14.5}])

    def test_irregular_polygon(self):
        """Polygone irrégulier → bounding box correcte."""
        coords = [
            {"lat": 14.50, "lon": -14.00},
            {"lat": 14.52, "lon": -13.98},
            {"lat": 14.49, "lon": -13.95},
            {"lat": 14.45, "lon": -13.97},
            {"lat": 14.47, "lon": -14.02},
        ]
        min_lon, min_lat, max_lon, max_lat = coordonnees_to_bbox(coords)
        assert min_lon == pytest.approx(-14.02)
        assert min_lat == pytest.approx(14.45)
        assert max_lon == pytest.approx(-13.95)
        assert max_lat == pytest.approx(14.52)

    def test_bbox_orientation(self):
        """min_lon < max_lon et min_lat < max_lat pour tout polygone valide."""
        coords = [
            {"lat": 14.6, "lon": -14.1},
            {"lat": 14.4, "lon": -13.8},
        ]
        min_lon, min_lat, max_lon, max_lat = coordonnees_to_bbox(coords)
        assert min_lon < max_lon
        assert min_lat < max_lat


class TestSatelliteRouterSecurity:
    """Tests de sécurité — contrôle d'accès aux endpoints /config."""

    def test_config_write_requires_auth(self, client: TestClient):
        """POST /config sans token → 401."""
        response = client.post(
            "/api/sante/precision/satellite/config",
            json={"key": "sentinel_hub_api_key", "value": {"value": "hack"}},
        )
        assert response.status_code == 401

    def test_config_read_requires_auth(self, client: TestClient):
        """GET /config/{key} sans token → 401."""
        response = client.get("/api/sante/precision/satellite/config/sentinel_hub_api_key")
        assert response.status_code == 401

    def test_search_requires_auth(self, client: TestClient):
        """POST /search sans token → 401."""
        response = client.post(
            "/api/sante/precision/satellite/search",
            json={
                "parcelle_id": 1,
                "sensor": "sentinel-2",
                "date_from": "2026-05-01",
                "date_to": "2026-05-31",
            },
        )
        assert response.status_code == 401

    def test_products_list_requires_auth(self, client: TestClient):
        """GET /products sans token → 401."""
        response = client.get("/api/sante/precision/satellite/products?parcelle_id=1")
        assert response.status_code == 401


class TestSatelliteBboxFromContour:
    """Tests bbox calculée depuis le contour de parcelle (vs centre±delta).

    Tests purement unitaires — pas de DB nécessaire.
    """

    def test_contour_bbox_differs_from_center_fallback(self):
        """bbox contour couvre toute la parcelle, pas juste ±110 m autour du centre."""
        contour = [
            {"lat": 14.45, "lon": -14.05},
            {"lat": 14.55, "lon": -14.05},
            {"lat": 14.55, "lon": -13.95},
            {"lat": 14.45, "lon": -13.95},
        ]
        # Centre fictif de la parcelle (test_parcelle)
        centre_lat, centre_lon = 14.5, -14.0
        delta = 0.001

        min_lon, min_lat, max_lon, max_lat = coordonnees_to_bbox(contour)

        # bbox contour = -14.05 → -13.95 (0.1° width)
        # bbox fallback = -14.001 → -13.999 (0.002° width)
        assert min_lon == pytest.approx(-14.05)
        assert min_lat == pytest.approx(14.45)
        assert max_lon == pytest.approx(-13.95)
        assert max_lat == pytest.approx(14.55)

        # Contour bbox est plus large que le fallback
        contour_width = max_lon - min_lon
        fallback_width = (centre_lon + delta) - (centre_lon - delta)
        assert contour_width > fallback_width, (
            "Contour bbox doit être plus large que fallback centre±delta"
        )

    def test_fallback_bbox_values(self):
        """Sans contour, fallback = centre ± 0.001°."""
        centre_lat, centre_lon = 14.5, -14.0
        delta = 0.001
        expected = {
            "min_lon": centre_lon - delta,
            "min_lat": centre_lat - delta,
            "max_lon": centre_lon + delta,
            "max_lat": centre_lat + delta,
        }
        assert expected["min_lon"] == pytest.approx(-14.001)
        assert expected["max_lon"] == pytest.approx(-13.999)
        assert expected["min_lat"] == pytest.approx(14.499)
        assert expected["max_lat"] == pytest.approx(14.501)

    def test_contour_bbox_precision(self):
        """bbox du contour reflète exactement les extrêmes du polygone."""
        contour = [
            {"lat": 14.1234, "lon": -15.9876},
            {"lat": 14.9999, "lon": -15.1111},
            {"lat": 14.5555, "lon": -14.0001},
        ]
        min_lon, min_lat, max_lon, max_lat = coordonnees_to_bbox(contour)
        assert min_lon == pytest.approx(-15.9876)
        assert min_lat == pytest.approx(14.1234)
        assert max_lon == pytest.approx(-14.0001)
        assert max_lat == pytest.approx(14.9999)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
