"""
Router Santé des Cultures + Agriculture de Précision.
Préfixe : /api/sante-cultures

Endpoints :
  POST /analyser                    → 202 Accepted (lance background task)
  GET  /analyse/{id}                → statut + résultat complet
  GET  /analyses/{parcelle_id}      → historique analyses d'une parcelle
  GET  /carte/{analyse_id}/{type}   → GeoJSON carte de précision
  GET  /indices/{parcelle_id}       → historique indices satellitaires
  GET  /prevision/{analyse_id}      → prévision rendement
  GET  /economie/{analyse_id}       → analyse économique
  GET  /niveaux/{parcelle_id}       → niveaux données disponibles
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.models.sante_cultures import (
    ScAnalyse, ScIndicesSatellitaires, ScCartePrecision,
    ScPrevisionRendement, ScAnalyseEconomique, StatutAnalyse,
)
from app.models.champ import Parcelle, Cartographie
from app.schemas.sante_cultures import (
    AnalyseSanteRequest, AnalyseSanteResponse, AnalyseDemarreeResponse,
    AnalyseSanteResume, NiveauxDisponibles, CarteInfo, IndicesHistorique,
    PrevisionRendementResult, AnalyseEconomiqueResult, FacteurLimitant,
)
from app.services.sante_cultures.orchestrateur import (
    demarrer_analyse, get_analyse_response, _run_pipeline, determine_niveau,
    niveaux_disponibles,
)
from app.services.sante_cultures.carte_service import generer_toutes_cartes
from app.services.sante_cultures.indice_service import traduire_tous

router = APIRouter(prefix="/api/sante-cultures", tags=["Santé des cultures Pro"])


def _check_parcelle(parcelle_id: int, user: User, db: Session) -> Parcelle:
    """Vérifie que la parcelle existe et appartient à l'org de l'utilisateur."""
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.org_id == user.org_id,
    ).first()
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")
    return parcelle


def _check_analyse(analyse_id: int, user: User, db: Session) -> ScAnalyse:
    """Vérifie que l'analyse existe et appartient à l'org."""
    analyse = db.query(ScAnalyse).filter(
        ScAnalyse.id == analyse_id,
        ScAnalyse.org_id == user.org_id,
    ).first()
    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    return analyse


# ── POST /analyser ───────────────────────────────────────────────────────────

@router.post("/analyser", response_model=AnalyseDemarreeResponse, status_code=202)
def analyser(
    req: AnalyseSanteRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Lance une analyse Santé des Cultures en arrière-plan.

    Retourne immédiatement avec l'`analyse_id` (statut `en_cours`).
    Interroger GET /analyse/{id} pour le résultat.
    """
    _check_parcelle(req.parcelle_id, user, db)

    resp = demarrer_analyse(req, db, org_id=user.org_id)

    # Lance le pipeline complet en background
    background_tasks.add_task(_run_pipeline, resp.analyse_id, req, db)

    return resp


# ── GET /analyse/{id} ────────────────────────────────────────────────────────

@router.get("/analyse/{analyse_id}", response_model=AnalyseSanteResponse)
def get_analyse(
    analyse_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Retourne le résultat complet d'une analyse (polling après POST /analyser)."""
    _check_analyse(analyse_id, user, db)

    result = get_analyse_response(analyse_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    return result


# ── GET /analyses/{parcelle_id} ──────────────────────────────────────────────

@router.get("/analyses/{parcelle_id}", response_model=List[AnalyseSanteResume])
def liste_analyses(
    parcelle_id: int,
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Historique des analyses d'une parcelle, triées par date décroissante."""
    _check_parcelle(parcelle_id, user, db)

    analyses = (
        db.query(ScAnalyse)
        .filter(
            ScAnalyse.parcelle_id == parcelle_id,
            ScAnalyse.org_id == user.org_id,
        )
        .order_by(ScAnalyse.analyse_le.desc())
        .limit(limit)
        .all()
    )

    result = []
    for a in analyses:
        culture_nom = None
        if a.contexte_entree:
            culture_nom = a.contexte_entree.get("culture_nom")
        result.append(AnalyseSanteResume(
            analyse_id     = a.id,
            statut         = a.statut,
            culture_nom    = culture_nom,
            score_sante    = a.score_sante,
            etat_general   = a.etat_general,
            niveau_donnees = a.niveau_donnees,
            analyse_le     = a.analyse_le,
        ))
    return result


# ── GET /carte/{analyse_id}/{type_carte} ─────────────────────────────────────

@router.get("/carte/{analyse_id}/{type_carte}")
def get_carte(
    analyse_id: int,
    type_carte: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retourne la carte de précision GeoJSON pour une analyse.

    `type_carte` : sante | hydrique | fertilite | risques

    La carte est générée à la demande (non pré-stockée) depuis les scores
    de l'analyse. Chaque cellule a un score, un label et une couleur hex.
    """
    types_valides = {"sante", "hydrique", "fertilite", "risques"}
    if type_carte not in types_valides:
        raise HTTPException(
            status_code=400,
            detail=f"type_carte invalide. Valeurs possibles : {types_valides}",
        )

    analyse = _check_analyse(analyse_id, user, db)

    if analyse.statut != StatutAnalyse.TERMINE.value:
        raise HTTPException(
            status_code=409,
            detail=f"Analyse non terminée (statut: {analyse.statut})",
        )

    res = analyse.resultat or {}
    scores_raw = res.get("scores", {})
    scores = {
        "composite":  analyse.score_sante   or 50.0,
        "hydrique":   scores_raw.get("hydrique",  50.0),
        "fertilite":  scores_raw.get("fertilite", 50.0),
        "maladie":    scores_raw.get("maladie",   100.0),
        "ravageur":   scores_raw.get("ravageur",  100.0),
    }

    # Coordonnées depuis cartographie
    parcelle = db.get(Parcelle, analyse.parcelle_id)
    coordonnees: List[Dict] = []
    if parcelle:
        carto = (
            db.query(Cartographie)
            .filter_by(parcelle_id=parcelle.id)
            .order_by(Cartographie.created_at.desc())
            .first()
        )
        if carto:
            coordonnees = carto.coordonnees or []

    superficie = parcelle.superficie_ha or 1.0 if parcelle else 1.0
    toutes = generer_toutes_cartes(scores, coordonnees, superficie)
    return toutes.get(type_carte, {"type": "FeatureCollection", "features": []})


# ── GET /indices/{parcelle_id} ───────────────────────────────────────────────

@router.get("/indices/{parcelle_id}", response_model=List[IndicesHistorique])
def historique_indices(
    parcelle_id: int,
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Historique des indices satellitaires pour une parcelle."""
    _check_parcelle(parcelle_id, user, db)

    indices = (
        db.query(ScIndicesSatellitaires)
        .filter_by(parcelle_id=parcelle_id)
        .order_by(ScIndicesSatellitaires.date_image.desc())
        .limit(limit)
        .all()
    )

    return [
        IndicesHistorique(
            date_image        = i.date_image,
            satellite         = i.satellite or "sentinel-2",
            ndvi_label        = i.ndvi_label,
            ndre_label        = i.ndre_label,
            ndwi_label        = i.ndwi_label,
            couverture_nuages = i.couverture_nuages,
            analyse_id        = i.analyse_id,
        )
        for i in indices
    ]


# ── GET /prevision/{analyse_id} ──────────────────────────────────────────────

@router.get("/prevision/{analyse_id}", response_model=PrevisionRendementResult)
def get_prevision(
    analyse_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Prévision de rendement pour une analyse terminée."""
    analyse = _check_analyse(analyse_id, user, db)

    if not analyse.prevision:
        raise HTTPException(status_code=404, detail="Prévision non disponible")

    prev = analyse.prevision
    return PrevisionRendementResult(
        rendement_estime    = prev.rendement_estime,
        rendement_potentiel = prev.rendement_potentiel,
        ecart_performance   = prev.ecart_performance,
        facteurs_limitants  = [FacteurLimitant(**f) for f in (prev.facteurs_limitants or [])],
        confiance           = prev.confiance,
    )


# ── GET /economie/{analyse_id} ───────────────────────────────────────────────

@router.get("/economie/{analyse_id}", response_model=AnalyseEconomiqueResult)
def get_economie(
    analyse_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Analyse économique : perte potentielle, gain, ROI."""
    analyse = _check_analyse(analyse_id, user, db)

    if not analyse.economie:
        raise HTTPException(status_code=404, detail="Analyse économique non disponible")

    eco = analyse.economie
    return AnalyseEconomiqueResult(
        superficie_ha                  = eco.superficie_ha,
        perte_potentielle_fcfa_ha      = eco.perte_potentielle_fcfa_ha,
        cout_correction_estime_fcfa_ha = eco.cout_correction_estime_fcfa_ha,
        gain_potentiel_fcfa_ha         = eco.gain_potentiel_fcfa_ha,
        roi_estime                     = eco.roi_estime,
    )


# ── GET /niveaux/{parcelle_id} ───────────────────────────────────────────────

@router.get("/niveaux/{parcelle_id}", response_model=NiveauxDisponibles)
def get_niveaux(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Vérifie quels niveaux de données sont disponibles pour une parcelle.

    Permet au client de savoir s'il y a un cache satellite récent
    avant de lancer une nouvelle analyse.
    """
    _check_parcelle(parcelle_id, user, db)
    return niveaux_disponibles(parcelle_id, db)
