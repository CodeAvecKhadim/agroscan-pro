"""
Pipeline diagnostic maladies.
Combine Rules Engine (60%) + matching symptômes bibliothèque (40%).
Filtre automatiquement par culture via agro_culture_maladies.
"""
from sqlalchemy.orm import Session, selectinload

from app.models.agronomie import Maladie, CultureMaladie
from app.models.sante import Consultation
from app.services.rules_evaluator import evaluate
from app.services.sante.contexte import build_contexte


def analyser_maladies(db: Session, consultation: Consultation, plan: str = "gratuit") -> list[dict]:
    """
    Retourne une liste classée de diagnostics maladies (max 5).
    Chaque item : {entite_type, entite_id, entite_nom, score_confiance,
                   score_rules, score_symptomes, regles_matches, methode}
    """
    ctx = build_contexte(db, consultation)
    culture_id = consultation.culture_id or ctx.get("culture_id")

    # 1. Rules Engine — catégorie maladie
    result = evaluate(db, ctx, categorie="maladie", plan=plan, persist=False)
    regles_declenchees = result.get("resultats", [])  # liste des règles déclenchées

    # Mapper code_regle → confiance de la règle
    regle_scores: dict[str, float] = {}
    for r in regles_declenchees:
        code = r.get("code", "")
        conf = r.get("confiance", 0.5)
        regle_scores[code] = float(conf) if conf else 0.5

    # 2. Candidats depuis bibliothèque (filtrés par culture si disponible)
    candidats = _candidats_maladies(db, culture_id)

    # 3. Scoring combiné
    symptomes_obs = ctx.get("obs_symptomes", [])
    resultats = []
    for cm in candidats:
        maladie = cm.maladie
        codes_maladie = _codes_pour_maladie(maladie.nom, regles_declenchees)

        s_rules = _score_rules_maladie(codes_maladie, regle_scores)
        s_symp  = _score_symptomes(maladie, symptomes_obs)
        score   = round(0.60 * s_rules + 0.40 * s_symp, 4)

        if score < 0.05:
            continue

        methode = _methode(s_rules, s_symp)
        resultats.append({
            "entite_type":     "maladie",
            "entite_id":       maladie.id,
            "entite_nom":      maladie.nom,
            "score_confiance": score,
            "score_rules":     s_rules,
            "score_symptomes": s_symp,
            "regles_matches":  codes_maladie,
            "methode":         methode,
        })

    # Trier par score DESC, top 5
    resultats.sort(key=lambda x: x["score_confiance"], reverse=True)
    return resultats[:5]


def _candidats_maladies(db: Session, culture_id: int | None) -> list[CultureMaladie]:
    q = (db.query(CultureMaladie)
         .options(selectinload(CultureMaladie.maladie)))
    if culture_id:
        q = q.filter(CultureMaladie.culture_id == culture_id)
    return q.all()


def _codes_pour_maladie(nom_maladie: str, regles: list[dict]) -> list[str]:
    """Règles dont l'action ou le titre mentionne cette maladie (matching souple)."""
    nom_lower = nom_maladie.lower()
    codes = []
    for r in regles:
        actions = r.get("actions", [])
        titre   = (r.get("titre") or "").lower()
        desc    = (r.get("description") or "").lower()
        for a in actions:
            if nom_lower in str(a).lower():
                codes.append(r["code"])
                break
        else:
            if nom_lower in titre or nom_lower in desc:
                codes.append(r["code"])
    return list(set(codes))


def _score_rules_maladie(codes: list[str], regle_scores: dict[str, float]) -> float:
    if not codes:
        return 0.0
    scores = [regle_scores.get(c, 0.4) for c in codes]
    return min(max(scores), 1.0)


def _score_symptomes(maladie: Maladie, symptomes_obs: list[str]) -> float:
    if not symptomes_obs:
        return 0.0
    texte = f"{maladie.symptomes or ''} {maladie.conditions_favorables or ''}".lower()
    matches = sum(1 for s in symptomes_obs if s.lower() in texte)
    return round(matches / len(symptomes_obs), 4)


def _methode(s_rules: float, s_symp: float) -> str:
    if s_rules > 0 and s_symp > 0:
        return "combinee"
    if s_rules > 0:
        return "rules_engine"
    if s_symp > 0:
        return "symptomes"
    return "bibliotheque"
