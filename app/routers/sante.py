"""
Routes API — Module SANTÉ DES CULTURES.
Préfixe : /api/sante
20 endpoints : consultations, observations, photos, analyse,
               diagnostics, traitements, suivis, référentiel, stats.
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.models.agronomie import Maladie, CultureMaladie, Ravageur, CultureRavageur
from app.models.sante import (
    Consultation, Observation, PhotoConsultation, Diagnostic,
    Traitement, Suivi, RapportSante,
    TypeConsultation, StatutConsultation, StatutDiagnostic, StatutTraitement,
    SourcePhoto,
)
from app.schemas.sante import (
    ConsultationCreate, ConsultationUpdate, ConsultationOut, ConsultationDetail,
    ObservationCreate, ObservationOut,
    PhotoOut,
    DiagnosticOut, DiagnosticConfirm,
    TraitementOut, TraitementAppliquer, TraitementSkip,
    SuiviCreate, SuiviOut,
    RapportOut,
    AnalyseResult,
    FicheMaladie, FicheRavageur,
    StatsConsultations, StatEntite,
)
from app.services.sante.upload import save_photo
from app.services.sante.diagnostic_maladies import analyser_maladies
from app.services.sante.diagnostic_ravageurs import analyser_ravageurs
from app.services.sante.fertilisation import analyser_fertilisation
from app.services.sante.plan_traitement import generer_plan
from app.services.rules_evaluator import evaluate
from app.services.sante.contexte import build_contexte

router = APIRouter(prefix="/api/sante", tags=["Santé des cultures"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_consultation(db: Session, cid: int, org_id: int) -> Consultation:
    c = (db.query(Consultation)
         .options(
             selectinload(Consultation.observations),
             selectinload(Consultation.photos),
             selectinload(Consultation.diagnostics),
             selectinload(Consultation.traitements),
             selectinload(Consultation.suivis),
         )
         .filter_by(id=cid, org_id=org_id)
         .first())
    if not c:
        raise HTTPException(404, "Consultation introuvable.")
    return c


def _type_upload(type_consultation: TypeConsultation) -> str:
    return {
        TypeConsultation.MALADIE:       "maladie",
        TypeConsultation.RAVAGEUR:      "ravageur",
        TypeConsultation.FERTILISATION: "maladie",
    }.get(type_consultation, "maladie")


def _resume_auto(type_c: TypeConsultation, diagnostics: list[dict]) -> str:
    if not diagnostics:
        return "Aucun diagnostic établi. Ajouter des observations pour affiner l'analyse."
    top = diagnostics[0]
    pct = round(top["score_confiance"] * 100)
    if type_c == TypeConsultation.MALADIE:
        return (f"Maladie probable : {top['entite_nom']} (confiance {pct}%). "
                f"Consultez le plan de traitement et surveillez l'évolution.")
    if type_c == TypeConsultation.RAVAGEUR:
        return (f"Ravageur probable : {top['entite_nom']} (confiance {pct}%). "
                f"Appliquer les mesures de lutte recommandées.")
    return (f"Carence probable : {top['entite_nom']} (confiance {pct}%). "
            f"Suivre le plan de correction fertilisation.")


# ── CONSULTATIONS ──────────────────────────────────────────────────────────────

@router.post("/consultations", response_model=ConsultationOut, status_code=201,
             summary="Créer une consultation")
def creer_consultation(
    data: ConsultationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    ctx = {}
    if data.stade_actuel:  ctx["stade_actuel"] = data.stade_actuel
    if data.mois:          ctx["mois"]          = data.mois
    if data.zone_agro:     ctx["zone_agro"]     = data.zone_agro
    if data.culture_id:    ctx["culture_id"]    = data.culture_id

    c = Consultation(
        org_id      = user.org_id,
        parcelle_id = data.parcelle_id,
        culture_id  = data.culture_id,
        type        = data.type,
        contexte    = ctx,
        created_by  = user.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/consultations", response_model=list[ConsultationOut],
            summary="Lister les consultations de l'organisation")
def lister_consultations(
    type: TypeConsultation | None = None,
    statut: StatutConsultation | None = None,
    parcelle_id: int | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    q = db.query(Consultation).filter_by(org_id=user.org_id)
    if type:         q = q.filter(Consultation.type == type)
    if statut:       q = q.filter(Consultation.statut == statut)
    if parcelle_id:  q = q.filter(Consultation.parcelle_id == parcelle_id)
    return q.order_by(Consultation.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/consultations/{cid}", response_model=ConsultationDetail,
            summary="Détail complet d'une consultation")
def detail_consultation(
    cid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    return _get_consultation(db, cid, user.org_id)


@router.delete("/consultations/{cid}", status_code=204,
               summary="Archiver une consultation")
def archiver_consultation(
    cid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    c = _get_consultation(db, cid, user.org_id)
    c.statut = StatutConsultation.ARCHIVE
    db.commit()


# ── OBSERVATIONS ───────────────────────────────────────────────────────────────

@router.post("/consultations/{cid}/observations",
             response_model=ObservationOut, status_code=201,
             summary="Ajouter une observation")
def ajouter_observation(
    cid: int,
    data: ObservationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    c = _get_consultation(db, cid, user.org_id)
    obs = Observation(
        consultation_id = c.id,
        type            = data.type,
        partie_plante   = data.partie_plante,
        valeur          = data.valeur,
        note_terrain    = data.note_terrain,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.get("/consultations/{cid}/observations",
            response_model=list[ObservationOut],
            summary="Lister les observations d'une consultation")
def lister_observations(
    cid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _get_consultation(db, cid, user.org_id)
    return db.query(Observation).filter_by(consultation_id=cid).all()


# ── PHOTOS ─────────────────────────────────────────────────────────────────────

@router.post("/consultations/{cid}/photos",
             response_model=PhotoOut, status_code=201,
             summary="Upload photo (stockage local)")
async def upload_photo(
    cid: int,
    source_photo: SourcePhoto = SourcePhoto.SMARTPHONE,
    observation_id: int | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    c = _get_consultation(db, cid, user.org_id)
    type_upload = _type_upload(c.type)
    info = await save_photo(file, type_upload)

    photo = PhotoConsultation(
        consultation_id = c.id,
        observation_id  = observation_id,
        source_photo    = source_photo,
        filename        = info["filename"],
        url             = info["url"],
        thumbnail_url   = info.get("thumbnail_url"),
        taille_ko       = info.get("taille_ko"),
        photo_meta      = info.get("metadata", {}),
    )
    db.add(photo)
    c.nb_photos = (c.nb_photos or 0) + 1
    db.commit()
    db.refresh(photo)
    return photo


# ── ANALYSE ────────────────────────────────────────────────────────────────────

@router.post("/consultations/{cid}/analyser",
             response_model=AnalyseResult,
             summary="Lancer l'analyse complète (Rules Engine + bibliothèque)")
def analyser(
    cid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    t0 = time.perf_counter()
    c = _get_consultation(db, cid, user.org_id)

    # Déterminer plan de l'org pour filtrer les règles premium
    from app.models import Subscription
    sub = db.query(Subscription).filter_by(org_id=user.org_id).first()
    plan = sub.plan.value if sub else "gratuit"

    # Pipeline selon type
    if c.type == TypeConsultation.MALADIE:
        diagnostics_raw = analyser_maladies(db, c, plan)
    elif c.type == TypeConsultation.RAVAGEUR:
        diagnostics_raw = analyser_ravageurs(db, c, plan)
    else:
        diagnostics_raw = analyser_fertilisation(db, c, plan)

    # Supprimer anciens diagnostics + traitements
    db.query(Diagnostic).filter_by(consultation_id=c.id).delete()
    db.query(Traitement).filter_by(consultation_id=c.id).delete()
    db.commit()

    # Persister diagnostics classés
    diag_objs: list[Diagnostic] = []
    for rang, d in enumerate(diagnostics_raw, start=1):
        obj = Diagnostic(
            consultation_id = c.id,
            rang            = rang,
            entite_type     = d["entite_type"],
            entite_id       = d["entite_id"],
            entite_nom      = d.get("entite_nom"),
            score_confiance = d["score_confiance"],
            score_rules     = d["score_rules"],
            score_symptomes = d["score_symptomes"],
            regles_matches  = d["regles_matches"],
            methode         = d["methode"],
        )
        db.add(obj)
        diag_objs.append(obj)
    db.commit()
    for obj in diag_objs:
        db.refresh(obj)

    # Générer plan de traitement depuis règles déclenchées
    ctx = build_contexte(db, c)
    result_re = evaluate(db, ctx, categorie=c.type.value, plan=plan, persist=False)
    traitements = generer_plan(db, c, diagnostics_raw, result_re.get("resultats", []))

    # Résumé + mise à jour statut
    resume = _resume_auto(c.type, diagnostics_raw)
    c.resume = resume
    c.statut = StatutConsultation.ANALYSE
    c.updated_at = datetime.now(timezone.utc)
    db.commit()

    duree_ms = int((time.perf_counter() - t0) * 1000)

    return AnalyseResult(
        consultation_id = c.id,
        type            = c.type,
        diagnostics     = [DiagnosticOut.model_validate(o) for o in diag_objs],
        traitements     = [TraitementOut.model_validate(t) for t in traitements],
        resume          = resume,
        duree_ms        = duree_ms,
    )


# ── DIAGNOSTICS ────────────────────────────────────────────────────────────────

@router.get("/consultations/{cid}/diagnostics",
            response_model=list[DiagnosticOut],
            summary="Résultats classés par confiance")
def lister_diagnostics(
    cid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _get_consultation(db, cid, user.org_id)
    return (db.query(Diagnostic)
            .filter_by(consultation_id=cid)
            .order_by(Diagnostic.rang)
            .all())


@router.post("/diagnostics/{did}/confirmer",
             response_model=DiagnosticOut,
             summary="Confirmer un diagnostic")
def confirmer_diagnostic(
    did: int,
    data: DiagnosticConfirm,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    d = db.query(Diagnostic).filter_by(id=did).first()
    if not d:
        raise HTTPException(404, "Diagnostic introuvable.")
    c = db.query(Consultation).filter_by(id=d.consultation_id, org_id=user.org_id).first()
    if not c:
        raise HTTPException(403, "Accès refusé.")
    d.statut       = data.statut
    d.note_expert  = data.note_expert
    d.confirme_par = user.id
    d.confirme_le  = datetime.now(timezone.utc)
    if data.statut == StatutDiagnostic.CONFIRME:
        c.statut = StatutConsultation.CONFIRME
    db.commit()
    db.refresh(d)
    return d


@router.post("/diagnostics/{did}/exclure",
             response_model=DiagnosticOut,
             summary="Exclure un diagnostic")
def exclure_diagnostic(
    did: int,
    note: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    d = db.query(Diagnostic).filter_by(id=did).first()
    if not d:
        raise HTTPException(404, "Diagnostic introuvable.")
    db.query(Consultation).filter_by(id=d.consultation_id, org_id=user.org_id).first() or (
        (_ for _ in ()).throw(HTTPException(403, "Accès refusé."))
    )
    d.statut       = StatutDiagnostic.EXCLU
    d.note_expert  = note
    d.confirme_par = user.id
    d.confirme_le  = datetime.now(timezone.utc)
    db.commit()
    db.refresh(d)
    return d


# ── TRAITEMENTS ────────────────────────────────────────────────────────────────

@router.get("/consultations/{cid}/traitements",
            response_model=list[TraitementOut],
            summary="Plan de traitement complet trié par urgence")
def lister_traitements(
    cid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _get_consultation(db, cid, user.org_id)
    return (db.query(Traitement)
            .filter_by(consultation_id=cid)
            .order_by(Traitement.priorite)
            .all())


@router.patch("/traitements/{tid}/appliquer",
              response_model=TraitementOut,
              summary="Marquer un traitement comme appliqué")
def appliquer_traitement(
    tid: int,
    data: TraitementAppliquer,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    t = _get_traitement_auteur(db, tid, user.org_id)
    t.statut     = StatutTraitement.APPLIQUE
    t.applique_le = data.applique_le
    t.note       = data.note
    db.commit()
    db.refresh(t)
    return t


@router.patch("/traitements/{tid}/skip",
              response_model=TraitementOut,
              summary="Ignorer un traitement")
def skip_traitement(
    tid: int,
    data: TraitementSkip,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    t = _get_traitement_auteur(db, tid, user.org_id)
    t.statut = StatutTraitement.SKIP
    t.note   = data.note
    db.commit()
    db.refresh(t)
    return t


def _get_traitement_auteur(db: Session, tid: int, org_id: int) -> Traitement:
    t = db.query(Traitement).filter_by(id=tid).first()
    if not t:
        raise HTTPException(404, "Traitement introuvable.")
    c = db.query(Consultation).filter_by(id=t.consultation_id, org_id=org_id).first()
    if not c:
        raise HTTPException(403, "Accès refusé.")
    return t


# ── SUIVIS ─────────────────────────────────────────────────────────────────────

@router.post("/consultations/{cid}/suivis",
             response_model=SuiviOut, status_code=201,
             summary="Ajouter un suivi post-traitement")
def ajouter_suivi(
    cid: int,
    data: SuiviCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    c = _get_consultation(db, cid, user.org_id)
    s = Suivi(
        consultation_id = c.id,
        date_suivi      = data.date_suivi,
        evolution       = data.evolution,
        efficacite      = data.efficacite,
        note            = data.note,
        photo_url       = data.photo_url,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/consultations/{cid}/suivis",
            response_model=list[SuiviOut],
            summary="Historique des suivis")
def lister_suivis(
    cid: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _get_consultation(db, cid, user.org_id)
    return (db.query(Suivi)
            .filter_by(consultation_id=cid)
            .order_by(Suivi.date_suivi)
            .all())


# ── RÉFÉRENTIEL ────────────────────────────────────────────────────────────────

@router.get("/maladies/{mid}/fiche",
            response_model=FicheMaladie,
            summary="Fiche complète d'une maladie")
def fiche_maladie(
    mid: int,
    culture_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    m = db.query(Maladie).filter_by(id=mid).first()
    if not m:
        raise HTTPException(404, "Maladie introuvable.")
    # Données culture-spécifiques si culture_id fourni
    cm: CultureMaladie | None = None
    if culture_id:
        cm = (db.query(CultureMaladie)
              .filter_by(maladie_id=mid, culture_id=culture_id)
              .first())
    return FicheMaladie(
        id                   = m.id,
        nom                  = m.nom,
        nom_scientifique     = m.nom_scientifique,
        pathogene_type       = m.pathogene_type,
        symptomes            = m.symptomes,
        conditions_favorables = m.conditions_favorables,
        gravite              = cm.gravite      if cm else None,
        frequence            = cm.frequence    if cm else None,
        stade_sensible       = cm.stade_sensible if cm else None,
        pertes_estimees      = cm.pertes_estimees if cm else None,
        prevention           = cm.prevention   if cm else None,
        traitement           = cm.traitement   if cm else None,
    )


@router.get("/ravageurs/{rid}/fiche",
            response_model=FicheRavageur,
            summary="Fiche complète d'un ravageur")
def fiche_ravageur(
    rid: int,
    culture_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    r = db.query(Ravageur).filter_by(id=rid).first()
    if not r:
        raise HTTPException(404, "Ravageur introuvable.")
    cr: CultureRavageur | None = None
    if culture_id:
        cr = (db.query(CultureRavageur)
              .filter_by(ravageur_id=rid, culture_id=culture_id)
              .first())
    return FicheRavageur(
        id               = r.id,
        nom              = r.nom,
        nom_scientifique = r.nom_scientifique,
        type_ravageur    = r.type_ravageur,
        description      = r.description,
        symptomes_degats = r.symptomes_degats,
        gravite          = cr.gravite        if cr else None,
        frequence        = cr.frequence      if cr else None,
        stade_sensible   = cr.stade_sensible if cr else None,
        pertes_estimees  = cr.pertes_estimees if cr else None,
        prevention       = cr.prevention     if cr else None,
        lutte            = cr.lutte          if cr else None,
    )


# ── STATS ──────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsConsultations,
            summary="Statistiques santé de l'organisation")
def stats_sante(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    from sqlalchemy import func

    total = db.query(Consultation).filter_by(org_id=user.org_id).count()
    nb_m  = db.query(Consultation).filter_by(org_id=user.org_id, type=TypeConsultation.MALADIE).count()
    nb_r  = db.query(Consultation).filter_by(org_id=user.org_id, type=TypeConsultation.RAVAGEUR).count()
    nb_f  = db.query(Consultation).filter_by(org_id=user.org_id, type=TypeConsultation.FERTILISATION).count()

    # Taux de confirmation global
    nb_confirmes = (db.query(Consultation)
                    .filter_by(org_id=user.org_id, statut=StatutConsultation.CONFIRME)
                    .count())
    taux_global = round(nb_confirmes / total * 100, 1) if total > 0 else 0.0

    # Top maladies (entite_nom le plus fréquent parmi diagnostics confirmés/probables)
    top_m = _top_entites(db, user.org_id, TypeConsultation.MALADIE)
    top_r = _top_entites(db, user.org_id, TypeConsultation.RAVAGEUR)

    return StatsConsultations(
        total_consultations         = total,
        maladies                    = nb_m,
        ravageurs                   = nb_r,
        fertilisations              = nb_f,
        top_maladies                = top_m,
        top_ravageurs               = top_r,
        taux_confirmation_global_pct = taux_global,
    )


def _top_entites(db: Session, org_id: int, type_c: TypeConsultation,
                 limit: int = 5) -> list[StatEntite]:
    from sqlalchemy import func

    # Jointure Consultation → Diagnostic, filtre org + type
    rows = (db.query(
                Diagnostic.entite_nom,
                func.count(Diagnostic.id).label("nb"),
                func.sum(
                    func.cast(Diagnostic.statut == StatutDiagnostic.CONFIRME, Integer_)
                ).label("nb_confirmes"),
            )
            .join(Consultation, Consultation.id == Diagnostic.consultation_id)
            .filter(Consultation.org_id == org_id, Consultation.type == type_c)
            .filter(Diagnostic.statut != StatutDiagnostic.EXCLU)
            .group_by(Diagnostic.entite_nom)
            .order_by(func.count(Diagnostic.id).desc())
            .limit(limit)
            .all())

    return [
        StatEntite(
            nom=r.entite_nom or "Inconnu",
            nb_consultations=r.nb,
            taux_confirmation_pct=round((r.nb_confirmes or 0) / r.nb * 100, 1),
        )
        for r in rows
    ]


# Import nécessaire pour _top_entites
from sqlalchemy import Integer as Integer_
