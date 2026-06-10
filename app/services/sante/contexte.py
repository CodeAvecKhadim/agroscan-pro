"""
Construction du contexte d'évaluation Rules Engine depuis une consultation.

Priorité (haute → basse) :
  1. Observations terrain (type=sol, type=meteo)
  2. Données Mon Champ (AnalyseSol + zone de la parcelle)
  3. Champs directs de la consultation (stade, mois, zone_agro)
"""
from sqlalchemy.orm import Session

from app.models.sante import Consultation, TypeObservation
from app.models.champ import Parcelle, AnalyseSol


def build_contexte(db: Session, consultation: Consultation) -> dict:
    """
    Construit le dict RulesContext à partir de toutes les sources disponibles.
    Retourne un dict compatible avec rules_evaluator.evaluate().
    """
    ctx: dict = {}

    # 1. Base depuis les champs directs de la consultation
    if consultation.contexte:
        ctx.update(consultation.contexte)

    # 2. Mon Champ — si parcelle liée
    if consultation.parcelle_id:
        parcelle = db.query(Parcelle).filter_by(id=consultation.parcelle_id).first()
        if parcelle:
            if parcelle.zone_agro and "zone_agro" not in ctx:
                ctx["zone_agro"] = parcelle.zone_agro
            if parcelle.culture_id and "culture_id" not in ctx:
                ctx["culture_id"] = parcelle.culture_id

            # Dernière analyse sol de la parcelle
            sol = (db.query(AnalyseSol)
                   .filter_by(parcelle_id=parcelle.id)
                   .order_by(AnalyseSol.date_analyse.desc())
                   .first())
            if sol:
                if sol.pH_eau is not None and "sol_pH" not in ctx:
                    ctx["sol_pH"] = float(sol.pH_eau)
                if sol.azote_total is not None and "sol_azote" not in ctx:
                    ctx["sol_azote"] = float(sol.azote_total)
                if sol.phosphore_assim is not None and "sol_phosphore" not in ctx:
                    ctx["sol_phosphore"] = float(sol.phosphore_assim)
                if sol.potassium_echang is not None and "sol_potassium" not in ctx:
                    ctx["sol_potassium"] = float(sol.potassium_echang)
                if sol.matiere_organique is not None and "sol_matiere_organique" not in ctx:
                    ctx["sol_matiere_organique"] = float(sol.matiere_organique)
                if sol.conductivite_ds_m is not None and "sol_conductivite" not in ctx:
                    ctx["sol_conductivite"] = float(sol.conductivite_ds_m)

    # 3. Observations terrain (priorité max — écrasent Mon Champ)
    for obs in consultation.observations:
        v = obs.valeur or {}
        if obs.type == TypeObservation.SOL:
            if "pH" in v:       ctx["sol_pH"]       = v["pH"]
            if "azote" in v:    ctx["sol_azote"]     = v["azote"]
            if "phosphore" in v: ctx["sol_phosphore"] = v["phosphore"]
            if "potassium" in v: ctx["sol_potassium"] = v["potassium"]
            if "humidite" in v:  ctx["sol_humidite"]  = v["humidite"]
            if "temperature" in v: ctx["sol_temperature"] = v["temperature"]
            if "matiere_organique" in v: ctx["sol_matiere_organique"] = v["matiere_organique"]
            if "conductivite" in v: ctx["sol_conductivite"] = v["conductivite"]

        elif obs.type == TypeObservation.METEO:
            if "temp_air" in v:    ctx["meteo_temp_air"]    = v["temp_air"]
            if "humidite_rel" in v: ctx["meteo_humidite_rel"] = v["humidite_rel"]
            if "pluie_24h" in v:   ctx["meteo_pluie_24h"]   = v["pluie_24h"]
            if "pluie_7j" in v:    ctx["meteo_pluie_7j"]    = v["meteo_pluie_7j"] if "meteo_pluie_7j" in v else v["pluie_7j"]
            if "vent" in v:        ctx["meteo_vent"]         = v["vent"]
            if "etp" in v:         ctx["meteo_etp"]          = v["etp"]

        elif obs.type == TypeObservation.SYMPTOME:
            existing = ctx.get("obs_symptomes", [])
            code = v.get("code")
            if code and code not in existing:
                existing.append(code)
            ctx["obs_symptomes"] = existing

        elif obs.type == TypeObservation.RAVAGEUR_OBSERVE:
            existing = ctx.get("obs_ravageurs", [])
            nom = v.get("nom")
            if nom and nom not in existing:
                existing.append(nom)
            ctx["obs_ravageurs"] = existing
            if "densite" in v:
                ctx["obs_densite_ravageur"] = v["densite"]

    return ctx
