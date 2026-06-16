"""
Rapports PDF — 5 types conformes au PRD Global V1.

Endpoints :
  GET /api/rapports/sante/{consultation_id}      → diagnostic maladie / ravageur / fertilisation
  GET /api/rapports/satellite/{parcelle_id}      → analyse NDVI + précision satellite
  GET /api/rapports/fertilite/{parcelle_id}      → profil sol chimique + recommandations
  GET /api/rapports/rendement/{parcelle_id}      → récolte, coûts, ROI campagne
  GET /api/rapports/exploitation                 → bilan global exploitation (toutes parcelles)
"""
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.models.champ import Parcelle, AnalyseSol, Cartographie, StatutParcelle
from app.models.sante import (
    Consultation, Diagnostic, Traitement, Suivi, RapportSante,
    TypeConsultation, StatutTraitement,
)
from app.models.ferme import Activite, Cout, MainOeuvre, TypeActivite
from app.models.analyses_satellite import AnalyseSatellite
from app.models.exploitation import Exploitation

router = APIRouter(prefix="/api/rapports", tags=["Rapports PDF"])


# ── Utilitaires ReportLab communs ──────────────────────────────────────────────

def _get_rl():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    return (A4, getSampleStyleSheet, ParagraphStyle, cm, colors,
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, TA_CENTER, TA_LEFT, TA_RIGHT)


def _styles_communs():
    (A4, getSampleStyleSheet, ParagraphStyle, cm, colors,
     SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
     HRFlowable, TA_CENTER, TA_LEFT, TA_RIGHT) = _get_rl()

    styles = getSampleStyleSheet()
    vert = colors.HexColor("#166534")
    gris = colors.HexColor("#6b7280")
    rouge = colors.HexColor("#991b1b")
    orange = colors.HexColor("#92400e")

    title_s = ParagraphStyle("title", parent=styles["Heading1"],
                             fontSize=18, spaceAfter=4,
                             textColor=vert, alignment=TA_CENTER)
    sub_s = ParagraphStyle("sub", parent=styles["Normal"],
                           fontSize=10, spaceAfter=4,
                           textColor=gris, alignment=TA_CENTER)
    section_s = ParagraphStyle("section", parent=styles["Heading2"],
                               fontSize=12, spaceBefore=10, spaceAfter=4,
                               textColor=vert)
    body_s = ParagraphStyle("body", parent=styles["Normal"],
                            fontSize=10, spaceAfter=3, leading=14)
    bold_s = ParagraphStyle("bold", parent=styles["Normal"],
                            fontSize=10, spaceAfter=3, leading=14,
                            fontName="Helvetica-Bold")
    footer_s = ParagraphStyle("footer", parent=styles["Normal"],
                              fontSize=8, textColor=gris, alignment=TA_CENTER)
    return (styles, vert, gris, rouge, orange, title_s, sub_s,
            section_s, body_s, bold_s, footer_s, cm, colors,
            Paragraph, Spacer, Table, TableStyle, HRFlowable, A4,
            SimpleDocTemplate, TA_CENTER, TA_LEFT)


def _header(story, titre, sous_titre, Paragraph, Spacer, cm,
            title_s, sub_s):
    story.append(Paragraph("AgroScan Pro", title_s))
    story.append(Paragraph(titre, sub_s))
    story.append(Paragraph(sous_titre, sub_s))
    story.append(Paragraph(
        f"Généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M')} UTC",
        sub_s,
    ))
    story.append(Spacer(1, 0.4 * cm))


def _footer(story, Paragraph, Spacer, cm, footer_s):
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(
        "© AgroScan Pro — Social Technologie | +221 78 491 90 11",
        footer_s,
    ))


def _tbl_style(colors, TableStyle):
    return TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0fdf4")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#166534")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.white, colors.HexColor("#f9fafb")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])


def _stream(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── 1. RAPPORT SANTÉ CULTURES ─────────────────────────────────────────────────

def _build_sante_pdf(consultation: Consultation, user_name: str) -> bytes:
    (styles, vert, gris, rouge, orange, title_s, sub_s, section_s,
     body_s, bold_s, footer_s, cm, colors, Paragraph, Spacer, Table,
     TableStyle, HRFlowable, A4, SimpleDocTemplate, TA_CENTER, TA_LEFT) = _styles_communs()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    type_label = {
        "maladie": "Diagnostic Maladie",
        "ravageur": "Diagnostic Ravageur",
        "fertilisation": "Plan de Fertilisation",
    }.get(consultation.type.value if hasattr(consultation.type, 'value') else str(consultation.type),
          "Diagnostic")

    _header(story, "Rapport Santé des Cultures",
            type_label, Paragraph, Spacer, cm, title_s, sub_s)

    # Informations consultation
    story.append(Paragraph("Informations Consultation", section_s))
    ctx = consultation.contexte or {}
    rows = [
        ["N° Consultation", f"#{consultation.id}"],
        ["Type", type_label],
        ["Statut", str(consultation.statut.value if hasattr(consultation.statut, 'value') else consultation.statut)],
        ["Culture", ctx.get("culture", "—")],
        ["Stade", ctx.get("stade", "—")],
        ["Zone agro-écologique", ctx.get("zone_agro", "—")],
        ["Date", consultation.created_at.strftime("%d/%m/%Y") if consultation.created_at else "—"],
        ["Réalisé par", user_name],
    ]
    tbl = Table(rows, colWidths=[5*cm, 11*cm])
    tbl.setStyle(_tbl_style(colors, TableStyle))
    story.append(tbl)
    story.append(Spacer(1, 0.3*cm))

    # Résumé
    if consultation.resume:
        story.append(Paragraph("Synthèse", section_s))
        story.append(Paragraph(consultation.resume, body_s))

    # Diagnostics
    if consultation.diagnostics:
        story.append(Paragraph("Diagnostics Identifiés", section_s))
        for d in consultation.diagnostics:
            conf_pct = int(d.score_confiance * 100)
            conf_color = vert if conf_pct >= 70 else (orange if conf_pct >= 40 else rouge)
            from reportlab.lib.styles import ParagraphStyle as PS
            conf_s = PS("conf", parent=styles["Normal"], fontSize=10,
                        textColor=conf_color, spaceAfter=2)
            story.append(Paragraph(
                f"<b>#{d.rang} — {d.entite_nom or '—'}</b>  "
                f"({d.entite_type.value if hasattr(d.entite_type, 'value') else d.entite_type})",
                body_s,
            ))
            story.append(Paragraph(f"Confiance : {conf_pct}%  |  Statut : {d.statut.value if hasattr(d.statut, 'value') else d.statut}", conf_s))
            if d.note_expert:
                story.append(Paragraph(f"Note expert : {d.note_expert}", body_s))
            story.append(Spacer(1, 0.2*cm))

    # Plan de traitement
    if consultation.traitements:
        story.append(Paragraph("Plan de Traitement", section_s))
        trait_rows = [["Priorité", "Type", "Traitement", "Produit", "Dose", "Statut"]]
        for t in sorted(consultation.traitements, key=lambda x: x.priorite or 5):
            trait_rows.append([
                str(t.priorite or "—"),
                str(t.type.value if hasattr(t.type, 'value') else t.type),
                t.titre[:40] if t.titre else "—",
                t.produit or "—",
                t.dose or "—",
                str(t.statut.value if hasattr(t.statut, 'value') else t.statut),
            ])
        tbl2 = Table(trait_rows, colWidths=[1.5*cm, 3*cm, 4.5*cm, 3*cm, 2*cm, 2*cm])
        tbl2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl2)
        story.append(Spacer(1, 0.3*cm))

    # Suivis
    if consultation.suivis:
        story.append(Paragraph("Suivi Post-Traitement", section_s))
        for s in consultation.suivis:
            evo = s.evolution.value if hasattr(s.evolution, 'value') else str(s.evolution or "—")
            story.append(Paragraph(
                f"<b>{s.date_suivi}</b> — Évolution : {evo} | Efficacité : {s.efficacite or '—'}/5",
                body_s,
            ))
            if s.note:
                story.append(Paragraph(f"Note : {s.note}", body_s))

    _footer(story, Paragraph, Spacer, cm, footer_s)
    doc.build(story)
    return buf.getvalue()


@router.get("/sante/{consultation_id}")
def rapport_sante(
    consultation_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Rapport PDF Santé des Cultures — diagnostic, traitements et suivis."""
    c = (db.query(Consultation)
         .options(
             selectinload(Consultation.diagnostics),
             selectinload(Consultation.traitements),
             selectinload(Consultation.suivis),
         )
         .filter_by(id=consultation_id, org_id=user.org_id)
         .first())
    if not c:
        raise HTTPException(404, "Consultation introuvable.")

    pdf_bytes = _build_sante_pdf(c, user.full_name)
    return _stream(pdf_bytes, f"sante_consultation_{consultation_id}.pdf")


# ── 2. RAPPORT PRÉCISION SATELLITE ────────────────────────────────────────────

def _build_satellite_pdf(parcelle: Parcelle, analyses: list, sol: Optional[AnalyseSol]) -> bytes:
    (styles, vert, gris, rouge, orange, title_s, sub_s, section_s,
     body_s, bold_s, footer_s, cm, colors, Paragraph, Spacer, Table,
     TableStyle, HRFlowable, A4, SimpleDocTemplate, TA_CENTER, TA_LEFT) = _styles_communs()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    _header(story, "Rapport Précision Satellite",
            f"Parcelle : {parcelle.nom}", Paragraph, Spacer, cm, title_s, sub_s)

    # Infos parcelle
    story.append(Paragraph("Informations Parcelle", section_s))
    rows = [
        ["Nom", parcelle.nom or "—"],
        ["Culture", parcelle.type_culture or "—"],
        ["Zone agro-écologique", parcelle.zone_agro or "—"],
        ["Superficie", f"{parcelle.superficie_ha:.2f} ha" if parcelle.superficie_ha else "—"],
        ["Coordonnées",
         f"{parcelle.centre_lat:.4f}, {parcelle.centre_lon:.4f}" if parcelle.centre_lat else "—"],
    ]
    tbl = Table(rows, colWidths=[5*cm, 11*cm])
    tbl.setStyle(_tbl_style(colors, TableStyle))
    story.append(tbl)
    story.append(Spacer(1, 0.3*cm))

    # Historique NDVI
    if analyses:
        story.append(Paragraph("Historique des Analyses Satellitaires", section_s))
        ndvi_rows = [["Date", "NDVI", "NDRE", "NDWI", "Couleur", "Message"]]
        for a in analyses[:10]:
            msg = (a.message_simple or "")[:50] + ("…" if len(a.message_simple or "") > 50 else "")
            ndvi_rows.append([
                str(a.date),
                str(a.ndvi_moyen or "—"),
                str(a.ndre or "—"),
                str(a.ndwi or "—"),
                a.couleur or "—",
                msg,
            ])
        tbl2 = Table(ndvi_rows, colWidths=[2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 5.5*cm])
        tbl2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl2)
        story.append(Spacer(1, 0.3*cm))

        # Dernière analyse détaillée
        dernier = analyses[0]
        if dernier.message_simple:
            story.append(Paragraph("Dernier Message d'Analyse", section_s))
            story.append(Paragraph(dernier.message_simple, body_s))

    # Analyse sol satellite
    if sol and sol.analyse_satellite:
        sat = sol.analyse_satellite
        story.append(Paragraph("Analyse Sol Satellite Détaillée", section_s))

        geo = sat.get("geographie", {})
        topo = sat.get("topographie", {})
        risques = sat.get("risques", {})

        if geo:
            story.append(Paragraph("Géographie", bold_s))
            for k, v in geo.items():
                story.append(Paragraph(f"• {k.replace('_', ' ').title()} : {v}", body_s))

        if topo:
            story.append(Paragraph("Topographie", bold_s))
            for k, v in topo.items():
                story.append(Paragraph(f"• {k.replace('_', ' ').title()} : {v}", body_s))

        if risques:
            story.append(Paragraph("Risques", bold_s))
            for k, v in risques.items():
                story.append(Paragraph(f"• {k.replace('_', ' ').title()} : {v}", body_s))

    _footer(story, Paragraph, Spacer, cm, footer_s)
    doc.build(story)
    return buf.getvalue()


@router.get("/satellite/{parcelle_id}")
def rapport_satellite(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Rapport PDF Précision Satellite — NDVI, indices et analyse sol."""
    parcelle = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not parcelle:
        raise HTTPException(404, "Parcelle introuvable.")

    analyses = (db.query(AnalyseSatellite)
                .filter_by(parcelle_id=parcelle_id, org_id=user.org_id)
                .order_by(AnalyseSatellite.date.desc())
                .all())

    sol = (db.query(AnalyseSol)
           .filter_by(parcelle_id=parcelle_id)
           .order_by(AnalyseSol.date_analyse.desc())
           .first())

    pdf_bytes = _build_satellite_pdf(parcelle, analyses, sol)
    return _stream(pdf_bytes, f"satellite_parcelle_{parcelle_id}.pdf")


# ── 3. RAPPORT FERTILITÉ ──────────────────────────────────────────────────────

def _build_fertilite_pdf(parcelle: Parcelle, sols: list) -> bytes:
    (styles, vert, gris, rouge, orange, title_s, sub_s, section_s,
     body_s, bold_s, footer_s, cm, colors, Paragraph, Spacer, Table,
     TableStyle, HRFlowable, A4, SimpleDocTemplate, TA_CENTER, TA_LEFT) = _styles_communs()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    _header(story, "Rapport de Fertilité du Sol",
            f"Parcelle : {parcelle.nom}", Paragraph, Spacer, cm, title_s, sub_s)

    # Infos parcelle
    story.append(Paragraph("Informations Parcelle", section_s))
    rows = [
        ["Nom", parcelle.nom or "—"],
        ["Culture", parcelle.type_culture or "—"],
        ["Zone agro-écologique", parcelle.zone_agro or "—"],
        ["Région", parcelle.region or "—"],
        ["Superficie", f"{parcelle.superficie_ha:.2f} ha" if parcelle.superficie_ha else "—"],
    ]
    tbl = Table(rows, colWidths=[5*cm, 11*cm])
    tbl.setStyle(_tbl_style(colors, TableStyle))
    story.append(tbl)
    story.append(Spacer(1, 0.3*cm))

    if not sols:
        story.append(Paragraph("Aucune analyse de sol disponible pour cette parcelle.", body_s))
    else:
        sol = sols[0]
        story.append(Paragraph(
            f"Dernière Analyse : {sol.date_analyse or '—'}  |  Source : {sol.source_analyse or '—'}",
            bold_s,
        ))
        story.append(Spacer(1, 0.2*cm))

        # Paramètres chimiques
        story.append(Paragraph("Paramètres Chimiques", section_s))
        params = [
            ["Paramètre", "Valeur", "Unité", "Interprétation"],
            ["pH eau", str(sol.pH_eau or "—"), "", _interp_ph(sol.pH_eau)],
            ["pH KCl", str(sol.pH_kcl or "—"), "", ""],
            ["Matière organique", str(sol.matiere_organique or "—"), "%", _interp_mo(sol.matiere_organique)],
            ["Azote total", str(sol.azote_total or "—"), "g/kg", ""],
            ["Phosphore assimilable", str(sol.phosphore_assim or "—"), "mg/kg", _interp_p(sol.phosphore_assim)],
            ["Potassium échangeable", str(sol.potassium_echang or "—"), "cmol+/kg", ""],
            ["Calcium", str(sol.calcium or "—"), "cmol+/kg", ""],
            ["Magnésium", str(sol.magnesium or "—"), "cmol+/kg", ""],
            ["CEC", str(sol.cec or "—"), "cmol+/kg", _interp_cec(sol.cec)],
            ["Conductivité", str(sol.conductivite_ds_m or "—"), "dS/m", _interp_ce(sol.conductivite_ds_m)],
        ]
        tbl2 = Table(params, colWidths=[5*cm, 3*cm, 3*cm, 5*cm])
        tbl2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl2)
        story.append(Spacer(1, 0.3*cm))

        # Paramètres physiques
        story.append(Paragraph("Paramètres Physiques", section_s))
        phys = [
            ["Texture", str(sol.texture.value if hasattr(sol.texture, 'value') else sol.texture or "—")],
            ["Profondeur labour", f"{sol.profondeur_labour_cm} cm" if sol.profondeur_labour_cm else "—"],
            ["Pierrosité", f"{sol.pierrosite_pct} %" if sol.pierrosite_pct else "—"],
            ["Érosion", str(sol.erosion.value if hasattr(sol.erosion, 'value') else sol.erosion or "—")],
        ]
        tbl3 = Table(phys, colWidths=[5*cm, 11*cm])
        tbl3.setStyle(_tbl_style(colors, TableStyle))
        story.append(tbl3)
        story.append(Spacer(1, 0.3*cm))

        # Recommandations
        recs = _recs_fertilite(sol)
        if recs:
            story.append(Paragraph("Recommandations de Fertilisation", section_s))
            for r in recs:
                story.append(Paragraph(f"• {r}", body_s))

        if sol.observations:
            story.append(Paragraph("Observations", section_s))
            story.append(Paragraph(sol.observations, body_s))

        # Historique
        if len(sols) > 1:
            story.append(Paragraph("Historique des Analyses", section_s))
            hist = [["Date", "pH eau", "MO (%)", "N (g/kg)", "P (mg/kg)", "K (cmol+/kg)", "Source"]]
            for s in sols[:5]:
                hist.append([
                    str(s.date_analyse or "—"),
                    str(s.pH_eau or "—"),
                    str(s.matiere_organique or "—"),
                    str(s.azote_total or "—"),
                    str(s.phosphore_assim or "—"),
                    str(s.potassium_echang or "—"),
                    s.source_analyse or "—",
                ])
            tbl4 = Table(hist, colWidths=[2.5*cm, 2*cm, 2*cm, 2*cm, 2.5*cm, 3*cm, 2*cm])
            tbl4.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f9fafb")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(tbl4)

    _footer(story, Paragraph, Spacer, cm, footer_s)
    doc.build(story)
    return buf.getvalue()


def _interp_ph(v):
    if v is None:
        return ""
    if v < 5.5:
        return "Très acide — risque toxicité Al/Mn"
    if v < 6.0:
        return "Acide — limiter cultures sensibles"
    if v <= 7.0:
        return "Optimal pour la plupart des cultures"
    if v <= 8.0:
        return "Légèrement alcalin — surveiller oligo-éléments"
    return "Très alcalin — carence probable en Fe/Mn/Zn"


def _interp_mo(v):
    if v is None:
        return ""
    if v < 1.0:
        return "Très faible — apporter matière organique"
    if v < 2.0:
        return "Faible — compost recommandé"
    if v <= 3.5:
        return "Moyen — satisfaisant"
    return "Élevé — très favorable"


def _interp_p(v):
    if v is None:
        return ""
    if v < 10:
        return "Déficient — fumure P urgente"
    if v < 30:
        return "Moyen — enrichissement conseillé"
    return "Satisfaisant"


def _interp_cec(v):
    if v is None:
        return ""
    if v < 6:
        return "Très faible rétention (sol sableux)"
    if v < 12:
        return "Faible — risque lessivage"
    if v <= 25:
        return "Moyen à élevé — bon tampon"
    return "Très élevé (sol argileux)"


def _interp_ce(v):
    if v is None:
        return ""
    if v < 0.2:
        return "Non salin"
    if v < 0.8:
        return "Légèrement salin"
    if v < 2.0:
        return "Modérément salin — sensibilité espèces"
    return "Fortement salin — action corrective requise"


def _recs_fertilite(sol: AnalyseSol) -> list:
    recs = []
    if sol.pH_eau and sol.pH_eau < 5.5:
        recs.append("Chaulage recommandé pour corriger l'acidité (objectif pH 6.0-6.5).")
    if sol.matiere_organique and sol.matiere_organique < 1.5:
        recs.append("Apport de compost ou fumier (10-15 t/ha) pour augmenter la MO.")
    if sol.phosphore_assim and sol.phosphore_assim < 15:
        recs.append("Fumure phosphatée : appliquer 40-60 kg P₂O₅/ha avant semis.")
    if sol.azote_total and sol.azote_total < 0.5:
        recs.append("Sol pauvre en azote — engrais azoté en fractionnement recommandé.")
    if sol.conductivite_ds_m and sol.conductivite_ds_m > 2.0:
        recs.append("Salinité élevée — lessivage et cultures tolérantes conseillés.")
    return recs


@router.get("/fertilite/{parcelle_id}")
def rapport_fertilite(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Rapport PDF Fertilité — profil chimique du sol + recommandations."""
    parcelle = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not parcelle:
        raise HTTPException(404, "Parcelle introuvable.")

    sols = (db.query(AnalyseSol)
            .filter_by(parcelle_id=parcelle_id)
            .order_by(AnalyseSol.date_analyse.desc())
            .all())

    pdf_bytes = _build_fertilite_pdf(parcelle, sols)
    return _stream(pdf_bytes, f"fertilite_parcelle_{parcelle_id}.pdf")


# ── 4. RAPPORT RENDEMENT ─────────────────────────────────────────────────────

def _build_rendement_pdf(parcelle: Parcelle, activites: list, couts: list,
                          mo_list: list) -> bytes:
    (styles, vert, gris, rouge, orange, title_s, sub_s, section_s,
     body_s, bold_s, footer_s, cm, colors, Paragraph, Spacer, Table,
     TableStyle, HRFlowable, A4, SimpleDocTemplate, TA_CENTER, TA_LEFT) = _styles_communs()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    _header(story, "Rapport Rendement & Campagne",
            f"Parcelle : {parcelle.nom}", Paragraph, Spacer, cm, title_s, sub_s)

    # Infos parcelle
    story.append(Paragraph("Informations Parcelle", section_s))
    rows = [
        ["Nom", parcelle.nom or "—"],
        ["Culture", parcelle.type_culture or "—"],
        ["Variété", parcelle.variete or "—"],
        ["Superficie", f"{parcelle.superficie_ha:.2f} ha" if parcelle.superficie_ha else "—"],
        ["Date de semis", str(parcelle.date_semis) if parcelle.date_semis else "—"],
        ["Stade actuel", parcelle.stade_culture or "—"],
    ]
    tbl = Table(rows, colWidths=[5*cm, 11*cm])
    tbl.setStyle(_tbl_style(colors, TableStyle))
    story.append(tbl)
    story.append(Spacer(1, 0.3*cm))

    # KPIs financiers
    total_couts = sum(c.montant_total_fcfa or 0 for c in couts)
    total_mo = sum(m.montant_total_fcfa or 0 for m in mo_list)
    total_depenses = total_couts + total_mo

    # Récoltes
    recoltes = [a for a in activites if a.type == TypeActivite.RECOLTE
                or (hasattr(a.type, 'value') and a.type.value == "recolte")]
    rendement_total_kg = 0
    prix_vente_total = 0
    for r in recoltes:
        det = r.details or {}
        rendement_total_kg += det.get("rendement_kg", 0) or 0
        prix_vente_total += det.get("prix_vente_fcfa", 0) or 0

    benefice = prix_vente_total - total_depenses
    roi_pct = (benefice / total_depenses * 100) if total_depenses > 0 else 0

    story.append(Paragraph("Résumé Financier Campagne", section_s))
    kpi_rows = [
        ["Indicateur", "Valeur"],
        ["Coûts intrants + matériel", f"{total_couts:,} FCFA"],
        ["Coûts main-d'œuvre", f"{total_mo:,} FCFA"],
        ["Total dépenses", f"{total_depenses:,} FCFA"],
        ["Revenus estimés (vente)", f"{prix_vente_total:,} FCFA"],
        ["Bénéfice net", f"{benefice:,} FCFA"],
        ["ROI campagne", f"{roi_pct:.1f} %"],
        ["Rendement total", f"{rendement_total_kg:,} kg"],
    ]
    if parcelle.superficie_ha and parcelle.superficie_ha > 0 and rendement_total_kg > 0:
        rdt_ha = rendement_total_kg / parcelle.superficie_ha
        kpi_rows.append(["Rendement / ha", f"{rdt_ha:,.0f} kg/ha"])

    tbl2 = Table(kpi_rows, colWidths=[9*cm, 7*cm])
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f0fdf4")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        # Colorier bénéfice
        ("TEXTCOLOR", (1, 5), (1, 5),
         colors.HexColor("#166534") if benefice >= 0 else colors.HexColor("#991b1b")),
        ("FONTNAME", (1, 5), (1, 5), "Helvetica-Bold"),
    ]))
    story.append(tbl2)
    story.append(Spacer(1, 0.3*cm))

    # Détail coûts par catégorie
    if couts:
        story.append(Paragraph("Détail des Dépenses par Catégorie", section_s))
        cats = {}
        for c in couts:
            cat = c.categorie.value if hasattr(c.categorie, 'value') else str(c.categorie)
            cats[cat] = cats.get(cat, 0) + (c.montant_total_fcfa or 0)
        cat_rows = [["Catégorie", "Montant (FCFA)"]]
        for cat, mont in sorted(cats.items(), key=lambda x: -x[1]):
            cat_rows.append([cat.replace("_", " ").title(), f"{mont:,}"])
        tbl3 = Table(cat_rows, colWidths=[10*cm, 6*cm])
        tbl3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl3)
        story.append(Spacer(1, 0.3*cm))

    # Activités clés
    if activites:
        story.append(Paragraph("Journal des Activités Clés", section_s))
        act_rows = [["Date", "Type", "Activité", "Statut", "Surface (ha)"]]
        for a in sorted(activites, key=lambda x: x.date_prevue or x.created_at):
            act_rows.append([
                str(a.date_prevue or "—"),
                str(a.type.value if hasattr(a.type, 'value') else a.type),
                (a.titre or "—")[:40],
                str(a.statut.value if hasattr(a.statut, 'value') else a.statut),
                str(a.surface_traitee_ha or "—"),
            ])
        tbl4 = Table(act_rows, colWidths=[2.5*cm, 3*cm, 6*cm, 2.5*cm, 2*cm])
        tbl4.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl4)

    _footer(story, Paragraph, Spacer, cm, footer_s)
    doc.build(story)
    return buf.getvalue()


@router.get("/rendement/{parcelle_id}")
def rapport_rendement(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Rapport PDF Rendement — récolte, coûts, ROI et activités campagne."""
    parcelle = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not parcelle:
        raise HTTPException(404, "Parcelle introuvable.")

    activites = (db.query(Activite)
                 .filter_by(parcelle_id=parcelle_id, org_id=user.org_id)
                 .order_by(Activite.date_prevue)
                 .all())

    act_ids = [a.id for a in activites]
    couts = db.query(Cout).filter(Cout.activite_id.in_(act_ids)).all() if act_ids else []
    mo_list = db.query(MainOeuvre).filter(MainOeuvre.activite_id.in_(act_ids)).all() if act_ids else []

    pdf_bytes = _build_rendement_pdf(parcelle, activites, couts, mo_list)
    return _stream(pdf_bytes, f"rendement_parcelle_{parcelle_id}.pdf")


# ── 5. RAPPORT EXPLOITATION ──────────────────────────────────────────────────

def _build_exploitation_pdf(org_name: str, parcelles: list, exploitations: list,
                             activites: list, couts: list) -> bytes:
    (styles, vert, gris, rouge, orange, title_s, sub_s, section_s,
     body_s, bold_s, footer_s, cm, colors, Paragraph, Spacer, Table,
     TableStyle, HRFlowable, A4, SimpleDocTemplate, TA_CENTER, TA_LEFT) = _styles_communs()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    _header(story, "Rapport d'Exploitation Global",
            org_name, Paragraph, Spacer, cm, title_s, sub_s)

    # KPIs globaux
    surface_totale = sum(p.superficie_ha or 0 for p in parcelles)
    nb_actives = sum(1 for p in parcelles if str(getattr(p.statut, 'value', p.statut)) == "active")
    total_couts = sum(c.montant_total_fcfa or 0 for c in couts)

    prod_totale = sum(float(e.production_estimee or 0) for e in exploitations)
    rev_totaux = sum(e.revenus_estimes or 0 for e in exploitations)

    story.append(Paragraph("Vue d'Ensemble", section_s))
    kpi = [
        ["KPI", "Valeur"],
        ["Nombre de parcelles", str(len(parcelles))],
        ["Parcelles actives", str(nb_actives)],
        ["Surface totale", f"{surface_totale:.2f} ha"],
        ["Total activités", str(len(activites))],
        ["Total dépenses", f"{total_couts:,} FCFA"],
        ["Production estimée (toutes saisons)", f"{prod_totale:,.0f} kg"],
        ["Revenus estimés", f"{rev_totaux:,} FCFA"],
    ]
    tbl = Table(kpi, colWidths=[9*cm, 7*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f0fdf4")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.3*cm))

    # Liste des parcelles
    story.append(Paragraph("Parcelles", section_s))
    parc_rows = [["Nom", "Culture", "Superficie (ha)", "Statut", "Score"]]
    for p in parcelles:
        parc_rows.append([
            p.nom or "—",
            p.type_culture or "—",
            f"{p.superficie_ha:.2f}" if p.superficie_ha else "—",
            str(getattr(p.statut, 'value', p.statut) or "—"),
            f"{p.score_completude or 0}/100",
        ])
    tbl2 = Table(parc_rows, colWidths=[4*cm, 4*cm, 3*cm, 3*cm, 2*cm])
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f9fafb")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl2)
    story.append(Spacer(1, 0.3*cm))

    # Exploitations (données saison)
    if exploitations:
        story.append(Paragraph("Données de Production par Saison", section_s))
        exp_rows = [["Saison", "Surface (ha)", "Production", "Unité", "Coûts (FCFA)", "Revenus (FCFA)"]]
        for e in exploitations:
            exp_rows.append([
                e.saison or "—",
                str(e.surface_cultivee or "—"),
                str(e.production_estimee or "—"),
                e.unite_production or "kg",
                f"{e.couts_estimes:,}" if e.couts_estimes else "—",
                f"{e.revenus_estimes:,}" if e.revenus_estimes else "—",
            ])
        tbl3 = Table(exp_rows, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 2*cm, 3.5*cm, 3*cm])
        tbl3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl3)
        story.append(Spacer(1, 0.3*cm))

    # Répartition activités
    if activites:
        story.append(Paragraph("Répartition des Activités", section_s))
        type_counts = {}
        for a in activites:
            t = a.type.value if hasattr(a.type, 'value') else str(a.type)
            type_counts[t] = type_counts.get(t, 0) + 1
        act_rows = [["Type d'activité", "Nombre"]]
        for typ, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
            act_rows.append([typ.replace("_", " ").title(), str(cnt)])
        tbl4 = Table(act_rows, colWidths=[10*cm, 6*cm])
        tbl4.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl4)

    _footer(story, Paragraph, Spacer, cm, footer_s)
    doc.build(story)
    return buf.getvalue()


@router.get("/exploitation")
def rapport_exploitation(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Rapport PDF Exploitation Global — toutes parcelles, activités et données financières."""
    from app.models import Organization

    org = db.query(Organization).filter_by(id=user.org_id).first()
    org_name = org.name if org else f"Organisation #{user.org_id}"

    parcelles = db.query(Parcelle).filter(
        Parcelle.org_id == user.org_id,
        Parcelle.statut != StatutParcelle.ARCHIVE,
    ).order_by(Parcelle.created_at).all()
    exploitations = db.query(Exploitation).filter_by(org_id=user.org_id).order_by(Exploitation.saison).all()
    activites = db.query(Activite).filter_by(org_id=user.org_id).order_by(Activite.date_prevue).all()

    act_ids = [a.id for a in activites]
    couts = db.query(Cout).filter(Cout.activite_id.in_(act_ids)).all() if act_ids else []

    pdf_bytes = _build_exploitation_pdf(org_name, parcelles, exploitations, activites, couts)
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return _stream(pdf_bytes, f"exploitation_global_{now_str}.pdf")
