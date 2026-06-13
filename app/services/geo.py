"""
Calculs géométriques purs — zéro dépendance externe.
Coordonnées WGS84 (latitude/longitude en degrés décimaux).
"""
import math
from typing import List, Dict, Tuple

# Rayon moyen de la Terre en mètres (WGS84)
_R = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en mètres entre deux points GPS (formule Haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * _R * math.asin(math.sqrt(a))


def _filter_gps_outliers(coords: List[Dict]) -> List[Dict]:
    """
    Supprime les points GPS aberrants qui créent des polygones auto-intersectants.
    Un point est aberrant si SES DEUX segments adjacents dépassent le seuil
    calculé via Q3+3×IQR (ou 5×Q3 quand IQR ≈ 0, cas grille uniforme).
    Itère jusqu'à convergence.
    """
    if len(coords) < 4:
        return coords

    pts = list(coords)
    for _ in range(10):
        n = len(pts)
        if n < 4:
            break

        dists = [
            haversine_m(pts[i]["lat"], pts[i]["lon"],
                        pts[(i + 1) % n]["lat"], pts[(i + 1) % n]["lon"])
            for i in range(n)
        ]

        sorted_d = sorted(dists)
        q1 = sorted_d[n // 4]
        q3 = sorted_d[3 * n // 4]
        iqr = q3 - q1

        # Quand IQR ≈ 0 (segments uniformes), on bascule sur 5×Q3
        # pour éviter un seuil nul ou trivial.
        if iqr < 1.0:
            if q3 < 0.1:
                break  # tous les points sont au même endroit
            threshold = max(q3 * 5.0, q3 + 20.0)
        else:
            threshold = q3 + 3.0 * iqr

        new_pts = [
            pts[i] for i in range(n)
            if not (dists[(i - 1) % n] > threshold and dists[i] > threshold)
        ]

        if len(new_pts) == n:
            break
        pts = new_pts

    return pts if len(pts) >= 3 else coords


def _to_local_xy(coords: List[Dict], ref_lat: float, ref_lon: float) -> List[Tuple[float, float]]:
    """Convertit des points GPS en mètres cartésiens (origine = ref_lat, ref_lon)."""
    xy = []
    for c in coords:
        lat, lon = c["lat"], c["lon"]
        x = haversine_m(ref_lat, ref_lon, ref_lat, lon) * (1 if lon >= ref_lon else -1)
        y = haversine_m(ref_lat, ref_lon, lat, ref_lon) * (1 if lat >= ref_lat else -1)
        xy.append((x, y))
    return xy


def surface_m2(coords: List[Dict]) -> float:
    """
    Superficie en m² d'un polygone GPS (liste de {lat, lon}).
    Formule de Shoelace (Gauss) sur projection locale.
    Précision ±1% pour parcelles <50 km².
    Les points GPS aberrants sont filtrés avant calcul.
    """
    if len(coords) < 3:
        return 0.0
    coords = _filter_gps_outliers(coords)
    if len(coords) < 3:
        return 0.0
    ref_lat = sum(c["lat"] for c in coords) / len(coords)
    ref_lon = sum(c["lon"] for c in coords) / len(coords)
    pts = _to_local_xy(coords, ref_lat, ref_lon)
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    return abs(area) / 2.0


def superficie_ha(coords: List[Dict]) -> float:
    """Superficie en hectares."""
    return surface_m2(coords) / 10_000.0


def perimetre_m(coords: List[Dict]) -> float:
    """Périmètre en mètres : somme des distances Haversine entre points consécutifs.
    Les points GPS aberrants sont filtrés avant calcul."""
    if len(coords) < 2:
        return 0.0
    coords = _filter_gps_outliers(coords)
    total = 0.0
    n = len(coords)
    for i in range(n):
        j = (i + 1) % n
        total += haversine_m(coords[i]["lat"], coords[i]["lon"],
                             coords[j]["lat"], coords[j]["lon"])
    return total


def centroide(coords: List[Dict]) -> Tuple[float, float]:
    """
    Centre géométrique (centroïde) du polygone.
    Retourne (lat, lon) du barycentre pondéré par les aires des triangles.
    Les points GPS aberrants sont filtrés avant calcul.
    """
    coords = _filter_gps_outliers(coords)
    if len(coords) < 3:
        lat = sum(c["lat"] for c in coords) / len(coords)
        lon = sum(c["lon"] for c in coords) / len(coords)
        return lat, lon

    ref_lat = sum(c["lat"] for c in coords) / len(coords)
    ref_lon = sum(c["lon"] for c in coords) / len(coords)
    pts = _to_local_xy(coords, ref_lat, ref_lon)
    n = len(pts)

    cx = cy = 0.0
    signed_area = 0.0
    for i in range(n):
        j = (i + 1) % n
        cross = pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
        signed_area += cross
        cx += (pts[i][0] + pts[j][0]) * cross
        cy += (pts[i][1] + pts[j][1]) * cross

    signed_area /= 2.0
    if abs(signed_area) < 1e-9:
        return ref_lat, ref_lon

    cx /= 6.0 * signed_area
    cy /= 6.0 * signed_area

    # Reconvertir cx/cy (mètres) en lat/lon
    deg_per_m_lat = 1.0 / 111_320.0
    deg_per_m_lon = 1.0 / (111_320.0 * math.cos(math.radians(ref_lat)))
    return ref_lat + cy * deg_per_m_lat, ref_lon + cx * deg_per_m_lon


def calcul_complet(coords: List[Dict]) -> Dict:
    """Retourne tous les métriques géométriques en un appel."""
    if not coords or len(coords) < 3:
        return {"superficie_m2": None, "superficie_ha": None,
                "perimetre_m": None, "centre_lat": None, "centre_lon": None}
    s_m2 = surface_m2(coords)
    p_m = perimetre_m(coords)
    clat, clon = centroide(coords)
    return {
        "superficie_m2": round(s_m2, 1),
        "superficie_ha": round(s_m2 / 10_000, 4),
        "perimetre_m": round(p_m, 1),
        "centre_lat": round(clat, 6),
        "centre_lon": round(clon, 6),
    }
