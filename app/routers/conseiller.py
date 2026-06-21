"""
Routeur Conseiller Agricole — M9
Endpoints : dashboard, producteurs, suivi parcelles, validation diagnostics, rapports.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
import io

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User, UserRole
from app.models.champ import Parcelle, AnalyseSol, Infrastructure, StatutParcelle
from app.models.observations import ObservationDiagnostic as Observation
from app.models.sante import Consultation, Diagnostic

router = APIRouter(prefix="/api/conseiller", tags=["Conseiller"])


def _require_conseiller(user: User = Depends(current_user)) -> User:
    allowed = {UserRole.CONSEILLER, UserRole.ADMIN, UserRole.OWNER, UserRole.SUPER_ADMIN}
    if user.role not in allowed:
        raise HTTPException(status_code=403, detail="Accès réservé aux conseillers agricoles.")
    return user


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def dashboard(
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """KPIs globaux du conseiller : parcelles suivies, observations en attente, alertes."""
    org_id = user.org_id

    nb_parcelles = db.query(func.count(Parcelle.id)).filter(
        Parcelle.org_id == org_id,
        Parcelle.statut != StatutParcelle.ARCHIVE,
    ).scalar() or 0
    nb_actives   = db.query(func.count(Parcelle.id)).filter(
        Parcelle.org_id == org_id,
        Parcelle.wizard_complet == True,
        Parcelle.statut != StatutParcelle.ARCHIVE,
    ).scalar() or 0
    nb_obs_attente = db.query(func.count(Observation.id)).filter(
        Observation.org_id == org_id,
        Observation.validation_conseiller == None,
        Observation.anomalie == True,
    ).scalar() or 0
    nb_consultations = db.query(func.count(Consultation.id)).filter(
        Consultation.org_id == org_id
    ).scalar() or 0

    score_moyen = db.query(func.avg(Parcelle.score_completude)).filter(
        Parcelle.org_id == org_id
    ).scalar()

    # Producteurs dans l'org
    nb_producteurs = db.query(func.count(User.id)).filter(
        User.org_id == org_id,
        User.is_active == True,
        User.role.in_([UserRole.PRODUCTEUR, UserRole.MEMBER, UserRole.OWNER]),
    ).scalar() or 0

    return {
        "nb_parcelles": nb_parcelles,
        "nb_parcelles_actives": nb_actives,
        "nb_parcelles_configuration": nb_parcelles - nb_actives,
        "nb_observations_en_attente": nb_obs_attente,
        "nb_consultations": nb_consultations,
        "score_moyen": round(float(score_moyen), 1) if score_moyen else 0,
        "nb_producteurs": nb_producteurs,
        "genere_le": datetime.now(timezone.utc).isoformat(),
    }


# ── PRODUCTEURS ───────────────────────────────────────────────────────────────

@router.get("/producteurs")
def lister_producteurs(
    search: Optional[str] = Query(None),
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """Liste tous les producteurs/membres de l'organisation avec leurs stats."""
    q = db.query(User).filter(
        User.org_id == user.org_id,
        User.is_active == True,
        User.role.in_([UserRole.PRODUCTEUR, UserRole.MEMBER, UserRole.OWNER, UserRole.TECHNICIEN]),
    )
    if search:
        term = f"%{search}%"
        q = q.filter(or_(User.full_name.ilike(term), User.email.ilike(term), User.phone.ilike(term)))

    producteurs = q.order_by(User.full_name).all()

    result = []
    for p in producteurs:
        nb_parcelles = db.query(func.count(Parcelle.id)).filter(
            Parcelle.org_id == user.org_id,
            Parcelle.created_by == p.id if hasattr(Parcelle, 'created_by') else True,
            Parcelle.statut != StatutParcelle.ARCHIVE,
        ).scalar() or 0

        result.append({
            "id": p.id,
            "full_name": p.full_name,
            "email": p.email,
            "phone": p.phone,
            "role": p.role.value,
            "profil": p.profil,
            "email_verified": p.email_verified,
            "phone_verified": p.phone_verified,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return result


# ── PARCELLES SUIVIES ─────────────────────────────────────────────────────────

@router.get("/parcelles")
def parcelles_suivies(
    statut: Optional[str] = Query(None),
    avec_anomalie: Optional[bool] = Query(None),
    limit: int = Query(100, le=500),
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """Liste parcelles de l'org avec état anomalie / retard."""
    q = db.query(Parcelle).filter(Parcelle.org_id == user.org_id)
    if statut:
        q = q.filter(Parcelle.statut == statut)
    parcelles = q.order_by(Parcelle.score_completude.asc()).limit(limit).all()

    result = []
    for p in parcelles:
        # Observations anomalie non validées
        nb_anomalies = db.query(func.count(Observation.id)).filter(
            Observation.parcelle_id == p.id,
            Observation.anomalie == True,
            Observation.validation_conseiller == None,
        ).scalar() or 0

        # Dernière consultation
        derniere_consult = db.query(Consultation).filter(
            Consultation.parcelle_id == p.id
        ).order_by(Consultation.created_at.desc()).first()

        result.append({
            "id": p.id,
            "nom": p.nom,
            "type_culture": p.type_culture,
            "statut": p.statut.value if p.statut else None,
            "wizard_complet": p.wizard_complet,
            "etape_wizard": p.etape_wizard,
            "superficie_ha": p.superficie_ha,
            "score_completude": p.score_completude,
            "region": p.region,
            "zone_agro": p.zone_agro,
            "nb_anomalies": nb_anomalies,
            "has_anomalie": nb_anomalies > 0,
            "derniere_consultation": derniere_consult.created_at.isoformat() if derniere_consult else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    if avec_anomalie is not None:
        result = [r for r in result if r["has_anomalie"] == avec_anomalie]

    return result


# ── OBSERVATIONS EN ATTENTE DE VALIDATION ─────────────────────────────────────

@router.get("/observations-a-valider")
def observations_a_valider(
    limit: int = Query(50, le=200),
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """Observations avec anomalie non encore validées par un conseiller."""
    obs = db.query(Observation).filter(
        Observation.org_id == user.org_id,
        Observation.anomalie == True,
        Observation.validation_conseiller == None,
    ).order_by(Observation.created_at.desc()).limit(limit).all()

    result = []
    for o in obs:
        result.append({
            "id": o.id,
            "parcelle_id": o.parcelle_id,
            "type": o.type,
            "chemin": o.chemin,
            "diagnostic": o.diagnostic,
            "etat_simple": o.etat_simple,
            "anomalie": o.anomalie,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })
    return result


@router.patch("/observations/{obs_id}/valider")
def valider_observation(
    obs_id: int,
    data: dict,
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """Valide une observation et ajoute le commentaire conseiller."""
    obs = db.query(Observation).filter(
        Observation.id == obs_id,
        Observation.org_id == user.org_id,
    ).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation introuvable.")

    commentaire = data.get("commentaire", "").strip()
    if not commentaire:
        raise HTTPException(status_code=422, detail="Le commentaire de validation est obligatoire.")

    obs.validation_conseiller = f"[{user.full_name}] {commentaire}"
    db.commit()
    db.refresh(obs)
    return {
        "id": obs.id,
        "validation_conseiller": obs.validation_conseiller,
        "message": "Observation validée.",
    }


# ── DIAGNOSTICS ───────────────────────────────────────────────────────────────

@router.get("/diagnostics-recents")
def diagnostics_recents(
    limit: int = Query(30, le=100),
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """Liste les diagnostics récents de toutes les parcelles de l'org."""
    try:
        consultations = db.query(Consultation).filter(
            Consultation.org_id == user.org_id,
        ).order_by(Consultation.created_at.desc()).limit(limit).all()

        return [{
            "id": c.id,
            "parcelle_id": c.parcelle_id,
            "statut": c.statut if hasattr(c, 'statut') else None,
            "niveau": c.niveau if hasattr(c, 'niveau') else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        } for c in consultations]
    except Exception:
        return []


@router.patch("/diagnostics/{diag_id}/valider")
def valider_diagnostic(
    diag_id: int,
    data: dict,
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """Valide ou infirme un diagnostic automatique."""
    diag = db.query(Diagnostic).filter(Diagnostic.id == diag_id).first()
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnostic introuvable.")

    action = data.get("action", "confirmer")
    if action == "confirmer":
        diag.confirme = True
        diag.exclu = False
    elif action == "exclure":
        diag.confirme = False
        diag.exclu = True
    else:
        raise HTTPException(status_code=422, detail="action doit être 'confirmer' ou 'exclure'.")

    commentaire = data.get("commentaire")
    if commentaire and hasattr(diag, 'commentaire_conseiller'):
        diag.commentaire_conseiller = commentaire

    db.commit()
    return {"id": diag_id, "action": action, "message": f"Diagnostic {action}é."}


# ── RAPPORT CONSEILLER (PDF) ──────────────────────────────────────────────────

@router.get("/rapport/{parcelle_id}")
def rapport_conseiller(
    parcelle_id: int,
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """
    Génère un rapport PDF conseiller pour une parcelle.
    Inclut : infos parcelle, sol, observations, diagnostics, recommandations.
    """
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.org_id == user.org_id,
    ).first()
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                                leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        GREEN = colors.HexColor("#047857")
        LIGHT = colors.HexColor("#d1fae5")

        # Titre
        titre_style = ParagraphStyle("titre", parent=styles["Title"],
                                     textColor=GREEN, fontSize=18, spaceAfter=6)
        story.append(Paragraph("🌾 Rapport Conseiller Agricole", titre_style))
        story.append(Paragraph(f"Parcelle : <b>{parcelle.nom}</b>", styles["Normal"]))
        story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par {user.full_name}",
                                styles["Normal"]))
        story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=12))

        # Infos parcelle
        story.append(Paragraph("Informations de la parcelle", styles["Heading2"]))
        data_table = [
            ["Culture", parcelle.type_culture or "—"],
            ["Superficie", f"{parcelle.superficie_ha:.4f} ha" if parcelle.superficie_ha else "—"],
            ["Région", parcelle.region or "—"],
            ["Zone agro-écologique", parcelle.zone_agro or "—"],
            ["Statut", parcelle.statut.value if parcelle.statut else "—"],
            ["Score complétude", f"{parcelle.score_completude}%"],
            ["Source d'eau", (parcelle.source_eau_principale or "—").replace("_", " ")],
            ["Irrigation", (parcelle.type_irrigation or "—").replace("_", " ")],
        ]
        t = Table(data_table, colWidths=[6*cm, 10*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Sol
        sol = db.query(AnalyseSol).filter(
            AnalyseSol.parcelle_id == parcelle_id
        ).order_by(AnalyseSol.created_at.desc()).first()

        if sol:
            story.append(Paragraph("Analyse du sol", styles["Heading2"]))
            sol_data = [
                ["pH eau", str(sol.pH_eau) if sol.pH_eau else "—"],
                ["Matière organique", f"{sol.matiere_organique}%" if sol.matiere_organique else "—"],
                ["Azote (N)", f"{sol.azote_total} mg/kg" if sol.azote_total else "—"],
                ["Phosphore (P)", f"{sol.phosphore_assim} mg/kg" if sol.phosphore_assim else "—"],
                ["Potassium (K)", f"{sol.potassium_echang} mg/kg" if sol.potassium_echang else "—"],
                ["Conductivité", f"{sol.conductivite_ds_m} dS/m" if sol.conductivite_ds_m else "—"],
                ["Source analyse", (sol.source_analyse or "—").replace("_", " ")],
            ]
            t2 = Table(sol_data, colWidths=[6*cm, 10*cm])
            t2.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t2)
            story.append(Spacer(1, 12))

        # Observations
        obs_list = db.query(Observation).filter(
            Observation.parcelle_id == parcelle_id,
        ).order_by(Observation.created_at.desc()).limit(10).all()

        if obs_list:
            story.append(Paragraph("Observations récentes", styles["Heading2"]))
            for o in obs_list:
                etat = o.etat_simple or "—"
                anomalie_txt = "⚠️ Anomalie détectée" if o.anomalie else "✓ Normal"
                validation = o.validation_conseiller or "En attente de validation"
                date_str = o.created_at.strftime("%d/%m/%Y") if o.created_at else "—"
                story.append(Paragraph(
                    f"<b>{date_str}</b> — {etat} — {anomalie_txt}<br/>"
                    f"<i>Conseiller : {validation}</i>",
                    styles["Normal"]
                ))
                story.append(Spacer(1, 4))
            story.append(Spacer(1, 8))

        # Infrastructures
        infras = db.query(Infrastructure).filter(
            Infrastructure.parcelle_id == parcelle_id
        ).all()
        if infras:
            story.append(Paragraph("Infrastructures", styles["Heading2"]))
            infra_data = [["Type", "Nom", "Catégorie"]] + [
                [i.type.replace("_", " "), i.nom or "—", i.categorie or "—"]
                for i in infras
            ]
            ti = Table(infra_data, colWidths=[5*cm, 6*cm, 5*cm])
            ti.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(ti)
            story.append(Spacer(1, 12))

        # Recommandations conseiller
        story.append(Paragraph("Recommandations du conseiller", styles["Heading2"]))
        reco_style = ParagraphStyle("reco", parent=styles["Normal"],
                                    borderColor=GREEN, borderWidth=1,
                                    borderPadding=8, leading=16)
        story.append(Paragraph(
            "Sur la base des données collectées, le conseiller recommande :<br/>"
            "• Vérifier le pH du sol et corriger si nécessaire.<br/>"
            "• Maintenir un suivi hebdomadaire des observations de santé des cultures.<br/>"
            "• Compléter le profil de la parcelle pour accéder aux recommandations IA.",
            reco_style
        ))

        # Footer
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
        story.append(Paragraph(
            f"<i>Rapport généré par AgroScan Pro — Conseiller : {user.full_name} — {datetime.now().strftime('%d/%m/%Y')}</i>",
            styles["Normal"]
        ))

        doc.build(story)
        buf.seek(0)

        # Sanitize filename: remplacer tout caractère non-ASCII par underscore
        import unicodedata, re as _re
        nom_safe = unicodedata.normalize("NFKD", parcelle.nom)
        nom_safe = nom_safe.encode("ascii", "ignore").decode("ascii")
        nom_safe = _re.sub(r"[^\w]", "_", nom_safe).strip("_") or "parcelle"
        nom_fichier = f"rapport_conseiller_{nom_safe}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nom_fichier}"'},
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab non installé. Impossible de générer le PDF.")


# ── STATISTIQUES GLOBALES ORG ─────────────────────────────────────────────────

@router.get("/statistiques")
def statistiques_org(
    user: User = Depends(_require_conseiller),
    db: Session = Depends(get_db),
):
    """Statistiques agrégées de l'organisation pour le conseiller."""
    org_id = user.org_id

    # Parcelles par statut (hors archives)
    statuts = db.query(
        Parcelle.statut, func.count(Parcelle.id)
    ).filter(
        Parcelle.org_id == org_id,
        Parcelle.statut != StatutParcelle.ARCHIVE,
    ).group_by(Parcelle.statut).all()

    # Parcelles par zone agro (hors archives)
    zones = db.query(
        Parcelle.zone_agro, func.count(Parcelle.id), func.avg(Parcelle.score_completude)
    ).filter(
        Parcelle.org_id == org_id,
        Parcelle.zone_agro != None,
        Parcelle.statut != StatutParcelle.ARCHIVE,
    ).group_by(Parcelle.zone_agro).all()

    # Surface totale (hors archives)
    surface_totale = db.query(func.sum(Parcelle.superficie_ha)).filter(
        Parcelle.org_id == org_id,
        Parcelle.statut != StatutParcelle.ARCHIVE,
    ).scalar() or 0

    # Cultures (hors archives)
    cultures = db.query(
        Parcelle.type_culture, func.count(Parcelle.id)
    ).filter(
        Parcelle.org_id == org_id,
        Parcelle.type_culture != None,
        Parcelle.statut != StatutParcelle.ARCHIVE,
    ).group_by(Parcelle.type_culture).order_by(func.count(Parcelle.id).desc()).limit(10).all()

    return {
        "surface_totale_ha": round(float(surface_totale), 2),
        "par_statut": {str(s.value if s else "inconnu"): n for s, n in statuts},
        "par_zone": [{"zone": z, "nb": n, "score_moyen": round(float(sc), 1) if sc else 0}
                     for z, n, sc in zones],
        "top_cultures": [{"culture": c, "nb": n} for c, n in cultures],
    }
