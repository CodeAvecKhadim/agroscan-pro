"""
Routeur Base Agronomique AgroScan Pro.
Endpoints publics (lecture seule) + routes OAD (Outil d'Aide à la Décision).

Routes :
  GET /api/agronomie/cultures               — liste avec filtres
  GET /api/agronomie/cultures/{id}          — fiche complète
  GET /api/agronomie/cultures/{id}/varietes
  GET /api/agronomie/cultures/{id}/stades
  GET /api/agronomie/cultures/{id}/calendrier
  GET /api/agronomie/cultures/{id}/nutrition
  GET /api/agronomie/cultures/{id}/eau
  GET /api/agronomie/cultures/{id}/maladies
  GET /api/agronomie/cultures/{id}/ravageurs
  GET /api/agronomie/cultures/{id}/rendement
  GET /api/agronomie/maladies               — catalogue maladies
  GET /api/agronomie/ravageurs              — catalogue ravageurs
  GET /api/agronomie/zones                  — zones agro-écologiques
  GET /api/agronomie/stade-actuel           — OAD : stade du jour
  GET /api/agronomie/recommandation         — OAD : cultures adaptées à une zone/mois
"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.agronomie import (
    Culture, Variete, BesoinEau, BesoinNutritionnel,
    StadePhenologique, CalendrierCultural, RendementReference,
    Maladie, CultureMaladie, Ravageur, CultureRavageur, RecommandationCulture,
)
from app.schemas.agronomie import (
    CultureResume, CultureDetail,
    VarieteOut, BesoinEauOut, BesoinNutritionnelOut, StadeOut,
    CalendrierOut, RendementOut, CultureMaladieOut, CultureRavageurOut,
    MaladieOut, RavageurOut, StadeActuelOut, CultureAdapteeOut, RecommandationOut,
)

router = APIRouter(prefix="/api/agronomie", tags=["Base Agronomique"])

ZONES_VALIDES = [
    "vallee_fleuve", "niayes", "bassin_arachidier",
    "senegal_oriental", "casamance", "zone_sylvopastorale",
]


def _get_culture_or_404(db: Session, culture_id: int) -> Culture:
    culture = db.query(Culture).filter(Culture.id == culture_id, Culture.actif == True).first()
    if not culture:
        raise HTTPException(status_code=404, detail="Culture introuvable.")
    return culture


# ─────────────────────────────────────────────
#  CATALOGUE CULTURES
# ─────────────────────────────────────────────

@router.get("/cultures", response_model=List[CultureResume])
def list_cultures(
    categorie: Optional[str] = Query(None, description="grandes_cultures | maraichage | arboriculture"),
    zone: Optional[str] = Query(None, description="Zone agro-écologique"),
    q: Optional[str] = Query(None, description="Recherche par nom"),
    db: Session = Depends(get_db),
):
    """Liste toutes les cultures avec filtres optionnels."""
    query = db.query(Culture).filter(Culture.actif == True)
    if categorie:
        query = query.filter(Culture.categorie == categorie)
    if q:
        query = query.filter(Culture.nom.ilike(f"%{q}%"))
    if zone:
        # Filtrer par zone via les calendriers
        query = query.join(CalendrierCultural).filter(
            CalendrierCultural.zone_agro == zone
        ).distinct()
    return query.order_by(Culture.categorie, Culture.nom).all()


@router.get("/cultures/{culture_id}", response_model=CultureDetail)
def get_culture(culture_id: int, db: Session = Depends(get_db)):
    """Fiche complète d'une culture avec toutes ses données agronomiques."""
    culture = (
        db.query(Culture)
        .options(
            selectinload(Culture.varietes),
            selectinload(Culture.parametres_climatiques),
            selectinload(Culture.besoins_eau),
            selectinload(Culture.besoins_nutritionnels),
            selectinload(Culture.stades),
            selectinload(Culture.calendriers),
            selectinload(Culture.rendements),
            selectinload(Culture.culture_maladies).selectinload(CultureMaladie.maladie),
            selectinload(Culture.culture_ravageurs).selectinload(CultureRavageur.ravageur),
            selectinload(Culture.recommandations),
        )
        .filter(Culture.id == culture_id, Culture.actif == True)
        .first()
    )
    if not culture:
        raise HTTPException(status_code=404, detail="Culture introuvable.")
    return culture


@router.get("/cultures/{culture_id}/varietes", response_model=List[VarieteOut])
def get_varietes(culture_id: int, db: Session = Depends(get_db)):
    _get_culture_or_404(db, culture_id)
    return db.query(Variete).filter(Variete.culture_id == culture_id).all()


@router.get("/cultures/{culture_id}/stades", response_model=List[StadeOut])
def get_stades(culture_id: int, db: Session = Depends(get_db)):
    _get_culture_or_404(db, culture_id)
    return (
        db.query(StadePhenologique)
        .filter(StadePhenologique.culture_id == culture_id)
        .order_by(StadePhenologique.ordre)
        .all()
    )


@router.get("/cultures/{culture_id}/calendrier", response_model=List[CalendrierOut])
def get_calendrier(
    culture_id: int,
    zone: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    _get_culture_or_404(db, culture_id)
    query = db.query(CalendrierCultural).filter(CalendrierCultural.culture_id == culture_id)
    if zone:
        query = query.filter(CalendrierCultural.zone_agro == zone)
    return query.all()


@router.get("/cultures/{culture_id}/nutrition", response_model=List[BesoinNutritionnelOut])
def get_nutrition(culture_id: int, db: Session = Depends(get_db)):
    _get_culture_or_404(db, culture_id)
    return db.query(BesoinNutritionnel).filter(BesoinNutritionnel.culture_id == culture_id).all()


@router.get("/cultures/{culture_id}/eau", response_model=List[BesoinEauOut])
def get_besoins_eau(culture_id: int, db: Session = Depends(get_db)):
    _get_culture_or_404(db, culture_id)
    return db.query(BesoinEau).filter(BesoinEau.culture_id == culture_id).all()


@router.get("/cultures/{culture_id}/maladies", response_model=List[CultureMaladieOut])
def get_maladies(culture_id: int, db: Session = Depends(get_db)):
    _get_culture_or_404(db, culture_id)
    return (
        db.query(CultureMaladie)
        .options(selectinload(CultureMaladie.maladie))
        .filter(CultureMaladie.culture_id == culture_id)
        .all()
    )


@router.get("/cultures/{culture_id}/ravageurs", response_model=List[CultureRavageurOut])
def get_ravageurs(culture_id: int, db: Session = Depends(get_db)):
    _get_culture_or_404(db, culture_id)
    return (
        db.query(CultureRavageur)
        .options(selectinload(CultureRavageur.ravageur))
        .filter(CultureRavageur.culture_id == culture_id)
        .all()
    )


@router.get("/cultures/{culture_id}/rendement", response_model=List[RendementOut])
def get_rendement(
    culture_id: int,
    zone: Optional[str] = Query(None),
    pratique: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    _get_culture_or_404(db, culture_id)
    query = db.query(RendementReference).filter(RendementReference.culture_id == culture_id)
    if zone:
        query = query.filter(RendementReference.zone_agro == zone)
    if pratique:
        query = query.filter(RendementReference.pratique == pratique)
    return query.all()


# ─────────────────────────────────────────────
#  CATALOGUES TRANSVERSAUX
# ─────────────────────────────────────────────

@router.get("/maladies", response_model=List[MaladieOut])
def list_maladies(
    type_pathogene: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Maladie)
    if type_pathogene:
        query = query.filter(Maladie.pathogene_type == type_pathogene)
    if q:
        query = query.filter(Maladie.nom.ilike(f"%{q}%"))
    return query.order_by(Maladie.nom).all()


@router.get("/maladies/{maladie_id}", response_model=MaladieOut)
def get_maladie(maladie_id: int, db: Session = Depends(get_db)):
    m = db.query(Maladie).filter(Maladie.id == maladie_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Maladie introuvable.")
    return m


@router.get("/ravageurs", response_model=List[RavageurOut])
def list_ravageurs(
    type_ravageur: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Ravageur)
    if type_ravageur:
        query = query.filter(Ravageur.type_ravageur == type_ravageur)
    if q:
        query = query.filter(Ravageur.nom.ilike(f"%{q}%"))
    return query.order_by(Ravageur.nom).all()


@router.get("/zones")
def list_zones():
    """Zones agro-écologiques du Sénégal couvertes par la base."""
    return {
        "zones": [
            {"code": "vallee_fleuve",       "label": "Vallée du Fleuve Sénégal",  "regions": ["Saint-Louis", "Matam", "Podor"]},
            {"code": "niayes",              "label": "Niayes",                    "regions": ["Dakar", "Thiès (côte)", "Saint-Louis (côte)"]},
            {"code": "bassin_arachidier",   "label": "Bassin Arachidier",         "regions": ["Kaolack", "Kaffrine", "Diourbel", "Thiès"]},
            {"code": "senegal_oriental",    "label": "Sénégal Oriental",          "regions": ["Tambacounda", "Kédougou"]},
            {"code": "casamance",           "label": "Casamance",                 "regions": ["Ziguinchor", "Sédhiou", "Kolda"]},
            {"code": "zone_sylvopastorale", "label": "Zone Sylvopastorale",       "regions": ["Louga", "Matam"]},
        ]
    }


# ─────────────────────────────────────────────
#  OAD — STADE ACTUEL
# ─────────────────────────────────────────────

@router.get("/stade-actuel", response_model=StadeActuelOut)
def stade_actuel(
    culture: str = Query(..., description="Nom de la culture (ex: Tomate)"),
    date_semis: str = Query(..., description="Date de semis ISO (ex: 2026-05-01)"),
    db: Session = Depends(get_db),
):
    """
    Calcule le stade phénologique actuel d'une culture en fonction de la date de semis.
    Retourne une phrase simple pour le producteur + les actions urgentes du moment.
    """
    try:
        semis = date.fromisoformat(date_semis)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utiliser YYYY-MM-DD.")

    aujourd_hui = date.today()
    jours = (aujourd_hui - semis).days

    if jours < 0:
        raise HTTPException(status_code=400, detail="La date de semis ne peut pas être dans le futur.")

    # Chercher la culture
    c = db.query(Culture).filter(func.lower(Culture.nom) == culture.lower().strip()).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Culture '{culture}' introuvable dans la base.")

    stades = (
        db.query(StadePhenologique)
        .filter(StadePhenologique.culture_id == c.id)
        .order_by(StadePhenologique.ordre)
        .all()
    )
    if not stades:
        raise HTTPException(status_code=404, detail="Stades phénologiques non disponibles pour cette culture.")

    stade_actuel = None
    stade_suivant = None
    jours_restants = None

    for i, s in enumerate(stades):
        debut = s.jours_debut or 0
        fin   = s.jours_fin   or 9999
        if debut <= jours <= fin:
            stade_actuel = s
            if i + 1 < len(stades):
                stade_suivant = stades[i + 1]
                jours_restants = max(0, fin - jours)
            break

    # Si après le dernier stade → récolte dépassée
    if stade_actuel is None:
        dernier = stades[-1]
        if jours > (dernier.jours_fin or 0):
            return StadeActuelOut(
                culture=c.nom,
                date_semis=date_semis,
                jours_depuis_semis=jours,
                stade_actuel="Récolte / Post-récolte",
                stade_suivant=None,
                jours_restants_stade=None,
                actions_urgentes=["Effectuer la récolte si ce n'est pas fait", "Préparer le stockage"],
                message_producteur="Votre culture est arrivée à maturité. Il est temps de récolter.",
            )
        # Avant le premier stade
        stade_actuel = stades[0]
        jours_restants = (stades[0].jours_debut or 0) - jours

    actions = stade_actuel.actions_cles or []
    message = _message_simple(stade_actuel.nom_stade, c.nom, jours_restants)

    return StadeActuelOut(
        culture=c.nom,
        date_semis=date_semis,
        jours_depuis_semis=jours,
        stade_actuel=stade_actuel.nom_stade,
        stade_suivant=stade_suivant.nom_stade if stade_suivant else None,
        jours_restants_stade=jours_restants,
        actions_urgentes=actions,
        message_producteur=message,
    )


def _message_simple(stade: str, culture: str, jours_restants: Optional[int]) -> str:
    """Traduit un stade technique en phrase simple pour le producteur."""
    s = stade.lower()
    r = f" (encore ~{jours_restants} jours)" if jours_restants else ""
    if "semis" in s or "germination" in s:
        return f"Votre {culture} vient d'être semé{r}. Assurez une bonne humidité du sol."
    if "levée" in s or "emergence" in s:
        return f"Vos plants de {culture} lèvent{r}. Surveillez les mauvaises herbes et l'humidité."
    if "tallage" in s or "croissance" in s or "végétat" in s:
        return f"Votre {culture} est en pleine croissance{r}. Fertilisez et irriguez régulièrement."
    if "floraison" in s or "montaison" in s:
        return f"Votre {culture} est en floraison{r}. Période critique : protégez des ravageurs."
    if "fructification" in s or "remplissage" in s or "grossissement" in s:
        return f"Les fruits de votre {culture} se forment{r}. Maintenez l'irrigation."
    if "maturation" in s or "maturité" in s:
        return f"Votre {culture} approche de la récolte{r}. Réduisez l'irrigation progressivement."
    if "récolte" in s:
        return f"Il est temps de récolter votre {culture}. Ne tardez pas pour éviter les pertes."
    return f"Votre {culture} est au stade {stade}{r}. Suivez les recommandations AgroScan."


# ─────────────────────────────────────────────
#  OAD — RECOMMANDATION CULTURES ADAPTÉES
# ─────────────────────────────────────────────

@router.get("/recommandation", response_model=List[CultureAdapteeOut])
def recommandation_cultures(
    zone: str = Query(..., description="Zone agro-écologique"),
    mois: int = Query(..., ge=1, le=12, description="Mois de semis souhaité (1-12)"),
    categorie: Optional[str] = Query(None, description="Filtrer par catégorie"),
    db: Session = Depends(get_db),
):
    """
    Recommande les cultures adaptées à une zone et un mois de semis donné.
    Retourne les cultures triées par score d'adaptation décroissant.
    """
    if zone not in ZONES_VALIDES:
        raise HTTPException(
            status_code=400,
            detail=f"Zone invalide. Zones valides : {', '.join(ZONES_VALIDES)}"
        )

    # Cultures ayant un calendrier pour cette zone avec semis compatible
    query = (
        db.query(Culture, CalendrierCultural)
        .join(CalendrierCultural)
        .filter(
            CalendrierCultural.zone_agro == zone,
            CalendrierCultural.mois_semis_debut <= mois,
            CalendrierCultural.mois_semis_fin >= mois,
            Culture.actif == True,
        )
    )
    if categorie:
        query = query.filter(Culture.categorie == categorie)

    resultats = query.all()
    if not resultats:
        return []

    out = []
    for culture, calendrier in resultats:
        # Score simplifié : toujours adapté si dans le calendrier
        score = 85
        raisons = [
            f"Culture adaptée à la zone {zone.replace('_', ' ')}",
            f"Période de semis : mois {calendrier.mois_semis_debut} à {calendrier.mois_semis_fin}",
        ]
        if calendrier.remarques:
            raisons.append(calendrier.remarques)

        # Rendement attendu
        rendement = db.query(RendementReference).filter(
            RendementReference.culture_id == culture.id,
            RendementReference.pratique == "amelioree",
        ).first()
        rdt_txt = None
        if rendement:
            rdt_txt = f"{rendement.rendement_moyen_t_ha} t/ha (pratique améliorée)"

        out.append(CultureAdapteeOut(
            culture=CultureResume.model_validate(culture),
            score_adaptation=score,
            raisons=raisons,
            periode_semis=f"Mois {calendrier.mois_semis_debut} à {calendrier.mois_semis_fin}",
            rendement_attendu=rdt_txt,
        ))

    return sorted(out, key=lambda x: x.score_adaptation, reverse=True)
