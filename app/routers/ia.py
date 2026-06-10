"""
Routes API — Module IA Agricole AgroScan.
Préfixe : /api/ia  (15 endpoints)
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user
from app.models import Subscription, User
from app.models.agronomie import Culture
from app.models.champ import Parcelle
from app.models.ia import (
    ConfigIA, Conversation, FeedbackIA, MessageIA,
    RecommandationIA, StatutConversation, StatutReco,
)
from app.schemas.ia import (
    AnalyseParcelle, ConfigIAOut, ConfigIAUpdate, ConversationCreate,
    ConversationDetail, ConversationOut, ContexteAgro, FeedbackCreate,
    FeedbackOut, MessageAssistantOut, MessageCreate, MessageOut,
    QuestionRapide, QuotaIA, RecommandationOut, RecoStatutUpdate, ReponseRapide,
)
from app.services.ia.assistant import repondre, repondre_question_rapide
from app.services.ia.context_builder import build_contexte
from app.services.ia.extractor import extraire_recommandations
from app.services.ia.quota import (
    limites, mois_courant, quota_ia,
    verifier_quota_conversation, verifier_quota_message,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ia", tags=["IA Agricole"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_plan(db: Session, org_id: int) -> str:
    sub = db.query(Subscription).filter_by(org_id=org_id).first()
    return sub.plan.value if sub else "gratuit"


def _get_config(db: Session, org_id: int) -> ConfigIA:
    cfg = db.query(ConfigIA).filter_by(org_id=org_id).first()
    if not cfg:
        cfg = ConfigIA(org_id=org_id)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _get_conversation(db: Session, conv_id: int, org_id: int) -> Conversation:
    conv = db.query(Conversation).filter_by(id=conv_id, org_id=org_id).first()
    if not conv:
        raise HTTPException(404, "Conversation introuvable")
    if conv.statut == StatutConversation.ARCHIVEE:
        raise HTTPException(410, "Conversation archivée")
    return conv


def _enrich_conv(conv: Conversation, db: Session) -> dict:
    d = ConversationOut.model_validate(conv).model_dump()
    if conv.parcelle_id:
        p = db.query(Parcelle).filter_by(id=conv.parcelle_id).first()
        d["parcelle_nom"] = p.nom if p else None
    if conv.culture_id:
        c = db.query(Culture).filter_by(id=conv.culture_id).first()
        d["culture_nom"] = c.nom if c else None
    return d


def _enrich_rec(rec: RecommandationIA, db: Session) -> dict:
    d = RecommandationOut.model_validate(rec).model_dump()
    if rec.parcelle_id:
        p = db.query(Parcelle).filter_by(id=rec.parcelle_id).first()
        d["parcelle_nom"] = p.nom if p else None
    if rec.culture_id:
        c = db.query(Culture).filter_by(id=rec.culture_id).first()
        d["culture_nom"] = c.nom if c else None
    return d


# ════════════════════════════════════════════════════════════════════════════
# CONVERSATIONS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/conversations", summary="Démarrer une conversation")
def creer_conversation(
    payload: ConversationCreate,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    plan = _get_plan(db, user.org_id)
    ok, raison = verifier_quota_conversation(db, user.org_id, plan)
    if not ok:
        raise HTTPException(429, raison)

    if payload.parcelle_id:
        p = db.query(Parcelle).filter_by(id=payload.parcelle_id, org_id=user.org_id).first()
        if not p:
            raise HTTPException(404, "Parcelle introuvable")

    conv = Conversation(
        org_id      = user.org_id,
        user_id     = user.id,
        parcelle_id = payload.parcelle_id,
        culture_id  = payload.culture_id,
        titre       = payload.titre,
        mode        = payload.mode,
        mois_periode = mois_courant(),
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Message initial optionnel → déclenche déjà une réponse
    if payload.message_initial:
        config = _get_config(db, user.org_id)
        ok_msg, raison_msg = verifier_quota_message(conv, plan)
        if ok_msg:
            try:
                repondre(db, conv, payload.message_initial,
                         user.org_id, user.id, plan, config)
                db.refresh(conv)
            except Exception as e:
                log.warning("Message initial échoué: %s", e)

    return _enrich_conv(conv, db)


@router.get("/conversations", summary="Liste des conversations")
def liste_conversations(
    statut: Optional[StatutConversation] = None,
    limit:  int = Query(20, le=50),
    offset: int = 0,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    q = db.query(Conversation).filter_by(org_id=user.org_id)
    if statut:
        q = q.filter(Conversation.statut == statut)
    else:
        q = q.filter(Conversation.statut != StatutConversation.ARCHIVEE)
    convs = q.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit).all()
    return {"conversations": [_enrich_conv(c, db) for c in convs], "nb": len(convs)}


@router.get("/conversations/{conv_id}", summary="Détail conversation + messages")
def detail_conversation(
    conv_id: int,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    conv = db.query(Conversation).filter_by(id=conv_id, org_id=user.org_id).first()
    if not conv:
        raise HTTPException(404, "Conversation introuvable")
    messages = (db.query(MessageIA)
                .filter_by(conversation_id=conv_id)
                .order_by(MessageIA.created_at)
                .all())
    d = _enrich_conv(conv, db)
    d["messages"] = [MessageOut.model_validate(m).model_dump() for m in messages]
    return d


@router.delete("/conversations/{conv_id}", status_code=204, summary="Archiver conversation")
def archiver_conversation(
    conv_id: int,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    conv = db.query(Conversation).filter_by(id=conv_id, org_id=user.org_id).first()
    if not conv:
        raise HTTPException(404, "Conversation introuvable")
    conv.statut = StatutConversation.ARCHIVEE
    db.commit()


# ════════════════════════════════════════════════════════════════════════════
# MESSAGES
# ════════════════════════════════════════════════════════════════════════════

@router.post("/conversations/{conv_id}/messages", summary="Envoyer un message → réponse IA")
def envoyer_message(
    conv_id: int,
    payload: MessageCreate,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    conv   = _get_conversation(db, conv_id, user.org_id)
    plan   = _get_plan(db, user.org_id)
    config = _get_config(db, user.org_id)

    ok, raison = verifier_quota_message(conv, plan)
    if not ok:
        raise HTTPException(429, raison)

    return repondre(
        db=db,
        conversation=conv,
        user_message=payload.contenu,
        org_id=user.org_id,
        user_id=user.id,
        plan=plan,
        config=config,
    )


@router.get("/conversations/{conv_id}/messages", summary="Historique messages")
def historique_messages(
    conv_id: int,
    limit:  int = Query(50, le=100),
    offset: int = 0,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    conv = db.query(Conversation).filter_by(id=conv_id, org_id=user.org_id).first()
    if not conv:
        raise HTTPException(404, "Conversation introuvable")
    messages = (db.query(MessageIA)
                .filter_by(conversation_id=conv_id)
                .order_by(MessageIA.created_at)
                .offset(offset)
                .limit(limit)
                .all())
    return {"messages": [MessageOut.model_validate(m).model_dump() for m in messages], "nb": len(messages)}


# ════════════════════════════════════════════════════════════════════════════
# ACCÈS RAPIDE
# ════════════════════════════════════════════════════════════════════════════

@router.post("/question", summary="Question rapide sans conversation")
def question_rapide(
    payload: QuestionRapide,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    plan   = _get_plan(db, user.org_id)
    config = _get_config(db, user.org_id)

    result = repondre_question_rapide(
        db=db,
        question=payload.question,
        org_id=user.org_id,
        user_id=user.id,
        plan=plan,
        parcelle_id=payload.parcelle_id,
        config=config,
    )
    return ReponseRapide(
        reponse=result["reponse"],
        modele=result.get("modele"),
        duree_ms=result["duree_ms"],
        fallback_mode=result["fallback_mode"],
    )


@router.post("/analyser-parcelle/{parcelle_id}", summary="Analyse IA complète d'une parcelle")
def analyser_parcelle(
    parcelle_id: int,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    """Crée une conversation en mode analyse_parcelle et génère l'analyse complète."""
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(404, "Parcelle introuvable")

    plan = _get_plan(db, user.org_id)
    ok, raison = verifier_quota_conversation(db, user.org_id, plan)
    if not ok:
        raise HTTPException(429, raison)

    config = _get_config(db, user.org_id)

    # Créer conversation dédiée
    from app.models.ia import ModeConversation
    conv = Conversation(
        org_id       = user.org_id,
        user_id      = user.id,
        parcelle_id  = parcelle_id,
        culture_id   = p.culture_id,
        titre        = f"Analyse — {p.nom}",
        mode         = ModeConversation.ANALYSE_PARCELLE,
        mois_periode = mois_courant(),
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Générer analyse
    question = (
        f"Fais une analyse complète de la parcelle {p.nom}. "
        f"Identifie les problèmes actuels et donne 3 à 5 recommandations prioritaires."
    )
    msg_result = repondre(
        db=db,
        conversation=conv,
        user_message=question,
        org_id=user.org_id,
        user_id=user.id,
        plan=plan,
        config=config,
    )

    recs = [_enrich_rec(r, db) for r in
            db.query(RecommandationIA)
            .filter_by(conversation_id=conv.id)
            .order_by(RecommandationIA.priorite)
            .all()]

    actions_urgentes = [r["titre"] for r in recs if r["priorite"] == 1][:5]

    return AnalyseParcelle(
        conversation_id  = conv.id,
        message_id       = msg_result.message.id,
        parcelle_nom     = p.nom,
        analyse          = msg_result.message.contenu,
        recommandations  = recs,
        actions_urgentes = actions_urgentes,
        duree_ms         = msg_result.message.duree_ms or 0,
    )


@router.get("/contexte", summary="Aperçu contexte agro (debug)")
def apercu_contexte(
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    plan   = _get_plan(db, user.org_id)
    config = _get_config(db, user.org_id)
    ctx = build_contexte(db, user.org_id, user.id, plan, config)
    return ctx


@router.get("/contexte/parcelle/{parcelle_id}", summary="Contexte focalisé sur une parcelle")
def apercu_contexte_parcelle(
    parcelle_id: int,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    p = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not p:
        raise HTTPException(404, "Parcelle introuvable")
    plan   = _get_plan(db, user.org_id)
    config = _get_config(db, user.org_id)
    ctx = build_contexte(db, user.org_id, user.id, plan, config, parcelle_id=parcelle_id)
    return ctx


# ════════════════════════════════════════════════════════════════════════════
# RECOMMANDATIONS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/recommandations", summary="Toutes les recommandations org")
def liste_recommandations(
    statut:      Optional[StatutReco]   = None,
    categorie:   Optional[str]          = None,
    parcelle_id: Optional[int]          = None,
    limit:       int = Query(30, le=100),
    offset:      int = 0,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    q = db.query(RecommandationIA).filter_by(org_id=user.org_id)
    if statut:
        q = q.filter(RecommandationIA.statut == statut)
    if categorie:
        from app.models.ia import CategorieReco
        try:
            q = q.filter(RecommandationIA.categorie == CategorieReco(categorie))
        except ValueError:
            pass
    if parcelle_id is not None:
        q = q.filter(RecommandationIA.parcelle_id == parcelle_id)
    recs = q.order_by(RecommandationIA.priorite, RecommandationIA.created_at.desc()).offset(offset).limit(limit).all()
    return {"recommandations": [_enrich_rec(r, db) for r in recs], "nb": len(recs)}


@router.get("/recommandations/{rec_id}", summary="Détail recommandation")
def detail_recommandation(
    rec_id: int,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    r = db.query(RecommandationIA).filter_by(id=rec_id, org_id=user.org_id).first()
    if not r:
        raise HTTPException(404, "Recommandation introuvable")
    if r.statut == StatutReco.NOUVELLE:
        r.statut = StatutReco.VUE
        db.commit()
    return _enrich_rec(r, db)


@router.patch("/recommandations/{rec_id}/statut", summary="Changer statut recommandation")
def update_statut_reco(
    rec_id:  int,
    payload: RecoStatutUpdate,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    r = db.query(RecommandationIA).filter_by(id=rec_id, org_id=user.org_id).first()
    if not r:
        raise HTTPException(404, "Recommandation introuvable")
    r.statut = payload.statut
    db.commit()
    return {"ok": True, "statut": r.statut}


# ════════════════════════════════════════════════════════════════════════════
# FEEDBACK
# ════════════════════════════════════════════════════════════════════════════

@router.post("/conversations/{conv_id}/feedback", summary="Laisser un feedback sur une réponse")
def creer_feedback(
    conv_id: int,
    payload: FeedbackCreate,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    conv = db.query(Conversation).filter_by(id=conv_id, org_id=user.org_id).first()
    if not conv:
        raise HTTPException(404, "Conversation introuvable")

    msg = db.query(MessageIA).filter_by(
        id=payload.message_id, conversation_id=conv_id
    ).first()
    if not msg:
        raise HTTPException(404, "Message introuvable")

    if not payload.valide():
        raise HTTPException(422, "Fournir au moins note ou utile")

    fb = FeedbackIA(
        org_id            = user.org_id,
        conversation_id   = conv_id,
        message_id        = payload.message_id,
        recommandation_id = payload.recommandation_id,
        note              = payload.note,
        utile             = payload.utile,
        commentaire       = payload.commentaire,
        amelioration      = payload.amelioration,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackOut.model_validate(fb)


@router.get("/conversations/{conv_id}/feedback", summary="Feedbacks d'une conversation")
def liste_feedback(
    conv_id: int,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    conv = db.query(Conversation).filter_by(id=conv_id, org_id=user.org_id).first()
    if not conv:
        raise HTTPException(404, "Conversation introuvable")
    fbs = db.query(FeedbackIA).filter_by(conversation_id=conv_id).all()
    return {"feedbacks": [FeedbackOut.model_validate(f).model_dump() for f in fbs], "nb": len(fbs)}


# ════════════════════════════════════════════════════════════════════════════
# CONFIG & QUOTA
# ════════════════════════════════════════════════════════════════════════════

@router.get("/config", summary="Config IA org")
def get_config(
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    return ConfigIAOut.model_validate(_get_config(db, user.org_id))


@router.patch("/config", summary="Modifier config IA")
def update_config(
    payload: ConfigIAUpdate,
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    cfg = _get_config(db, user.org_id)
    for field in ["langue", "ton", "focus_cultures", "inclure_meteo",
                  "inclure_regles", "inclure_historique_sante", "inclure_couts"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(cfg, field, val)
    cfg.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cfg)
    return ConfigIAOut.model_validate(cfg)


@router.get("/quota", summary="Quota IA restant")
def get_quota(
    user: User     = Depends(current_user),
    db: Session    = Depends(get_db),
):
    plan = _get_plan(db, user.org_id)
    return quota_ia(db, user.org_id, plan)
