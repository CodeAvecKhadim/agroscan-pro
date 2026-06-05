import json
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import current_user

router = APIRouter(prefix="/api/parcelles", tags=["parcelles"])

FREE_PARCEL_LIMIT = 2  # parcelles gratuites par utilisateur (avant abonnement)


class ParcelleIn(BaseModel):
    nom: str
    culture: Optional[str] = None
    superficie_ha: Optional[float] = None
    superficie_m2: Optional[float] = None
    centre_lat: Optional[float] = None
    centre_lng: Optional[float] = None
    contour: Optional[Any] = None
    precision_m: Optional[float] = None
    methode: Optional[str] = None


@router.post("")
def creer_parcelle(p: ParcelleIn, db: Session = Depends(get_db), user=Depends(current_user)):
    cnt = db.execute(
        text("SELECT count(*) FROM parcelles WHERE user_id=:u"), {"u": user.id}
    ).scalar() or 0
    if cnt >= FREE_PARCEL_LIMIT:
        raise HTTPException(
            status_code=402,
            detail="Limite gratuite atteinte : 2 parcelles. Pour cartographier plus de parcelles, un abonnement sera necessaire (frais a venir). Contact : +221 78 491 90 11.",
        )
    res = db.execute(
        text(
            "INSERT INTO parcelles "
            "(user_id, nom, culture, superficie_ha, superficie_m2, centre_lat, centre_lng, contour, precision_m, methode) "
            "VALUES (:user_id, :nom, :culture, :superficie_ha, :superficie_m2, :centre_lat, :centre_lng, CAST(:contour AS JSONB), :precision_m, :methode) "
            "RETURNING id"
        ),
        {
            "user_id": user.id, "nom": p.nom, "culture": p.culture,
            "superficie_ha": p.superficie_ha, "superficie_m2": p.superficie_m2,
            "centre_lat": p.centre_lat, "centre_lng": p.centre_lng,
            "contour": json.dumps(p.contour) if p.contour is not None else None,
            "precision_m": p.precision_m, "methode": p.methode,
        },
    )
    new_id = res.scalar()
    db.commit()
    return {"ok": True, "id": new_id}


@router.get("")
def lister_parcelles(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.execute(
        text(
            "SELECT id, nom, culture, superficie_ha, superficie_m2, "
            "centre_lat, centre_lng, precision_m, methode, created_at "
            "FROM parcelles WHERE user_id=:u ORDER BY created_at DESC"
        ),
        {"u": user.id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{pid}")
def lire_parcelle(pid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    r = db.execute(
        text(
            "SELECT id, nom, culture, superficie_ha, superficie_m2, "
            "centre_lat, centre_lng, contour, precision_m, methode, created_at "
            "FROM parcelles WHERE id=:id AND user_id=:u"
        ),
        {"id": pid, "u": user.id},
    ).mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")
    return dict(r)


@router.delete("/{pid}")
def supprimer_parcelle(pid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    res = db.execute(
        text("DELETE FROM parcelles WHERE id=:id AND user_id=:u"),
        {"id": pid, "u": user.id},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")
    return {"ok": True, "deleted": pid}
