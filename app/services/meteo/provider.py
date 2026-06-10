"""
Abstraction API météo — Open-Meteo (gratuit, sans clé).
Remplacer cette classe pour migrer vers un autre provider (WeatherAPI, Meteomatics...).
Utilise requests (httpx non installé).
"""
import logging
from datetime import date, timedelta
from typing import Optional

import requests

log = logging.getLogger(__name__)

# Centroïdes GPS par zone agro-écologique (Sénégal)
GPS_ZONES: dict[str, tuple[float, float]] = {
    "vallee_fleuve":       (16.02, -16.50),
    "niayes":              (14.70, -17.43),
    "bassin_arachidier":   (14.13, -15.55),
    "senegal_oriental":    (13.67, -13.68),
    "casamance":           (12.56, -16.27),
    "zone_sylvopastorale": (15.56, -14.22),
}

# WMO weather codes → description française
_WMO_FR: dict[int, str] = {
    0: "Ciel dégagé", 1: "Principalement dégagé", 2: "Partiellement nuageux",
    3: "Couvert", 45: "Brouillard", 48: "Givre",
    51: "Bruine légère", 53: "Bruine modérée", 55: "Bruine dense",
    61: "Pluie légère", 63: "Pluie modérée", 65: "Pluie forte",
    71: "Neige légère", 73: "Neige modérée", 75: "Neige forte",
    80: "Averses légères", 81: "Averses modérées", 82: "Averses violentes",
    85: "Averses de neige", 86: "Averses de neige fortes",
    95: "Orage", 96: "Orage avec grêle", 99: "Orage avec forte grêle",
}

VARIABLES_DAILY = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "relative_humidity_2m_max",
    "et0_fao_evapotranspiration",
    "weather_code",
]

VARIABLES_CURRENT = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "weather_code",
    "et0_fao_evapotranspiration",
]

_BASE_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT  = 15  # secondes


class OpenMeteoProvider:
    """Client Open-Meteo — gratuit, sans clé API, jusqu'à 16 jours."""

    def conditions_actuelles(self, lat: float, lon: float) -> dict:
        """Fetch conditions météo actuelles."""
        params = {
            "latitude":  lat,
            "longitude": lon,
            "current":   ",".join(VARIABLES_CURRENT),
            "timezone":  "Africa/Dakar",
            "wind_speed_unit": "kmh",
        }
        data = self._get(params)
        current = data.get("current", {})
        code = current.get("weather_code", 0)
        return {
            "temp_actuelle": current.get("temperature_2m"),
            "humidite_rel":  current.get("relative_humidity_2m"),
            "pluie_mm":      current.get("precipitation"),
            "vent_kmh":      current.get("wind_speed_10m"),
            "direction_vent": current.get("wind_direction_10m"),
            "etp_mm":        current.get("et0_fao_evapotranspiration"),
            "code_meteo":    code,
            "description_fr": self.wmo_description(code),
        }

    def previsions(self, lat: float, lon: float, jours: int = 16) -> list[dict]:
        """Fetch prévisions quotidiennes N jours (max 16)."""
        jours = min(max(jours, 1), 16)
        params = {
            "latitude":   lat,
            "longitude":  lon,
            "daily":      ",".join(VARIABLES_DAILY),
            "timezone":   "Africa/Dakar",
            "wind_speed_unit": "kmh",
            "forecast_days": jours,
        }
        data = self._get(params)
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        result = []
        for i, d in enumerate(dates):
            code = (daily.get("weather_code") or [None]*len(dates))[i]
            result.append({
                "date":            d,
                "temp_min":        _safe(daily, "temperature_2m_min", i),
                "temp_max":        _safe(daily, "temperature_2m_max", i),
                "pluie_mm":        _safe(daily, "precipitation_sum", i),
                "pluie_proba_pct": _safe(daily, "precipitation_probability_max", i),
                "vent_kmh":        _safe(daily, "wind_speed_10m_max", i),
                "humidite_pct":    _safe(daily, "relative_humidity_2m_max", i),
                "etp_mm":          _safe(daily, "et0_fao_evapotranspiration", i),
                "code_meteo":      code,
                "description_fr":  self.wmo_description(code) if code is not None else None,
            })
        return result

    @staticmethod
    def wmo_description(code: Optional[int]) -> str:
        if code is None:
            return "Inconnu"
        return _WMO_FR.get(int(code), f"Code météo {code}")

    def _get(self, params: dict) -> dict:
        try:
            r = requests.get(_BASE_URL, params=params, timeout=_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            log.error("Open-Meteo timeout")
            raise RuntimeError("API météo indisponible (timeout)")
        except requests.exceptions.RequestException as e:
            log.error("Open-Meteo erreur: %s", e)
            raise RuntimeError(f"API météo erreur: {e}")


def _safe(daily: dict, key: str, i: int):
    lst = daily.get(key)
    if lst and i < len(lst):
        return lst[i]
    return None


def get_provider() -> OpenMeteoProvider:
    return OpenMeteoProvider()


def gps_pour_zone(zone_agro: Optional[str]) -> tuple[float, float]:
    """GPS fallback par zone si pas de coordonnées parcelle."""
    if zone_agro and zone_agro in GPS_ZONES:
        return GPS_ZONES[zone_agro]
    return GPS_ZONES["bassin_arachidier"]
