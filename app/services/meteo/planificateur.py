"""
Planificateur intelligent — fenêtres météo optimales pour activités agricoles.
Analyse prévisions 14j et recommande les meilleurs jours pour chaque type d'activité.
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.champ import Parcelle
from app.models.ferme import Activite, StatutActivite, TypeActivite
from app.models.meteo import RecommandationPlan, SourcePlanificateur, StatutPlanificateur

log = logging.getLogger(__name__)

# Contraintes météo par type d'activité (valeurs = seuils à ne pas dépasser)
CONTRAINTES: dict[str, dict] = {
    "traitement": {
        "pluie_max_mm":     5.0,    # pas de pluie le jour J
        "vent_max_kmh":     20.0,   # risque dérive
        "pluie_3j_max_mm":  15.0,   # rémanence : pas de pluie forte dans les 3j suivants
        "temp_max_c":       35.0,   # brûlures foliaires si trop chaud
    },
    "traitement_phytosanitaire": {
        "pluie_max_mm":  5.0,
        "vent_max_kmh":  20.0,
        "pluie_3j_max_mm": 15.0,
        "temp_max_c":    35.0,
    },
    "irrigation": {
        "pluie_max_mm":     15.0,   # inutile si pluie prévue
        "etp_min_mm":       4.0,    # irriguer si ETP élevée
    },
    "recolte": {
        "pluie_max_mm":     2.0,    # grain sec
        "humidite_max_pct": 70,
        "vent_max_kmh":     30.0,
    },
    "semis": {
        "temp_min_c":   20.0,       # sol assez chaud
        "pluie_max_mm": 40.0,       # pas de battance
        "vent_max_kmh": 35.0,
    },
    "plantation": {
        "pluie_max_mm": 40.0,
        "temp_max_c":   38.0,
    },
    "fertilisation": {
        "pluie_apres_mm":  5.0,     # légère pluie favorable (fixation)
        "vent_max_kmh":    25.0,
        "pluie_forte_max": 30.0,    # pas de pluie forte (lessivage)
    },
    "desherbage": {
        "pluie_max_mm":  10.0,
        "vent_max_kmh":  30.0,
    },
}

_TYPE_ACTIVITE_MAP = {
    TypeActivite.TRAITEMENT:    "traitement",
    TypeActivite.IRRIGATION:    "irrigation",
    TypeActivite.RECOLTE:       "recolte",
    TypeActivite.SEMIS:         "semis",
    TypeActivite.PLANTATION:    "plantation",
    TypeActivite.FERTILISATION: "fertilisation",
    TypeActivite.DESHERBAGE:    "desherbage",
}


def generer_recommandations(
    db: Session,
    org_id: int,
    parcelles: list[Parcelle],
    previsions_par_parcelle: dict[int, list[dict]],
) -> list[RecommandationPlan]:
    """
    Pour chaque activité planifiée (statut=planifie) par parcelle,
    trouve la meilleure fenêtre météo dans les 14j.
    """
    nouvelles: list[RecommandationPlan] = []
    today = date.today()

    for parcelle in parcelles:
        previsions = previsions_par_parcelle.get(parcelle.id, [])
        if not previsions:
            continue

        # Activités planifiées de cette parcelle
        activites_planifiees = (
            db.query(Activite)
            .filter(
                Activite.org_id == org_id,
                Activite.parcelle_id == parcelle.id,
                Activite.statut == StatutActivite.PLANIFIE,
            )
            .all()
        )

        for activite in activites_planifiees:
            type_str = _TYPE_ACTIVITE_MAP.get(activite.type)
            if not type_str:
                continue

            contraintes = CONTRAINTES.get(type_str, {})
            meilleur_jour = _trouver_meilleur_jour(previsions, type_str, contraintes)

            if meilleur_jour is None:
                continue

            rec_date = _parse_date(meilleur_jour["date"])
            if rec_date is None:
                continue

            # Éviter doublons
            existant = db.query(RecommandationPlan).filter_by(
                org_id=org_id,
                parcelle_id=parcelle.id,
                activite_id=activite.id,
                statut=StatutPlanificateur.RECOMMANDE,
            ).filter(RecommandationPlan.expire_le >= today).first()

            if existant:
                # Mettre à jour si meilleure date trouvée
                existant.date_recommandee  = rec_date
                existant.conditions_ok     = meilleur_jour["ok"]
                existant.detail_conditions = meilleur_jour["details"]
                existant.raison            = _raison(type_str, meilleur_jour)
                continue

            rec = RecommandationPlan(
                org_id           = org_id,
                parcelle_id      = parcelle.id,
                culture_id       = parcelle.culture_id,
                activite_id      = activite.id,
                date_recommandee = rec_date,
                type_activite    = type_str,
                titre            = f"Fenêtre optimale : {activite.titre or type_str} le {rec_date.strftime('%d/%m')}",
                priorite         = _priorite(type_str, meilleur_jour),
                raison           = _raison(type_str, meilleur_jour),
                fenetre_debut    = today,
                fenetre_fin      = today + timedelta(days=14),
                conditions_ok    = meilleur_jour["ok"],
                detail_conditions = meilleur_jour["details"],
                statut           = StatutPlanificateur.RECOMMANDE,
                source           = SourcePlanificateur.METEO,
                expire_le        = today + timedelta(days=7),
            )
            db.add(rec)
            nouvelles.append(rec)

    if nouvelles or True:
        db.commit()

    return nouvelles


def evaluer_jour(type_activite: str, meteo_jour: dict) -> dict:
    """Évalue si un jour est favorable pour un type d'activité donné."""
    contraintes = CONTRAINTES.get(type_activite, {})
    return _evaluer(meteo_jour, contraintes, type_activite, [])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _trouver_meilleur_jour(
    previsions: list[dict],
    type_activite: str,
    contraintes: dict,
) -> Optional[dict]:
    """Retourne le jour avec le meilleur score sur 14 jours."""
    candidates = []
    for i, jour in enumerate(previsions[:14]):
        suivants = previsions[i+1:i+4]
        eval_result = _evaluer(jour, contraintes, type_activite, suivants)
        if eval_result["score"] > 30:
            candidates.append(eval_result)

    if not candidates:
        return None

    return max(candidates, key=lambda x: x["score"])


def _evaluer(
    jour: dict,
    contraintes: dict,
    type_activite: str,
    suivants: list[dict],
) -> dict:
    score = 100
    raisons_ko: list[str] = []
    detail: dict = {}

    pluie = jour.get("pluie_mm") or 0.0
    vent  = jour.get("vent_kmh") or 0.0
    tmax  = jour.get("temp_max")
    tmin  = jour.get("temp_min")
    hum   = jour.get("humidite_pct")
    etp   = jour.get("etp_mm") or 0.0

    if "pluie_max_mm" in contraintes:
        if pluie > contraintes["pluie_max_mm"]:
            score -= 60
            raisons_ko.append(f"Pluie {pluie:.0f}mm > seuil {contraintes['pluie_max_mm']}mm")
        detail["pluie_ok"] = pluie <= contraintes["pluie_max_mm"]

    if "vent_max_kmh" in contraintes:
        if vent > contraintes["vent_max_kmh"]:
            score -= 40
            raisons_ko.append(f"Vent {vent:.0f}km/h > seuil {contraintes['vent_max_kmh']}km/h")
        detail["vent_ok"] = vent <= contraintes["vent_max_kmh"]

    if "temp_max_c" in contraintes and tmax is not None:
        if tmax > contraintes["temp_max_c"]:
            score -= 30
            raisons_ko.append(f"Temp {tmax:.0f}°C > seuil {contraintes['temp_max_c']}°C")
        detail["temp_ok"] = tmax <= contraintes["temp_max_c"]

    if "temp_min_c" in contraintes and tmin is not None:
        if tmin < contraintes["temp_min_c"]:
            score -= 30
            raisons_ko.append(f"Temp min {tmin:.0f}°C < seuil {contraintes['temp_min_c']}°C")
        detail["temp_min_ok"] = tmin >= contraintes["temp_min_c"]

    if "humidite_max_pct" in contraintes and hum is not None:
        if hum > contraintes["humidite_max_pct"]:
            score -= 25
            raisons_ko.append(f"Humidité {hum}% > seuil {contraintes['humidite_max_pct']}%")
        detail["humidite_ok"] = hum <= contraintes["humidite_max_pct"]

    if "etp_min_mm" in contraintes:
        if etp < contraintes["etp_min_mm"]:
            score -= 20
        detail["etp_ok"] = etp >= contraintes["etp_min_mm"]

    # Pluie dans les 3 jours suivants (rémanence traitements)
    if "pluie_3j_max_mm" in contraintes and suivants:
        pluie_3j = sum(j.get("pluie_mm") or 0 for j in suivants)
        if pluie_3j > contraintes["pluie_3j_max_mm"]:
            score -= 30
            raisons_ko.append(f"Pluie 3j suivants {pluie_3j:.0f}mm > seuil")
        detail["pluie_3j_ok"] = pluie_3j <= contraintes["pluie_3j_max_mm"]

    # Pluie légère après fertilisation = favorable
    if "pluie_apres_mm" in contraintes and suivants:
        pluie_demain = suivants[0].get("pluie_mm") or 0
        if pluie_demain >= contraintes["pluie_apres_mm"]:
            score += 10  # bonus
        if "pluie_forte_max" in contraintes and pluie_demain > contraintes["pluie_forte_max"]:
            score -= 40
            raisons_ko.append("Pluie forte prévue demain (lessivage engrais)")

    score = max(0, min(100, score))

    return {
        "date":    jour.get("date"),
        "score":   score,
        "ok":      score >= 60,
        "raisons_ko": raisons_ko,
        "details": detail,
        "meteo":   {"pluie_mm": pluie, "vent_kmh": vent, "temp_max": tmax, "etp_mm": etp},
    }


def _priorite(type_activite: str, eval_result: dict) -> int:
    """1=urgent, 5=normal."""
    if type_activite in ("traitement", "recolte"):
        return 1 if eval_result["ok"] else 2
    if type_activite == "irrigation":
        return 2
    return 3


def _raison(type_activite: str, eval_result: dict) -> str:
    if not eval_result["ok"]:
        return "Conditions météo sous-optimales : " + "; ".join(eval_result.get("raisons_ko", []))
    meteo = eval_result.get("meteo", {})
    return (f"Conditions favorables : pluie {meteo.get('pluie_mm', 0):.0f}mm, "
            f"vent {meteo.get('vent_kmh', 0):.0f}km/h, "
            f"temp max {meteo.get('temp_max', '?')}°C")


def _parse_date(d) -> Optional[date]:
    if isinstance(d, date):
        return d
    try:
        return date.fromisoformat(str(d))
    except Exception:
        return None
