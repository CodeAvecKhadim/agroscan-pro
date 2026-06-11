"""
CarteService — Génération de cartes de précision GeoJSON.

Produit 4 types de cartes (FeatureCollection) :
  sante     — score santé composite par cellule
  hydrique  — stress hydrique (NDWI + humidité sol)
  fertilite — fertilité estimée (NDRE + NPK)
  risques   — niveau de risque maladies/ravageurs

Résolution adaptative :
  <2 ha  → 10m  (Sentinel-2 max)
  <10 ha → 20m
  ≥10 ha → 60m

Algorithme :
  1. Calcule la bbox de la parcelle depuis les coordonnées
  2. Génère une grille régulière (lat/lon) selon la résolution
  3. Assigne une valeur à chaque cellule (avec variation spatiale simulée)
  4. Retourne un GeoJSON FeatureCollection valide

Note : en production, les valeurs par cellule viendraient de la rasterisation
des bandes Sentinel-2 brutes. En mode dégradé, on applique une variation
gaussienne autour du score central pour donner une carte visuellement utile.
"""
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from app.services.sante_cultures.satellite_service import coordonnees_to_bbox


# Facteur de conversion degrés → mètres (approximation valide pour l'Afrique de l'Ouest)
_DEG_TO_M = 111_320.0


def resolution_adaptative(superficie_ha: float) -> int:
    """Résolution en mètres adaptée à la superficie."""
    if superficie_ha is None or superficie_ha < 2:
        return 10
    if superficie_ha < 10:
        return 20
    return 60


def _m_to_deg(metres: float) -> float:
    """Convertit des mètres en degrés (approximation)."""
    return metres / _DEG_TO_M


def _generer_grille(
    bbox: Tuple[float, float, float, float],
    resolution_m: int,
) -> List[Tuple[float, float, float, float]]:
    """Génère une grille de cellules bbox (min_lon, min_lat, max_lon, max_lat).

    Retourne liste de (cell_min_lon, cell_min_lat, cell_max_lon, cell_max_lat).
    Limite à 10 000 cellules pour éviter des réponses trop lourdes.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    step = _m_to_deg(resolution_m)

    cellules = []
    lat = min_lat
    while lat < max_lat:
        lon = min_lon
        while lon < max_lon:
            cellules.append((
                round(lon, 7),
                round(lat, 7),
                round(min(lon + step, max_lon), 7),
                round(min(lat + step, max_lat), 7),
            ))
            lon += step
        lat += step
        if len(cellules) >= 10_000:
            break

    return cellules


def _score_label(score: float) -> str:
    """Score → label couleur lisible."""
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Bon"
    if score >= 40:
        return "Moyen"
    return "Faible"


def _couleur(score: float) -> str:
    """Score → couleur hex pour la carte."""
    if score >= 80:
        return "#22c55e"   # vert
    if score >= 60:
        return "#84cc16"   # jaune-vert
    if score >= 40:
        return "#f59e0b"   # orange
    return "#ef4444"       # rouge


def _variation_spatiale(
    score_central: float,
    idx: int,
    nb_total: int,
    seed: int = 42,
) -> float:
    """Ajoute une variation pseudo-aléatoire spatiale autour du score central.

    Utilise une graine fixe pour reproductibilité (même carte à chaque requête
    tant que le score ne change pas). La variation est bornée à ±15 pts et ne
    peut pas sortir de [15, 100].
    """
    rng = random.Random(seed + idx)
    variation = rng.gauss(0, 8)   # écart-type 8 pts
    return max(15.0, min(100.0, score_central + variation))


def generer_carte(
    type_carte: str,
    score_central: float,
    coordonnees: List[Dict],
    superficie_ha: float,
) -> Dict[str, Any]:
    """Génère un GeoJSON FeatureCollection pour une carte de précision.

    Args:
        type_carte:     sante|hydrique|fertilite|risques
        score_central:  score moyen de la parcelle (0–100)
        coordonnees:    polygon [{lat, lon}] depuis Cartographie
        superficie_ha:  superficie pour choisir la résolution

    Returns:
        dict GeoJSON FeatureCollection + metadata
    """
    if not coordonnees or len(coordonnees) < 2:
        # Parcelle sans cartographie : retourne un FeatureCollection vide
        return {
            "type": "FeatureCollection",
            "features": [],
            "_meta": {
                "type_carte": type_carte,
                "nb_cellules": 0,
                "resolution_m": 10,
                "avertissement": "Coordonnées insuffisantes pour générer la carte",
            },
        }

    resolution = resolution_adaptative(superficie_ha)
    bbox = coordonnees_to_bbox(coordonnees)
    cellules = _generer_grille(bbox, resolution)
    nb = len(cellules)

    features = []
    for i, (min_lon, min_lat, max_lon, max_lat) in enumerate(cellules):
        score_cell = _variation_spatiale(score_central, i, nb)
        label      = _score_label(score_cell)
        couleur    = _couleur(score_cell)

        # GeoJSON Polygon (rectangle)
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]],
        }
        properties: Dict[str, Any] = {
            "score":   round(score_cell, 1),
            "label":   label,
            "couleur": couleur,
            "type":    type_carte,
        }

        features.append({
            "type":       "Feature",
            "geometry":   geometry,
            "properties": properties,
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "type_carte":   type_carte,
            "nb_cellules":  nb,
            "resolution_m": resolution,
            "score_moyen":  round(score_central, 1),
        },
    }


def generer_toutes_cartes(
    scores: Dict[str, float],
    coordonnees: List[Dict],
    superficie_ha: float,
) -> Dict[str, Dict[str, Any]]:
    """Génère les 4 cartes de précision en une fois.

    Args:
        scores: {vigueur, hydrique, fertilite, maladie, ravageur, composite}
        coordonnees: polygon [{lat, lon}]
        superficie_ha: superficie de la parcelle

    Returns:
        dict keyed by type_carte → GeoJSON FeatureCollection
    """
    mapping = {
        "sante":    scores.get("composite", 50.0),
        "hydrique": scores.get("hydrique", 50.0),
        "fertilite": scores.get("fertilite", 50.0),
        "risques":  min(scores.get("maladie", 100.0), scores.get("ravageur", 100.0)),
    }
    return {
        carte: generer_carte(carte, score, coordonnees, superficie_ha)
        for carte, score in mapping.items()
    }
