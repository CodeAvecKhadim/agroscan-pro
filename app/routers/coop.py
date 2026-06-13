"""
Routeur Coopérative — M10 : gestion multi-membres, multi-parcelles, statistiques globales.

Endpoints :
  POST /api/coop/members                  — inviter un membre
  GET  /api/coop/members                  — lister les membres
  PATCH /api/coop/members/{id}            — modifier un membre
  DELETE /api/coop/members/{id}           — désactiver un membre
  POST /api/coop/farms                    — ajouter une exploitation
  GET  /api/coop/farms                    — lister les exploitations
  GET  /api/coop/dashboard                — tableau de bord global
  GET  /api/coop/statistiques             — KPIs agrégés (membres, parcelles, coûts, rendement)
  GET  /api/coop/membres/performances     — comparaison performance par membre
  GET  /api/coop/parcelles                — toutes les parcelles (tous membres)
  GET  /api/coop/activites                — toutes les activités récentes
  GET  /api/coop/alertes                  — alertes santé actives (toute la coop)
  GET  /api/coop/rapport-consolide        — rapport PDF consolidé
"""
import io
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.deps import current_user, current_subscription, require_feature, require_role
from app.core.security import hash_password
from app.models import (User, Farm, Analysis, Subscription, UserRole)
from app.models.champ import Parcelle
from app.models.ferme import Activite, Cout, MainOeuvre, TypeActivite
from app.models.sante import Consultation, Diagnostic, StatutConsultation
from app.models.exploitation import Exploitation
from app.schemas import FarmIn, FarmOut, InviteMemberIn, UserOut
from app.services.plans import features_for

router = APIRouter(prefix="/api/coop", tags=["Coopérative"])


def _require_coop(user: User = Depends(current_user)) -> User:
    allowed = {UserRole.OWNER, UserRole.ADMIN, UserRole.SUPER_ADMIN,
               UserRole.CONSEILLER}
    role_val = user.role.value if hasattr(user.role, 'value') else str(user.role)
    allowed_vals = {r.value for r in allowed}
    if role_val not in allowed_vals:
        raise HTTPException(403, "Accès réservé aux gestionnaires de coopérative.")
    return user


# ── Membres ────────────────────────────────────────────────────────────────────

@router.post("/members", response_model=UserOut, status_code=201,
             dependencies=[Depends(require_feature("multi_user"))])
def invite_member(
    data: InviteMemberIn,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    sub: Subscription = Depends(current_subscription),
    db: Session = Depends(get_db),
):
    """Ajoute un membre à la coopérative, dans la limite des sièges payés."""
    count = db.query(func.count(User.id)).filter(User.org_id == user.org_id).scalar()
    if count >= sub.seats:
        raise HTTPException(
            status_code=402,
            detail=f"Limite de {sub.seats} membre(s) atteinte. Ajoutez des sièges.",
        )
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé.")

    member = User(
        org_id=user.org_id, full_name=data.full_name, email=data.email,
        phone=data.phone, hashed_password=hash_password(data.password), role=data.role,
        profil="producteur",
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/members", response_model=List[UserOut],
            dependencies=[Depends(require_feature("multi_user"))])
def list_members(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Liste les membres de la coopérative."""
    return db.query(User).filter(User.org_id == user.org_id).all()


@router.patch("/members/{member_id}", response_model=UserOut)
def update_member(
    member_id: int,
    data: dict,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Modifier le rôle, nom ou téléphone d'un membre."""
    member = db.query(User).filter_by(id=member_id, org_id=user.org_id).first()
    if not member:
        raise HTTPException(404, "Membre introuvable.")
    allowed = {"full_name", "phone", "role", "profil"}
    for k, v in data.items():
        if k in allowed and v is not None:
            if k == "role":
                try:
                    v = UserRole(v)
                except ValueError:
                    raise HTTPException(400, f"Rôle '{v}' invalide.")
            setattr(member, k, v)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/members/{member_id}", status_code=204)
def deactivate_member(
    member_id: int,
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Désactiver un compte membre (soft delete)."""
    member = db.query(User).filter_by(id=member_id, org_id=user.org_id).first()
    if not member:
        raise HTTPException(404, "Membre introuvable.")
    if member.id == user.id:
        raise HTTPException(400, "Impossible de désactiver votre propre compte.")
    member.is_active = False
    db.commit()


# ── Exploitations (legacy) ─────────────────────────────────────────────────────

@router.post("/farms", response_model=FarmOut, status_code=201,
             dependencies=[Depends(require_feature("multi_farm"))])
def create_farm(data: FarmIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Enregistre une exploitation / parcelle."""
    farm = Farm(org_id=user.org_id, **data.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/farms", response_model=List[FarmOut],
            dependencies=[Depends(require_feature("multi_farm"))])
def list_farms(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Liste les exploitations de l'organisation."""
    return db.query(Farm).filter(Farm.org_id == user.org_id).all()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """
    Vue d'ensemble globale : membres, parcelles, analyses, performances,
    répartition par culture et région.
    """
    org_id = user.org_id
    n_members = db.query(func.count(User.id)).filter(
        User.org_id == org_id, User.is_active == True).scalar()
    n_parcelles = db.query(func.count(Parcelle.id)).filter(Parcelle.org_id == org_id).scalar()
    surface_totale = db.query(func.sum(Parcelle.superficie_ha)).filter(
        Parcelle.org_id == org_id).scalar() or 0
    n_analyses = db.query(func.count(Analysis.id)).filter(Analysis.org_id == org_id).scalar()
    avg_score = db.query(func.avg(Analysis.score)).filter(Analysis.org_id == org_id).scalar()
    avg_completude = db.query(func.avg(Parcelle.score_completude)).filter(
        Parcelle.org_id == org_id).scalar() or 0

    # Activités
    n_activites = db.query(func.count(Activite.id)).filter(
        Activite.org_id == org_id).scalar()
    total_couts = db.query(func.sum(Cout.montant_total_fcfa)).filter(
        Cout.org_id == org_id).scalar() or 0
    total_mo = db.query(func.sum(MainOeuvre.montant_total_fcfa)).filter(
        MainOeuvre.org_id == org_id).scalar() or 0

    # Consultations santé
    n_consultations = db.query(func.count(Consultation.id)).filter(
        Consultation.org_id == org_id).scalar()
    n_en_cours = db.query(func.count(Consultation.id)).filter(
        Consultation.org_id == org_id,
        Consultation.statut == StatutConsultation.EN_COURS,
    ).scalar()

    # Répartition cultures
    by_culture = dict(
        db.query(Parcelle.type_culture, func.count(Parcelle.id))
          .filter(Parcelle.org_id == org_id, Parcelle.type_culture.isnot(None))
          .group_by(Parcelle.type_culture)
          .order_by(desc(func.count(Parcelle.id)))
          .limit(10).all()
    )
    by_region = dict(
        db.query(Parcelle.region, func.count(Parcelle.id))
          .filter(Parcelle.org_id == org_id, Parcelle.region.isnot(None))
          .group_by(Parcelle.region).all()
    )

    # Répartition activités par type
    by_activite = dict(
        db.query(Activite.type, func.count(Activite.id))
          .filter(Activite.org_id == org_id)
          .group_by(Activite.type).all()
    )
    by_activite = {str(k.value if hasattr(k, 'value') else k): v
                   for k, v in by_activite.items()}

    return {
        "membres": n_members,
        "parcelles": n_parcelles,
        "surface_totale_ha": round(float(surface_totale), 2),
        "analyses": n_analyses,
        "score_moyen": round(float(avg_score), 1) if avg_score else 0,
        "score_completude_moyen": round(float(avg_completude), 1),
        "activites": n_activites,
        "total_depenses_fcfa": int(total_couts + total_mo),
        "consultations_sante": n_consultations,
        "consultations_en_cours": n_en_cours,
        "par_culture": by_culture,
        "par_region": by_region,
        "par_type_activite": by_activite,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Statistiques globales ──────────────────────────────────────────────────────

@router.get("/statistiques")
def statistiques(
    user: User = Depends(_require_coop),
    db: Session = Depends(get_db),
):
    """KPIs agrégés pour la coopérative (production, finances, rendement)."""
    org_id = user.org_id

    # Production
    exploitations = db.query(Exploitation).filter_by(org_id=org_id).all()
    prod_totale = sum(float(e.production_estimee or 0) for e in exploitations)
    rev_totaux = sum(e.revenus_estimes or 0 for e in exploitations)
    couts_estimes = sum(e.couts_estimes or 0 for e in exploitations)

    # Coûts réels (activités)
    total_intrants = db.query(func.sum(Cout.montant_total_fcfa)).filter(
        Cout.org_id == org_id).scalar() or 0
    total_mo = db.query(func.sum(MainOeuvre.montant_total_fcfa)).filter(
        MainOeuvre.org_id == org_id).scalar() or 0
    couts_reels = int(total_intrants + total_mo)

    # Récoltes
    recoltes = db.query(Activite).filter(
        Activite.org_id == org_id,
        Activite.type == TypeActivite.RECOLTE,
    ).all()
    rendement_recolte_kg = sum(
        (a.details or {}).get("rendement_kg", 0) or 0
        for a in recoltes
    )

    # Superficie par zone
    par_zone = dict(
        db.query(Parcelle.zone_agro, func.sum(Parcelle.superficie_ha))
          .filter(Parcelle.org_id == org_id, Parcelle.zone_agro.isnot(None))
          .group_by(Parcelle.zone_agro).all()
    )
    par_zone = {k: round(float(v or 0), 2) for k, v in par_zone.items()}

    # Score complétude moyen par culture
    par_culture_score = db.query(
        Parcelle.type_culture,
        func.avg(Parcelle.score_completude),
        func.count(Parcelle.id),
        func.sum(Parcelle.superficie_ha),
    ).filter(
        Parcelle.org_id == org_id, Parcelle.type_culture.isnot(None)
    ).group_by(Parcelle.type_culture).all()

    cultures_stats = [
        {
            "culture": row[0],
            "score_moyen": round(float(row[1] or 0), 1),
            "nb_parcelles": row[2],
            "surface_ha": round(float(row[3] or 0), 2),
        }
        for row in par_culture_score
    ]

    # Tendance mensuelle activités (6 derniers mois)
    six_mois = datetime.now(timezone.utc) - timedelta(days=180)
    activites_recentes = db.query(Activite).filter(
        Activite.org_id == org_id,
        Activite.created_at >= six_mois,
    ).all()
    par_mois = {}
    for a in activites_recentes:
        if a.created_at:
            mois = a.created_at.strftime("%Y-%m")
            par_mois[mois] = par_mois.get(mois, 0) + 1

    return {
        "production": {
            "prod_totale_kg": prod_totale,
            "revenus_estimes_fcfa": rev_totaux,
            "couts_estimes_fcfa": couts_estimes,
            "benefice_estime_fcfa": rev_totaux - couts_estimes,
            "rendement_recolte_kg": rendement_recolte_kg,
        },
        "finances": {
            "couts_reels_fcfa": couts_reels,
            "intrants_fcfa": int(total_intrants),
            "main_oeuvre_fcfa": int(total_mo),
        },
        "surfaces": {
            "par_zone_agro": par_zone,
        },
        "cultures": cultures_stats,
        "activites_par_mois": dict(sorted(par_mois.items())),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Performances par membre ────────────────────────────────────────────────────

@router.get("/membres/performances")
def performances_membres(
    user: User = Depends(_require_coop),
    db: Session = Depends(get_db),
):
    """Comparaison des performances par membre (parcelles, surface, coûts, activités)."""
    org_id = user.org_id
    membres = db.query(User).filter_by(org_id=org_id, is_active=True).all()

    results = []
    for m in membres:
        parcelles = db.query(Parcelle).filter_by(org_id=org_id).filter(
            Parcelle.score_completude >= 0).all()
        # Parcelles associées à ce membre via activités
        activites = db.query(Activite).filter_by(org_id=org_id, created_by=m.id).all()
        act_ids = [a.id for a in activites]
        couts_m = db.query(func.sum(Cout.montant_total_fcfa)).filter(
            Cout.activite_id.in_(act_ids)).scalar() or 0 if act_ids else 0
        mo_m = db.query(func.sum(MainOeuvre.montant_total_fcfa)).filter(
            MainOeuvre.activite_id.in_(act_ids)).scalar() or 0 if act_ids else 0
        consultations_m = db.query(func.count(Consultation.id)).filter_by(
            org_id=org_id, created_by=m.id).scalar()

        results.append({
            "membre_id": m.id,
            "nom": m.full_name,
            "email": m.email,
            "role": m.role.value if hasattr(m.role, 'value') else str(m.role),
            "nb_activites": len(activites),
            "couts_totaux_fcfa": int(couts_m + mo_m),
            "consultations_sante": consultations_m,
        })

    return {
        "membres": results,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Parcelles globales ─────────────────────────────────────────────────────────

@router.get("/parcelles")
def all_parcelles(
    culture: Optional[str] = Query(None),
    zone_agro: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(_require_coop),
    db: Session = Depends(get_db),
):
    """Toutes les parcelles de la coopérative avec filtres."""
    q = db.query(Parcelle).filter_by(org_id=user.org_id)
    if culture:
        q = q.filter(Parcelle.type_culture.ilike(f"%{culture}%"))
    if zone_agro:
        q = q.filter(Parcelle.zone_agro == zone_agro)
    if min_score is not None:
        q = q.filter(Parcelle.score_completude >= min_score)
    total = q.count()
    items = q.order_by(desc(Parcelle.created_at)).offset(skip).limit(limit).all()
    return {
        "total": total,
        "parcelles": [
            {
                "id": p.id,
                "nom": p.nom,
                "culture": p.type_culture,
                "surface_ha": p.superficie_ha,
                "zone_agro": p.zone_agro,
                "region": p.region,
                "statut": p.statut.value if hasattr(p.statut, 'value') else str(p.statut),
                "score": p.score_completude,
                "wizard_complet": p.wizard_complet,
                "code": p.code_parcelle,
                "created_at": p.created_at,
            }
            for p in items
        ],
    }


# ── Activités récentes ─────────────────────────────────────────────────────────

@router.get("/activites")
def activites_recentes(
    jours: int = Query(30, ge=1, le=365),
    type_activite: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(_require_coop),
    db: Session = Depends(get_db),
):
    """Activités récentes de tous les membres de la coopérative."""
    from datetime import timedelta
    depuis = datetime.now(timezone.utc) - timedelta(days=jours)
    q = db.query(Activite).filter(
        Activite.org_id == user.org_id,
        Activite.created_at >= depuis,
    )
    if type_activite:
        try:
            q = q.filter(Activite.type == TypeActivite(type_activite))
        except ValueError:
            pass
    total = q.count()
    items = q.order_by(desc(Activite.created_at)).offset(skip).limit(limit).all()
    return {
        "total": total,
        "activites": [
            {
                "id": a.id,
                "type": a.type.value if hasattr(a.type, 'value') else str(a.type),
                "titre": a.titre,
                "statut": a.statut.value if hasattr(a.statut, 'value') else str(a.statut),
                "date_prevue": a.date_prevue,
                "parcelle_id": a.parcelle_id,
                "created_by": a.created_by,
                "created_at": a.created_at,
            }
            for a in items
        ],
    }


# ── Alertes santé actives ──────────────────────────────────────────────────────

@router.get("/alertes")
def alertes_sante(
    user: User = Depends(_require_coop),
    db: Session = Depends(get_db),
):
    """Consultations santé en cours (toute la coopérative) — alertes actives."""
    consultations = db.query(Consultation).filter(
        Consultation.org_id == user.org_id,
        Consultation.statut == StatutConsultation.EN_COURS,
    ).order_by(desc(Consultation.created_at)).limit(50).all()

    alertes = []
    for c in consultations:
        diag = (db.query(Diagnostic)
                .filter_by(consultation_id=c.id)
                .order_by(Diagnostic.rang)
                .first())
        alertes.append({
            "consultation_id": c.id,
            "type": c.type.value if hasattr(c.type, 'value') else str(c.type),
            "parcelle_id": c.parcelle_id,
            "date": c.created_at,
            "diagnostic_principal": diag.entite_nom if diag else None,
            "confiance": diag.score_confiance if diag else None,
            "contexte": c.contexte or {},
        })

    return {
        "nb_alertes": len(alertes),
        "alertes": alertes,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Rapport consolidé PDF ─────────────────────────────────────────────────────

@router.get("/rapport-consolide")
def rapport_consolide(
    user: User = Depends(_require_coop),
    db: Session = Depends(get_db),
):
    """Rapport PDF consolidé de la coopérative (dashboard complet)."""
    from app.models import Organization
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER

    org = db.query(Organization).filter_by(id=user.org_id).first()
    org_name = org.name if org else f"Coopérative #{user.org_id}"

    # Données
    dash = dashboard.__wrapped__(user, db) if hasattr(dashboard, '__wrapped__') else None

    org_id = user.org_id
    n_membres = db.query(func.count(User.id)).filter_by(org_id=org_id, is_active=True).scalar()
    n_parcelles = db.query(func.count(Parcelle.id)).filter_by(org_id=org_id).scalar()
    surface = db.query(func.sum(Parcelle.superficie_ha)).filter_by(org_id=org_id).scalar() or 0
    total_couts = (db.query(func.sum(Cout.montant_total_fcfa)).filter_by(org_id=org_id).scalar() or 0) + \
                  (db.query(func.sum(MainOeuvre.montant_total_fcfa)).filter_by(org_id=org_id).scalar() or 0)

    by_culture = db.query(
        Parcelle.type_culture, func.count(Parcelle.id), func.sum(Parcelle.superficie_ha)
    ).filter(
        Parcelle.org_id == org_id, Parcelle.type_culture.isnot(None)
    ).group_by(Parcelle.type_culture).order_by(desc(func.count(Parcelle.id))).all()

    buf = io.BytesIO()
    vert = colors.HexColor("#166534")
    gris = colors.HexColor("#6b7280")

    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("t", parent=styles["Heading1"], fontSize=18,
                             spaceAfter=4, textColor=vert, alignment=TA_CENTER)
    sub_s = ParagraphStyle("s", parent=styles["Normal"], fontSize=10,
                           spaceAfter=4, textColor=gris, alignment=TA_CENTER)
    section_s = ParagraphStyle("sec", parent=styles["Heading2"], fontSize=12,
                               spaceBefore=10, spaceAfter=4, textColor=vert)
    body_s = ParagraphStyle("b", parent=styles["Normal"], fontSize=10,
                            spaceAfter=3, leading=14)
    footer_s = ParagraphStyle("f", parent=styles["Normal"], fontSize=8,
                              textColor=gris, alignment=TA_CENTER)

    tbl_head = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), vert),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0fdf4")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])

    story = []
    story.append(Paragraph("AgroScan Pro", title_s))
    story.append(Paragraph("Rapport Consolidé Coopérative", sub_s))
    story.append(Paragraph(org_name, sub_s))
    story.append(Paragraph(
        f"Généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M')} UTC", sub_s))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Vue d'Ensemble", section_s))
    kpi = Table([
        ["KPI", "Valeur"],
        ["Membres actifs", str(n_membres)],
        ["Parcelles", str(n_parcelles)],
        ["Surface totale", f"{float(surface):.2f} ha"],
        ["Total dépenses", f"{int(total_couts):,} FCFA"],
    ], colWidths=[9*cm, 7*cm])
    kpi.setStyle(tbl_head)
    story.append(kpi)
    story.append(Spacer(1, 0.3*cm))

    if by_culture:
        story.append(Paragraph("Répartition par Culture", section_s))
        cult_rows = [["Culture", "Nbre parcelles", "Surface (ha)"]]
        for row in by_culture[:10]:
            cult_rows.append([
                row[0] or "—",
                str(row[1]),
                f"{float(row[2] or 0):.2f}",
            ])
        cult_tbl = Table(cult_rows, colWidths=[7*cm, 4.5*cm, 4.5*cm])
        cult_tbl.setStyle(tbl_head)
        story.append(cult_tbl)

    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("© AgroScan Pro — Social Technologie | +221 78 491 90 11", footer_s))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="coop_consolide_{now_str}.pdf"'},
    )
