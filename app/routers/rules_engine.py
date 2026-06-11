"""
Router Rules Engine — AgroScan Pro.
Endpoints :
  POST /api/rules/evaluer              — évaluation principale
  GET  /api/rules/liste                — liste règles (toutes catégories)
  GET  /api/rules/maladies             — liste règles maladies
  GET  /api/rules/ravageurs            — liste règles ravageurs
  GET  /api/rules/fertilisation        — liste règles fertilisation
  GET  /api/rules/irrigation           — liste règles irrigation
  GET  /api/rules/meteo                — liste règles météo
  GET  /api/rules/calendrier           — liste règles calendrier cultural
  GET  /api/rules/rendement            — liste règles rendement
  GET  /api/rules/historique           — déclenchements récents
  GET  /api/rules/{code}               — détail d'une règle
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.rules_engine import RegleMoteur, RegleCulture, RegleDeclenchement
from app.schemas.rules_engine import (
    RulesContext, EvaluationResponse, RegleDeclencheeResult,
    RegleListItem, RegleDetail,
)
from app.services.rules_evaluator import evaluate

router = APIRouter(prefix="/api/rules", tags=["Rules Engine"])


# ── Helpers ────────────────────────────────────────────────────────────────

def _query_rules(
    db: Session,
    categorie: str,
    active_only: bool,
    plan: Optional[str],
    gravite: Optional[str],
    culture: Optional[str],
    skip: int,
    limit: int,
) -> list:
    q = (
        db.query(RegleMoteur)
        .options(selectinload(RegleMoteur.cultures).selectinload(RegleCulture.culture))
        .filter(RegleMoteur.categorie == categorie)
    )
    if active_only:
        q = q.filter(RegleMoteur.active == True)
    if plan:
        q = q.filter(RegleMoteur.plan_requis == plan)
    if gravite:
        q = q.filter(RegleMoteur.gravite == gravite)

    rules = q.order_by(RegleMoteur.priorite.desc()).offset(skip).limit(limit).all()

    if culture:
        rules = [r for r in rules if any(rc.culture.nom == culture for rc in r.cultures)]

    return [
        RegleListItem(
            id=r.id, code=r.code, categorie=r.categorie,
            sous_categorie=r.sous_categorie, nom=r.nom,
            gravite=r.gravite or "faible", priorite=r.priorite or 5,
            confiance=r.confiance or 0.80, plan_requis=r.plan_requis or "gratuit",
            active=r.active, nb_cultures=len(r.cultures),
        )
        for r in rules
    ]


# ── Évaluation ─────────────────────────────────────────────────────────────

@router.post("/evaluer", response_model=EvaluationResponse)
def evaluer_regles(
    context: RulesContext,
    categorie: str = Query("maladie", description="maladie | ravageur | fertilisation | irrigation | meteo | calendrier | rendement"),
    plan: str = Query("gratuit", description="gratuit | premium | cooperative"),
    persist: bool = Query(False, description="Persiste les déclenchements en base"),
    db: Session = Depends(get_db),
):
    """Évalue toutes les règles actives de la catégorie donnée contre le contexte parcelle fourni."""
    result = evaluate(
        db=db,
        context=context.model_dump(),
        categorie=categorie,
        plan=plan,
        persist=persist,
    )
    return result


# ── Liste générique ─────────────────────────────────────────────────────────

@router.get("/liste", response_model=List[RegleListItem])
def lister_regles(
    categorie: str = Query(..., description="maladie | ravageur | fertilisation | irrigation | meteo | calendrier | rendement"),
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Liste les règles d'une catégorie donnée avec filtres optionnels."""
    return _query_rules(db, categorie, active_only, plan, gravite, culture, skip, limit)


# ── Endpoints par catégorie ──────────────────────────────────────────────────

@router.get("/maladies", response_model=List[RegleListItem])
def lister_regles_maladies(
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return _query_rules(db, "maladie", active_only, plan, gravite, culture, skip, limit)


@router.get("/ravageurs", response_model=List[RegleListItem])
def lister_regles_ravageurs(
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return _query_rules(db, "ravageur", active_only, plan, gravite, culture, skip, limit)


@router.get("/fertilisation", response_model=List[RegleListItem])
def lister_regles_fertilisation(
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return _query_rules(db, "fertilisation", active_only, plan, gravite, culture, skip, limit)


@router.get("/irrigation", response_model=List[RegleListItem])
def lister_regles_irrigation(
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return _query_rules(db, "irrigation", active_only, plan, gravite, culture, skip, limit)


@router.get("/meteo", response_model=List[RegleListItem])
def lister_regles_meteo(
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return _query_rules(db, "meteo", active_only, plan, gravite, culture, skip, limit)


@router.get("/calendrier", response_model=List[RegleListItem])
def lister_regles_calendrier(
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return _query_rules(db, "calendrier", active_only, plan, gravite, culture, skip, limit)


@router.get("/rendement", response_model=List[RegleListItem])
def lister_regles_rendement(
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return _query_rules(db, "rendement", active_only, plan, gravite, culture, skip, limit)


# ── Alias de compatibilité ──────────────────────────────────────────────────

@router.get("/regles", response_model=List[RegleListItem])
def lister_regles_alias(
    categorie: str = Query(..., description="maladie | ravageur | fertilisation | irrigation | meteo | calendrier | rendement"),
    active_only: bool = Query(True),
    plan: Optional[str] = Query(None),
    gravite: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Alias de /liste pour compatibilité."""
    return _query_rules(db, categorie, active_only, plan, gravite, culture, skip, limit)


# ── Statistiques ────────────────────────────────────────────────────────────

@router.get("/stats/rapport")
def rapport_rules_engine(db: Session = Depends(get_db)):
    """Rapport complet : total règles, par catégorie, cultures couvertes."""
    from sqlalchemy import func
    from app.models.rules_engine import RegleCulture
    from app.models.agronomie import Culture

    categories = ["maladie", "ravageur", "fertilisation", "irrigation", "meteo", "calendrier", "rendement"]
    par_categorie = {}
    total = 0
    for cat in categories:
        n = db.query(RegleMoteur).filter(RegleMoteur.active == True, RegleMoteur.categorie == cat).count()
        par_categorie[cat] = n
        total += n

    # Cultures couvertes (au moins 1 règle liée)
    cultures_ids = (
        db.query(RegleCulture.culture_id)
        .join(RegleMoteur)
        .filter(RegleMoteur.active == True)
        .distinct()
        .all()
    )
    cultures_ids = [c[0] for c in cultures_ids]
    cultures_noms = [
        c.nom for c in db.query(Culture).filter(Culture.id.in_(cultures_ids)).all()
    ] if cultures_ids else []

    return {
        "total_regles": total,
        "par_categorie": par_categorie,
        "nb_cultures_couvertes": len(cultures_ids),
        "cultures_couvertes": sorted(cultures_noms),
        "objectif": "500-520 règles",
        "statut": "✓ Objectif atteint" if total >= 490 else f"En cours ({total}/500)",
    }


@router.get("/stats/culture/{culture_nom}")
def regles_par_culture(
    culture_nom: str,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Toutes les règles associées à une culture donnée."""
    from app.models.agronomie import Culture

    culture = db.query(Culture).filter_by(nom=culture_nom).first()
    if not culture:
        raise HTTPException(status_code=404, detail=f"Culture '{culture_nom}' introuvable")

    q = (
        db.query(RegleMoteur)
        .options(selectinload(RegleMoteur.cultures))
        .join(RegleCulture)
        .filter(RegleCulture.culture_id == culture.id)
    )
    if active_only:
        q = q.filter(RegleMoteur.active == True)

    rules = q.order_by(RegleMoteur.categorie, RegleMoteur.priorite.desc()).all()
    par_categorie: dict = {}
    for r in rules:
        cat = r.categorie
        if cat not in par_categorie:
            par_categorie[cat] = []
        par_categorie[cat].append({
            "code": r.code,
            "nom": r.nom,
            "gravite": r.gravite,
            "priorite": r.priorite,
        })

    return {
        "culture": culture_nom,
        "total_regles": len(rules),
        "par_categorie": par_categorie,
    }


# ── Activation/désactivation règle ─────────────────────────────────────────

@router.patch("/{code}/toggle")
def toggle_regle(
    code: str,
    active: bool = Query(..., description="True pour activer, False pour désactiver"),
    db: Session = Depends(get_db),
):
    """Active ou désactive une règle."""
    rule = db.query(RegleMoteur).filter_by(code=code).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Règle '{code}' introuvable")
    rule.active = active
    db.commit()
    return {"code": code, "active": active, "message": f"Règle {'activée' if active else 'désactivée'}"}


# ── Historique ──────────────────────────────────────────────────────────────

@router.get("/historique")
def historique_declenchements(
    org_id: int = Query(..., description="ID de l'organisation"),
    limit: int = Query(50, ge=1, le=200),
    acquitte: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Retourne les déclenchements récents pour une organisation."""
    q = (
        db.query(RegleDeclenchement)
        .filter(RegleDeclenchement.org_id == org_id)
        .order_by(RegleDeclenchement.declenche_le.desc())
    )
    if acquitte is not None:
        q = q.filter(RegleDeclenchement.acquitte == acquitte)

    items = q.limit(limit).all()
    return [
        {
            "id": d.id,
            "regle_code": d.regle.code if d.regle else None,
            "regle_nom": d.regle.nom if d.regle else None,
            "score_confiance": d.score_confiance,
            "declenche_le": d.declenche_le,
            "acquitte": d.acquitte,
            "resultat": d.resultat,
        }
        for d in items
    ]


# ── Détail (DOIT être dernier — path param attrape tout) ────────────────────

@router.get("/{code}", response_model=RegleDetail)
def detail_regle(code: str, db: Session = Depends(get_db)):
    """Retourne le détail complet d'une règle par son code."""
    r = (
        db.query(RegleMoteur)
        .options(selectinload(RegleMoteur.cultures).selectinload(RegleCulture.culture))
        .filter(RegleMoteur.code == code)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail=f"Règle '{code}' introuvable")

    return RegleDetail(
        id=r.id, code=r.code, categorie=r.categorie,
        sous_categorie=r.sous_categorie, nom=r.nom,
        description=r.description,
        gravite=r.gravite or "faible", priorite=r.priorite or 5,
        confiance=r.confiance or 0.80, plan_requis=r.plan_requis or "gratuit",
        active=r.active, nb_cultures=len(r.cultures),
        zones_applicables=r.zones_applicables,
        stades_applicables=r.stades_applicables,
        mois_applicables=r.mois_applicables,
        conditions=r.conditions,
        actions=r.actions,
        source=r.source,
        version=r.version or "1.0",
    )
