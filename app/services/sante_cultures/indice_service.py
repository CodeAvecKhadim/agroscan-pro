"""
IndiceService — Traduction indices satellitaires → labels lisibles.
Les valeurs brutes (ex: NDVI=0.52) ne sont JAMAIS exposées au producteur.
"""
from typing import Optional


# Seuils par indice : (threshold, label) trié décroissant
# Si valeur >= threshold → label. Dernier bucket = "Faible".
_THRESHOLDS = {
    "ndvi":    [(0.6, "Excellent"), (0.4, "Bon"), (0.2, "Moyen")],
    "ndre":    [(0.5, "Excellent"), (0.3, "Bon"), (0.1, "Moyen")],
    "savi":    [(0.5, "Excellent"), (0.3, "Bon"), (0.15, "Moyen")],
    "evi":     [(0.5, "Excellent"), (0.35, "Bon"), (0.15, "Moyen")],
    "msavi":   [(0.5, "Excellent"), (0.3, "Bon"), (0.15, "Moyen")],
    # NDWI : eau en surface (B3-B8)/(B3+B8)
    "ndwi":    [(0.2, "Excellent"), (0.0, "Bon"), (-0.2, "Moyen")],
    # NDMI : humidité végétation (B8A-B11)/(B8A+B11)
    "ndmi":    [(0.3, "Excellent"), (0.1, "Bon"), (-0.1, "Moyen")],
    # Biomasse estimée (t MS/ha) — seuils zone sahélienne
    "biomasse": [(8.0, "Excellent"), (4.0, "Bon"), (1.5, "Moyen")],
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


def estimer_biomasse(ndvi: Optional[float], evi: Optional[float]) -> Optional[float]:
    """Estime la biomasse aérienne sèche (t MS/ha) depuis NDVI et EVI.

    Formule empirique Senegal (zones sahéliennes/soudaniennes) :
      biomasse ≈ 3.5 * EVI + 1.2 (si EVI dispo)
      ou biomasse ≈ 2.8 * NDVI + 0.5 (si NDVI seulement)
    Valeur nulle si aucun indice disponible.
    """
    if evi is not None and evi >= 0:
        return round(max(0.0, 3.5 * evi + 1.2), 2)
    if ndvi is not None and ndvi >= 0:
        return round(max(0.0, 2.8 * ndvi + 0.5), 2)
    return None


def traduire_tous(raw: dict) -> dict:
    """Traduit tous les indices d'un dict raw en labels.

    Entrée : {ndvi: 0.52, ndre: 0.31, ndmi: 0.15, ...}
    Sortie : {ndvi_label: 'Bon', ndre_label: 'Bon', ...}
    Calcule aussi biomasse si absent.
    """
    biomasse = raw.get("biomasse") or estimer_biomasse(raw.get("ndvi"), raw.get("evi"))
    return {
        "ndvi_label":     to_label("ndvi",     raw.get("ndvi")),
        "ndre_label":     to_label("ndre",      raw.get("ndre")),
        "savi_label":     to_label("savi",      raw.get("savi")),
        "evi_label":      to_label("evi",        raw.get("evi")),
        "msavi_label":    to_label("msavi",     raw.get("msavi")),
        "ndwi_label":     to_label("ndwi",      raw.get("ndwi")),
        "ndmi_label":     to_label("ndmi",      raw.get("ndmi")),
        "biomasse":       biomasse,
        "biomasse_label": to_label("biomasse",  biomasse),
    }
