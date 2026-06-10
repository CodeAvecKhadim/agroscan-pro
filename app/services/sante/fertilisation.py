"""
Pipeline fertilisation intelligente — 4 sources fusionnées :
  1. Rules Engine (categorie=fertilisation)
  2. Analyse sol Mon Champ (AnalyseSol)
  3. Capteur terrain (observations.type=sol — prioritaire)
  4. Bibliothèque maladies type=carence (agro_maladies)
"""
from sqlalchemy.orm import Session

from app.models.agronomie import Maladie
from app.models.sante import Consultation
from app.services.rules_evaluator import evaluate
from app.services.sante.contexte import build_contexte


# Seuils indicatifs (valeurs typiques sols Sénégal)
_SEUILS_CARENCE = {
    "sol_pH":       {"min": 5.5, "max": 7.5, "carence_label": "Acidité/Alcalinité sol"},
    "sol_azote":    {"min": 80,  "max": None, "carence_label": "Carence Azote (N)"},
    "sol_phosphore": {"min": 15, "max": None, "carence_label": "Carence Phosphore (P)"},
    "sol_potassium": {"min": 80, "max": None, "carence_label": "Carence Potassium (K)"},
    "sol_matiere_organique": {"min": 1.0, "max": None, "carence_label": "Faible matière organique"},
}


def analyser_fertilisation(db: Session, consultation: Consultation, plan: str = "gratuit") -> list[dict]:
    """
    Retourne une liste de carences/corrections détectées.
    Format compatible avec generer_plan() — entite_type='carence'.
    """
    ctx = build_contexte(db, consultation)
    culture_id = consultation.culture_id or ctx.get("culture_id")

    # 1. Rules Engine fertilisation
    result = evaluate(db, ctx, categorie="fertilisation", plan=plan, persist=False)
    regles_declenchees = result.get("resultats", [])  # liste des règles déclenchées

    regle_scores: dict[str, float] = {}
    for r in regles_declenchees:
        regle_scores[r.get("code", "")] = float(r.get("confiance", 0.6))

    # 2. Analyse carences depuis contexte sol (comparaison seuils)
    carences_sol = _detecter_carences_sol(ctx)

    # 3. Maladies de type carence depuis bibliothèque
    carences_biblio = _carences_bibliotheque(db, culture_id)

    # 4. Fusion
    resultats: dict[str, dict] = {}

    # Ajouter carences sol
    for c in carences_sol:
        key = c["label"]
        resultats[key] = {
            "entite_type":     "carence",
            "entite_id":       0,
            "entite_nom":      c["label"],
            "score_confiance": c["score"],
            "score_rules":     0.0,
            "score_symptomes": c["score"],
            "regles_matches":  [],
            "methode":         "symptomes",
            "valeur_mesuree":  c.get("valeur"),
            "seuil_min":       c.get("seuil_min"),
        }

    # Enrichir/ajouter depuis rules engine
    for r in regles_declenchees:
        code  = r.get("code", "")
        titre = r.get("titre", code)
        score = regle_scores.get(code, 0.5)
        if titre not in resultats:
            resultats[titre] = {
                "entite_type":     "carence",
                "entite_id":       0,
                "entite_nom":      titre,
                "score_confiance": score,
                "score_rules":     score,
                "score_symptomes": 0.0,
                "regles_matches":  [code],
                "methode":         "rules_engine",
            }
        else:
            # Fusionner — rules engine booste le score
            existing = resultats[titre]
            existing["score_rules"]     = score
            existing["regles_matches"].append(code)
            combined = round(0.6 * score + 0.4 * existing["score_symptomes"], 4)
            existing["score_confiance"] = combined
            existing["methode"]         = "combinee"

    # Enrichir depuis bibliothèque maladies carences
    for m in carences_biblio:
        if m.nom not in resultats:
            resultats[m.nom] = {
                "entite_type":     "carence",
                "entite_id":       m.id,
                "entite_nom":      m.nom,
                "score_confiance": 0.3,
                "score_rules":     0.0,
                "score_symptomes": 0.3,
                "regles_matches":  [],
                "methode":         "bibliotheque",
            }

    liste = list(resultats.values())
    liste.sort(key=lambda x: x["score_confiance"], reverse=True)
    return liste[:8]


def _detecter_carences_sol(ctx: dict) -> list[dict]:
    """Détecte les carences par comparaison aux seuils indicatifs."""
    carences = []
    for param, seuils in _SEUILS_CARENCE.items():
        valeur = ctx.get(param)
        if valeur is None:
            continue
        carence = False
        score   = 0.0
        if seuils["min"] is not None and valeur < seuils["min"]:
            carence = True
            manque  = seuils["min"] - valeur
            score   = min(1.0, round(manque / seuils["min"], 3))
        if seuils["max"] is not None and valeur > seuils["max"]:
            carence = True
            score   = min(1.0, round((valeur - seuils["max"]) / seuils["max"], 3))
        if carence:
            carences.append({
                "label":     seuils["carence_label"],
                "param":     param,
                "valeur":    valeur,
                "seuil_min": seuils["min"],
                "score":     max(score, 0.4),
            })
    return carences


def _carences_bibliotheque(db: Session, culture_id: int | None) -> list[Maladie]:
    """Maladies de type physiologique (carences) de la bibliothèque."""
    return (db.query(Maladie)
            .filter(Maladie.pathogene_type == "physiologique")
            .limit(20)
            .all())
