"""
Routes API — Module MÉTÉO & ALERTES INTELLIGENTES.
Préfixe : /api/meteo  (20 endpoints)
"""
import time
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User, Subscription
from app.models.champ import Parcelle
from app.models.agronomie import Culture
from app.models.meteo import (
    Alerte, ConfigAlertes, ConditionMeteo, NiveauAlerte,
    Prevision, RecommandationPlan, SourceMeteo, StatutPlanificateur, TypeAlerte,
)
from app.schemas.meteo import (
    AlerteOut, AlerteResume, AnalyseRisque, ConfigAlertesOut, ConfigAlertesUpdate,
    ConditionManuelle, ConditionOut, DashboardMeteo, PlanStatutUpdate,
    PrevisionJour, PrevisionOut, RecommandationOut, ResultatGeneration,
    RisqueDetail, StatsAlertes,
)
from app.services.meteo import cache as meteo_cache
from app.services.meteo.provider import gps_pour_zone
from app.services.meteo.alertes_meteo import generer_alertes_meteo
from app.services.meteo.alertes_agrono import generer_alertes_agronomiques
from app.services.meteo.planificateur import generer_recommandations, evaluer_jour

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meteo", tags=["Météo & Alertes"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_config(db: Session, org_id: int) -> ConfigAlertes:
    cfg = db.query(ConfigAlertes).filter_by(org_id=org_id).first()
    if not cfg:
        cfg = ConfigAlertes(org_id=org_id)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _get_plan(db: Session, org_id: int) -> str:
    sub = db.query(Subscription).filter_by(org_id=org_id).first()
    return sub.plan.value if sub else "gratuit"


def _parcelles_actives(db: Session, org_id: int) -> list[Parcelle]:
    from app.models.champ import StatutParcelle
    return (db.query(Parcelle)
            .filter(Parcelle.org_id == org_id,
                    Parcelle.statut == StatutParcelle.ACTIVE)
            .all())


def _coords_parcelle(parcelle: Parcelle) -> tuple[float, float]:
    if parcelle.centre_lat and parcelle.centre_lon:
        return parcelle.centre_lat, parcelle.centre_lon
    return gps_pour_zone(parcelle.zone_agro)


def _condition_out(c: ConditionMeteo, db: Session) -> dict:
    d = {k: getattr(c, k) for k in ConditionOut.model_fields}
    return d


def _alerte_out_enrichie(a: Alerte, db: Session) -> dict:
    d = AlerteOut.model_validate(a).model_dump()
    if a.parcelle_id:
        p = db.query(Parcelle).filter_by(id=a.parcelle_id).first()
        d["parcelle_nom"] = p.nom if p else None
    if a.culture_id:
        c = db.query(Culture).filter_by(id=a.culture_id).first()
        d["culture_nom"] = c.nom if c else None
    return d


def _rec_out_enrichie(r: RecommandationPlan, db: Session) -> dict:
    d = RecommandationOut.model_validate(r).model_dump()
    if r.parcelle_id:
        p = db.query(Parcelle).filter_by(id=r.parcelle_id).first()
        d["parcelle_nom"] = p.nom if p else None
    if r.culture_id:
        c = db.query(Culture).filter_by(id=r.culture_id).first()
        d["culture_nom"] = c.nom if c else None
    return d


def _prevision_out(prev: Prevision) -> dict:
    jours = [PrevisionJour(**j) for j in (prev.donnees or [])]
    pluie_tot = sum(j.pluie_mm or 0 for j in jours)
    tmax_vals = [j.temp_max for j in jours if j.temp_max]
    return {
        "id":             prev.id,
        "parcelle_id":    prev.parcelle_id,
        "zone_agro":      prev.zone_agro,
        "horizon_jours":  prev.horizon_jours,
        "jours":          [j.model_dump() for j in jours],
        "pluie_totale_mm": round(pluie_tot, 1),
        "temp_moy_max":   round(sum(tmax_vals)/len(tmax_vals), 1) if tmax_vals else None,
        "genere_le":      prev.genere_le,
        "expire_le":      prev.expire_le,
    }


def _stats_alertes(db: Session, org_id: int) -> StatsAlertes:
    alertes = db.query(Alerte).filter_by(org_id=org_id).all()
    total = len(alertes)
    non_lues = sum(1 for a in alertes if not a.lu)
    critique = sum(1 for a in alertes if a.niveau == NiveauAlerte.CRITIQUE)
    avert    = sum(1 for a in alertes if a.niveau == NiveauAlerte.AVERTISSEMENT)
    info     = sum(1 for a in alertes if a.niveau == NiveauAlerte.INFO)
    par_type: dict[str, int] = {}
    for a in alertes:
        par_type[a.type_alerte.value] = par_type.get(a.type_alerte.value, 0) + 1
    return StatsAlertes(
        nb_total=total,
        nb_critique=critique,
        nb_avertissement=avert,
        nb_info=info,
        nb_non_lues=non_lues,
        taux_lecture_pct=round((total - non_lues) / total * 100, 1) if total else 0.0,
        par_type=par_type,
    )


# ════════════════════════════════════════════════════════════════════════════
# CONDITIONS ACTUELLES
# ════════════════════════════════════════════════════════════════════════════

@router.get("/conditions", summary="Conditions météo toutes parcelles org")
def conditions_org(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Conditions actuelles pour toutes les parcelles actives de l'org."""
    parcelles = _parcelles_actives(db, user.org_id)
    resultats = []
    for p in parcelles:
        lat, lon = _coords_parcelle(p)
        try:
            cond = meteo_cache.get_conditions(db, user.org_id, lat, lon, p.id, p.zone_agro)
            resultats.append(ConditionOut.model_validate(cond).model_dump())
        except Exception as e:
            log.warning("Conditions parcelle %d: %s", p.id, e)
    return {"parcelles": resultats, "nb": len(resultats)}


@router.get("/parcelles/{parcelle_id}/conditions", summary="Conditions d'une parcelle")
def conditions_parcelle(
    parcelle_id: int,
    force_refresh: bool = Query(False),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")
    lat, lon = _coords_parcelle(p)
    cond = meteo_cache.get_conditions(db, user.org_id, lat, lon, p.id, p.zone_agro, force_refresh)
    return ConditionOut.model_validate(cond)


@router.post("/parcelles/{parcelle_id}/conditions", summary="Injecter données capteur terrain")
def injecter_conditions(
    parcelle_id: int,
    payload: ConditionManuelle,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Override conditions depuis capteur terrain (source=capteur)."""
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")

    now = datetime.now(timezone.utc)
    existing = db.query(ConditionMeteo).filter_by(
        org_id=user.org_id, parcelle_id=parcelle_id
    ).first()

    data = payload.model_dump(exclude={"parcelle_id", "lat", "lon", "zone_agro"}, exclude_none=True)

    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        existing.source = SourceMeteo.CAPTEUR
        existing.heure_releve = now
        existing.date_releve  = now.date()
    else:
        from datetime import timedelta
        existing = ConditionMeteo(
            org_id=user.org_id,
            parcelle_id=parcelle_id,
            lat=payload.lat,
            lon=payload.lon,
            zone_agro=payload.zone_agro or p.zone_agro,
            source=SourceMeteo.CAPTEUR,
            heure_releve=now,
            date_releve=now.date(),
            expire_le=now + timedelta(hours=6),
            **data,
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return ConditionOut.model_validate(existing)


# ════════════════════════════════════════════════════════════════════════════
# PRÉVISIONS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/parcelles/{parcelle_id}/previsions", summary="Prévisions météo N jours")
def previsions_parcelle(
    parcelle_id: int,
    jours: int = Query(7, ge=1, le=16),
    force_refresh: bool = Query(False),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")
    lat, lon = _coords_parcelle(p)
    prev = meteo_cache.get_previsions(
        db, user.org_id, lat, lon, jours, p.id, p.zone_agro, force_refresh
    )
    return _prevision_out(prev)


@router.get("/zones/{zone}/previsions", summary="Prévisions par zone agro-écologique")
def previsions_zone(
    zone: str,
    jours: int = Query(7, ge=1, le=16),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    lat, lon = gps_pour_zone(zone)
    prev = meteo_cache.get_previsions(
        db, user.org_id, lat, lon, jours, None, zone
    )
    return _prevision_out(prev)


# ════════════════════════════════════════════════════════════════════════════
# ALERTES
# ════════════════════════════════════════════════════════════════════════════

@router.get("/alertes", summary="Liste alertes actives")
def liste_alertes(
    type_alerte: Optional[TypeAlerte] = None,
    niveau:      Optional[NiveauAlerte] = None,
    parcelle_id: Optional[int] = None,
    lu:          Optional[bool] = None,
    limit:       int = Query(50, le=200),
    offset:      int = 0,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    q = db.query(Alerte).filter_by(org_id=user.org_id)
    if type_alerte:
        q = q.filter(Alerte.type_alerte == type_alerte)
    if niveau:
        q = q.filter(Alerte.niveau == niveau)
    if parcelle_id is not None:
        q = q.filter(Alerte.parcelle_id == parcelle_id)
    if lu is not None:
        q = q.filter(Alerte.lu == lu)
    alertes = q.order_by(Alerte.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "alertes": [AlerteResume.model_validate(a).model_dump() for a in alertes],
        "nb": len(alertes),
    }


@router.get("/alertes/{alerte_id}", summary="Détail alerte")
def detail_alerte(
    alerte_id: int,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    a = db.query(Alerte).filter_by(id=alerte_id, org_id=user.org_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    return _alerte_out_enrichie(a, db)


@router.post("/alertes/{alerte_id}/lire", summary="Marquer alerte comme lue")
def marquer_lue(
    alerte_id: int,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    a = db.query(Alerte).filter_by(id=alerte_id, org_id=user.org_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    a.lu    = True
    a.lu_le = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.post("/alertes/{alerte_id}/action", summary="Marquer action prise")
def marquer_action(
    alerte_id: int,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    a = db.query(Alerte).filter_by(id=alerte_id, org_id=user.org_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    a.action_prise = True
    a.lu           = True
    a.lu_le        = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.delete("/alertes/{alerte_id}", status_code=204, summary="Archiver/supprimer alerte")
def supprimer_alerte(
    alerte_id: int,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    a = db.query(Alerte).filter_by(id=alerte_id, org_id=user.org_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    db.delete(a)
    db.commit()


# ════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION ALERTES
# ════════════════════════════════════════════════════════════════════════════

@router.post("/alertes/generer", summary="Générer toutes alertes (météo + agrono)")
def generer_toutes_alertes(
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    """
    Pipeline complet :
    1. Fetch météo (cache/API) pour chaque parcelle active
    2. Alertes météo (seuils pluie/vent/chaleur/sécheresse)
    3. Alertes agronomiques (Rules Engine × météo × culture)
    4. Recommandations planificateur
    """
    t0 = time.perf_counter()
    config = _get_config(db, user.org_id)
    plan   = _get_plan(db, user.org_id)
    parcelles = _parcelles_actives(db, user.org_id)

    nb_meteo = nb_agrono = nb_plan = 0
    conditions_map: dict[int, ConditionMeteo] = {}
    previsions_map: dict[int, list[dict]] = {}

    for p in parcelles:
        lat, lon = _coords_parcelle(p)
        try:
            cond = meteo_cache.get_conditions(db, user.org_id, lat, lon, p.id, p.zone_agro)
            prev = meteo_cache.get_previsions(db, user.org_id, lat, lon, 16, p.id, p.zone_agro)
            conditions_map[p.id] = cond
            previsions_map[p.id] = prev.donnees or []

            if config.alertes_meteo_actives:
                nouvelles = generer_alertes_meteo(
                    db, user.org_id, cond, prev.donnees or [],
                    config, p.id, p.culture_id,
                )
                nb_meteo += len(nouvelles)

        except Exception as e:
            log.warning("Météo parcelle %d: %s", p.id, e)

    if any([config.alertes_maladies_actives, config.alertes_ravageurs_actives,
            config.alertes_fertilisation_actives, config.alertes_irrigation_actives]):
        agrono = generer_alertes_agronomiques(
            db, user.org_id, parcelles, plan, config, conditions_map
        )
        nb_agrono = len(agrono)

    if config.alertes_planificateur_actives:
        recs = generer_recommandations(db, user.org_id, parcelles, previsions_map)
        nb_plan = len(recs)

    duree_ms = int((time.perf_counter() - t0) * 1000)
    return ResultatGeneration(
        nb_alertes_meteo=nb_meteo,
        nb_alertes_agrono=nb_agrono,
        nb_recommandations=nb_plan,
        nb_alertes_total=nb_meteo + nb_agrono,
        parcelles_analysees=len(parcelles),
        duree_ms=duree_ms,
    )


@router.post("/parcelles/{parcelle_id}/analyser", summary="Analyse risques complète d'une parcelle")
def analyser_parcelle(
    parcelle_id: int,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    """Score risque 0-100 + liste risques + recommandations pour une parcelle."""
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")

    config = _get_config(db, user.org_id)
    plan   = _get_plan(db, user.org_id)
    lat, lon = _coords_parcelle(p)

    cond = meteo_cache.get_conditions(db, user.org_id, lat, lon, p.id, p.zone_agro)
    prev = meteo_cache.get_previsions(db, user.org_id, lat, lon, 7, p.id, p.zone_agro)
    previsions = prev.donnees or []

    risques: list[RisqueDetail] = []
    recommandations: list[str] = []
    score_risque = 0

    # Alertes météo → risques
    alertes_m = generer_alertes_meteo(
        db, user.org_id, cond, previsions, config, p.id, p.culture_id
    )
    for a in alertes_m:
        niveau_score = {"critique": 40, "avertissement": 20, "info": 5}.get(a.niveau.value, 5)
        score_risque = min(100, score_risque + niveau_score)
        risques.append(RisqueDetail(
            type=a.type_alerte.value,
            niveau=a.niveau.value,
            description=a.titre,
            recommandation=a.message,
        ))

    # Alertes agrono → risques
    alertes_a = generer_alertes_agronomiques(
        db, user.org_id, [p], plan, config, {p.id: cond}
    )
    for a in alertes_a:
        niveau_score = {"critique": 30, "avertissement": 15, "info": 5}.get(a.niveau.value, 5)
        score_risque = min(100, score_risque + niveau_score)
        risques.append(RisqueDetail(
            type=a.type_alerte.value,
            niveau=a.niveau.value,
            description=a.titre,
            recommandation=a.message,
        ))
        if a.details and a.details.get("recommandations"):
            recommandations.extend(a.details["recommandations"][:2])

    culture_nom = None
    if p.culture_id:
        c = db.query(Culture).filter_by(id=p.culture_id).first()
        culture_nom = c.nom if c else None

    return AnalyseRisque(
        parcelle_id=parcelle_id,
        parcelle_nom=p.nom,
        culture_nom=culture_nom,
        score_risque=score_risque,
        risques=risques,
        recommandations=list(set(recommandations))[:10],
        conditions={
            "temp": cond.temp_actuelle,
            "humidite": cond.humidite_rel,
            "pluie_mm": cond.pluie_mm,
            "vent_kmh": cond.vent_kmh,
            "description": cond.description_fr,
        },
        genere_le=datetime.now(timezone.utc),
    )


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

@router.get("/config", summary="Config alertes org")
def get_config(
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    cfg = _get_config(db, user.org_id)
    return ConfigAlertesOut.model_validate(cfg)


@router.patch("/config", summary="Modifier config alertes")
def update_config(
    payload: ConfigAlertesUpdate,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    cfg = _get_config(db, user.org_id)

    if payload.seuils is not None:
        merged = dict(cfg.seuils or {})
        merged.update(payload.seuils)
        cfg.seuils = merged

    for field in [
        "alertes_meteo_actives", "alertes_maladies_actives",
        "alertes_ravageurs_actives", "alertes_fertilisation_actives",
        "alertes_irrigation_actives", "alertes_planificateur_actives",
        "heure_envoi_alertes",
    ]:
        val = getattr(payload, field)
        if val is not None:
            setattr(cfg, field, val)

    db.commit()
    db.refresh(cfg)
    return ConfigAlertesOut.model_validate(cfg)


# ════════════════════════════════════════════════════════════════════════════
# PLANIFICATEUR
# ════════════════════════════════════════════════════════════════════════════

@router.get("/planificateur", summary="Recommandations planificateur org")
def planificateur_org(
    statut: Optional[StatutPlanificateur] = None,
    parcelle_id: Optional[int] = None,
    limit: int = Query(20, le=100),
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    q = db.query(RecommandationPlan).filter_by(org_id=user.org_id)
    if statut:
        q = q.filter(RecommandationPlan.statut == statut)
    if parcelle_id is not None:
        q = q.filter(RecommandationPlan.parcelle_id == parcelle_id)
    recs = q.order_by(RecommandationPlan.priorite, RecommandationPlan.date_recommandee).limit(limit).all()
    return {
        "recommandations": [_rec_out_enrichie(r, db) for r in recs],
        "nb": len(recs),
    }


@router.get("/parcelles/{parcelle_id}/planificateur", summary="Recommandations d'une parcelle")
def planificateur_parcelle(
    parcelle_id: int,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")
    recs = (db.query(RecommandationPlan)
            .filter_by(org_id=user.org_id, parcelle_id=parcelle_id)
            .order_by(RecommandationPlan.priorite, RecommandationPlan.date_recommandee)
            .all())
    return {"recommandations": [_rec_out_enrichie(r, db) for r in recs], "nb": len(recs)}


@router.post("/planificateur/generer", summary="Regénérer recommandations planificateur")
def generer_planificateur(
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    parcelles = _parcelles_actives(db, user.org_id)
    previsions_map: dict[int, list[dict]] = {}

    for p in parcelles:
        lat, lon = _coords_parcelle(p)
        try:
            prev = meteo_cache.get_previsions(db, user.org_id, lat, lon, 14, p.id, p.zone_agro)
            previsions_map[p.id] = prev.donnees or []
        except Exception as e:
            log.warning("Prévisions parcelle %d: %s", p.id, e)

    recs = generer_recommandations(db, user.org_id, parcelles, previsions_map)
    return {"nb_recommandations": len(recs), "recommandations": [_rec_out_enrichie(r, db) for r in recs]}


@router.patch("/planificateur/{rec_id}/statut", summary="Changer statut recommandation")
def update_statut_plan(
    rec_id: int,
    payload: PlanStatutUpdate,
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    r = db.query(RecommandationPlan).filter_by(id=rec_id, org_id=user.org_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recommandation introuvable")
    r.statut = payload.statut
    db.commit()
    return {"ok": True, "statut": r.statut}


# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════════════

@router.get("/dashboard", summary="Dashboard météo synthèse")
def dashboard(
    user: User   = Depends(current_user),
    db: Session  = Depends(get_db),
):
    """Vue synthèse : conditions + alertes actives + recommandations top."""
    parcelles = _parcelles_actives(db, user.org_id)
    conditions_out = []

    for p in parcelles:
        lat, lon = _coords_parcelle(p)
        try:
            cond = meteo_cache.get_conditions(db, user.org_id, lat, lon, p.id, p.zone_agro)
            conditions_out.append(ConditionOut.model_validate(cond).model_dump())
        except Exception:
            pass

    alertes_actives = (db.query(Alerte)
                       .filter_by(org_id=user.org_id, lu=False)
                       .order_by(Alerte.niveau.desc(), Alerte.created_at.desc())
                       .limit(10)
                       .all())

    nb_critiques = sum(1 for a in alertes_actives if a.niveau == NiveauAlerte.CRITIQUE)

    recs_top = (db.query(RecommandationPlan)
                .filter_by(org_id=user.org_id, statut=StatutPlanificateur.RECOMMANDE)
                .order_by(RecommandationPlan.priorite, RecommandationPlan.date_recommandee)
                .limit(5)
                .all())

    stats = _stats_alertes(db, user.org_id)

    return DashboardMeteo(
        conditions_parcelles=conditions_out,
        nb_alertes_actives=len(alertes_actives),
        nb_alertes_critiques=nb_critiques,
        alertes_recentes=[AlerteResume.model_validate(a).model_dump() for a in alertes_actives],
        recommandations_top=[_rec_out_enrichie(r, db) for r in recs_top],
        stats=stats,
    )
