from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.services import credits

router = APIRouter(prefix="/api/credits", tags=["Crédits"])


@router.get("/services")
def liste_services(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT code, nom, cout_credits FROM services "
                           "WHERE actif = TRUE ORDER BY id")).mappings().all()
    return {"services": [dict(r) for r in rows]}


@router.get("/solde")
def solde(user: User = Depends(current_user), db: Session = Depends(get_db)):
    bal = credits.grant_trial_if_needed(db, user.id)
    return {"solde": bal, "historique": credits.recent_ledger(db, user.id, 10)}
