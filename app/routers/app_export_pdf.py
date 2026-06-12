"""
Router Export PDF — rapport agronomique par parcelle.
Préfixe : /api/app
Endpoint : GET /parcelles/{parcelle_id}/export-pdf
"""
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user
from app.models import User
from app.models.champ import Parcelle
from app.services.score_champ import calculer_score

router = APIRouter(prefix="/api/app", tags=["Export PDF"])


def _build_pdf(parcelle: Parcelle, score_data: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"],
        fontSize=18, spaceAfter=6, textColor=colors.HexColor("#166534"),
        alignment=TA_CENTER,
    )
    sub_style = ParagraphStyle(
        "sub", parent=styles["Normal"],
        fontSize=10, spaceAfter=4, textColor=colors.HexColor("#6b7280"),
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        "section", parent=styles["Heading2"],
        fontSize=12, spaceBefore=12, spaceAfter=4,
        textColor=colors.HexColor("#14532d"),
    )
    body_style = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontSize=10, spaceAfter=3, leading=14,
    )

    story = []

    # En-tête
    story.append(Paragraph("AgroScan Pro", title_style))
    story.append(Paragraph("Rapport Agronomique de Parcelle", sub_style))
    story.append(Paragraph(
        f"Généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M')} UTC",
        sub_style,
    ))
    story.append(Spacer(1, 0.5*cm))

    # Informations parcelle
    story.append(Paragraph("Informations de la Parcelle", section_style))

    infos = [
        ["Nom", parcelle.nom or "—"],
        ["Culture", parcelle.type_culture or "—"],
        ["Variété", parcelle.variete or "—"],
        ["Zone agro-écologique", parcelle.zone_agro or "—"],
        ["Superficie", f"{parcelle.superficie_ha:.2f} ha" if parcelle.superficie_ha else "—"],
        ["Date de semis", str(parcelle.date_semis) if parcelle.date_semis else "—"],
        ["Stade actuel", parcelle.stade_culture or "—"],
        ["Code parcelle", parcelle.code_parcelle or "—"],
        ["Statut", parcelle.statut or "—"],
    ]

    tbl = Table(infos, colWidths=[5*cm, 11*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0fdf4")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#166534")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.3*cm))

    # Score complétude
    story.append(Paragraph("Score de Complétude du Dossier", section_style))

    score_total = score_data.get("score", 0)
    niveau = score_data.get("niveau", "—")
    manquants = score_data.get("champs_manquants", [])

    score_color = colors.HexColor("#166534") if score_total >= 70 else (
        colors.HexColor("#92400e") if score_total >= 40 else colors.HexColor("#991b1b")
    )
    score_style = ParagraphStyle(
        "score", parent=styles["Normal"],
        fontSize=28, textColor=score_color, alignment=TA_CENTER, spaceAfter=4,
    )
    story.append(Paragraph(f"{score_total}/100", score_style))
    story.append(Paragraph(f"Niveau : {niveau}", ParagraphStyle(
        "niveau", parent=styles["Normal"], fontSize=11,
        alignment=TA_CENTER, spaceAfter=6, textColor=colors.HexColor("#374151"),
    )))

    if manquants:
        story.append(Paragraph("Informations manquantes :", body_style))
        for m in manquants:
            story.append(Paragraph(f"  • {m}", body_style))
    else:
        story.append(Paragraph("✓ Dossier complet", ParagraphStyle(
            "ok", parent=styles["Normal"], fontSize=11,
            textColor=colors.HexColor("#166534"), spaceAfter=4,
        )))

    story.append(Spacer(1, 0.3*cm))

    # Localisation
    if parcelle.centre_lat and parcelle.centre_lon:
        story.append(Paragraph("Localisation GPS", section_style))
        story.append(Paragraph(
            f"Latitude : {parcelle.centre_lat:.6f} | Longitude : {parcelle.centre_lon:.6f}",
            body_style,
        ))

    # Pied de page
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "© AgroScan Pro — Social Technologie | +221 78 491 90 11",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#9ca3af"), alignment=TA_CENTER),
    ))

    doc.build(story)
    return buf.getvalue()


@router.get("/parcelles/{parcelle_id}/export-pdf")
def exporter_rapport_pdf(
    parcelle_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Génère un rapport PDF agronomique pour une parcelle."""
    parcelle = db.query(Parcelle).filter_by(id=parcelle_id, org_id=user.org_id).first()
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")

    score_obj = calculer_score(db, parcelle)
    total = score_obj.total
    if total >= 80:
        niveau = "Excellent"
    elif total >= 60:
        niveau = "Bon"
    elif total >= 40:
        niveau = "Moyen"
    else:
        niveau = "Insuffisant"
    score_data = {
        "score": total,
        "niveau": niveau,
        "champs_manquants": score_obj.manquants,
    }
    pdf_bytes = _build_pdf(parcelle, score_data)

    nom_fichier = f"rapport_{parcelle.code_parcelle or parcelle_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nom_fichier}"'},
    )
