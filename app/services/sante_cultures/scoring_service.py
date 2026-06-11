"""
ScoringService — Calcul du Score Santé Composite AgroScan.

Score Santé = Σ(wᵢ × scoreᵢ) sur 5 dimensions :
  Vigueur     (w=0.30) — NDVI / EVI
  Hydrique    (w=0.25) — NDWI + Rules Engine irrigation
  Fertilité   (w=0.20) — NDRE + Rules Engine fertilisation
  Maladie     (w=0.15) — Rules Engine maladie (inversé)
  Ravageur    (w=0.10) — Rules Engine ravageur (inversé)

Résultat : 0–100, labels : Excellent ≥80 | Bon 60–79 | Moyen 40–59 | Faible <40
"""
from typing import Optional

# ── Poids du score composite ─────────────────────────────────────────────────
POIDS = {
    "vigueur":   0.30,
    "hydrique":  0.25,
    "fertilite": 0.20,
    "maladie":   0.15,
    "ravageur":  0.10,
}
assert abs(sum(POIDS.values()) - 1.0) < 1e-9, "Poids doivent sommer à 1.0"

# ── Poids déduction par gravité ───────────────────────────────────────────────
_GRAVITE_POIDS = {
    "critique": 40,
    "elevee":   20,
    "moyenne":  10,
    "faible":    5,
}
_MAX_DEDUCTION = 80   # Score risque jamais < 20


def score_depuis_ndvi(ndvi: Optional[float]) -> float:
    """NDVI → score vigueur 0–100."""
    if ndvi is None:
        return 50.0   # neutre si données absentes
    if ndvi >= 0.6:
        return 100.0
    if ndvi >= 0.4:
        return 75.0
    if ndvi >= 0.2:
        return 45.0
    return 15.0


def score_depuis_evi(evi: Optional[float]) -> float:
    """EVI → score vigueur 0–100 (complément de NDVI)."""
    if evi is None:
        return 50.0
    if evi >= 0.5:
        return 100.0
    if evi >= 0.35:
        return 75.0
    if evi >= 0.15:
        return 45.0
    return 15.0


def score_vigueur(ndvi: Optional[float], evi: Optional[float] = None) -> float:
    """Score vigueur végétale (0–100). Moyenne NDVI+EVI si EVI disponible."""
    s_ndvi = score_depuis_ndvi(ndvi)
    if evi is not None:
        s_evi = score_depuis_evi(evi)
        return (s_ndvi * 0.6 + s_evi * 0.4)   # NDVI poids légèrement supérieur
    return s_ndvi


def score_depuis_ndwi(ndwi: Optional[float]) -> float:
    """NDWI → composante hydrique 0–100.

    ndwi élevé (>0.2) = bonne humidité = score élevé.
    """
    if ndwi is None:
        return 50.0
    if ndwi >= 0.2:
        return 100.0
    if ndwi >= 0.0:
        return 70.0
    if ndwi >= -0.2:
        return 40.0
    return 15.0


def score_risque(regles_declenchees: list) -> float:
    """Calcule un score risque (100 = aucun risque) depuis les règles déclenchées.

    Déduit des points par gravité × confiance.
    Plancher = 20 (on ne descend jamais à 0).
    """
    deduction = sum(
        _GRAVITE_POIDS.get(r.get("gravite", "faible"), 5) * r.get("confiance", 0.5)
        for r in regles_declenchees
    )
    return max(100.0 - min(deduction, _MAX_DEDUCTION), 20.0)


def score_hydrique(
    ndwi: Optional[float],
    sol_humidite: Optional[float],
    regles_irrigation: list,
    niveau: int,
) -> float:
    """Score stress hydrique (0–100, 100=aucun stress).

    Niveau 1 : NDWI satellite uniquement
    Niveau 2/3 : NDWI + sol_humidite + règles irrigation
    """
    s_ndwi = score_depuis_ndwi(ndwi)

    # Correction capteur sol (niveau 2+)
    if niveau >= 2 and sol_humidite is not None:
        if sol_humidite >= 60:
            s_sol = 100.0
        elif sol_humidite >= 40:
            s_sol = 70.0
        elif sol_humidite >= 25:
            s_sol = 40.0
        else:
            s_sol = 15.0
        s_base = s_ndwi * 0.4 + s_sol * 0.6
    else:
        s_base = s_ndwi

    # Pénalité règles irrigation déclenchées
    if regles_irrigation:
        s_regles = score_risque(regles_irrigation)
        return s_base * 0.7 + s_regles * 0.3

    return s_base


def score_fertilite(
    ndre: Optional[float],
    sol_azote: Optional[float],
    sol_phosphore: Optional[float],
    sol_potassium: Optional[float],
    regles_fertilisation: list,
    niveau: int,
) -> float:
    """Score fertilité (0–100).

    Niveau 1 : NDRE (chlorophylle proxy)
    Niveau 2/3 : NDRE + NPK capteur/labo
    """
    if ndre is None:
        s_ndre = 50.0
    elif ndre >= 0.5:
        s_ndre = 100.0
    elif ndre >= 0.3:
        s_ndre = 75.0
    elif ndre >= 0.1:
        s_ndre = 45.0
    else:
        s_ndre = 15.0

    # Niveau 3 : données labo complètes (NPK)
    if niveau >= 3 and sol_azote is not None and sol_phosphore is not None:
        scores_sol = []
        # Azote : seuil carence < 30 mg/kg
        if sol_azote >= 60:
            scores_sol.append(100.0)
        elif sol_azote >= 30:
            scores_sol.append(65.0)
        else:
            scores_sol.append(25.0)
        # Phosphore : seuil carence < 10 mg/kg
        if sol_phosphore >= 20:
            scores_sol.append(100.0)
        elif sol_phosphore >= 10:
            scores_sol.append(60.0)
        else:
            scores_sol.append(20.0)
        # Potassium (si disponible)
        if sol_potassium is not None:
            if sol_potassium >= 150:
                scores_sol.append(100.0)
            elif sol_potassium >= 80:
                scores_sol.append(65.0)
            else:
                scores_sol.append(25.0)
        s_sol = sum(scores_sol) / len(scores_sol)
        s_base = s_ndre * 0.3 + s_sol * 0.7
    else:
        s_base = s_ndre

    # Pénalité règles fertilisation
    if regles_fertilisation:
        s_regles = score_risque(regles_fertilisation)
        return s_base * 0.6 + s_regles * 0.4

    return s_base


def score_composite(
    vigueur: float,
    hydrique: float,
    fertilite: float,
    maladie: float,
    ravageur: float,
) -> float:
    """Score Santé Composite (0–100) pondéré."""
    return (
        vigueur   * POIDS["vigueur"]   +
        hydrique  * POIDS["hydrique"]  +
        fertilite * POIDS["fertilite"] +
        maladie   * POIDS["maladie"]   +
        ravageur  * POIDS["ravageur"]
    )


def score_to_etat(score: float) -> str:
    """Score → label état général."""
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Bon"
    if score >= 40:
        return "Moyen"
    return "Faible"
