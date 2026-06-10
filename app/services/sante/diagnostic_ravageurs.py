"""
Pipeline diagnostic ravageurs.
Combine Rules Engine (70%) + matching observations directes (30%).
Inclut seuil économique et niveau d'urgence.
"""
from sqlalchemy.orm import Session, selectinload

from app.models.agronomie import Ravageur, CultureRavageur
from app.models.sante import Consultation
from app.services.rules_evaluator import evaluate
from app.services.sante.contexte import build_contexte


def analyser_ravageurs(db: Session, consultation: Consultation, plan: str = "gratuit") -> list[dict]:
    """
    Retourne une liste classée de diagnostics ravageurs (max 5).
    Chaque item : {entite_type, entite_id, entite_nom, score_confiance,
                   score_rules, score_symptomes, regles_matches, methode}
    """
    ctx = build_contexte(db, consultation)
    culture_id = consultation.culture_id or ctx.get("culture_id")

    # 1. Rules Engine — catégorie ravageur
    result = evaluate(db, ctx, categorie="ravageur", plan=plan, persist=False)
    regles_declenchees = result.get("resultats", [])  # liste des règles déclenchées

    regle_scores: dict[str, float] = {}
    for r in regles_declenchees:
        code = r.get("code", "")
        conf = r.get("confiance", 0.5)
        regle_scores[code] = float(conf) if conf else 0.5

    # 2. Candidats bibliothèque filtrés par culture
    candidats = _candidats_ravageurs(db, culture_id)

    # 3. Observations directes
    ravageurs_obs = ctx.get("obs_ravageurs", [])
    densite_obs   = ctx.get("obs_densite_ravageur", "")

    resultats = []
    for cr in candidats:
        ravageur = cr.ravageur
        codes    = _codes_pour_ravageur(ravageur.nom, regles_declenchees)

        s_rules = _score_rules(codes, regle_scores)
        s_obs   = _score_observation(ravageur, ravageurs_obs)
        score   = round(0.70 * s_rules + 0.30 * s_obs, 4)

        if score < 0.05:
            continue

        methode = _methode(s_rules, s_obs)
        resultats.append({
            "entite_type":     "ravageur",
            "entite_id":       ravageur.id,
            "entite_nom":      ravageur.nom,
            "score_confiance": score,
            "score_rules":     s_rules,
            "score_symptomes": s_obs,
            "regles_matches":  codes,
            "methode":         methode,
        })

    resultats.sort(key=lambda x: x["score_confiance"], reverse=True)
    return resultats[:5]


def _candidats_ravageurs(db: Session, culture_id: int | None) -> list[CultureRavageur]:
    q = (db.query(CultureRavageur)
         .options(selectinload(CultureRavageur.ravageur)))
    if culture_id:
        q = q.filter(CultureRavageur.culture_id == culture_id)
    return q.all()


def _codes_pour_ravageur(nom_ravageur: str, regles: list[dict]) -> list[str]:
    nom_lower = nom_ravageur.lower()
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


def _score_rules(codes: list[str], regle_scores: dict[str, float]) -> float:
    if not codes:
        return 0.0
    scores = [regle_scores.get(c, 0.4) for c in codes]
    return min(max(scores), 1.0)


def _score_observation(ravageur: Ravageur, ravageurs_obs: list[str]) -> float:
    """Score 1.0 si nom exact, 0.5 si partiel, 0.0 sinon."""
    if not ravageurs_obs:
        return 0.0
    nom_lower = ravageur.nom.lower()
    noms_sci  = (ravageur.nom_scientifique or "").lower()
    for obs in ravageurs_obs:
        obs_lower = obs.lower()
        if obs_lower == nom_lower or obs_lower in nom_lower:
            return 1.0
        if noms_sci and obs_lower in noms_sci:
            return 0.8
        if nom_lower in obs_lower:
            return 0.5
    return 0.0


def _methode(s_rules: float, s_obs: float) -> str:
    if s_rules > 0 and s_obs > 0:
        return "combinee"
    if s_rules > 0:
        return "rules_engine"
    if s_obs > 0:
        return "symptomes"
    return "bibliotheque"
