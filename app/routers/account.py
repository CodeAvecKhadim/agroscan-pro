"""
Router Account — /api/account
Endpoints RGPD/CDP : export des données utilisateur et suppression de compte.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user
from app.core.security import verify_password
from app.models import User

router = APIRouter(prefix="/api/account", tags=["Mon Compte"])


class DeleteAccountIn(BaseModel):
    password: str


# ── Export données (RGPD / CDP droit d'accès) ────────────────────────────────

@router.get("/export", summary="Exporter toutes mes données (JSON)")
def export_account_data(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Retourne toutes les données personnelles de l'utilisateur en JSON.
    Conforme à l'article 20 RGPD et à la loi 2008-12 CDP Sénégal.
    """
    org_id  = user.org_id
    user_id = user.id

    # Profil utilisateur (sans mot de passe)
    profil = {
        "id":            user.id,
        "full_name":     user.full_name,
        "email":         user.email,
        "phone":         user.phone,
        "role":          user.role,
        "profil":        user.profil,
        "created_at":    user.created_at.isoformat() if user.created_at else None,
    }

    # Parcelles
    parcelles = db.execute(text("""
        SELECT id, nom, type_culture, surface_ha, statut, created_at
        FROM champ_parcelles WHERE org_id = :org_id ORDER BY created_at
    """), {"org_id": org_id}).mappings().all()

    # Observations terrain
    observations = db.execute(text("""
        SELECT id, parcelle_id, date_observation, irrigation_effectuee,
               pluie_observee, etat_feuilles, ravageurs_observes,
               maladie_observee, confiance_observation, notes, created_at
        FROM observations_terrain WHERE org_id = :org_id ORDER BY created_at
    """), {"org_id": org_id}).mappings().all()

    # Conversations IA
    conversations = db.execute(text("""
        SELECT id, titre, mode, statut, nb_messages, tokens_total, created_at
        FROM ia_conversations WHERE org_id = :org_id ORDER BY created_at
    """), {"org_id": org_id}).mappings().all()

    conv_ids = [c["id"] for c in conversations]
    messages_ia = []
    if conv_ids:
        messages_ia = db.execute(text("""
            SELECT id, conversation_id, role, contenu, tokens_in, tokens_out, created_at
            FROM ia_messages
            WHERE conversation_id = ANY(:ids)
            ORDER BY created_at
        """), {"ids": conv_ids}).mappings().all()

    # Analyses sol
    analyses = db.execute(text("""
        SELECT id, created_at, mesures, resultats
        FROM analyses WHERE org_id = :org_id ORDER BY created_at
    """), {"org_id": org_id}).mappings().all()

    # Activités ferme
    activites = db.execute(text("""
        SELECT id, type_activite, date_activite, culture, notes, created_at
        FROM gf_activites WHERE org_id = :org_id ORDER BY date_activite
    """), {"org_id": org_id}).mappings().all()

    return JSONResponse(content={
        "export_date":    datetime.now(timezone.utc).isoformat(),
        "generated_by":   "AgroScan Pro — Social Technologie",
        "profil":         dict(profil),
        "parcelles":      [dict(r) for r in parcelles],
        "observations_terrain": [dict(r) for r in observations],
        "conversations_ia":     [dict(r) for r in conversations],
        "messages_ia":          [dict(r) for r in messages_ia],
        "analyses_sol":         [dict(r) for r in analyses],
        "activites_ferme":      [dict(r) for r in activites],
    }, media_type="application/json",
       headers={"Content-Disposition": "attachment; filename=mes-donnees-agroscan.json"})


# ── Suppression de compte (RGPD / CDP droit à l'oubli) ───────────────────────

@router.delete("", status_code=200, summary="Supprimer mon compte et toutes mes données")
def delete_account(
    body: DeleteAccountIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Supprime définitivement le compte et toutes les données associées.
    - Compte solo : suppression complète (org + toutes les données)
    - Membre d'une coopérative : anonymisation + suppression du compte utilisateur
    Irréversible. Exige confirmation du mot de passe.
    """
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=403, detail="Mot de passe incorrect.")

    org_id  = user.org_id
    user_id = user.id

    # Compter les membres de l'org
    nb_membres = db.execute(
        text("SELECT COUNT(*) FROM users WHERE org_id = :org_id"),
        {"org_id": org_id}
    ).scalar()

    if nb_membres == 1:
        # Compte solo — suppression complète de l'organisation
        _delete_org_full(db, org_id)
    else:
        # Membre d'une coop — anonymisation + suppression du user
        _anonymize_and_delete_user(db, user_id, org_id)

    db.commit()
    return {"message": "Compte supprimé. Toutes vos données ont été effacées."}


def _delete_org_full(db: Session, org_id: int) -> None:
    """Supprime toutes les données d'une organisation en ordre safe."""
    # Ordre: dépendants → tables racines
    steps = [
        # IA — feedback d'abord (dépend de messages et recommandations)
        "DELETE FROM ia_feedback WHERE conversation_id IN (SELECT id FROM ia_conversations WHERE org_id = :org_id)",
        "DELETE FROM ia_recommandations WHERE conversation_id IN (SELECT id FROM ia_conversations WHERE org_id = :org_id)",
        "DELETE FROM ia_conversations WHERE org_id = :org_id",
        "DELETE FROM ia_config WHERE org_id = :org_id",
        # Météo
        "DELETE FROM mt_planificateur WHERE org_id = :org_id",
        "DELETE FROM mt_config_alertes WHERE org_id = :org_id",
        "DELETE FROM mt_alertes WHERE org_id = :org_id",
        "DELETE FROM mt_previsions WHERE org_id = :org_id",
        "DELETE FROM mt_conditions WHERE org_id = :org_id",
        # Champ — enfants des parcelles (NO ACTION) puis parcelles
        "DELETE FROM champ_cartographies WHERE parcelle_id IN (SELECT id FROM champ_parcelles WHERE org_id = :org_id)",
        "DELETE FROM champ_sols WHERE parcelle_id IN (SELECT id FROM champ_parcelles WHERE org_id = :org_id)",
        "DELETE FROM champ_infrastructures WHERE parcelle_id IN (SELECT id FROM champ_parcelles WHERE org_id = :org_id)",
        "DELETE FROM champ_sources_eau WHERE parcelle_id IN (SELECT id FROM champ_parcelles WHERE org_id = :org_id)",
        "DELETE FROM champ_parcelles WHERE org_id = :org_id",
        # Finances
        "DELETE FROM payments WHERE subscription_id IN (SELECT id FROM subscriptions WHERE org_id = :org_id)",
        "DELETE FROM subscriptions WHERE org_id = :org_id",
        # Analyses sol (NO ACTION)
        "DELETE FROM analyses WHERE org_id = :org_id",
        # Compteurs
        "DELETE FROM usage_counters WHERE org_id = :org_id",
        # Users
        "DELETE FROM users WHERE org_id = :org_id",
        # Org (cascade supprime fermes et le reste)
        "DELETE FROM organizations WHERE id = :org_id",
    ]
    for stmt in steps:
        db.execute(text(stmt), {"org_id": org_id})


def _anonymize_and_delete_user(db: Session, user_id: int, org_id: int) -> None:
    """Anonymise les données d'un membre de coop puis supprime son compte."""
    # Mise à NULL des données personnelles liées à ce user dans d'autres tables
    db.execute(text("UPDATE analyses SET user_id = NULL WHERE user_id = :uid"), {"uid": user_id})
    # Suppression du compte
    db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
