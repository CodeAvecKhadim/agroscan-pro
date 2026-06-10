"""
Router — Module MON CHAMP.
18 endpoints sur /api/champ.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.models.champ import (
    Parcelle, Cartographie, AnalyseSol, Infrastructure, SourceEau,
    StatutParcelle,
)
from app.schemas.champ import (
    ParcelleCreate, ParcelleUpdate, ParcelleOut, ParcelleSummary, ParcelleDetail,
    CartographieCreate, CartographieOut,
    AnalyseSolCreate, AnalyseSolOut,
    InfrastructureCreate, InfrastructureUpdate, InfrastructureOut,
    SourceEauCreate, SourceEauUpdate, SourceEauOut,
    ScoreCompletude, RapportInitial,
)
from app.services.geo import calcul_complet
from app.services.score_champ import calculer_score, maj_score_parcelle

router = APIRouter(prefix="/api/champ", tags=["Mon Champ"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_parcelle(db: Session, parcelle_id: int, org_id: int) -> Parcelle:
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    return p


def _gen_code(db: Session, org_id: int) -> str:
    """Génère un code unique PARC-{org_id}-{seq}."""
    count = db.query(Parcelle).filter_by(org_id=org_id).count()
    return f"PARC-{org_id:03d}-{count + 1:03d}"


def _carto_active(db: Session, parcelle_id: int) -> Optional[Cartographie]:
    return db.query(Cartographie).filter_by(parcelle_id=parcelle_id, actif=True).first()


def _sol_recent(db: Session, parcelle_id: int) -> Optional[AnalyseSol]:
    return (db.query(AnalyseSol)
            .filter_by(parcelle_id=parcelle_id)
            .order_by(AnalyseSol.date_analyse.desc(), AnalyseSol.created_at.desc())
            .first())


def _build_carto_out(carto: Cartographie, parcelle: Parcelle) -> CartographieOut:
    return CartographieOut(
        id=carto.id, parcelle_id=carto.parcelle_id,
        type_geometrie=carto.type_geometrie,
        coordonnees=carto.coordonnees,
        projection=carto.projection,
        source_mesure=carto.source_mesure,
        precision_m=carto.precision_m,
        date_mesure=carto.date_mesure,
        actif=carto.actif,
        superficie_m2=parcelle.superficie_m2,
        superficie_ha=parcelle.superficie_ha,
        perimetre_m=parcelle.perimetre_m,
        centre_lat=parcelle.centre_lat,
        centre_lon=parcelle.centre_lon,
        created_at=carto.created_at,
    )


# ── PARCELLES ─────────────────────────────────────────────────────────────────

@router.post("/parcelles", response_model=ParcelleOut, status_code=201)
def creer_parcelle(
    data: ParcelleCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Créer une nouvelle parcelle."""
    code = data.code_parcelle or _gen_code(db, user.org_id)

    # Vérifier unicité code
    if db.query(Parcelle).filter_by(code_parcelle=code).first():
        raise HTTPException(status_code=409, detail=f"Code parcelle '{code}' déjà utilisé.")

    p = Parcelle(
        org_id=user.org_id,
        nom=data.nom,
        code_parcelle=code,
        type_culture=data.type_culture,
        culture_id=data.culture_id,
        zone_agro=data.zone_agro,
        region=data.region,
        localite=data.localite,
        statut=data.statut,
        description=data.description,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    maj_score_parcelle(db, p)
    return p


@router.get("/parcelles", response_model=List[ParcelleSummary])
def lister_parcelles(
    statut: Optional[StatutParcelle] = Query(None),
    zone_agro: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Lister les parcelles de l'organisation."""
    q = db.query(Parcelle).filter(
        Parcelle.org_id == user.org_id,
        Parcelle.statut != StatutParcelle.ARCHIVE,
    )
    if statut:
        q = q.filter(Parcelle.statut == statut)
    if zone_agro:
        q = q.filter(Parcelle.zone_agro == zone_agro)
    if culture:
        q = q.filter(Parcelle.type_culture.ilike(f"%{culture}%"))
    return q.order_by(Parcelle.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/parcelles/{parcelle_id}", response_model=ParcelleDetail)
def detail_parcelle(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Fiche complète d'une parcelle avec toutes ses données."""
    p = _get_parcelle(db, parcelle_id, user.org_id)

    carto = _carto_active(db, p.id)
    sol = _sol_recent(db, p.id)
    infras = db.query(Infrastructure).filter_by(parcelle_id=p.id).all()
    eaux = db.query(SourceEau).filter_by(parcelle_id=p.id).all()

    return ParcelleDetail(
        **ParcelleOut.model_validate(p).model_dump(),
        cartographie_active=_build_carto_out(carto, p) if carto else None,
        sol_recent=AnalyseSolOut.model_validate(sol) if sol else None,
        infrastructures=[InfrastructureOut.model_validate(i) for i in infras],
        sources_eau=[SourceEauOut.model_validate(e) for e in eaux],
    )


@router.put("/parcelles/{parcelle_id}", response_model=ParcelleOut)
def modifier_parcelle(
    parcelle_id: int,
    data: ParcelleUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Modifier les informations d'une parcelle."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    p.updated_at = datetime.now(timezone.utc)
    db.commit()
    maj_score_parcelle(db, p)
    return p


@router.delete("/parcelles/{parcelle_id}", status_code=204)
def archiver_parcelle(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Archiver une parcelle (soft delete)."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    p.statut = StatutParcelle.ARCHIVE
    p.updated_at = datetime.now(timezone.utc)
    db.commit()


# ── CARTOGRAPHIE ──────────────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/cartographie", response_model=CartographieOut, status_code=201)
def ajouter_cartographie(
    parcelle_id: int,
    data: CartographieCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Saisir ou remplacer le polygon GPS d'une parcelle."""
    p = _get_parcelle(db, parcelle_id, user.org_id)

    # Désactiver ancienne cartographie active
    db.query(Cartographie).filter_by(parcelle_id=p.id, actif=True).update({"actif": False})

    coords = [c.model_dump() for c in data.coordonnees]
    carto = Cartographie(
        parcelle_id=p.id,
        type_geometrie=data.type_geometrie,
        coordonnees=coords,
        projection=data.projection,
        source_mesure=data.source_mesure,
        precision_m=data.precision_m,
        date_mesure=data.date_mesure,
        actif=True,
    )
    db.add(carto)

    # Calcul géométrique + mise à jour parcelle
    geo = calcul_complet(coords)
    p.superficie_m2 = geo["superficie_m2"]
    p.superficie_ha = geo["superficie_ha"]
    p.perimetre_m = geo["perimetre_m"]
    p.centre_lat = geo["centre_lat"]
    p.centre_lon = geo["centre_lon"]
    p.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(carto)
    maj_score_parcelle(db, p)

    return _build_carto_out(carto, p)


@router.get("/parcelles/{parcelle_id}/cartographie", response_model=CartographieOut)
def get_cartographie(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Récupérer la cartographie active + métriques calculées."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    carto = _carto_active(db, p.id)
    if not carto:
        raise HTTPException(status_code=404, detail="Aucune cartographie renseignée.")
    return _build_carto_out(carto, p)


@router.put("/parcelles/{parcelle_id}/cartographie", response_model=CartographieOut)
def mettre_a_jour_cartographie(
    parcelle_id: int,
    data: CartographieCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Remplace le polygon actif (identique à POST — route sémantique)."""
    return ajouter_cartographie(parcelle_id, data, user, db)


# ── SOL ───────────────────────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/sol", response_model=AnalyseSolOut, status_code=201)
def ajouter_analyse_sol(
    parcelle_id: int,
    data: AnalyseSolCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Enregistrer une analyse de sol."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    sol = AnalyseSol(parcelle_id=p.id, **data.model_dump())
    db.add(sol)
    db.commit()
    db.refresh(sol)
    maj_score_parcelle(db, p)
    return sol


@router.get("/parcelles/{parcelle_id}/sol", response_model=AnalyseSolOut)
def derniere_analyse_sol(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Dernière analyse de sol."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    sol = _sol_recent(db, p.id)
    if not sol:
        raise HTTPException(status_code=404, detail="Aucune analyse sol renseignée.")
    return sol


@router.get("/parcelles/{parcelle_id}/sol/historique", response_model=List[AnalyseSolOut])
def historique_sol(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Historique complet des analyses de sol."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    return (db.query(AnalyseSol)
            .filter_by(parcelle_id=p.id)
            .order_by(AnalyseSol.date_analyse.desc())
            .all())


# ── INFRASTRUCTURE ────────────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/infrastructures", response_model=InfrastructureOut, status_code=201)
def ajouter_infrastructure(
    parcelle_id: int,
    data: InfrastructureCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Ajouter une infrastructure à la parcelle."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    infra_data = data.model_dump()
    loc = infra_data.pop("localisation", None)
    infra = Infrastructure(
        parcelle_id=p.id,
        **infra_data,
        localisation=loc,
    )
    db.add(infra)
    db.commit()
    db.refresh(infra)
    maj_score_parcelle(db, p)
    return infra


@router.get("/parcelles/{parcelle_id}/infrastructures", response_model=List[InfrastructureOut])
def lister_infrastructures(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    p = _get_parcelle(db, parcelle_id, user.org_id)
    return db.query(Infrastructure).filter_by(parcelle_id=p.id).all()


@router.put("/infrastructures/{infra_id}", response_model=InfrastructureOut)
def modifier_infrastructure(
    infra_id: int,
    data: InfrastructureUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    infra = db.query(Infrastructure).filter_by(id=infra_id).first()
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure introuvable.")
    # Vérifier appartenance org
    p = db.query(Parcelle).filter_by(id=infra.parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=403, detail="Accès refusé.")
    update = data.model_dump(exclude_none=True)
    loc = update.pop("localisation", None)
    for k, v in update.items():
        setattr(infra, k, v)
    if loc is not None:
        infra.localisation = loc
    db.commit()
    db.refresh(infra)
    return infra


@router.delete("/infrastructures/{infra_id}", status_code=204)
def supprimer_infrastructure(
    infra_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    infra = db.query(Infrastructure).filter_by(id=infra_id).first()
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure introuvable.")
    p = db.query(Parcelle).filter_by(id=infra.parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=403, detail="Accès refusé.")
    db.delete(infra)
    db.commit()
    maj_score_parcelle(db, p)


# ── SOURCES EAU ───────────────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/sources-eau", response_model=SourceEauOut, status_code=201)
def ajouter_source_eau(
    parcelle_id: int,
    data: SourceEauCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Ajouter une source d'eau."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    eau_data = data.model_dump()
    loc = eau_data.pop("localisation", None)
    eau = SourceEau(
        parcelle_id=p.id,
        **eau_data,
        localisation=loc,
    )
    db.add(eau)
    db.commit()
    db.refresh(eau)
    maj_score_parcelle(db, p)
    return eau


@router.get("/parcelles/{parcelle_id}/sources-eau", response_model=List[SourceEauOut])
def lister_sources_eau(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    p = _get_parcelle(db, parcelle_id, user.org_id)
    return db.query(SourceEau).filter_by(parcelle_id=p.id).all()


@router.put("/sources-eau/{eau_id}", response_model=SourceEauOut)
def modifier_source_eau(
    eau_id: int,
    data: SourceEauUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    eau = db.query(SourceEau).filter_by(id=eau_id).first()
    if not eau:
        raise HTTPException(status_code=404, detail="Source d'eau introuvable.")
    p = db.query(Parcelle).filter_by(id=eau.parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=403, detail="Accès refusé.")
    update = data.model_dump(exclude_none=True)
    loc = update.pop("localisation", None)
    for k, v in update.items():
        setattr(eau, k, v)
    if loc is not None:
        eau.localisation = loc
    db.commit()
    db.refresh(eau)
    return eau


# ── SCORE & RAPPORT ───────────────────────────────────────────────────────────

@router.get("/parcelles/{parcelle_id}/score", response_model=ScoreCompletude)
def score_completude(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Score de complétude détaillé par dimension."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    return calculer_score(db, p)


@router.get("/parcelles/{parcelle_id}/rapport", response_model=RapportInitial)
def rapport_initial(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Rapport initial complet de la parcelle."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    carto = _carto_active(db, p.id)
    sol = _sol_recent(db, p.id)
    infras = db.query(Infrastructure).filter_by(parcelle_id=p.id).all()
    eaux = db.query(SourceEau).filter_by(parcelle_id=p.id).all()
    score = calculer_score(db, p)

    return RapportInitial(
        parcelle=ParcelleOut.model_validate(p),
        cartographie=_build_carto_out(carto, p) if carto else None,
        sol=AnalyseSolOut.model_validate(sol) if sol else None,
        infrastructures=[InfrastructureOut.model_validate(i) for i in infras],
        sources_eau=[SourceEauOut.model_validate(e) for e in eaux],
        score=score,
        genere_le=datetime.now(timezone.utc),
    )
