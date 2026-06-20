#!/usr/bin/env python3
"""
Nettoyage de points GPS aberrants enregistrés lors d'un tour de terrain.

Usage :
    python scripts/nettoyer_gps.py points.geojson [--seuil 20] [--out propre.geojson]
    python scripts/nettoyer_gps.py points.csv     [--seuil 20] [--out propre.geojson]

Format CSV attendu : colonnes lat,lon (en-tête obligatoire).
Format GeoJSON : FeatureCollection de Points, ou liste de coordonnées [lon, lat].

Logique :
    Pour chaque point i, calcule la distance de Haversine avec le point i-1.
    Si distance > seuil (défaut 20 m), le point est supprimé.
    Le polygone est recalculé à partir des points restants.
    La superficie est calculée par la formule de Gauss (shoelace) sur sphère.
"""
import argparse
import json
import csv
import math
import sys
from pathlib import Path


# ── Haversine ──────────────────────────────────────────────────────────────────

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en mètres entre deux points WGS84."""
    R = 6_371_000  # rayon Terre en mètres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Superficie (shoelace sphérique) ───────────────────────────────────────────

def superficie_ha(points: list[dict]) -> float:
    """
    Superficie d'un polygone planaire (projection locale) en hectares.
    Précis pour de petites surfaces (< 10 km²).
    """
    if len(points) < 3:
        return 0.0

    # Centroïde local pour projection plate
    lat0 = sum(p["lat"] for p in points) / len(points)
    lon0 = sum(p["lon"] for p in points) / len(points)
    R = 6_371_000

    def to_xy(p):
        x = math.radians(p["lon"] - lon0) * R * math.cos(math.radians(lat0))
        y = math.radians(p["lat"] - lat0) * R
        return x, y

    coords = [to_xy(p) for p in points]
    n = len(coords)
    area = 0.0
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2 / 10_000  # m² → ha


# ── Lecture entrée ─────────────────────────────────────────────────────────────

def lire_geojson(path: Path) -> list[dict]:
    with open(path) as f:
        data = json.load(f)

    points = []
    if data.get("type") == "FeatureCollection":
        for feat in data["features"]:
            geom = feat.get("geometry", {})
            if geom.get("type") == "Point":
                lon, lat = geom["coordinates"][:2]
                points.append({"lat": lat, "lon": lon})
    elif data.get("type") == "Feature":
        geom = data.get("geometry", {})
        if geom.get("type") in ("Polygon", "LineString"):
            ring = geom["coordinates"][0] if geom["type"] == "Polygon" else geom["coordinates"]
            for lon, lat, *_ in ring:
                points.append({"lat": lat, "lon": lon})
    elif isinstance(data, list):
        for item in data:
            if "lat" in item and "lon" in item:
                points.append({"lat": float(item["lat"]), "lon": float(item["lon"])})
    return points


def lire_csv(path: Path) -> list[dict]:
    points = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                points.append({"lat": float(row["lat"]), "lon": float(row["lon"])})
            except (KeyError, ValueError):
                continue
    return points


# ── Nettoyage ─────────────────────────────────────────────────────────────────

def nettoyer(points: list[dict], seuil_m: float) -> tuple[list[dict], list[int]]:
    """
    Retourne (points_propres, indices_supprimes).
    Le premier point est toujours conservé.
    """
    if not points:
        return [], []

    propres = [points[0]]
    supprimes = []

    for i in range(1, len(points)):
        prev = propres[-1]
        curr = points[i]
        dist = haversine_m(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
        if dist <= seuil_m:
            propres.append(curr)
        else:
            supprimes.append(i)

    return propres, supprimes


# ── Export GeoJSON ─────────────────────────────────────────────────────────────

def exporter_geojson(points: list[dict], path: Path, superficie: float) -> None:
    if len(points) < 3:
        print("ERREUR : moins de 3 points restants — impossible de former un polygone.", file=sys.stderr)
        sys.exit(1)

    # Fermer le polygone
    anneau = [[p["lon"], p["lat"]] for p in points]
    if anneau[0] != anneau[-1]:
        anneau.append(anneau[0])

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "superficie_ha": round(superficie, 4),
                    "nb_points": len(points),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [anneau],
                },
            }
        ],
    }
    with open(path, "w") as f:
        json.dump(geojson, f, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Nettoyage GPS — supprime points aberrants et recalcule polygone")
    parser.add_argument("fichier", help="Fichier GeoJSON ou CSV d'entrée")
    parser.add_argument("--seuil", type=float, default=20.0, help="Distance max entre deux points consécutifs (mètres, défaut=20)")
    parser.add_argument("--out", default=None, help="Fichier GeoJSON de sortie (défaut: <fichier>_propre.geojson)")
    args = parser.parse_args()

    chemin = Path(args.fichier)
    if not chemin.exists():
        print(f"ERREUR : fichier introuvable : {chemin}", file=sys.stderr)
        sys.exit(1)

    # Lecture
    ext = chemin.suffix.lower()
    if ext == ".geojson" or ext == ".json":
        points = lire_geojson(chemin)
    elif ext == ".csv":
        points = lire_csv(chemin)
    else:
        print(f"ERREUR : format non supporté ({ext}). Utilisez .geojson ou .csv", file=sys.stderr)
        sys.exit(1)

    if len(points) < 3:
        print(f"ERREUR : seulement {len(points)} point(s) dans le fichier — minimum 3 requis.", file=sys.stderr)
        sys.exit(1)

    print(f"Points lus          : {len(points)}")

    # Superficie brute
    sup_brute = superficie_ha(points)
    print(f"Superficie brute    : {sup_brute:.4f} ha")

    # Nettoyage
    propres, supprimes = nettoyer(points, args.seuil)
    print(f"Points aberrants    : {len(supprimes)} supprimé(s) (distance > {args.seuil} m)")
    if supprimes:
        print(f"  Indices supprimés : {supprimes}")
    print(f"Points restants     : {len(propres)}")

    # Superficie propre
    sup_propre = superficie_ha(propres)
    print(f"Superficie corrigée : {sup_propre:.4f} ha")

    # Export
    sortie = Path(args.out) if args.out else chemin.with_name(chemin.stem + "_propre.geojson")
    exporter_geojson(propres, sortie, sup_propre)
    print(f"GeoJSON exporté     : {sortie}")


if __name__ == "__main__":
    main()
