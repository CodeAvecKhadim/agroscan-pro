"""
Orchestrateur principal IA — pipeline complet question → réponse.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ia import (
    ConfigIA, Conversation, MessageIA, RoleMessage, StatutConversation,
)
from app.schemas.ia import ContexteAgro, MessageAssistantOut, MessageOut
from app.services.ia import llm_provider
from app.services.ia.context_builder import build_contexte
from app.services.ia.extractor import extraire_recommandations
from app.services.ia.quota import limites
from app.services.ia.system_prompt import build_system_prompt
from app.services.rules_evaluator import evaluate

log = logging.getLogger(__name__)

_CATEGORIES_RULES = ["maladie", "ravageur", "fertilisation", "irrigation"]


def repondre(
    db: Session,
    conversation: Conversation,
    user_message: str,
    org_id: int,
    user_id: int,
    plan: str,
    config: Optional[ConfigIA] = None,
) -> MessageAssistantOut:
    """
    Pipeline complet :
    1. Sauvegarder message user
    2. Construire contexte agro
    3. Appeler Claude (ou fallback rules)
    4. Sauvegarder réponse assistant
    5. Extraire recommandations
    6. Retourner MessageAssistantOut
    """
    t0 = time.perf_counter()
    lim = limites(plan)

    # ── 1. Sauvegarder message user ───────────────────────────────────────────
    msg_user = MessageIA(
        conversation_id=conversation.id,
        org_id=org_id,
        role=RoleMessage.USER,
        contenu=user_message,
    )
    db.add(msg_user)
    db.flush()

    # ── 2. Contexte agro ──────────────────────────────────────────────────────
    ctx = build_contexte(
        db=db,
        org_id=org_id,
        user_id=user_id,
        plan=plan,
        config=config,
        parcelle_id=conversation.parcelle_id,
    )

    # ── 3. Historique messages (trimmed) ──────────────────────────────────────
    messages_db = (db.query(MessageIA)
                   .filter_by(conversation_id=conversation.id)
                   .filter(MessageIA.role.in_([RoleMessage.USER, RoleMessage.ASSISTANT]))
                   .order_by(MessageIA.created_at.asc())
                   .all())

    max_hist = lim["history_msgs"]
    messages_hist = _trim_historique(messages_db, max_hist)

    # ── 4. Appel IA ───────────────────────────────────────────────────────────
    fallback_mode = False
    ton = config.ton.value if config and config.ton else "simple"
    mode = conversation.mode.value if conversation.mode else "libre"

    system = build_system_prompt(ctx, ton=ton, mode=mode,
                                  max_contexte_chars=lim["tokens_max"] * 4)

    if llm_provider.disponible():
        try:
            result = llm_provider.chat(
                messages=messages_hist,
                system=system,
                modele=lim["modele"],
                max_tokens=lim["tokens_max"],
            )
        except RuntimeError as e:
            log.warning("Claude indisponible, fallback rules: %s", e)
            result = _fallback_rules(db, ctx, user_message, plan)
            fallback_mode = True
    else:
        result = _fallback_rules(db, ctx, user_message, plan)
        fallback_mode = True

    contenu_reponse = result["contenu"]
    duree_ms = int((time.perf_counter() - t0) * 1000)

    # ── 5. Sauvegarder réponse assistant ──────────────────────────────────────
    msg_assistant = MessageIA(
        conversation_id=conversation.id,
        org_id=org_id,
        role=RoleMessage.ASSISTANT,
        contenu=contenu_reponse,
        tokens_in=result.get("tokens_in"),
        tokens_out=result.get("tokens_out"),
        modele=result.get("modele"),
        duree_ms=duree_ms,
        contexte_inject={
            "parcelles": len(ctx.parcelles),
            "alertes": len(ctx.meteo.get("alertes_actives", [])),
            "regles": len(ctx.regles.get("declenchees", [])),
        },
    )
    db.add(msg_assistant)
    db.flush()

    # ── 6. Mise à jour conversation ───────────────────────────────────────────
    conversation.nb_messages = (conversation.nb_messages or 0) + 2
    conversation.tokens_total = (conversation.tokens_total or 0) + \
                                 (result.get("tokens_in", 0) or 0) + \
                                 (result.get("tokens_out", 0) or 0)
    conversation.updated_at = datetime.now(timezone.utc)

    # Auto-titre si premier échange
    if conversation.nb_messages <= 2 and not conversation.titre:
        conversation.titre = _auto_titre(user_message)

    db.commit()
    db.refresh(msg_assistant)

    # ── 7. Extraire recommandations ───────────────────────────────────────────
    recs = []
    if not fallback_mode or lim["extraction"]:
        try:
            recs = extraire_recommandations(
                db=db,
                conversation_id=conversation.id,
                message_id=msg_assistant.id,
                org_id=org_id,
                texte_reponse=contenu_reponse,
                ctx=ctx,
                plan=plan,
                parcelle_id=conversation.parcelle_id,
                culture_id=conversation.culture_id,
            )
        except Exception as e:
            log.warning("Extraction recommandations échouée: %s", e)

    # ── Quota restant ─────────────────────────────────────────────────────────
    quota_msg_restant = None
    max_msg = lim["msg_conv"]
    if max_msg:
        quota_msg_restant = max(0, max_msg - (conversation.nb_messages or 0))

    from app.schemas.ia import MessageOut, RecommandationOut
    return MessageAssistantOut(
        message=MessageOut.model_validate(msg_assistant),
        recommandations=[_rec_out(r) for r in recs],
        quota_restant=quota_msg_restant,
        fallback_mode=fallback_mode,
    )


def repondre_question_rapide(
    db: Session,
    question: str,
    org_id: int,
    user_id: int,
    plan: str,
    parcelle_id: Optional[int] = None,
    config: Optional[ConfigIA] = None,
) -> dict:
    """Question éphémère sans conversation persistante."""
    t0 = time.perf_counter()
    lim = limites(plan)

    ctx = build_contexte(db, org_id, user_id, plan, config, parcelle_id)

    ton = config.ton.value if config and config.ton else "simple"
    system = build_system_prompt(ctx, ton=ton, max_contexte_chars=lim["tokens_max"] * 4)

    fallback_mode = False
    if llm_provider.disponible():
        try:
            result = llm_provider.chat(
                messages=[{"role": "user", "content": question}],
                system=system,
                modele=lim["modele"],
                max_tokens=lim["tokens_max"],
            )
        except RuntimeError:
            result = _fallback_rules(db, ctx, question, plan)
            fallback_mode = True
    else:
        result = _fallback_rules(db, ctx, question, plan)
        fallback_mode = True

    return {
        "reponse":       result["contenu"],
        "modele":        result.get("modele"),
        "duree_ms":      int((time.perf_counter() - t0) * 1000),
        "fallback_mode": fallback_mode,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _trim_historique(messages: list[MessageIA], max_count: int) -> list[dict]:
    """Garde les N derniers messages pour ne pas saturer le contexte."""
    relevant = [m for m in messages if m.role in (RoleMessage.USER, RoleMessage.ASSISTANT)]
    # Toujours inclure le 1er message (contexte initial)
    if len(relevant) > max_count:
        premier = relevant[0]
        derniers = relevant[-(max_count - 1):]
        relevant = [premier] + derniers
    return [
        {"role": m.role.value, "content": m.contenu}
        for m in relevant
    ]


def _fallback_rules(db: Session, ctx: ContexteAgro, user_message: str, plan: str) -> dict:
    """
    Mode dégradé sans clé API Claude.
    Run Rules Engine sur le contexte, format réponse structurée.
    """
    if not ctx.parcelles:
        return {
            "contenu": (
                "Je n'ai pas accès à vos données de parcelles pour générer des recommandations. "
                "Ajoutez une parcelle dans Mon Champ pour des conseils personnalisés."
            ),
            "tokens_in": 0, "tokens_out": 0, "modele": "fallback_rules",
        }

    parc = ctx.parcelles[0]
    culture_nom = parc.get("culture") or ""
    zone = parc.get("zone_agro") or ""
    sol = parc.get("sol", {})

    context_dict = {
        "org_id":        ctx.producteur.get("org_id"),
        "culture_nom":   culture_nom,
        "zone_agro":     zone,
        "mois":          int(ctx.date_contexte.split("-")[1]) if ctx.date_contexte else 6,
    }
    if sol.get("pH"):                    context_dict["sol_pH"] = sol["pH"]
    if sol.get("azote_g_kg"):            context_dict["sol_azote"] = sol["azote_g_kg"]
    if sol.get("phosphore_mg_kg"):       context_dict["sol_phosphore"] = sol["phosphore_mg_kg"]
    if sol.get("matiere_organique_pct"): context_dict["sol_matiere_organique"] = sol["matiere_organique_pct"]
    if ctx.meteo.get("conditions"):
        cond = ctx.meteo["conditions"]
        if cond.get("temp_c"):       context_dict["meteo_temp_air"] = cond["temp_c"]
        if cond.get("humidite_pct"): context_dict["meteo_humidite_rel"] = cond["humidite_pct"]
        if cond.get("pluie_mm"):     context_dict["meteo_pluie_24h"] = cond["pluie_mm"]
        if cond.get("vent_kmh"):     context_dict["meteo_vent"] = cond["vent_kmh"]

    # Symptômes des consultations récentes → déclenchement règles obs.*
    obs_symptoms = []
    obs_ravageurs = []
    for c in ctx.sante.get("consultations_recentes", []):
        symp = c.get("symptomes", "") or ""
        if symp:
            # Extraire mots-clés agronomiques depuis texte libre
            mots = symp.lower().replace(",", " ").replace(".", " ").split()
            obs_symptoms.extend(mots)
    if obs_symptoms:
        context_dict["obs_symptomes"] = obs_symptoms

    lignes = [
        f"**Analyse agronomique pour {parc['nom']} ({culture_nom})**\n",
        f"Zone : {zone} | Sol : {', '.join(f'{k} {v}' for k, v in sol.items()) or 'non renseigné'}\n",
    ]

    regles_codes = []
    for categorie in _CATEGORIES_RULES:
        try:
            result = evaluate(db, context_dict, categorie=categorie, plan=plan, persist=False)
            for r in result.get("resultats", [])[:3]:
                gravite = r.get("gravite", "faible")
                if gravite in ("critique", "elevee", "haute"):
                    code = r.get("code", "")
                    nom = r.get("nom", "")
                    recs_raw = r.get("recommandations", [])
                    alertes_raw = r.get("alertes", [])

                    def _str(item):
                        if isinstance(item, dict):
                            return item.get("message") or item.get("titre") or item.get("action") or str(item)
                        return str(item)

                    recs = [_str(rc) for rc in recs_raw]
                    alertes = [_str(al) for al in alertes_raw]
                    regles_codes.append(code)
                    lignes.append(f"\n⚠ **[{code}] {nom}** ({gravite})")
                    for al in alertes[:2]:
                        lignes.append(f"  • {al}")
                    for rec in recs[:2]:
                        lignes.append(f"\nRECOMMANDATION : {rec[:80]}")
                        lignes.append(f"ACTION : Appliquer : {rec}")
                        lignes.append(f"POURQUOI : Règle agronomique {code} déclenchée")
                        lignes.append(f"DÉLAI : 7 jours")
        except Exception as e:
            log.debug("Rules fallback %s: %s", categorie, e)

    if len(lignes) <= 3:
        lignes.append(
            "\nAucune alerte agronomique critique détectée pour vos parcelles actuelles. "
            "Continuez vos activités selon le plan prévu."
        )

    return {
        "contenu":    "\n".join(lignes),
        "tokens_in":  0,
        "tokens_out": 0,
        "modele":     "fallback_rules",
        "regles_codes": regles_codes,
    }


def _auto_titre(user_message: str) -> str:
    """Génère un titre court depuis le premier message."""
    cleaned = user_message.strip().split("\n")[0]
    if len(cleaned) <= 60:
        return cleaned
    # Tronquer à un mot limite
    words = cleaned[:60].split()
    return " ".join(words[:-1]) + "…" if words else "Conversation"


def _rec_out(rec):
    from app.schemas.ia import RecommandationOut
    return RecommandationOut.model_validate(rec)
