"""
IndiceService — Traduction indices satellitaires → labels lisibles.
Les valeurs brutes (ex: NDVI=0.52) ne sont JAMAIS exposées au producteur.
"""
from typing import Optional


# Seuils par indice : (threshold, label) trié décroissant
# Si valeur >= threshold → label. Dernier bucket = "Faible".
_THRESHOLDS = {
    "ndvi":  [(0.6, "Excellent"), (0.4, "Bon"), (0.2, "Moyen")],
    "ndre":  [(0.5, "Excellent"), (0.3, "Bon"), (0.1, "Moyen")],
    "savi":  [(0.5, "Excellent"), (0.3, "Bon"), (0.15, "Moyen")],
    "evi":   [(0.5, "Excellent"), (0.35, "Bon"), (0.15, "Moyen")],
    "msavi": [(0.5, "Excellent"), (0.3, "Bon"), (0.15, "Moyen")],
    # NDWI : valeur positive = eau/humidité, négatif = sec
    "ndwi":  [(0.2, "Excellent"), (0.0, "Bon"), (-0.2, "Moyen")],
}


def to_label(index_name: str, value: Optional[float]) -> Optional[str]:
    """Traduit une valeur d'indice en label Excellent/Bon/Moyen/Faible.

    Retourne None si la valeur est None ou l'indice inconnu.
    """
    if value is None:
        return None
    thresholds = _THRESHOLDS.get(index_name)
    if thresholds is None:
        return None
    for threshold, label in thresholds:
        if value >= threshold:
            return label
    return "Faible"


def ndwi_to_stress_label(ndwi: Optional[float]) -> Optional[str]:
    """NDWI traduit en label stress hydrique (inversé — ndwi élevé = bon).

    Retourne le label depuis la perspective du stress :
    NDWI élevé = humidité bonne → pas de stress.
    """
    return to_label("ndwi", ndwi)


def traduire_tous(raw: dict) -> dict:
    """Traduit tous les indices d'un dict raw en labels.

    Entrée : {ndvi: 0.52, ndre: 0.31, ...}
    Sortie : {ndvi_label: 'Bon', ndre_label: 'Bon', ...}
    """
    return {
        "ndvi_label":  to_label("ndvi",  raw.get("ndvi")),
        "ndre_label":  to_label("ndre",  raw.get("ndre")),
        "savi_label":  to_label("savi",  raw.get("savi")),
        "evi_label":   to_label("evi",   raw.get("evi")),
        "msavi_label": to_label("msavi", raw.get("msavi")),
        "ndwi_label":  to_label("ndwi",  raw.get("ndwi")),
    }
