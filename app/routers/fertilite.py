"""
Routeur d'interprétation de la fertilité des sols.
- POST /api/fertilite/interpreter : interprète une analyse de sol de laboratoire
  (pH, CE, N, P, K, matière organique, texture) et renvoie le diagnostic complet.

Contrôle d'accès :
- soumis au même quota mensuel que les analyses (plan gratuit = 3/mois) ;
- sur le plan gratuit, on renvoie une version ALLÉGÉE (niveau + diagnostic simple
  + carences) ; le diagnostic technique détaillé et les actions chiffrées complètes
  sont réservés aux plans payants.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user, current_subscription, enforce_analysis_quota, get_usage
from app.models import User, Subscription, Analysis
from app.schemas import FertiliteIn
from app.services.plans import features_for
from app.services.fertilite import MoteurFertilite, AnalyseSol, Texture

router = APIRouter(prefix="/api/fertilite", tags=["Fertilité du sol"])
_moteur = MoteurFertilite()


def _parse_texture(val):
    if not val:
        return None
    for t in Texture:
        if t.value == val.strip().lower():
            return t
    return None


@router.post("/interpreter")
def interpreter(
    data: FertiliteIn,
    user: User = Depends(enforce_analysis_quota),       # ← quota du plan gratuit
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """Interprète une analyse de sol et renvoie le diagnostic de fertilité."""
    analyse = AnalyseSol(
        ph=data.ph, ce=data.ce, ce_unite=data.ce_unite,
        azote=data.azote, phosphore=data.phosphore, potassium=data.potassium,
        matiere_organique=data.matiere_organique, texture=_parse_texture(data.texture),
    )
    diag = _moteur.diagnostiquer(analyse).to_dict()

    # Enregistre l'analyse dans l'historique (réutilise la table Analysis).
    record = Analysis(
        org_id=user.org_id, user_id=user.id, farm_id=data.farm_id,
        culture="(analyse de sol)", region=None,
        measurements={k: v for k, v in data.model_dump().items()
                      if k not in ("farm_id",) and v is not None},
        score=diag["score_sur_100"], verdict=diag["niveau_fertilite"], advanced=False,
    )
    db.add(record)
    uc = get_usage(db, user.org_id)
    uc.analyses_count += 1
    db.commit()

    feats = features_for(sub.plan)
    if not feats["advanced_reco"]:
        # Version allégée pour le plan gratuit.
        return {
            "niveau_fertilite": diag["niveau_fertilite"],
            "score_sur_100": diag["score_sur_100"],
            "diagnostic_general": diag["diagnostic_general"],
            "carences": diag["carences"],
            "cultures_recommandees": diag["cultures_recommandees"][:3],
            "premium_requis": ["diagnostic_technique", "actions_correctives",
                               "risques", "contraintes_detaillees"],
            "avertissement": diag["avertissement"],
        }

    # Version complète (premium / coopérative).
    return diag


# ---------------------------------------------------------------------------
#  Génération du rapport PDF (réservé aux plans avec pdf_reports)
# ---------------------------------------------------------------------------
import os
import tempfile
from fastapi import Body
from fastapi.responses import FileResponse
from app.core.deps import require_feature
from app.services.rapport_pdf import RapportPDF

_pdf = RapportPDF()


@router.post("/rapport-pdf")
def rapport_pdf(
    data: FertiliteIn,
    producteur: dict = Body(default={}, embed=True),
    user: User = Depends(current_user),
    sub: Subscription = Depends(require_feature("pdf_reports")),   # ← Premium/Coop only
    db: Session = Depends(get_db),
):
    """
    Génère le rapport PDF professionnel à partir d'une analyse de sol.
    Corps attendu :
      {
        "data": { ...analyse de sol... },
        "producteur": {"nom":..., "localite":..., "region":..., "culture":...,
                       "technicien":..., "latitude":..., "longitude":..., "superficie":...}
      }
    Réservé aux plans Premium et Coopérative (fonctionnalité 'pdf_reports').
    """
    analyse = AnalyseSol(
        ph=data.ph, ce=data.ce, ce_unite=data.ce_unite,
        azote=data.azote, phosphore=data.phosphore, potassium=data.potassium,
        matiere_organique=data.matiere_organique, texture=_parse_texture(data.texture),
    )
    diag = _moteur.diagnostiquer(analyse).to_dict()

    numero = _pdf.numero_unique(user.org_id)
    out_dir = tempfile.mkdtemp(prefix="agroscan_")
    out_path = os.path.join(out_dir, f"{numero}.pdf")
    _pdf.generer(diag, producteur or {}, out_path, numero=numero, org_id=user.org_id)

    return FileResponse(out_path, media_type="application/pdf",
                        filename=f"Rapport_AgroScan_{numero}.pdf")
