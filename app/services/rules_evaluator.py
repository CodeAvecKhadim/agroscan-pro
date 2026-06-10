"""
Rules Evaluator — moteur d'évaluation des règles AgroScan Pro.

Pipeline :
  1. Aplatissement du contexte → namespace {field: value}
  2. Filtrage des règles applicables (zone / stade / mois / culture)
  3. Évaluation récursive des conditions JSONB (DSL AND/OR/clauses)
  4. Tri : gravite DESC + priorite DESC
  5. Persistance optionnelle dans re_declenchements
"""
import time
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, selectinload

from app.models.rules_engine import RegleMoteur, RegleCulture, RegleDeclenchement, RegleSession
from app.models.agronomie import Culture

log = logging.getLogger(__name__)

_GRAVITE_ORDER = {"critique": 4, "elevee": 3, "moyenne": 2, "faible": 1}
_PLAN_ORDER = ["gratuit", "premium", "cooperative"]


def _flatten(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Convertit RulesContext (snake_case) en namespace à points."""
    return {
        "sol.pH":                ctx.get("sol_pH"),
        "sol.azote":             ctx.get("sol_azote"),
        "sol.phosphore":         ctx.get("sol_phosphore"),
        "sol.potassium":         ctx.get("sol_potassium"),
        "sol.humidite":          ctx.get("sol_humidite"),
        "sol.temperature":       ctx.get("sol_temperature"),
        "sol.matiere_organique": ctx.get("sol_matiere_organique"),
        "sol.conductivite":      ctx.get("sol_conductivite"),
        "meteo.temp_air":        ctx.get("meteo_temp_air"),
        "meteo.humidite_rel":    ctx.get("meteo_humidite_rel"),
        "meteo.pluie_24h":       ctx.get("meteo_pluie_24h"),
        "meteo.pluie_7j":        ctx.get("meteo_pluie_7j"),
        "meteo.vent":            ctx.get("meteo_vent"),
        "meteo.etp":             ctx.get("meteo_etp"),
        "culture.stade":         ctx.get("stade_actuel"),
        "culture.zone":          ctx.get("zone_agro"),
        "culture.mois":          ctx.get("mois"),
        "culture.jours_semis":   ctx.get("jours_semis"),
        "obs.symptomes":         ctx.get("obs_symptomes") or [],
        "obs.ravageurs":         ctx.get("obs_ravageurs") or [],
        "obs.densite_ravageur":  ctx.get("obs_densite_ravageur"),
    }


def _eval_clause(clause: Dict[str, Any], flat: Dict[str, Any]) -> bool:
    """Évaluation récursive d'une clause (simple ou composée)."""
    if "operator" in clause:
        op = clause["operator"]
        sub = clause.get("clauses", [])
        if op == "AND":
            return all(_eval_clause(c, flat) for c in sub)
        if op == "OR":
            return any(_eval_clause(c, flat) for c in sub)
        return False

    field = clause.get("field")
    op = clause.get("op")
    value = clause.get("value")
    value2 = clause.get("value2")
    actual = flat.get(field)

    if actual is None and op not in ("is_null",):
        return False  # donnée absente → règle non déclenchable

    try:
        if op == "eq":        return actual == value
        if op == "ne":        return actual != value
        if op == "lt":        return actual < value
        if op == "lte":       return actual <= value
        if op == "gt":        return actual > value
        if op == "gte":       return actual >= value
        if op == "between":   return value <= actual <= value2
        if op == "in":        return actual in value
        if op == "not_in":    return actual not in value
        if op == "contains":  return value in actual
        if op == "not_null":  return actual is not None
        if op == "is_null":   return actual is None
    except (TypeError, KeyError):
        return False

    return False


def _rule_applicable(rule: RegleMoteur, culture_id: Optional[int], ctx: Dict[str, Any]) -> bool:
    """Vérifie que la règle s'applique au contexte courant."""
    # Culture
    linked_ids = [rc.culture_id for rc in rule.cultures]
    if linked_ids and culture_id not in linked_ids:
        return False

    # Zone
    zone = ctx.get("zone_agro")
    if rule.zones_applicables and zone and zone not in rule.zones_applicables:
        return False

    # Stade
    stade = ctx.get("stade_actuel")
    if rule.stades_applicables and stade and stade not in rule.stades_applicables:
        return False

    # Mois
    mois = ctx.get("mois")
    if rule.mois_applicables and mois and mois not in rule.mois_applicables:
        return False

    return True


def evaluate(
    db: Session,
    context: Dict[str, Any],
    categorie: str = "maladie",
    plan: str = "gratuit",
    persist: bool = False,
) -> Dict[str, Any]:
    """
    Évalue toutes les règles actives de la catégorie donnée contre le contexte.

    Args:
        db:        session SQLAlchemy
        context:   dict issu de RulesContext.model_dump()
        categorie: filtre catégorie (default 'maladie')
        plan:      plan de l'org pour filtrer les règles premium
        persist:   si True, persiste les déclenchements + session

    Returns:
        dict EvaluationResponse-compatible
    """
    t0 = time.perf_counter()

    # Résoudre la culture
    culture_nom = context.get("culture_nom", "")
    culture = db.query(Culture).filter_by(nom=culture_nom).first()
    culture_id = culture.id if culture else None

    # Plan filter
    max_idx = _PLAN_ORDER.index(plan) if plan in _PLAN_ORDER else 0
    allowed_plans = _PLAN_ORDER[: max_idx + 1]

    # Charger les règles (avec jointure cultures pour filtrage)
    rules: List[RegleMoteur] = (
        db.query(RegleMoteur)
        .options(selectinload(RegleMoteur.cultures))
        .filter(
            RegleMoteur.active == True,
            RegleMoteur.categorie == categorie,
            RegleMoteur.plan_requis.in_(allowed_plans),
        )
        .all()
    )

    flat = _flatten(context)
    triggered = []
    evaluated = 0

    for rule in rules:
        evaluated += 1
        if not _rule_applicable(rule, culture_id, context):
            continue
        try:
            fired = _eval_clause(rule.conditions, flat)
        except Exception as e:
            log.warning("Erreur éval règle %s : %s", rule.code, e)
            fired = False

        if not fired:
            continue

        # Construire le résultat
        actions = rule.actions or {}
        result = {
            "code": rule.code,
            "nom": rule.nom,
            "categorie": rule.categorie,
            "sous_categorie": rule.sous_categorie,
            "gravite": rule.gravite or "faible",
            "priorite": rule.priorite or 5,
            "confiance": rule.confiance or 0.80,
            "alertes": actions.get("alertes", []),
            "recommandations": actions.get("recommandations", []),
            "risque": actions.get("risque"),
        }
        triggered.append(result)

        if persist and context.get("org_id"):
            db.add(RegleDeclenchement(
                regle_id=rule.id,
                org_id=context["org_id"],
                parcelle_id=context.get("parcelle_id"),
                contexte_entree=context,
                resultat=result,
                score_confiance=rule.confiance,
            ))

    # Tri : gravite DESC, priorite DESC
    triggered.sort(
        key=lambda r: (_GRAVITE_ORDER.get(r["gravite"], 0), r["priorite"]),
        reverse=True,
    )

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    if persist and context.get("org_id"):
        db.add(RegleSession(
            org_id=context["org_id"],
            parcelle_id=context.get("parcelle_id"),
            contexte=context,
            regles_evaluees=evaluated,
            regles_declenchees=len(triggered),
            duree_ms=elapsed_ms,
        ))
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            log.error("Erreur persistance session : %s", e)

    return {
        "culture_evaluee": culture_nom,
        "zone": context.get("zone_agro"),
        "stade": context.get("stade_actuel"),
        "regles_evaluees": evaluated,
        "regles_declenchees": len(triggered),
        "duree_ms": elapsed_ms,
        "alertes_critiques": sum(1 for r in triggered if r["gravite"] == "critique"),
        "alertes_elevees": sum(1 for r in triggered if r["gravite"] == "elevee"),
        "resultats": triggered,
    }
