"""
Moteur de score de complétude — Module MON CHAMP.
Score 0-100 recalculé automatiquement après chaque modification.
"""
from sqlalchemy.orm import Session

from app.models.champ import Parcelle, Cartographie, AnalyseSol, Infrastructure, SourceEau
from app.schemas.champ import ScoreCompletude, DimensionScore


_POIDS = {
    "cartographie":  25,
    "sol":           25,
    "culture_zone":  15,
    "sources_eau":   15,
    "infrastructures": 10,
    "localisation":  10,
}


def _dim(score: int, max_score: int, manquant: str = None) -> DimensionScore:
    return DimensionScore(
        score=score, max=max_score,
        pct=round(score / max_score * 100, 1),
        complete=(score == max_score),
        manquant=manquant if score < max_score else None,
    )


def calculer_score(db: Session, parcelle: Parcelle) -> ScoreCompletude:
    """Calcule et retourne le score de complétude d'une parcelle."""

    manquants = []

    # 1. Cartographie (25) — polygon actif ≥ 3 points
    carto = (db.query(Cartographie)
             .filter_by(parcelle_id=parcelle.id, actif=True)
             .first())
    if carto and carto.coordonnees and len(carto.coordonnees) >= 3:
        d_carto = _dim(25, 25)
    else:
        d_carto = _dim(0, 25, "Délimitation GPS manquante")
        manquants.append("Délimitation GPS")

    # 2. Sol (25) — pH + azote + phosphore + potassium présents
    sol = (db.query(AnalyseSol)
           .filter_by(parcelle_id=parcelle.id)
           .order_by(AnalyseSol.date_analyse.desc())
           .first())
    if sol:
        params_sol = [sol.pH_eau, sol.azote_total, sol.phosphore_assim, sol.potassium_echang]
        nb_renseignes = sum(1 for p in params_sol if p is not None)
        sol_score = round(nb_renseignes / 4 * 25)
        if nb_renseignes == 4:
            d_sol = _dim(25, 25)
        else:
            manquants_sol = []
            if sol.pH_eau is None: manquants_sol.append("pH")
            if sol.azote_total is None: manquants_sol.append("Azote")
            if sol.phosphore_assim is None: manquants_sol.append("Phosphore")
            if sol.potassium_echang is None: manquants_sol.append("Potassium")
            d_sol = _dim(sol_score, 25, "Analyse incomplète : " + ", ".join(manquants_sol))
            manquants.append("Analyse sol complète (" + ", ".join(manquants_sol) + ")")
    else:
        d_sol = _dim(0, 25, "Aucune analyse sol")
        manquants.append("Analyse sol")

    # 3. Culture + zone agro + date semis (15)
    culture_ok = bool(parcelle.culture_id or parcelle.type_culture)
    zone_ok = bool(parcelle.zone_agro)
    semis_ok = bool(getattr(parcelle, "date_semis", None))
    cz_score = 0
    cz_miss = []
    if culture_ok:
        cz_score += 7
    else:
        cz_miss.append("Culture")
    if zone_ok:
        cz_score += 6
    else:
        cz_miss.append("Zone agro-écologique")
    if semis_ok:
        cz_score += 2
    else:
        cz_miss.append("Date de semis")
    d_culture_zone = _dim(cz_score, 15,
                          "Manquant : " + ", ".join(cz_miss) if cz_miss else None)
    if cz_miss:
        manquants.extend(cz_miss)

    # 4. Sources d'eau (15) — ≥ 1 renseignée
    nb_eau = db.query(SourceEau).filter_by(parcelle_id=parcelle.id).count()
    if nb_eau >= 1:
        d_eau = _dim(15, 15)
    else:
        d_eau = _dim(0, 15, "Aucune source d'eau renseignée")
        manquants.append("Source d'eau")

    # 5. Infrastructures (10) — ≥ 1 renseignée
    nb_infra = db.query(Infrastructure).filter_by(parcelle_id=parcelle.id).count()
    if nb_infra >= 1:
        d_infra = _dim(10, 10)
    else:
        d_infra = _dim(0, 10, "Aucune infrastructure renseignée")
        manquants.append("Infrastructures")

    # 6. Localisation texte (10) — région + localité
    region_ok = bool(parcelle.region)
    local_ok = bool(parcelle.localite)
    loc_score = 0
    loc_miss = []
    if region_ok:
        loc_score += 5
    else:
        loc_miss.append("Région")
    if local_ok:
        loc_score += 5
    else:
        loc_miss.append("Localité")
    d_loc = _dim(loc_score, 10,
                 "Manquant : " + ", ".join(loc_miss) if loc_miss else None)
    if loc_miss:
        manquants.extend(loc_miss)

    total = (d_carto.score + d_sol.score + d_culture_zone.score
             + d_eau.score + d_infra.score + d_loc.score)

    return ScoreCompletude(
        total=total,
        cartographie=d_carto,
        sol=d_sol,
        culture_zone=d_culture_zone,
        sources_eau=d_eau,
        infrastructures=d_infra,
        localisation=d_loc,
        manquants=manquants,
    )


def maj_score_parcelle(db: Session, parcelle: Parcelle) -> Parcelle:
    """Recalcule et persiste le score sur la parcelle."""
    score = calculer_score(db, parcelle)
    parcelle.score_completude = score.total
    parcelle.score_detail = score.model_dump()
    db.commit()
    db.refresh(parcelle)
    return parcelle
