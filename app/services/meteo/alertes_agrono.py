"""
Alertes agronomiques — Rules Engine × météo × culture × zone.
Catégories : maladie, ravageur, fertilisation, irrigation.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.models.agronomie import Culture
from app.models.champ import Parcelle, AnalyseSol
from app.models.meteo import Alerte, ConfigAlertes, NiveauAlerte, TypeAlerte
from app.services.rules_evaluator import evaluate

log = logging.getLogger(__name__)

# Gravité règle → niveau alerte
_GRAVITE_NIVEAU = {
    "critique": NiveauAlerte.CRITIQUE,
    "elevee":   NiveauAlerte.AVERTISSEMENT,
    "haute":    NiveauAlerte.AVERTISSEMENT,
    "moyenne":  NiveauAlerte.INFO,
    "faible":   NiveauAlerte.INFO,
}

_CATEGORIE_TYPE = {
    "maladie":       TypeAlerte.MALADIE,
    "ravageur":      TypeAlerte.RAVAGEUR,
    "fertilisation": TypeAlerte.FERTILISATION,
    "irrigation":    TypeAlerte.IRRIGATION,
}


def generer_alertes_agronomiques(
    db: Session,
    org_id: int,
    parcelles: list[Parcelle],
    plan: str = "gratuit",
    config: Optional[ConfigAlertes] = None,
    conditions_par_parcelle: Optional[dict] = None,
) -> list[Alerte]:
    """
    Pour chaque parcelle active, appelle Rules Engine pour 4 catégories
    et convertit les règles critiques/élevées en alertes DB.
    """
    nouvelles: list[Alerte] = []

    for parcelle in parcelles:
        if not parcelle.culture_id:
            continue

        culture = db.query(Culture).filter_by(id=parcelle.culture_id).first()
        if not culture:
            continue

        conditions = (conditions_par_parcelle or {}).get(parcelle.id)
        ctx = _construire_contexte(db, parcelle, culture, conditions)

        categories_actives = _categories_actives(config)

        for categorie in categories_actives:
            try:
                result = evaluate(db, ctx, categorie=categorie, plan=plan, persist=False)
            except Exception as e:
                log.warning("Rules Engine erreur parcelle %d categ %s: %s", parcelle.id, categorie, e)
                continue

            resultats = result.get("resultats", [])
            for r in resultats:
                gravite = r.get("gravite", "faible")
                niveau  = _GRAVITE_NIVEAU.get(gravite, NiveauAlerte.INFO)

                # Seulement avertissement et critique (pas info pour éviter spam)
                if niveau == NiveauAlerte.INFO and categorie not in ("fertilisation",):
                    continue

                sous_type = r.get("sous_categorie") or r.get("code", categorie)

                if _existe_recente(db, org_id, parcelle.id, sous_type):
                    continue

                alertes_raw = r.get("alertes", [])
                recommandations_raw = r.get("recommandations", [])
                titre = r.get("nom") or f"Alerte {categorie}"

                # alertes peut être list[str] ou list[dict{titre,message,...}]
                def _texte(item):
                    if isinstance(item, dict):
                        return item.get("message") or item.get("titre") or str(item)
                    return str(item)

                alertes_texte = [_texte(a) for a in alertes_raw]
                recommandations = [_texte(rc) for rc in recommandations_raw]

                message = "; ".join(alertes_texte[:3]) if alertes_texte else titre
                if recommandations:
                    message += " — Recommandation : " + recommandations[0]

                a = Alerte(
                    org_id=org_id,
                    parcelle_id=parcelle.id,
                    culture_id=parcelle.culture_id,
                    type_alerte=_CATEGORIE_TYPE.get(categorie, TypeAlerte.MALADIE),
                    sous_type=sous_type[:80],
                    niveau=niveau,
                    titre=titre[:200],
                    message=message,
                    regle_code=r.get("code"),
                    details={
                        "categorie": categorie,
                        "gravite":   gravite,
                        "confiance": r.get("confiance"),
                        "recommandations": recommandations,
                        "contexte_meteo": {
                            "temp": ctx.get("meteo_temp_air"),
                            "humidite": ctx.get("meteo_humidite_rel"),
                            "pluie_mm": ctx.get("meteo_pluie_mm"),
                        },
                    },
                    valable_du=datetime.now(timezone.utc),
                )
                db.add(a)
                nouvelles.append(a)

    if nouvelles:
        db.commit()

    return nouvelles


# ── Helpers ───────────────────────────────────────────────────────────────────

def _construire_contexte(
    db: Session,
    parcelle: Parcelle,
    culture: Culture,
    conditions=None,
) -> dict:
    """Construit le contexte Rules Engine depuis la parcelle + météo actuelle."""
    import calendar
    now = datetime.now(timezone.utc)
    mois = now.month

    ctx: dict = {
        "org_id":      parcelle.org_id,
        "culture_nom": culture.nom,
        "zone_agro":   parcelle.zone_agro or "",
        "mois":        mois,
        "saison":      _saison(mois),
    }

    # Données sol (dernière analyse)
    sol = (db.query(AnalyseSol)
           .filter_by(parcelle_id=parcelle.id)
           .order_by(AnalyseSol.id.desc())
           .first())
    if sol:
        if sol.pH_eau is not None:
            ctx["sol_pH"] = float(sol.pH_eau)
        if sol.azote_total is not None:
            ctx["sol_azote"] = float(sol.azote_total)
        if sol.phosphore_assim is not None:
            ctx["sol_phosphore"] = float(sol.phosphore_assim)

    # Météo actuelle
    if conditions:
        if conditions.temp_actuelle is not None:
            ctx["meteo_temp_air"] = conditions.temp_actuelle
        if conditions.humidite_rel is not None:
            ctx["meteo_humidite_rel"] = conditions.humidite_rel
        if conditions.pluie_mm is not None:
            ctx["meteo_pluie_mm"] = conditions.pluie_mm
        if conditions.vent_kmh is not None:
            ctx["meteo_vent_kmh"] = conditions.vent_kmh
        if conditions.etp_mm is not None:
            ctx["meteo_etp_mm"] = conditions.etp_mm

    return ctx


def _saison(mois: int) -> str:
    if mois in (6, 7, 8, 9, 10):
        return "hivernage"
    elif mois in (11, 12, 1, 2):
        return "saison_seche_froide"
    return "saison_seche_chaude"


def _categories_actives(config: Optional[ConfigAlertes]) -> list[str]:
    if config is None:
        return ["maladie", "ravageur", "fertilisation", "irrigation"]
    cats = []
    if config.alertes_maladies_actives:      cats.append("maladie")
    if config.alertes_ravageurs_actives:     cats.append("ravageur")
    if config.alertes_fertilisation_actives: cats.append("fertilisation")
    if config.alertes_irrigation_actives:    cats.append("irrigation")
    return cats


def _existe_recente(
    db: Session, org_id: int, parcelle_id: int, sous_type: str,
    heures: int = 24,
) -> bool:
    seuil = datetime.now(timezone.utc) - timedelta(hours=heures)
    return db.query(Alerte).filter(
        Alerte.org_id == org_id,
        Alerte.parcelle_id == parcelle_id,
        Alerte.sous_type == sous_type,
        Alerte.created_at >= seuil,
    ).first() is not None
