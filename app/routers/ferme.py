"""
Routes API — Module GESTION DE FERME.
Préfixe : /api/ferme
22 endpoints : activités, preuves, coûts, main-d'œuvre, journal, bilans.
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.models.ferme import (
    Activite, Preuve, Cout, MainOeuvre, JournalEntree,
    TypeActivite, StatutActivite, TypePreuve, SourcePreuve,
    CategorieCoût, TypeMainOeuvre, TypeJournal,
)
from app.schemas.ferme import (
    ActiviteCreate, ActiviteUpdate, ActiviteOut, ActiviteDetail,
    DemarrerActivite, TerminerActivite,
    PreuveOut,
    CoutCreate, CoutUpdate, CoutOut,
    MainOeuvreCreate, MainOeuvreOut,
    JournalCreate, JournalOut,
    BilanParcelle, StatsActivites,
)
from app.services.ferme.upload_preuve import save_preuve, delete_preuve
from app.services.ferme.activite import (
    demarrer_activite as svc_demarrer,
    terminer_activite as svc_terminer,
    cout_total,
)
from app.services.ferme.bilan import bilan_parcelle as svc_bilan
from app.services.ferme.journal import journal_parcelle, activites_journal

router = APIRouter(prefix="/api/ferme", tags=["Gestion de ferme"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_activite(db: Session, aid: int, org_id: int) -> Activite:
    a = (db.query(Activite)
         .options(
             selectinload(Activite.preuves),
             selectinload(Activite.couts),
             selectinload(Activite.main_oeuvre),
             selectinload(Activite.journal),
         )
         .filter_by(id=aid, org_id=org_id)
         .first())
    if not a:
        raise HTTPException(status_code=404, detail="Activité introuvable.")
    return a


def _enrich(activite: Activite, db: Session) -> dict:
    """Ajoute champs calculés à l'activité."""
    d = {c.name: getattr(activite, c.name) for c in activite.__table__.columns}
    d["cout_total_fcfa"] = cout_total(db, activite.id)
    d["nb_preuves"]      = len(activite.preuves)
    return d


# ── ACTIVITÉS ──────────────────────────────────────────────────────────────────

@router.post("/activites", response_model=ActiviteOut, status_code=201,
             summary="Planifier une activité agricole")
def creer_activite(
    data: ActiviteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = Activite(
        org_id          = user.org_id,
        parcelle_id     = data.parcelle_id,
        culture_id      = data.culture_id,
        consultation_id = data.consultation_id,
        type            = data.type,
        titre           = data.titre,
        description     = data.description,
        date_prevue     = data.date_prevue,
        stade_culture   = data.stade_culture,
        surface_traitee_ha = data.surface_traitee_ha,
        details         = data.details,
        note            = data.note,
        created_by      = user.id,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return ActiviteOut(**_enrich(a, db))


@router.get("/activites", response_model=list[ActiviteOut],
            summary="Lister les activités")
def lister_activites(
    type: TypeActivite | None = None,
    statut: StatutActivite | None = None,
    parcelle_id: int | None = None,
    culture_id: int | None = None,
    date_debut: date | None = None,
    date_fin: date | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    q = (db.query(Activite)
         .options(selectinload(Activite.preuves),
                  selectinload(Activite.couts),
                  selectinload(Activite.main_oeuvre))
         .filter_by(org_id=user.org_id))
    if type:        q = q.filter(Activite.type == type)
    if statut:      q = q.filter(Activite.statut == statut)
    if parcelle_id: q = q.filter(Activite.parcelle_id == parcelle_id)
    if culture_id:  q = q.filter(Activite.culture_id == culture_id)
    if date_debut:  q = q.filter(Activite.date_prevue >= date_debut)
    if date_fin:    q = q.filter(Activite.date_prevue <= date_fin)
    activites = q.order_by(Activite.date_prevue.desc()).offset(offset).limit(limit).all()
    return [ActiviteOut(**_enrich(a, db)) for a in activites]


@router.get("/activites/{aid}", response_model=ActiviteDetail,
            summary="Détail complet d'une activité")
def detail_activite(
    aid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = _get_activite(db, aid, user.org_id)
    base = _enrich(a, db)
    return ActiviteDetail(
        **base,
        preuves     = a.preuves,
        couts       = a.couts,
        main_oeuvre = a.main_oeuvre,
        journal     = a.journal,
    )


@router.patch("/activites/{aid}", response_model=ActiviteOut,
              summary="Modifier une activité")
def modifier_activite(
    aid: int,
    data: ActiviteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = _get_activite(db, aid, user.org_id)
    if a.statut == StatutActivite.ANNULE:
        raise HTTPException(status_code=400, detail="Activité annulée, non modifiable.")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(a, field, val)
    a.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(a)
    return ActiviteOut(**_enrich(a, db))


@router.delete("/activites/{aid}", status_code=204,
               summary="Annuler une activité")
def annuler_activite(
    aid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = _get_activite(db, aid, user.org_id)
    if a.statut == StatutActivite.TERMINE:
        raise HTTPException(status_code=400, detail="Activité terminée, impossible d'annuler.")
    a.statut     = StatutActivite.ANNULE
    a.updated_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/activites/{aid}/demarrer", response_model=ActiviteOut,
             summary="Démarrer une activité (GPS + météo)")
def demarrer(
    aid: int,
    data: DemarrerActivite,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = _get_activite(db, aid, user.org_id)
    a = svc_demarrer(db, a, data.conditions_meteo or {}, data.localisation_debut or {})
    return ActiviteOut(**_enrich(a, db))


@router.post("/activites/{aid}/terminer", response_model=ActiviteOut,
             summary="Clôturer une activité")
def terminer(
    aid: int,
    data: TerminerActivite,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = _get_activite(db, aid, user.org_id)
    a = svc_terminer(
        db, a,
        data.date_fin,
        data.duree_minutes,
        data.note,
        data.details_complementaires,
    )
    return ActiviteOut(**_enrich(a, db))


# ── PREUVES ────────────────────────────────────────────────────────────────────

@router.post("/activites/{aid}/preuves", response_model=PreuveOut, status_code=201,
             summary="Upload photo ou vidéo (≤ 3 min)")
async def upload_preuve(
    aid: int,
    source: SourcePreuve = SourcePreuve.SMARTPHONE,
    lat: float | None = None,
    lon: float | None = None,
    horodatage_terrain: datetime | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = _get_activite(db, aid, user.org_id)
    info = await save_preuve(file)

    localisation = {}
    if lat is not None and lon is not None:
        localisation = {"lat": lat, "lon": lon}

    p = Preuve(
        activite_id        = a.id,
        org_id             = user.org_id,
        type               = info["type"],
        filename           = info["filename"],
        url                = info["url"],
        taille_ko          = info.get("taille_ko"),
        source             = source,
        localisation       = localisation,
        horodatage_terrain = horodatage_terrain,
        photo_meta         = info.get("photo_meta", {}),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/activites/{aid}/preuves", response_model=list[PreuveOut],
            summary="Lister les preuves d'une activité")
def lister_preuves(
    aid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _get_activite(db, aid, user.org_id)
    return db.query(Preuve).filter_by(activite_id=aid).order_by(Preuve.uploaded_at).all()


@router.delete("/preuves/{pid}", status_code=204,
               summary="Supprimer une preuve")
def supprimer_preuve(
    pid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    p = db.query(Preuve).filter_by(id=pid, org_id=user.org_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Preuve introuvable.")
    delete_preuve(p.filename)
    db.delete(p)
    db.commit()


# ── COÛTS ──────────────────────────────────────────────────────────────────────

@router.post("/activites/{aid}/couts", response_model=CoutOut, status_code=201,
             summary="Ajouter une dépense")
def ajouter_cout(
    aid: int,
    data: CoutCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = _get_activite(db, aid, user.org_id)
    c = Cout(
        activite_id        = a.id,
        org_id             = user.org_id,
        categorie          = data.categorie,
        sous_categorie     = data.sous_categorie,
        description        = data.description,
        quantite           = data.quantite,
        unite              = data.unite,
        prix_unitaire_fcfa = data.prix_unitaire_fcfa,
        montant_total_fcfa = data.montant_total_fcfa,
        fournisseur        = data.fournisseur,
        date_achat         = data.date_achat,
        recu               = data.recu,
        note               = data.note,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/activites/{aid}/couts", response_model=list[CoutOut],
            summary="Lister les dépenses d'une activité")
def lister_couts(
    aid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _get_activite(db, aid, user.org_id)
    return db.query(Cout).filter_by(activite_id=aid).order_by(Cout.created_at).all()


@router.patch("/couts/{cid}", response_model=CoutOut,
              summary="Modifier une dépense")
def modifier_cout(
    cid: int,
    data: CoutUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    c = db.query(Cout).filter_by(id=cid, org_id=user.org_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Coût introuvable.")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(c, field, val)
    # Recalcul si quantite ou prix changé mais pas montant
    if data.montant_total_fcfa is None and c.prix_unitaire_fcfa and c.quantite:
        c.montant_total_fcfa = int(c.prix_unitaire_fcfa * c.quantite)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/couts/{cid}", status_code=204,
               summary="Supprimer une dépense")
def supprimer_cout(
    cid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    c = db.query(Cout).filter_by(id=cid, org_id=user.org_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Coût introuvable.")
    db.delete(c)
    db.commit()


# ── MAIN-D'ŒUVRE ───────────────────────────────────────────────────────────────

@router.post("/activites/{aid}/main-oeuvre", response_model=MainOeuvreOut, status_code=201,
             summary="Enregistrer de la main-d'œuvre")
def ajouter_mo(
    aid: int,
    data: MainOeuvreCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    a = _get_activite(db, aid, user.org_id)
    montant = int(data.taux_journalier_fcfa * data.duree_jours * data.nb_personnes)
    mo = MainOeuvre(
        activite_id          = a.id,
        org_id               = user.org_id,
        type                 = data.type,
        description          = data.description,
        nb_personnes         = data.nb_personnes,
        duree_jours          = data.duree_jours,
        taux_journalier_fcfa = data.taux_journalier_fcfa,
        montant_total_fcfa   = montant,
        note                 = data.note,
    )
    db.add(mo)
    db.commit()
    db.refresh(mo)
    return mo


@router.get("/activites/{aid}/main-oeuvre", response_model=list[MainOeuvreOut],
            summary="Lister la main-d'œuvre d'une activité")
def lister_mo(
    aid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _get_activite(db, aid, user.org_id)
    return db.query(MainOeuvre).filter_by(activite_id=aid).order_by(MainOeuvre.created_at).all()


# ── JOURNAL ────────────────────────────────────────────────────────────────────

@router.post("/journal", response_model=JournalOut, status_code=201,
             summary="Ajouter une entrée au journal")
def ajouter_journal(
    data: JournalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    j = JournalEntree(
        org_id      = user.org_id,
        parcelle_id = data.parcelle_id,
        activite_id = data.activite_id,
        date_entree = data.date_entree,
        type        = data.type,
        titre       = data.titre,
        contenu     = data.contenu,
        created_by  = user.id,
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


@router.get("/journal", response_model=list[JournalOut],
            summary="Journal complet de l'organisation")
def lister_journal(
    parcelle_id: int | None = None,
    type: TypeJournal | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    return journal_parcelle(db, user.org_id, parcelle_id, type.value if type else None, limit, offset)


@router.get("/parcelles/{pid}/journal", response_model=list[JournalOut],
            summary="Journal d'une parcelle")
def journal_parcelle_route(
    pid: int,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    return journal_parcelle(db, user.org_id, pid, None, limit, offset)


# ── BILANS & STATS ─────────────────────────────────────────────────────────────

@router.get("/parcelles/{pid}/bilan", response_model=BilanParcelle,
            summary="Bilan complet d'une parcelle")
def bilan_parcelle_route(
    pid: int,
    periode_debut: date | None = None,
    periode_fin: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    return svc_bilan(db, pid, user.org_id, periode_debut, periode_fin)


@router.get("/stats", response_model=StatsActivites,
            summary="Statistiques globales de la ferme")
def stats_ferme(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    from sqlalchemy import func

    activites = db.query(Activite).filter_by(org_id=user.org_id).all()
    total = len(activites)

    par_type   = {}
    par_statut = {}
    for a in activites:
        par_type[a.type.value]     = par_type.get(a.type.value, 0) + 1
        par_statut[a.statut.value] = par_statut.get(a.statut.value, 0) + 1

    # Coût total tous types
    cout_total_all = 0
    nb_preuves     = 0
    parcelles_ids  = set()
    for a in activites:
        cout_total_all += sum(c.montant_total_fcfa or 0 for c in a.couts)
        cout_total_all += sum(m.montant_total_fcfa or 0 for m in a.main_oeuvre)
        nb_preuves     += len(a.preuves)
        if a.parcelle_id:
            parcelles_ids.add(a.parcelle_id)

    return StatsActivites(
        total_activites             = total,
        par_type                    = par_type,
        par_statut                  = par_statut,
        cout_total_fcfa             = cout_total_all,
        cout_moyen_par_activite_fcfa = (cout_total_all // total) if total else 0,
        nb_parcelles_actives        = len(parcelles_ids),
        nb_preuves_total            = nb_preuves,
    )


@router.get("/calendrier", response_model=list[ActiviteOut],
            summary="Activités planifiées (vue calendrier)")
def calendrier(
    date_debut: date | None = None,
    date_fin: date | None = None,
    parcelle_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    q = (db.query(Activite)
         .options(selectinload(Activite.preuves),
                  selectinload(Activite.couts),
                  selectinload(Activite.main_oeuvre))
         .filter(
             Activite.org_id == user.org_id,
             Activite.statut.in_([StatutActivite.PLANIFIE, StatutActivite.EN_COURS]),
         ))
    if date_debut:  q = q.filter(Activite.date_prevue >= date_debut)
    if date_fin:    q = q.filter(Activite.date_prevue <= date_fin)
    if parcelle_id: q = q.filter(Activite.parcelle_id == parcelle_id)
    activites = q.order_by(Activite.date_prevue).all()
    return [ActiviteOut(**_enrich(a, db)) for a in activites]
