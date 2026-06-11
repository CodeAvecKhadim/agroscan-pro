"""
SatelliteService — Sentinel Hub Process API (Sentinel-2).
Calcule NDVI, NDRE, SAVI, EVI, MSAVI, NDWI côté serveur Copernicus.

Credentials requis dans .env :
  SENTINELHUB_CLIENT_ID=
  SENTINELHUB_CLIENT_SECRET=

Mode dégradé : si credentials absents, retourne des valeurs simulées
basées sur la saison (permettant tests sans accès Sentinel Hub).
"""
import logging
import math
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings

log = logging.getLogger(__name__)

# ── Evalscript Sentinel-2 ────────────────────────────────────────────────────
# Calcule 6 indices en un seul appel API (économise des Processing Units)
# Bandes utilisées: B02(Blue), B03(Green), B04(Red), B08(NIR), B8A(RedEdge), B11(SWIR)

EVALSCRIPT_S2_INDICES = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B03", "B04", "B08", "B8A", "B11", "CLM"] }],
    output: { bands: 7, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(s) {
  let ndvi  = (s.B08 - s.B04) / (s.B08 + s.B04 + 1e-10);
  let ndre  = (s.B08 - s.B8A) / (s.B08 + s.B8A + 1e-10);
  let L     = 0.5;
  let savi  = ((s.B08 - s.B04) / (s.B08 + s.B04 + L + 1e-10)) * (1 + L);
  let evi   = 2.5 * (s.B08 - s.B04) / (s.B08 + 6*s.B04 - 7.5*s.B02 + 1 + 1e-10);
  let msavi = (2*s.B08 + 1 - Math.sqrt(Math.pow(2*s.B08 + 1, 2) - 8*(s.B08 - s.B04))) / 2;
  let ndwi  = (s.B03 - s.B11) / (s.B03 + s.B11 + 1e-10);
  let cloud = s.CLM;
  return [ndvi, ndre, savi, evi, msavi, ndwi, cloud];
}
"""


def coordonnees_to_bbox(coordonnees: list[dict]) -> tuple[float, float, float, float]:
    """Convertit polygon [{lat, lon}, ...] en bbox (min_lon, min_lat, max_lon, max_lat).

    Sentinel Hub attend (west, south, east, north) = (min_lon, min_lat, max_lon, max_lat).
    """
    if not coordonnees:
        raise ValueError("Coordonnées vides — impossible de calculer le bbox")
    lats = [c["lat"] for c in coordonnees]
    lons = [c["lon"] for c in coordonnees]
    return (min(lons), min(lats), max(lons), max(lats))


def resolution_adaptative(superficie_ha: float) -> int:
    """Résolution Sentinel-2 adaptée à la superficie de la parcelle."""
    if superficie_ha is None or superficie_ha < 2:
        return 10   # 10m — résolution maximale S2
    if superficie_ha < 10:
        return 20   # 20m
    return 60       # 60m — grandes parcelles


def _fetch_via_sentinelhub(
    bbox: tuple,
    date_debut: date,
    date_fin: date,
    resolution: int,
) -> Optional[dict]:
    """Appel réel Sentinel Hub Process API.

    Retourne dict avec indices moyennés sur la parcelle ou None si échec.
    """
    try:
        from sentinelhub import (
            SHConfig, BBox, CRS, DataCollection, SentinelHubStatistical,
            Geometry,
        )
        from sentinelhub import MosaickingOrder
    except ImportError:
        log.error("sentinelhub non installé")
        return None

    client_id     = getattr(settings, "SENTINELHUB_CLIENT_ID",     "")
    client_secret = getattr(settings, "SENTINELHUB_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return None

    try:
        config = SHConfig()
        config.sh_client_id     = client_id
        config.sh_client_secret = client_secret

        sh_bbox = BBox(bbox=bbox, crs=CRS.WGS84)

        request = SentinelHubStatistical(
            aggregation=SentinelHubStatistical.aggregation(
                evalscript=EVALSCRIPT_S2_INDICES,
                time_interval=(date_debut.isoformat(), date_fin.isoformat()),
                aggregation_interval="P1D",
                resolution=(resolution, resolution),
            ),
            input_data=[
                SentinelHubStatistical.input_data(
                    DataCollection.SENTINEL2_L2A,
                    mosaicking_order=MosaickingOrder.LEAST_CC,
                )
            ],
            bbox=sh_bbox,
            config=config,
        )

        data = request.get_data()[0]
        if not data or "data" not in data or not data["data"]:
            return None

        # Agrège les statistiques sur la période (prend la première date valide)
        for entry in data["data"]:
            stats = entry.get("outputs", {}).get("default", {}).get("bands", {})
            if not stats:
                continue

            def mean(band_key):
                return stats.get(band_key, {}).get("stats", {}).get("mean")

            cloud_mean = mean("B7")
            if cloud_mean is not None and cloud_mean > 0.9:
                continue  # image trop nuageuse

            return {
                "ndvi":               mean("B1"),
                "ndre":               mean("B2"),
                "savi":               mean("B3"),
                "evi":                mean("B4"),
                "msavi":              mean("B5"),
                "ndwi":               mean("B6"),
                "couverture_nuages":  (cloud_mean or 0) * 100,
                "date_image":         entry.get("interval", {}).get("from", "")[:10],
                "sentinelhub_request_id": None,
            }

        return None

    except Exception as e:
        log.warning("Sentinel Hub API error: %s", e)
        return None


def _indices_simules(mois: int, culture_nom: str) -> dict:
    """Valeurs simulées quand Sentinel Hub n'est pas configuré.

    Basées sur la saison (hivernage sénégalais juin-octobre).
    Utilisées pour dev/test sans crédentials Copernicus.
    """
    # Hivernage = végétation active (NDVI élevé)
    if 6 <= mois <= 10:
        ndvi  = 0.55
        ndwi  = 0.10
        ndre  = 0.35
    # Saison sèche = végétation faible
    elif mois in (11, 12, 1, 2):
        ndvi  = 0.25
        ndwi  = -0.15
        ndre  = 0.15
    # Transition
    else:
        ndvi  = 0.40
        ndwi  = -0.05
        ndre  = 0.25

    L     = 0.5
    savi  = ((ndvi) / (1 + L + 1e-10)) * (1 + L)
    evi   = ndvi * 0.9
    msavi = ndvi * 0.85

    return {
        "ndvi":               round(ndvi, 3),
        "ndre":               round(ndre, 3),
        "savi":               round(savi, 3),
        "evi":                round(evi, 3),
        "msavi":              round(msavi, 3),
        "ndwi":               round(ndwi, 3),
        "couverture_nuages":  5.0,
        "date_image":         date.today().isoformat(),
        "sentinelhub_request_id": None,
        "source": "simule",
    }


def fetch_indices(
    coordonnees: list[dict],
    superficie_ha: float,
    mois: int,
    culture_nom: str,
) -> dict:
    """Récupère les indices satellitaires pour une parcelle.

    Tente Sentinel Hub en premier, replie sur simulation si pas de credentials.

    Args:
        coordonnees:  polygon [{lat, lon}] depuis Cartographie.coordonnees
        superficie_ha: superficie pour résolution adaptative
        mois:         mois en cours (1-12), utilisé pour la fenêtre temporelle
        culture_nom:  nom culture (pour simulation saisonnière)

    Returns:
        dict avec: ndvi, ndre, savi, evi, msavi, ndwi, couverture_nuages,
                   date_image, sentinelhub_request_id, source
    """
    client_id     = getattr(settings, "SENTINELHUB_CLIENT_ID",     "")
    client_secret = getattr(settings, "SENTINELHUB_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        log.info("Sentinel Hub non configuré → indices simulés (culture=%s, mois=%d)", culture_nom, mois)
        result = _indices_simules(mois, culture_nom)
        return result

    try:
        bbox       = coordonnees_to_bbox(coordonnees)
        resolution = resolution_adaptative(superficie_ha)

        # Fenêtre temporelle : 30 jours glissants
        today      = date.today()
        date_debut = today - timedelta(days=30)

        result = _fetch_via_sentinelhub(bbox, date_debut, today, resolution)

        if result:
            result["source"] = "sentinel_hub"
            log.info("Sentinel Hub OK — NDVI=%.3f, nuages=%.1f%%",
                     result.get("ndvi", 0), result.get("couverture_nuages", 0))
            return result

        log.warning("Sentinel Hub retourne pas de données valides → indices simulés")

    except Exception as e:
        log.warning("Erreur fetch satellite: %s → fallback simulation", e)

    return {**_indices_simules(mois, culture_nom), "source": "simule_fallback"}
