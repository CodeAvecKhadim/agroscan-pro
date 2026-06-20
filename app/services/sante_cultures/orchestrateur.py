"""
Orchestrateur Santé des Cultures — pipeline principal.

Coordonne :
  1. Détermination niveau de données (N1/N2/N3)
  2. Fetch indices satellitaires (cache 10j ou Sentinel Hub)
  3. Traduction indices → labels
  4. Évaluation Rules Engine (toutes catégories utiles)
  5. Calcul scores (vigueur / hydrique / fertilité / maladie / ravageur / composite)
  6. Prévision rendement
  7. Analyse économique
  8. Persistance DB + retour AnalyseSanteResponse

Appelé en background (BackgroundTask FastAPI) — le POST /analyser renvoie 202.
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.sante_cultures import (
    ScAnalyse, ScIndicesSatellitaires, StatutAnalyse,
    ScPrevisionRendement, ScAnalyseEconomique,
)
from app.models.champ import Parcelle, Cartographie
from app.models.agronomie import Culture
from app.schemas.sante_cultures import (
    AnalyseSanteRequest, AnalyseSanteResponse, AnalyseDemarreeResponse,
    ScoresDetail, IndicesResult, PrevisionRendementResult,
    AnalyseEconomiqueResult, NiveauxDisponibles, FacteurLimitant,
)
from app.services.sante_cultures.satellite_service import fetch_indices
from app.services.sante_cultures.indice_service import traduire_tous
from app.services.sante_cultures.scoring_service import (
    score_vigueur, score_hydrique, score_fertilite,
    score_risque, score_composite, score_to_etat,
)
from app.services.rules_evaluator import evaluate as re_evaluate

log = logging.getLogger(__name__)

_SATELLITE_CACHE_DAYS = 10   # TTL cache Sentinel-2 (cadence revisit)


# ── Niveau de données disponible ────────────────────────────────────────────

def determine_niveau(req: AnalyseSanteRequest) -> int:
    """Retourne le niveau 1, 2 ou 3 selon les données fournies.

    N1 : satellite + météo + Rules Engine (toujours disponible)
    N2 : + capteur 8-en-1 (pH, EC, humidité, température, NPK optionnels)
    N3 : + labo complet (azote, phosphore, potassium documentés)
    """
    if req.capteur is None:
        return 1
    cap = req.capteur
    # N3 : NPK présents (données labo complètes)
    if (cap.sol_azote is not None and
            cap.sol_phosphore is not None and
            cap.sol_potassium is not None):
        return 3
    # N2 : au moins un champ capteur renseigné
    return 2


def niveaux_disponibles(parcelle_id: int, db: Session) -> NiveauxDisponibles:
    """Évalue les niveaux de données disponibles pour une parcelle."""
    # Cache satellite : dernière analyse < 10 jours ?
    cutoff = datetime.now(timezone.utc) - timedelta(days=_SATELLITE_CACHE_DAYS)
    recent = (
        db.query(ScIndicesSatellitaires)
        .filter(
            ScIndicesSatellitaires.parcelle_id == parcelle_id,
            ScIndicesSatellitaires.date_calcul >= cutoff,
        )
        .first()
    )
    sat_cache = recent is not None

    descriptions = {
        1: "Satellite + météo + moteur de règles",
        2: "Satellite + capteur 8-en-1 + moteur de règles",
        3: "Satellite + capteur + données laboratoire",
    }
    return NiveauxDisponibles(
        parcelle_id=parcelle_id,
        niveau_max=1,         # le caller ajuste si capteur fourni
        capteur_disponible=False,
        labo_disponible=False,
        satellite_cache=sat_cache,
        description_niveau=descriptions[1],
    )


# ── Cache indices ────────────────────────────────────────────────────────────

def _check_satellite_cache(parcelle_id: int, db: Session) -> Optional[ScIndicesSatellitaires]:
    """Retourne les indices récents si en cache (<10j), sinon None."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=_SATELLITE_CACHE_DAYS)
    return (
        db.query(ScIndicesSatellitaires)
        .filter(
            ScIndicesSatellitaires.parcelle_id == parcelle_id,
            ScIndicesSatellitaires.date_calcul >= cutoff,
        )
        .order_by(ScIndicesSatellitaires.date_calcul.desc())
        .first()
    )


# ── Construction contexte Rules Engine ──────────────────────────────────────

def _build_re_context(
    req: AnalyseSanteRequest,
    parcelle: Parcelle,
    raw_indices: Dict[str, Any],
) -> Dict[str, Any]:
    """Construit le dict contexte pour rules_evaluator.evaluate()."""
    ctx: Dict[str, Any] = {
        "culture_nom":   req.culture_nom,
        "org_id":        parcelle.org_id,
        "parcelle_id":   parcelle.id,
        "zone_agro":     req.zone_agro or parcelle.zone_agro,
        "stade_actuel":  req.stade_actuel,
        "mois":          req.mois or datetime.now().month,
    }
    # Données capteur (niveau 2+)
    if req.capteur:
        cap = req.capteur
        if cap.sol_pH            is not None: ctx["sol_pH"]             = cap.sol_pH
        if cap.sol_conductivite  is not None: ctx["sol_conductivite"]   = cap.sol_conductivite
        if cap.sol_azote         is not None: ctx["sol_azote"]          = cap.sol_azote
        if cap.sol_phosphore     is not None: ctx["sol_phosphore"]      = cap.sol_phosphore
        if cap.sol_potassium     is not None: ctx["sol_potassium"]      = cap.sol_potassium
        if cap.sol_humidite      is not None: ctx["sol_humidite"]       = cap.sol_humidite
        if cap.sol_temperature   is not None: ctx["sol_temperature"]    = cap.sol_temperature
        if cap.sol_matiere_organique is not None:
            ctx["sol_matiere_organique"] = cap.sol_matiere_organique

    return ctx


# ── Pipeline principal ───────────────────────────────────────────────────────

def _run_pipeline(
    analyse_id: int,
    req: AnalyseSanteRequest,
    db: Session,
) -> None:
    """Pipeline complet exécuté en background. Met à jour sc_analyses.statut."""
    t0 = time.perf_counter()

    try:
        analyse = db.get(ScAnalyse, analyse_id)
        if not analyse:
            log.error("analyse_id %d introuvable", analyse_id)
            return

        parcelle = db.get(Parcelle, req.parcelle_id)
        if not parcelle:
            _fail(db, analyse, "Parcelle introuvable")
            return

        niveau = determine_niveau(req)
        analyse.niveau_donnees = niveau
        mois = req.mois or datetime.now().month

        # ── Étape 1 : Indices satellitaires ─────────────────────────────────
        cached = _check_satellite_cache(parcelle.id, db)
        if cached:
            raw_indices = {
                "ndvi": cached.ndvi, "ndre": cached.ndre, "savi": cached.savi,
                "evi": cached.evi, "msavi": cached.msavi, "ndwi": cached.ndwi,
                "ndmi": cached.ndmi, "biomasse": cached.biomasse,
                "couverture_nuages": cached.couverture_nuages,
                "date_image": str(cached.date_image),
                "source": "cache",
            }
            indices_db = cached
        else:
            # Récupère coordonnées depuis cartographie
            carto = (
                db.query(Cartographie)
                .filter_by(parcelle_id=parcelle.id)
                .order_by(Cartographie.created_at.desc())
                .first()
            )
            coordonnees = carto.coordonnees if carto else []
            superficie  = parcelle.superficie_ha or 1.0

            raw_indices = fetch_indices(coordonnees, superficie, mois, req.culture_nom)

            # Persiste en cache
            labels = traduire_tous(raw_indices)
            indices_db = ScIndicesSatellitaires(
                parcelle_id  = parcelle.id,
                analyse_id   = analyse_id,
                date_image   = raw_indices.get("date_image") or str(datetime.now().date()),
                satellite    = "sentinel-2",
                ndvi         = raw_indices.get("ndvi"),
                ndre         = raw_indices.get("ndre"),
                savi         = raw_indices.get("savi"),
                evi          = raw_indices.get("evi"),
                msavi        = raw_indices.get("msavi"),
                ndwi         = raw_indices.get("ndwi"),
                ndmi         = raw_indices.get("ndmi"),
                biomasse     = labels.get("biomasse"),
                couverture_nuages = raw_indices.get("couverture_nuages"),
                temperature_canopee = raw_indices.get("temperature_surface"),
                ndvi_label   = labels.get("ndvi_label"),
                ndre_label   = labels.get("ndre_label"),
                savi_label   = labels.get("savi_label"),
                evi_label    = labels.get("evi_label"),
                msavi_label  = labels.get("msavi_label"),
                ndwi_label   = labels.get("ndwi_label"),
                ndmi_label   = labels.get("ndmi_label"),
                biomasse_label = labels.get("biomasse_label"),
                expire_le    = datetime.now(timezone.utc) + timedelta(days=_SATELLITE_CACHE_DAYS),
            )
            db.add(indices_db)
            db.flush()

        # ── Étape 2 : Règles (4 catégories) ─────────────────────────────────
        re_ctx = _build_re_context(req, parcelle, raw_indices)

        re_maladie    = re_evaluate(db, re_ctx, categorie="maladie")
        re_ravageur   = re_evaluate(db, re_ctx, categorie="ravageur")
        re_irrigation = re_evaluate(db, re_ctx, categorie="irrigation")
        re_fertilisation = re_evaluate(db, re_ctx, categorie="fertilisation")

        regles_maladie     = re_maladie.get("resultats", [])
        regles_ravageur    = re_ravageur.get("resultats", [])
        regles_irrigation  = re_irrigation.get("resultats", [])
        regles_fertilisation = re_fertilisation.get("resultats", [])

        # ── Étape 3 : Scores ─────────────────────────────────────────────────
        cap = req.capteur

        s_vigueur  = score_vigueur(raw_indices.get("ndvi"), raw_indices.get("evi"))
        s_hydrique = score_hydrique(
            ndwi         = raw_indices.get("ndwi"),
            sol_humidite = cap.sol_humidite if cap else None,
            regles_irrigation = regles_irrigation,
            niveau       = niveau,
        )
        s_fertilite = score_fertilite(
            ndre           = raw_indices.get("ndre"),
            sol_azote      = cap.sol_azote if cap else None,
            sol_phosphore  = cap.sol_phosphore if cap else None,
            sol_potassium  = cap.sol_potassium if cap else None,
            regles_fertilisation = regles_fertilisation,
            niveau         = niveau,
        )
        s_maladie  = score_risque(regles_maladie)
        s_ravageur = score_risque(regles_ravageur)

        s_composite = score_composite(s_vigueur, s_hydrique, s_fertilite, s_maladie, s_ravageur)
        etat        = score_to_etat(s_composite).lower()

        # ── Étape 4 : Prévision rendement ────────────────────────────────────
        prevision = _calcul_prevision(req.culture_nom, s_composite, niveau, db)

        # ── Étape 5 : Analyse économique ─────────────────────────────────────
        economie = _calcul_economie(
            req.culture_nom,
            parcelle.superficie_ha or 1.0,
            prevision,
        )

        # ── Persistance ──────────────────────────────────────────────────────
        toutes_alertes = []
        toutes_recommandations = []
        for bloc in [re_maladie, re_ravageur, re_irrigation, re_fertilisation]:
            for r in bloc.get("resultats", []):
                toutes_alertes.extend(r.get("alertes", []))
                toutes_recommandations.extend(r.get("recommandations", []))

        nb_declenches = sum(
            len(b.get("resultats", []))
            for b in [re_maladie, re_ravageur, re_irrigation, re_fertilisation]
        )

        # Prévision DB
        prev_db = ScPrevisionRendement(
            analyse_id          = analyse_id,
            culture_id          = analyse.culture_id,
            rendement_estime    = prevision.rendement_estime,
            rendement_potentiel = prevision.rendement_potentiel,
            ecart_performance   = prevision.ecart_performance,
            facteurs_limitants  = [f.model_dump() for f in prevision.facteurs_limitants],
            confiance           = prevision.confiance,
        )
        db.add(prev_db)

        # Économie DB
        eco_db = ScAnalyseEconomique(
            analyse_id                    = analyse_id,
            superficie_ha                 = economie.superficie_ha,
            rendement_actuel_estime_t_ha  = prevision.rendement_estime,
            rendement_potentiel_t_ha      = prevision.rendement_potentiel,
            perte_volume_t_ha             = (
                (prevision.rendement_potentiel or 0) - (prevision.rendement_estime or 0)
            ),
            prix_marche_fcfa_kg           = _prix_marche(req.culture_nom),
            perte_potentielle_fcfa_ha     = economie.perte_potentielle_fcfa_ha,
            cout_correction_estime_fcfa_ha = economie.cout_correction_estime_fcfa_ha,
            gain_potentiel_fcfa_ha        = economie.gain_potentiel_fcfa_ha,
            roi_estime                    = economie.roi_estime,
        )
        db.add(eco_db)

        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        # Mise à jour analyse
        labels = traduire_tous(raw_indices)
        analyse.statut          = StatutAnalyse.TERMINE.value
        analyse.duree_ms        = elapsed_ms
        analyse.score_sante     = round(s_composite, 1)
        analyse.score_vigueur   = round(s_vigueur, 1)
        analyse.score_hydrique  = round(s_hydrique, 1)
        analyse.score_fertilite = round(s_fertilite, 1)
        analyse.score_maladie   = round(s_maladie, 1)
        analyse.score_ravageur  = round(s_ravageur, 1)
        analyse.etat_general    = etat

        # Cache résultat JSON complet pour re-lecture rapide sans recalcul
        analyse.resultat = {
            "scores": {
                "vigueur": s_vigueur, "hydrique": s_hydrique,
                "fertilite": s_fertilite, "maladie": s_maladie, "ravageur": s_ravageur,
            },
            "indices": {**labels, "date_image": raw_indices.get("date_image")},
            "alertes": toutes_alertes,
            "recommandations": toutes_recommandations,
            "regles_declenchees": nb_declenches,
        }

        db.commit()
        log.info("Analyse %d terminée — score=%.1f (%s) en %dms",
                 analyse_id, s_composite, etat, elapsed_ms)

    except Exception as exc:
        log.exception("Pipeline analyse %d erreur : %s", analyse_id, exc)
        try:
            analyse = db.get(ScAnalyse, analyse_id)
            if analyse:
                _fail(db, analyse, str(exc)[:500])
        except Exception:
            pass


def _fail(db: Session, analyse: ScAnalyse, msg: str) -> None:
    """Marque une analyse en erreur."""
    analyse.statut          = StatutAnalyse.ERREUR.value
    analyse.erreur_message  = msg
    try:
        db.commit()
    except Exception:
        db.rollback()


# ── Prévision rendement (référentiels cultures Sénégal) ─────────────────────

# Rendements potentiels (T/ha) — bassin sénégalais, conditions optimales
_RENDEMENTS_REF: Dict[str, float] = {
    "Riz":         6.0,
    "Maïs":        5.5,
    "Mil":         2.0,
    "Sorgho":      2.5,
    "Arachide":    2.0,
    "Niébé":       1.5,
    "Sésame":      1.2,
    "Coton":       2.5,
    "Manioc":     25.0,
    "Patate douce": 15.0,
    "Tomate":     30.0,
    "Oignon":     20.0,
    "Gombo":       5.0,
    "Aubergine":  10.0,
    "Piment":      5.0,
    "Chou":       20.0,
    "Laitue":     15.0,
    "Concombre":  15.0,
    "Haricot vert": 6.0,
    "Bissap":      1.0,
}
_RENDEMENT_DEFAUT = 3.0   # si culture non référencée


def _calcul_prevision(
    culture_nom: str,
    score: float,
    niveau: int,
    db: Session,
) -> PrevisionRendementResult:
    """Prévision rendement basée sur score composite + référentiel culture."""
    potentiel = _RENDEMENTS_REF.get(culture_nom, _RENDEMENT_DEFAUT)

    # Coefficient performance : score 100 → 0.95 (marge gestion), score 20 → 0.20
    coeff = max(0.20, min(0.95, score / 100 * 0.95))
    estime = round(potentiel * coeff, 2)
    ecart = round((estime - potentiel) / potentiel * 100, 1) if potentiel else 0

    # Facteurs limitants (simplifiés)
    facteurs: List[FacteurLimitant] = []
    if score < 60:
        facteurs.append(FacteurLimitant(
            facteur="Score santé insuffisant",
            impact_pct=abs(ecart),
            source="satellite",
        ))

    # Confiance croît avec le niveau de données
    confiance = {1: 0.60, 2: 0.72, 3: 0.85}.get(niveau, 0.60)

    return PrevisionRendementResult(
        rendement_estime    = estime,
        rendement_potentiel = potentiel,
        ecart_performance   = ecart,
        facteurs_limitants  = facteurs,
        confiance           = confiance,
    )


# ── Analyse économique ───────────────────────────────────────────────────────

# Prix marchés de référence (FCFA/kg) — Sénégal 2025
_PRIX_MARCHE: Dict[str, float] = {
    "Riz":          300,
    "Maïs":         150,
    "Mil":          175,
    "Sorgho":       160,
    "Arachide":     400,
    "Niébé":        400,
    "Tomate":       200,
    "Oignon":       300,
    "Pomme de terre": 350,
    "Manioc":       100,
    "Patate douce": 200,
    "Sésame":       800,
    "Coton":        265,
    "Bissap":       600,
}
_PRIX_DEFAUT = 200.0   # FCFA/kg


def _prix_marche(culture_nom: str) -> float:
    return _PRIX_MARCHE.get(culture_nom, _PRIX_DEFAUT)


def _calcul_economie(
    culture_nom: str,
    superficie_ha: float,
    prevision: PrevisionRendementResult,
) -> AnalyseEconomiqueResult:
    """ROI = (gain_potentiel - cout_correction) / cout_correction × 100."""
    prix_kg       = _prix_marche(culture_nom)
    prix_t        = prix_kg * 1000   # FCFA/T

    estime    = prevision.rendement_estime    or 0
    potentiel = prevision.rendement_potentiel or 0

    perte_vol          = max(0, potentiel - estime)
    perte_fcfa_ha      = perte_vol * prix_t
    cout_correction_ha = perte_fcfa_ha * 0.30   # hypothèse : 30% du manque à gagner
    gain_potentiel_ha  = perte_fcfa_ha

    roi = 0.0
    if cout_correction_ha > 0:
        roi = round((gain_potentiel_ha - cout_correction_ha) / cout_correction_ha * 100, 1)

    return AnalyseEconomiqueResult(
        superficie_ha                  = round(superficie_ha, 2),
        perte_potentielle_fcfa_ha      = round(perte_fcfa_ha, 0),
        cout_correction_estime_fcfa_ha = round(cout_correction_ha, 0),
        gain_potentiel_fcfa_ha         = round(gain_potentiel_ha, 0),
        roi_estime                     = roi,
    )


# ── Point d'entrée public ────────────────────────────────────────────────────

def demarrer_analyse(
    req: AnalyseSanteRequest,
    db: Session,
    org_id: int,
) -> AnalyseDemarreeResponse:
    """Crée l'enregistrement en DB + retourne immédiatement (202 Accepted).

    Le pipeline complet est exécuté via BackgroundTask dans le routeur.
    """
    # Résoudre culture_id (optionnel)
    culture = db.query(Culture).filter_by(nom=req.culture_nom).first()

    analyse = ScAnalyse(
        parcelle_id    = req.parcelle_id,
        culture_id     = culture.id if culture else None,
        org_id         = org_id,
        statut         = StatutAnalyse.EN_COURS.value,
        niveau_donnees = determine_niveau(req),
        contexte_entree = req.model_dump(exclude_none=True),
    )
    db.add(analyse)
    db.commit()
    db.refresh(analyse)

    return AnalyseDemarreeResponse(analyse_id=analyse.id)


def get_analyse_response(analyse_id: int, db: Session) -> Optional[AnalyseSanteResponse]:
    """Reconstruit l'AnalyseSanteResponse depuis la DB."""
    analyse = db.get(ScAnalyse, analyse_id)
    if not analyse:
        return None

    res = analyse.resultat or {}
    scores_raw  = res.get("scores", {})
    indices_raw = res.get("indices", {})

    # Culture nom
    culture_nom = None
    if analyse.culture_id:
        c = db.get(Culture, analyse.culture_id)
        culture_nom = c.nom if c else None
    elif analyse.contexte_entree:
        culture_nom = analyse.contexte_entree.get("culture_nom")

    # Prévision
    prevision_resp = None
    if analyse.prevision:
        prev = analyse.prevision
        prevision_resp = PrevisionRendementResult(
            rendement_estime    = prev.rendement_estime,
            rendement_potentiel = prev.rendement_potentiel,
            ecart_performance   = prev.ecart_performance,
            facteurs_limitants  = [
                FacteurLimitant(**f)
                for f in (prev.facteurs_limitants or [])
            ],
            confiance = prev.confiance,
        )

    # Économie
    eco_resp = None
    if analyse.economie:
        eco = analyse.economie
        eco_resp = AnalyseEconomiqueResult(
            superficie_ha                  = eco.superficie_ha,
            perte_potentielle_fcfa_ha      = eco.perte_potentielle_fcfa_ha,
            cout_correction_estime_fcfa_ha = eco.cout_correction_estime_fcfa_ha,
            gain_potentiel_fcfa_ha         = eco.gain_potentiel_fcfa_ha,
            roi_estime                     = eco.roi_estime,
        )

    return AnalyseSanteResponse(
        analyse_id      = analyse.id,
        statut          = analyse.statut,
        culture_evaluee = culture_nom,
        parcelle_id     = analyse.parcelle_id,
        niveau_donnees  = analyse.niveau_donnees,
        duree_ms        = analyse.duree_ms,
        erreur_message  = analyse.erreur_message,
        score_sante     = analyse.score_sante,
        etat_general    = analyse.etat_general,
        scores          = ScoresDetail(
            vigueur    = scores_raw.get("vigueur"),
            hydrique   = scores_raw.get("hydrique"),
            fertilite  = scores_raw.get("fertilite"),
            maladie    = scores_raw.get("maladie"),
            ravageur   = scores_raw.get("ravageur"),
        ) if scores_raw else None,
        indices         = IndicesResult(
            date_image           = indices_raw.get("date_image"),
            vigueur              = indices_raw.get("ndvi_label"),
            chlorophylle         = indices_raw.get("ndre_label"),
            stress_hydrique      = indices_raw.get("ndwi_label"),
            humidite_vegetation  = indices_raw.get("ndmi_label"),
            vigueur_detail       = indices_raw.get("evi_label"),
            savi_label           = indices_raw.get("savi_label"),
            msavi_label          = indices_raw.get("msavi_label"),
            biomasse             = indices_raw.get("biomasse"),
            biomasse_label       = indices_raw.get("biomasse_label"),
            couverture_nuages    = indices_raw.get("couverture_nuages"),
        ) if indices_raw else None,
        alertes             = res.get("alertes", []),
        recommandations     = res.get("recommandations", []),
        regles_declenchees  = res.get("regles_declenchees", 0),
        prevision_rendement = prevision_resp,
        analyse_economique  = eco_resp,
        analyse_le          = analyse.analyse_le,
    )
