"""
Router Satellite Producteur — Phase 4.
Préfixe : /api/app/satellite

Endpoints :
  GET  /{parcelle_id}            → Dernière analyse (ou déclenchement auto si > 7j)
  POST /{parcelle_id}/analyser   → Forcer nouvelle analyse
  GET  /historique/{parcelle_id} → Historique analyses (conseiller/admin uniquement)
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user, require_profil
from app.models import User
from app.models.champ import Parcelle, Cartographie
from app.models.analyses_satellite import AnalyseSatellite
from app.services.sante_cultures.satellite_service import fetch_indices
from app.services.ndvi_message import ndvi_to_message

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/app/satellite", tags=["Satellite producteur"])

_CACHE_JOURS = 7  # durée cache analyse satellite


class AnalyseSatOut(BaseModel):
    parcelle_id: int
    date: date
    message_simple: str
    couleur: str  # vert | orange | rouge
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyseSatTechOut(AnalyseSatOut):
    ndvi_moyen: Optional[float] = None
    ndre: Optional[float] = None
    ndwi: Optional[float] = None


def _to_out(a: AnalyseSatellite) -> AnalyseSatOut:
    return AnalyseSatOut(
        parcelle_id=a.parcelle_id,
        date=a.date,
        message_simple=a.message_simple,
        couleur=a.couleur,
        source=a.source,
        created_at=a.created_at,
    )


def _run_analyse(db: Session, parcelle: Parcelle, org_id: int, lang: str = "fr") -> AnalyseSatellite:
    """Déclenche l'analyse via fetch_indices et stocke le résultat."""
    # Récupérer contour le plus récent
    carto = (
        db.query(Cartographie)
        .filter_by(parcelle_id=parcelle.id)
        .order_by(Cartographie.created_at.desc())
        .first()
    )
    coordonnees = carto.coordonnees if carto and carto.coordonnees else []

    # Fallback si pas de contour : point centre fictif
    if not coordonnees and parcelle.centre_lat and parcelle.centre_lon:
        d = 0.001
        lat, lon = parcelle.centre_lat, parcelle.centre_lon
        coordonnees = [
            {"lat": lat - d, "lon": lon - d},
            {"lat": lat + d, "lon": lon - d},
            {"lat": lat + d, "lon": lon + d},
            {"lat": lat - d, "lon": lon + d},
        ]

    mois = datetime.now(timezone.utc).month
    culture_nom = parcelle.type_culture or "culture"
    superficie_ha = float(parcelle.superficie_ha or 1.0)

    indices = fetch_indices(
        coordonnees=coordonnees,
        superficie_ha=superficie_ha,
        mois=mois,
        culture_nom=culture_nom,
    )

    ndvi = indices.get("ndvi")
    ndwi = indices.get("ndwi")
    source = indices.get("source", "sentinel-2")
    _lang = lang

    message, couleur = ndvi_to_message(ndvi, ndwi, source, lang=_lang)

    analyse = AnalyseSatellite(
        org_id=org_id,
        parcelle_id=parcelle.id,
        date=date.today(),
        ndvi_moyen=round(ndvi, 3) if ndvi is not None else None,
        ndre=round(indices.get("ndre", 0), 3) if indices.get("ndre") is not None else None,
        ndwi=round(ndwi, 3) if ndwi is not None else None,
        message_simple=message,
        couleur=couleur,
        source=source.replace("simule_fallback", "simule"),
    )
    db.add(analyse)
    db.commit()
    db.refresh(analyse)
    log.info("Analyse satellite créée parcelle=%d NDVI=%.3f source=%s", parcelle.id, ndvi or 0, source)
    return analyse


def _get_parcelle(db: Session, parcelle_id: int, org_id: int) -> Parcelle:
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    return p


@router.get("/{parcelle_id}", response_model=AnalyseSatOut)
def get_analyse(
    parcelle_id: int,
    lang: str = "fr",
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Dernière analyse satellite — déclenche si aucune récente (< 7 jours).
    lang : fr | wo | pu — langue du message producteur.
    """
    p = _get_parcelle(db, parcelle_id, user.org_id)

    seuil = date.today() - timedelta(days=_CACHE_JOURS)
    derniere = (
        db.query(AnalyseSatellite)
        .filter(
            AnalyseSatellite.parcelle_id == parcelle_id,
            AnalyseSatellite.org_id == user.org_id,
            AnalyseSatellite.date >= seuil,
        )
        .order_by(AnalyseSatellite.date.desc())
        .first()
    )

    if derniere:
        # Retraduit le message dans la langue demandée
        from app.services.ndvi_message import ndvi_to_message as _ntm
        msg, _ = _ntm(derniere.ndvi_moyen, derniere.ndwi, derniere.source or "sentinel-2", lang=lang)
        out = _to_out(derniere)
        out.message_simple = msg
        return out

    analyse = _run_analyse(db, p, user.org_id, lang=lang)
    return _to_out(analyse)


@router.post("/{parcelle_id}/analyser", response_model=AnalyseSatOut)
def forcer_analyse(
    parcelle_id: int,
    lang: str = "fr",
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Force une nouvelle analyse satellite (ignore le cache)."""
    p = _get_parcelle(db, parcelle_id, user.org_id)
    analyse = _run_analyse(db, p, user.org_id, lang=lang)
    return _to_out(analyse)


@router.get("/historique/{parcelle_id}", response_model=list[AnalyseSatTechOut])
def historique_analyse(
    parcelle_id: int,
    limit: int = 10,
    user: User = Depends(require_profil("conseiller", "admin")),
    db: Session = Depends(get_db),
):
    """Historique analyses avec valeurs NDVI/NDRE/NDWI (conseiller/admin)."""
    analyses = (
        db.query(AnalyseSatellite)
        .filter_by(parcelle_id=parcelle_id, org_id=user.org_id)
        .order_by(AnalyseSatellite.date.desc())
        .limit(limit)
        .all()
    )
    return [
        AnalyseSatTechOut(
            parcelle_id=a.parcelle_id,
            date=a.date,
            message_simple=a.message_simple,
            couleur=a.couleur,
            source=a.source,
            created_at=a.created_at,
            ndvi_moyen=float(a.ndvi_moyen) if a.ndvi_moyen else None,
            ndre=float(a.ndre) if a.ndre else None,
            ndwi=float(a.ndwi) if a.ndwi else None,
        )
        for a in analyses
    ]
