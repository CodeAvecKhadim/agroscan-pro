"""
Router — Module MON CHAMP.
Wizard 12 étapes + CRUD parcelles/carto/sol/infra/eau + import KML/KMZ.
"""
import io
import json as _json
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import (current_user, current_subscription, enforce_parcelle_limit,
                            effective_plan, require_role)
from app.models import UserRole
from app.models import Subscription
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
    AnalyseSatelliteSolOut,
)
from app.services.geo import calcul_complet
from app.services.score_champ import calculer_score, maj_score_parcelle
from app.services.calendrier import deriver_stade
from app.services.activites import generer_activites_calendrier
from app.services.analyse_satellite_sol import analyser_sol_depuis_satellite

router = APIRouter(prefix="/api/champ", tags=["Mon Champ"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_parcelle(db: Session, parcelle_id: int, org_id: int, include_archived: bool = False) -> Parcelle:
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    if not include_archived and p.statut == StatutParcelle.ARCHIVE:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    return p


def _gen_code(db: Session, org_id: int) -> str:
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
    user: User = Depends(enforce_parcelle_limit),
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """Étape 1 du wizard — créer une nouvelle parcelle (nom + eau + irrigation)."""
    from app.services.plans import features_for
    if data.superficie_ha if hasattr(data, 'superficie_ha') else None:
        plan = effective_plan(sub)
        max_ha = features_for(plan)["max_ha_per_parcelle"]
        if max_ha is not None and data.superficie_ha > max_ha:
            from fastapi import status as http_status
            raise HTTPException(
                status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
                detail=(f"Superficie {data.superficie_ha} ha dépasse la limite de {max_ha} ha "
                        f"sur le plan {plan.value}. Passez au plan Premium."),
            )

    code = data.code_parcelle or _gen_code(db, user.org_id)
    if db.query(Parcelle).filter_by(code_parcelle=code).first():
        raise HTTPException(status_code=409, detail=f"Code parcelle '{code}' déjà utilisé.")

    stade = data.stade_culture
    if not stade and data.type_culture and data.date_semis:
        stade = deriver_stade(data.type_culture, data.date_semis)

    p = Parcelle(
        org_id=user.org_id,
        nom=data.nom,
        code_parcelle=code,
        source_eau_principale=data.source_eau_principale,
        type_irrigation=data.type_irrigation,
        type_culture=data.type_culture,
        culture_id=data.culture_id,
        zone_agro=data.zone_agro,
        region=data.region,
        localite=data.localite,
        statut=data.statut,
        description=data.description,
        date_semis=data.date_semis,
        variete=data.variete,
        stade_culture=stade,
        etape_wizard=data.etape_wizard or 1,
        wizard_complet=False,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    maj_score_parcelle(db, p)

    if p.type_culture and p.date_semis:
        generer_activites_calendrier(
            db=db, parcelle_id=p.id, org_id=p.org_id,
            culture=p.type_culture, date_semis=p.date_semis,
            created_by_id=user.id,
        )

    return p


@router.get("/parcelles", response_model=List[ParcelleSummary])
def lister_parcelles(
    statut: Optional[StatutParcelle] = Query(None),
    zone_agro: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    wizard_complet: Optional[bool] = Query(None),
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
    if wizard_complet is not None:
        q = q.filter(Parcelle.wizard_complet == wizard_complet)
    return q.order_by(Parcelle.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/parcelles/archivees", response_model=List[ParcelleSummary])
def lister_parcelles_archivees(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Liste les parcelles supprimées (archivées) de l'organisation."""
    return (
        db.query(Parcelle)
        .filter(Parcelle.org_id == user.org_id, Parcelle.statut == StatutParcelle.ARCHIVE)
        .order_by(Parcelle.deleted_at.desc())
        .offset(skip).limit(limit).all()
    )


@router.get("/parcelles/{parcelle_id}", response_model=ParcelleDetail)
def detail_parcelle(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Fiche complète d'une parcelle."""
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
    """Modifier les informations d'une parcelle (y compris étape_wizard)."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    patch = data.model_dump(exclude_none=True)

    if "stade_culture" not in patch:
        culture_apres = patch.get("type_culture", p.type_culture)
        semis_apres = patch.get("date_semis", p.date_semis)
        if culture_apres and semis_apres:
            patch["stade_culture"] = deriver_stade(culture_apres, semis_apres)

    for field, value in patch.items():
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
    """Suppression logique d'une parcelle (soft delete)."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    now = datetime.now(timezone.utc)
    p.statut = StatutParcelle.ARCHIVE
    p.deleted_at = now
    p.updated_at = now
    db.commit()


@router.post("/parcelles/{parcelle_id}/restaurer", response_model=ParcelleOut)
def restaurer_parcelle(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Restaure une parcelle archivée vers le statut ACTIVE."""
    p = _get_parcelle(db, parcelle_id, user.org_id, include_archived=True)
    if p.statut != StatutParcelle.ARCHIVE:
        raise HTTPException(status_code=400, detail="Cette parcelle n'est pas archivée.")
    p.statut = StatutParcelle.ACTIVE
    p.deleted_at = None
    p.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(p)
    return p


# ── CARTOGRAPHIE ──────────────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/cartographie", response_model=CartographieOut, status_code=201)
def ajouter_cartographie(
    parcelle_id: int,
    data: CartographieCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Étapes 4-5 du wizard — saisir le polygon GPS d'une parcelle."""
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

    geo = calcul_complet(coords)
    p.superficie_m2 = geo["superficie_m2"]
    p.superficie_ha = geo["superficie_ha"]
    p.perimetre_m = geo["perimetre_m"]
    p.centre_lat = geo["centre_lat"]
    p.centre_lon = geo["centre_lon"]
    p.updated_at = datetime.now(timezone.utc)
    # Avancer le wizard à l'étape 5 (calculs effectués)
    if p.etape_wizard and p.etape_wizard < 5:
        p.etape_wizard = 5

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
    return ajouter_cartographie(parcelle_id, data, user, db)


# ── ANALYSE SOL SATELLITE ─────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/analyse-sol-satellite",
             response_model=AnalyseSatelliteSolOut, status_code=201)
def declencher_analyse_sol_satellite(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Étape 6-7 du wizard — analyse satellite automatique du sol depuis les coordonnées GPS."""
    p = _get_parcelle(db, parcelle_id, user.org_id)

    if not p.centre_lat or not p.centre_lon:
        raise HTTPException(
            status_code=422,
            detail="Cartographie GPS requise avant l'analyse satellite du sol."
        )

    analyse = analyser_sol_depuis_satellite(
        lat=p.centre_lat,
        lon=p.centre_lon,
        zone_agro=p.zone_agro,
    )

    # Mettre à jour la région et zone agro depuis l'analyse satellite
    if not p.region and analyse["administration"]["region"] != "Région indéterminée":
        p.region = analyse["administration"]["region"]
    if not p.zone_agro and analyse.get("zone_key"):
        p.zone_agro = analyse["zone_key"]

    # Créer ou mettre à jour l'analyse sol satellite
    sol_sat = db.query(AnalyseSol).filter_by(
        parcelle_id=p.id, source_analyse="satellite"
    ).first()

    if sol_sat:
        sol_sat.analyse_satellite = analyse
        sol_sat.created_at = datetime.now(timezone.utc)
    else:
        sol_sat = AnalyseSol(
            parcelle_id=p.id,
            source_analyse="satellite",
            date_analyse=date.today(),
            analyse_satellite=analyse,
        )
        db.add(sol_sat)

    # Avancer le wizard à l'étape 7
    if p.etape_wizard and p.etape_wizard < 7:
        p.etape_wizard = 7
    p.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(sol_sat)
    maj_score_parcelle(db, p)

    return AnalyseSatelliteSolOut(
        parcelle_id=p.id,
        **{k: v for k, v in analyse.items() if k != "zone_key"},
        genere_le=datetime.now(timezone.utc),
    )


@router.get("/parcelles/{parcelle_id}/analyse-sol-satellite",
            response_model=AnalyseSatelliteSolOut)
def get_analyse_sol_satellite(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Récupérer la dernière analyse satellite du sol."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    sol_sat = db.query(AnalyseSol).filter_by(
        parcelle_id=p.id, source_analyse="satellite"
    ).order_by(AnalyseSol.created_at.desc()).first()

    if not sol_sat or not sol_sat.analyse_satellite:
        raise HTTPException(status_code=404, detail="Aucune analyse satellite du sol disponible.")

    data = sol_sat.analyse_satellite
    return AnalyseSatelliteSolOut(
        parcelle_id=p.id,
        geographie=data.get("geographie", {}),
        administration=data.get("administration", {}),
        topographie=data.get("topographie", {}),
        hydrologie=data.get("hydrologie", {}),
        risques=data.get("risques", {}),
        historique=data.get("historique", {}),
        profil_sol=data.get("profil_sol", {}),
        genere_le=sol_sat.created_at,
    )


# ── SOL ───────────────────────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/sol", response_model=AnalyseSolOut, status_code=201)
def ajouter_analyse_sol(
    parcelle_id: int,
    data: AnalyseSolCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Étape 8 du wizard (capteur 8-en-1) ou analyse laboratoire."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    sol_data = data.model_dump()
    sol = AnalyseSol(parcelle_id=p.id, **sol_data)
    db.add(sol)
    # Avancer wizard si capteur 8-en-1
    if p.etape_wizard and p.etape_wizard < 9:
        p.etape_wizard = 9
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
    p = _get_parcelle(db, parcelle_id, user.org_id)
    # Retourne la dernière analyse non-satellite en priorité, sinon satellite
    sol = (db.query(AnalyseSol)
           .filter(AnalyseSol.parcelle_id == p.id,
                   AnalyseSol.source_analyse != "satellite")
           .order_by(AnalyseSol.date_analyse.desc(), AnalyseSol.created_at.desc())
           .first())
    if not sol:
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
    p = _get_parcelle(db, parcelle_id, user.org_id)
    return (db.query(AnalyseSol)
            .filter_by(parcelle_id=p.id)
            .order_by(AnalyseSol.date_analyse.desc())
            .all())


# ── INFRASTRUCTURE ────────────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/infrastructures",
             response_model=InfrastructureOut, status_code=201)
def ajouter_infrastructure(
    parcelle_id: int,
    data: InfrastructureCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Étape 9 du wizard — ajouter une infrastructure à la parcelle."""
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


@router.post("/infrastructures/{infra_id}/photo", response_model=InfrastructureOut)
async def uploader_photo_infrastructure(
    infra_id: int,
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Upload d'une photo pour une infrastructure (étape 9)."""
    from app.services.sante.upload import save_photo
    infra = db.query(Infrastructure).filter_by(id=infra_id).first()
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructure introuvable.")
    p = db.query(Parcelle).filter_by(id=infra.parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=403, detail="Accès refusé.")
    result = await save_photo(file, "infrastructure")
    infra.photo_url = result["url"]
    db.commit()
    db.refresh(infra)
    return infra


# ── SOURCES EAU ───────────────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/sources-eau",
             response_model=SourceEauOut, status_code=201)
def ajouter_source_eau(
    parcelle_id: int,
    data: SourceEauCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    p = _get_parcelle(db, parcelle_id, user.org_id)
    eau_data = data.model_dump()
    loc = eau_data.pop("localisation", None)
    eau = SourceEau(parcelle_id=p.id, **eau_data, localisation=loc)
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


# ── IMPORT KML / KMZ ─────────────────────────────────────────────────────────

_KML_NS = {
    "kml": "http://www.opengis.net/kml/2.2",
    "kml22": "http://earth.google.com/kml/2.2",
    "kml21": "http://earth.google.com/kml/2.1",
}


def _parse_kml_bytes(kml_bytes: bytes) -> List[dict]:
    """Extrait les coordonnées GPS d'un KML sous forme [{lat, lon}, ...]."""
    root = ET.fromstring(kml_bytes)
    # Deviner le namespace
    ns = ""
    tag = root.tag
    if tag.startswith("{"):
        ns = tag[1:tag.index("}")]

    coords_text = None
    prefix = f"{{{ns}}}" if ns else ""

    for path in [
        f".//{prefix}coordinates",
        ".//coordinates",
    ]:
        el = root.find(path)
        if el is not None and el.text:
            coords_text = el.text.strip()
            break

    if not coords_text:
        raise HTTPException(status_code=422, detail="Aucune balise <coordinates> trouvée dans le fichier KML.")

    points = []
    for token in coords_text.split():
        parts = token.split(",")
        if len(parts) >= 2:
            try:
                lon, lat = float(parts[0]), float(parts[1])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    points.append({"lat": lat, "lon": lon})
            except ValueError:
                continue

    if len(points) < 3:
        raise HTTPException(status_code=422, detail=f"KML valide mais seulement {len(points)} points — minimum 3 requis pour un polygone.")

    return points


def _parse_geojson_bytes(content: bytes) -> List[dict]:
    """Extrait les coordonnées d'un GeoJSON (FeatureCollection, Feature ou Geometry)."""
    try:
        data = _json.loads(content)
    except Exception:
        raise HTTPException(status_code=422, detail="Fichier GeoJSON invalide (JSON mal formé).")

    coords_list = None

    def _extract_polygon(geom: dict) -> Optional[List]:
        gtype = geom.get("type", "")
        if gtype == "Polygon":
            rings = geom.get("coordinates", [])
            return rings[0] if rings else None
        if gtype == "MultiPolygon":
            polys = geom.get("coordinates", [])
            return polys[0][0] if polys and polys[0] else None
        if gtype == "GeometryCollection":
            for g in geom.get("geometries", []):
                r = _extract_polygon(g)
                if r:
                    return r
        return None

    gtype = data.get("type", "")
    if gtype == "FeatureCollection":
        for feat in data.get("features", []):
            geom = feat.get("geometry") or {}
            r = _extract_polygon(geom)
            if r:
                coords_list = r
                break
    elif gtype == "Feature":
        geom = data.get("geometry") or {}
        coords_list = _extract_polygon(geom)
    else:
        coords_list = _extract_polygon(data)

    if not coords_list:
        raise HTTPException(status_code=422, detail="Aucun Polygon trouvé dans le fichier GeoJSON.")

    points = []
    for c in coords_list:
        if len(c) >= 2:
            try:
                lon, lat = float(c[0]), float(c[1])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    points.append({"lat": lat, "lon": lon})
            except (TypeError, ValueError):
                continue

    if len(points) < 3:
        raise HTTPException(status_code=422, detail=f"GeoJSON valide mais seulement {len(points)} points — minimum 3 requis.")
    return points


def _extract_kml_from_kmz(content: bytes) -> bytes:
    """Extrait le premier fichier .kml d'une archive KMZ (ZIP)."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            kml_files = [n for n in zf.namelist() if n.lower().endswith(".kml")]
            if not kml_files:
                raise HTTPException(status_code=422, detail="Aucun fichier .kml trouvé dans l'archive KMZ.")
            return zf.read(kml_files[0])
    except zipfile.BadZipFile:
        raise HTTPException(status_code=422, detail="Le fichier n'est pas un KMZ valide (archive ZIP corrompue).")


@router.post("/parcelles/{parcelle_id}/import-kml", response_model=CartographieOut, status_code=201)
async def importer_kml_kmz(
    parcelle_id: int,
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Importe un fichier KML, KMZ ou GeoJSON et crée une cartographie pour la parcelle.
    Accepte : .kml, .kmz, .geojson, .json (GeoJSON).
    """
    p = _get_parcelle(db, parcelle_id, user.org_id)

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 Mo).")

    filename = (file.filename or "").lower()
    if filename.endswith(".geojson") or filename.endswith(".json"):
        coords = _parse_geojson_bytes(content)
    elif filename.endswith(".kmz"):
        coords = _parse_kml_bytes(_extract_kml_from_kmz(content))
    elif filename.endswith(".kml"):
        coords = _parse_kml_bytes(content)
    else:
        # Heuristique : JSON → GeoJSON, sinon KMZ, sinon KML
        stripped = content.strip()
        if stripped.startswith(b"{") or stripped.startswith(b"["):
            coords = _parse_geojson_bytes(content)
        else:
            try:
                kml_bytes = _extract_kml_from_kmz(content)
                coords = _parse_kml_bytes(kml_bytes)
            except HTTPException:
                coords = _parse_kml_bytes(content)

    # Désactiver ancienne cartographie
    db.query(Cartographie).filter_by(parcelle_id=p.id, actif=True).update({"actif": False})

    from app.models.champ import SourceMesure as SM, TypeGeometrie as TG
    carto = Cartographie(
        parcelle_id=p.id,
        type_geometrie=TG.POLYGON,
        coordonnees=coords,
        projection="WGS84",
        source_mesure=SM.IMPORT_FICHIER,
        date_mesure=date.today(),
        actif=True,
    )
    db.add(carto)

    geo = calcul_complet(coords)
    p.superficie_m2 = geo["superficie_m2"]
    p.superficie_ha = geo["superficie_ha"]
    p.perimetre_m = geo["perimetre_m"]
    p.centre_lat = geo["centre_lat"]
    p.centre_lon = geo["centre_lon"]
    p.updated_at = datetime.now(timezone.utc)
    if p.etape_wizard and p.etape_wizard < 5:
        p.etape_wizard = 5

    db.commit()
    db.refresh(carto)
    maj_score_parcelle(db, p)

    return _build_carto_out(carto, p)


# ── SCORE & RAPPORT ───────────────────────────────────────────────────────────

@router.get("/parcelles/{parcelle_id}/score", response_model=ScoreCompletude)
def score_completude(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    p = _get_parcelle(db, parcelle_id, user.org_id)
    return calculer_score(db, p)


@router.get("/parcelles/{parcelle_id}/rapport", response_model=RapportInitial)
def rapport_initial(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
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


# ── ACTIVATION (étape 12) ─────────────────────────────────────────────────────

@router.post("/parcelles/{parcelle_id}/finaliser", response_model=ParcelleOut)
def finaliser_parcelle(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Étape 12 — activer la parcelle après finalisation du wizard."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    p.wizard_complet = True
    p.etape_wizard = 12
    p.date_activation = datetime.now(timezone.utc)
    p.statut = StatutParcelle.ACTIVE
    p.updated_at = datetime.now(timezone.utc)
    db.commit()
    maj_score_parcelle(db, p)
    return p
