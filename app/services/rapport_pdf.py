"""
================================================================================
 GÉNÉRATEUR DE RAPPORT PDF — AgroScan Pro / Social Technologie
================================================================================
Produit un rapport d'analyse de sol professionnel, multi-pages, à partir d'un
diagnostic de fertilité (moteur app/services/fertilite.py).

Contenu :
  1. Page de couverture (logo, titre, n° unique, date, QR code)
  2. Informations producteur + localisation GPS
  3. Résultats d'analyse (tableau des 7 paramètres)
  4. Graphiques (jauge de fertilité + barres des paramètres)
  5. Diagnostic automatique (général + technique)
  6. Recommandations (carences, excès, contraintes, risques)
  7. Plan de fertilisation (actions correctives chiffrées)
  8. Cultures recommandées
  9. Signature numérique AgroScan Pro

Charte graphique : VERT (#1f7a3d agronomie) + BLEU (#1b6ca8 eau/technologie).
Dépendances : reportlab, qrcode, pillow.
"""
from __future__ import annotations

import io
import hashlib
from datetime import datetime, timezone
from typing import Optional

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, FrameBreak, NextPageTemplate, PageBreak, Flowable,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF

# ---------------------------------------------------------------------------
#  CHARTE GRAPHIQUE — vert & bleu
# ---------------------------------------------------------------------------
VERT       = HexColor("#1f7a3d")   # vert agronomie
VERT_FONCE = HexColor("#145a2c")
VERT_CLAIR = HexColor("#e6f3ea")
BLEU       = HexColor("#1b6ca8")   # bleu eau / technologie
BLEU_FONCE = HexColor("#0f4c75")
BLEU_CLAIR = HexColor("#e4f0f8")
GRIS       = HexColor("#5b6670")
GRIS_CLAIR = HexColor("#f1f4f6")
OR         = HexColor("#d99125")
ROUGE      = HexColor("#c0392b")
ORANGE     = HexColor("#e08a1e")

# Couleur associée à chaque niveau de fertilité
COULEUR_NIVEAU = {
    "Excellent":   VERT,
    "Bon":         HexColor("#5aa469"),
    "Moyen":       OR,
    "Faible":      ORANGE,
    "Très faible": ROUGE,
}

CONTACT = "+221 78 491 90 11"
SOCIETE = "Social Technologie"


# ---------------------------------------------------------------------------
#  ÉLÉMENTS GRAPHIQUES PERSONNALISÉS
# ---------------------------------------------------------------------------
class LogoAgro(Flowable):
    """Logo vectoriel : pastille verte avec une pousse/feuille stylisée."""

    def __init__(self, taille: float = 13 * mm, sur_fond_sombre: bool = False):
        super().__init__()
        self.width = self.height = taille
        self.sombre = sur_fond_sombre

    def draw(self):
        c = self.canv
        s = self.width
        # pastille ronde
        c.setFillColor(white if self.sombre else VERT)
        c.circle(s / 2, s / 2, s / 2, fill=1, stroke=0)
        # tige + deux feuilles
        coul = VERT if self.sombre else white
        c.setStrokeColor(coul)
        c.setLineWidth(s * 0.07)
        c.line(s * 0.5, s * 0.24, s * 0.5, s * 0.7)          # tige
        c.setFillColor(coul)
        # feuille gauche
        c.bezier(s * 0.5, s * 0.55, s * 0.3, s * 0.5, s * 0.28, s * 0.72, s * 0.5, s * 0.74)
        # feuille droite
        c.bezier(s * 0.5, s * 0.62, s * 0.7, s * 0.58, s * 0.74, s * 0.8, s * 0.5, s * 0.82)


class JaugeFertilite(Flowable):
    """Demi-jauge circulaire affichant le score de fertilité /100."""

    def __init__(self, score: int, niveau: str, taille: float = 95 * mm):
        super().__init__()
        self.score = max(0, min(100, score))
        self.niveau = niveau
        self.width = taille
        self.height = taille * 0.62

    def draw(self):
        c = self.canv
        cx, cy, r = self.width / 2, 8 * mm, self.width * 0.38
        coul = COULEUR_NIVEAU.get(self.niveau, BLEU)
        # Arc de fond (gris) puis arc coloré proportionnel au score.
        c.saveState()
        c.setLineWidth(13)
        c.setStrokeColor(GRIS_CLAIR)
        c.arc(cx - r, cy - r, cx + r, cy + r, 0, 180)
        c.setStrokeColor(coul)
        # 180° = score 100 ; l'arc part de la gauche (180°) vers la droite.
        extent = 180 * (self.score / 100.0)
        c.arc(cx - r, cy - r, cx + r, cy + r, 180 - extent, extent)
        c.restoreState()
        # Valeur centrale
        c.setFillColor(coul)
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(cx, cy + 2 * mm, str(self.score))
        c.setFont("Helvetica", 9)
        c.setFillColor(GRIS)
        c.drawCentredString(cx, cy - 4 * mm, "indice / 100")
        # Niveau
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(coul)
        c.drawCentredString(cx, cy + r + 4 * mm, self.niveau.upper())


class BarresParametres(Flowable):
    """Barres horizontales : position de chaque paramètre vs sa plage optimale."""

    def __init__(self, evaluations, largeur: float = 92 * mm):
        super().__init__()
        self.evals = [e for e in evaluations if e.get("valeur") is not None]
        self.width = largeur
        self.height = max(20 * mm, len(self.evals) * 11 * mm + 6 * mm)

    def _coul_statut(self, st):
        return {
            "optimal": VERT,
            "carence": ORANGE, "excès": ORANGE,
            "carence sévère": ROUGE, "excès sévère": ROUGE,
        }.get(st, GRIS)

    def draw(self):
        c = self.canv
        x0 = 34 * mm                      # début des barres (après le label)
        bar_w = self.width - x0 - 20 * mm
        y = self.height - 8 * mm
        for e in self.evals:
            st = e.get("statut", "")
            coul = self._coul_statut(st)
            # Label paramètre
            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(black)
            label = e["parametre"][:16]
            c.drawString(0, y - 1.5 * mm, label)
            # Piste grise
            c.setFillColor(GRIS_CLAIR)
            c.roundRect(x0, y - 3.4 * mm, bar_w, 4.6 * mm, 2, fill=1, stroke=0)
            # Remplissage : statut "optimal" = plein vert ; sinon partiel coloré
            ratio = 1.0 if st == "optimal" else (0.45 if "sévère" not in st else 0.22)
            c.setFillColor(coul)
            c.roundRect(x0, y - 3.4 * mm, bar_w * ratio, 4.6 * mm, 2, fill=1, stroke=0)
            # Valeur + unité à droite
            c.setFont("Helvetica", 8)
            c.setFillColor(GRIS)
            val = e.get("valeur")
            unite = e.get("unite", "")
            txt = f"{val} {unite}".strip()
            c.drawString(x0 + bar_w + 3 * mm, y - 1.5 * mm, txt)
            y -= 11 * mm


# ---------------------------------------------------------------------------
#  GÉNÉRATEUR
# ---------------------------------------------------------------------------
class RapportPDF:
    """Construit le rapport PDF complet."""

    def __init__(self):
        self.styles = self._styles()

    # ---- styles ----
    def _styles(self):
        s = getSampleStyleSheet()
        s.add(ParagraphStyle("CoverTitle", fontName="Helvetica-Bold", fontSize=30,
                             textColor=white, leading=34, alignment=TA_LEFT))
        s.add(ParagraphStyle("CoverSub", fontName="Helvetica", fontSize=13,
                             textColor=white, leading=18, alignment=TA_LEFT))
        s.add(ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=15,
                             textColor=VERT_FONCE, spaceBefore=4, spaceAfter=8))
        s.add(ParagraphStyle("Body2", fontName="Helvetica", fontSize=10,
                             textColor=HexColor("#2a2f34"), leading=15, spaceAfter=4))
        s.add(ParagraphStyle("Mini", fontName="Helvetica", fontSize=8,
                             textColor=GRIS, leading=11))
        s.add(ParagraphStyle("Action", fontName="Helvetica", fontSize=9.5,
                             textColor=HexColor("#2a2f34"), leading=14,
                             leftIndent=6, spaceAfter=5, bulletIndent=0))
        s.add(ParagraphStyle("WhiteRight", fontName="Helvetica", fontSize=9,
                             textColor=white, alignment=TA_RIGHT, leading=13))
        return s

    # ---- QR code ----
    def _qr(self, contenu: str, taille=32 * mm) -> Image:
        qr = qrcode.QRCode(version=1, box_size=10, border=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(contenu)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f4c75", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return Image(buf, width=taille, height=taille)

    # ---- numéro unique + signature ----
    @staticmethod
    def numero_unique(org_id: int = 0, ref: Optional[str] = None) -> str:
        if ref:
            return ref
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"AGS-{org_id:04d}-{ts}"

    @staticmethod
    def signature_numerique(numero: str, diag: dict) -> str:
        """Empreinte SHA-256 (tronquée) scellant le contenu du rapport."""
        base = f"{numero}|{diag.get('niveau_fertilite')}|{diag.get('score_sur_100')}|{SOCIETE}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16].upper()

    # ---- bandeau d'en-tête (pages internes) ----
    def _header_footer(self, canvas, doc):
        canvas.saveState()
        w, h = A4
        # bandeau supérieur dégradé vert→bleu (simulé par deux rectangles)
        canvas.setFillColor(VERT)
        canvas.rect(0, h - 16 * mm, w / 2, 16 * mm, fill=1, stroke=0)
        canvas.setFillColor(BLEU)
        canvas.rect(w / 2, h - 16 * mm, w / 2, 16 * mm, fill=1, stroke=0)
        canvas.setFillColor(white)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(15 * mm, h - 11 * mm, "AgroScan Pro")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - 15 * mm, h - 11 * mm, f"{SOCIETE} · {CONTACT}")
        # pied de page
        canvas.setStrokeColor(GRIS_CLAIR)
        canvas.setLineWidth(0.5)
        canvas.line(15 * mm, 14 * mm, w - 15 * mm, 14 * mm)
        canvas.setFillColor(GRIS)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(15 * mm, 9 * mm,
                          f"Rapport {doc._numero}  ·  Outil d'orientation (~70%) — ne remplace pas une analyse de laboratoire certifiée")
        canvas.drawRightString(w - 15 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    # ---- couverture (fond plein, pas d'en-tête) ----
    def _cover_bg(self, canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(VERT_FONCE)
        canvas.rect(0, 0, w, h, fill=1, stroke=0)
        # grande vague bleue en bas
        canvas.setFillColor(BLEU_FONCE)
        canvas.rect(0, 0, w, h * 0.32, fill=1, stroke=0)
        canvas.setFillColor(BLEU)
        canvas.rect(0, h * 0.30, w, 4 * mm, fill=1, stroke=0)
        # motif discret
        canvas.setFillColor(HexColor("#2a8a4d"))
        for i in range(6):
            canvas.circle(w - 20 * mm, h - 30 * mm - i * 9 * mm, 2 * mm, fill=1, stroke=0)
        canvas.restoreState()

    # ===================================================================
    #  CONSTRUCTION DU DOCUMENT
    # ===================================================================
    def generer(self, diag: dict, producteur: dict, sortie_path: str,
                numero: Optional[str] = None, org_id: int = 0) -> str:
        """
        diag       : dict issu de DiagnosticSol.to_dict()
        producteur : {nom, localite, region, culture, technicien, latitude, longitude, superficie}
        sortie_path: chemin du PDF à écrire
        """
        numero = self.numero_unique(org_id, numero)
        date_gen = datetime.now(timezone.utc).strftime("%d/%m/%Y à %H:%M UTC")
        signature = self.signature_numerique(numero, diag)
        qr_contenu = (f"AgroScan Pro|{numero}|{producteur.get('nom','-')}|"
                      f"Fertilite:{diag.get('niveau_fertilite')}|Sig:{signature}|{CONTACT}")

        doc = BaseDocTemplate(sortie_path, pagesize=A4,
                              leftMargin=15 * mm, rightMargin=15 * mm,
                              topMargin=22 * mm, bottomMargin=18 * mm,
                              title=f"Rapport AgroScan {numero}", author=SOCIETE)
        doc._numero = numero

        w, h = A4
        # Frame couverture (plein cadre) + frame contenu (sous l'en-tête)
        cover_frame = Frame(15 * mm, 15 * mm, w - 30 * mm, h - 30 * mm, id="cover")
        body_frame = Frame(15 * mm, 16 * mm, w - 30 * mm, h - 40 * mm, id="body")
        doc.addPageTemplates([
            PageTemplate(id="Cover", frames=[cover_frame], onPage=self._cover_bg),
            PageTemplate(id="Body", frames=[body_frame], onPage=self._header_footer),
        ])

        story = []
        story += self._page_couverture(diag, producteur, numero, date_gen, qr_contenu)
        story.append(NextPageTemplate("Body"))
        story.append(PageBreak())
        story += self._page_infos_resultats(diag, producteur)
        story.append(PageBreak())
        story += self._page_diagnostic_reco(diag)
        story.append(PageBreak())
        story += self._page_plan_cultures_signature(diag, producteur, numero, signature, date_gen, qr_contenu)

        doc.build(story)
        return sortie_path

    # ---- PAGE 1 : COUVERTURE ----
    def _page_couverture(self, diag, prod, numero, date_gen, qr_contenu):
        e = []
        e.append(Spacer(1, 8 * mm))
        # logo vectoriel + nom
        logo = Table([[LogoAgro(13 * mm, sur_fond_sombre=True),
                       Paragraph('<font color="white"><b>AgroScan&nbsp;Pro</b></font>',
                                 ParagraphStyle("lg", fontName="Helvetica-Bold", fontSize=22, textColor=white))]],
                      colWidths=[16 * mm, 118 * mm])
        logo.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        e.append(logo)
        e.append(Spacer(1, 4 * mm))
        e.append(Paragraph(f'<font color="#cfe8d6">une solution {SOCIETE}</font>', self.styles["CoverSub"]))
        e.append(Spacer(1, 28 * mm))
        e.append(Paragraph("RAPPORT<br/>D'ANALYSE DE SOL", self.styles["CoverTitle"]))
        e.append(Spacer(1, 6 * mm))
        niveau = diag.get("niveau_fertilite", "—")
        coul = COULEUR_NIVEAU.get(niveau, BLEU)
        badge = Table([[Paragraph(f'<font color="white"><b>FERTILITÉ : {niveau.upper()}</b></font>',
                                  ParagraphStyle("b", fontName="Helvetica-Bold", fontSize=13, textColor=white))]],
                      colWidths=[85 * mm])
        badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), coul),
                                   ("TOPPADDING", (0, 0), (-1, -1), 6),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 12)]))
        e.append(badge)
        e.append(Spacer(1, 40 * mm))

        # bloc bas : infos + QR (sur la vague bleue)
        qr = self._qr(qr_contenu, 30 * mm)
        infos = [
            Paragraph(f'<font color="white"><b>Producteur :</b> {prod.get("nom","—")}</font>', self.styles["CoverSub"]),
            Paragraph(f'<font color="#bcd9ee">N° de rapport : <b>{numero}</b></font>', self.styles["Mini"]),
            Paragraph(f'<font color="#bcd9ee">Généré le {date_gen}</font>', self.styles["Mini"]),
        ]
        bloc = Table([[infos, qr]], colWidths=[110 * mm, 35 * mm])
        bloc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                                  ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
        # encapsule la liste de paragraphes dans une sous-table
        infos_tbl = Table([[p] for p in infos], colWidths=[108 * mm])
        infos_tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                                       ("TOPPADDING", (0, 0), (-1, -1), 1),
                                       ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
        bloc = Table([[infos_tbl, qr]], colWidths=[110 * mm, 35 * mm])
        bloc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
        e.append(bloc)
        return e

    # ---- PAGE 2 : INFOS PRODUCTEUR + GPS + RÉSULTATS + GRAPHIQUES ----
    def _page_infos_resultats(self, diag, prod):
        e = []
        e.append(Paragraph("1 · Informations producteur & localisation", self.styles["H2"]))

        lat, lng = prod.get("latitude"), prod.get("longitude")
        gps = f"{lat}, {lng}" if (lat is not None and lng is not None) else "Non renseignée"
        maps = (f'<font color="#1b6ca8">https://maps.google.com/?q={lat},{lng}</font>'
                if (lat is not None and lng is not None) else "—")
        info_rows = [
            ["Producteur", prod.get("nom", "—"), "Région", prod.get("region", "—")],
            ["Localité", prod.get("localite", "—"), "Culture visée", prod.get("culture", "—")],
            ["Technicien", prod.get("technicien", "—"), "Superficie", f'{prod.get("superficie","—")} ha'],
            ["Coordonnées GPS", gps, "Lien carte", Paragraph(maps, self.styles["Mini"])],
        ]
        t = Table(info_rows, colWidths=[32 * mm, 56 * mm, 30 * mm, 47 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), VERT_CLAIR),
            ("BACKGROUND", (2, 0), (2, -1), BLEU_CLAIR),
            ("TEXTCOLOR", (0, 0), (0, -1), VERT_FONCE),
            ("TEXTCOLOR", (2, 0), (2, -1), BLEU_FONCE),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ]))
        e.append(t)
        e.append(Spacer(1, 8 * mm))

        # Résultats d'analyse (tableau des paramètres)
        e.append(Paragraph("2 · Résultats d'analyse", self.styles["H2"]))
        head = ["Paramètre", "Valeur", "Plage de référence", "Statut"]
        rows = [head]
        for ev in diag.get("evaluations", []):
            val = "—" if ev.get("valeur") is None else f'{ev["valeur"]} {ev.get("unite","")}'.strip()
            rows.append([ev["parametre"], val, ev.get("plage_ref", "—"), ev.get("statut", "—").capitalize()])
        rt = Table(rows, colWidths=[42 * mm, 30 * mm, 58 * mm, 35 * mm], repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), BLEU),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRIS_CLAIR]),
            ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#d8dee3")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]
        # colorer la colonne statut
        for i, ev in enumerate(diag.get("evaluations", []), start=1):
            st = ev.get("statut", "")
            col = {"optimal": VERT, "carence": ORANGE, "excès": ORANGE,
                   "carence sévère": ROUGE, "excès sévère": ROUGE}.get(st, GRIS)
            style.append(("TEXTCOLOR", (3, i), (3, i), col))
            style.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
        rt.setStyle(TableStyle(style))
        e.append(rt)
        e.append(Spacer(1, 8 * mm))

        # Graphiques
        e.append(Paragraph("3 · Visualisation", self.styles["H2"]))
        jauge = JaugeFertilite(diag.get("score_sur_100", 0), diag.get("niveau_fertilite", "—"))
        barres = BarresParametres(diag.get("evaluations", []))
        graph = Table([[jauge, barres]], colWidths=[72 * mm, 93 * mm])
        graph.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        e.append(graph)
        return e

    # ---- PAGE 3 : DIAGNOSTIC + RECOMMANDATIONS ----
    def _page_diagnostic_reco(self, diag):
        e = []
        e.append(Paragraph("4 · Diagnostic automatique", self.styles["H2"]))
        # encadré "français simple"
        simple = diag.get("diagnostic_general", "")
        box = Table([[Paragraph(f'<b>En clair :</b> {simple}', self.styles["Body2"])]],
                    colWidths=[165 * mm])
        box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), VERT_CLAIR),
                                 ("BOX", (0, 0), (-1, -1), 1, VERT),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                                 ("TOPPADDING", (0, 0), (-1, -1), 8),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        e.append(box)
        e.append(Spacer(1, 5 * mm))
        # diagnostic technique
        e.append(Paragraph("Diagnostic technique", ParagraphStyle(
            "h3", fontName="Helvetica-Bold", fontSize=11, textColor=BLEU_FONCE, spaceAfter=4)))
        for ligne in diag.get("diagnostic_technique", "").split("\n"):
            e.append(Paragraph(ligne.replace("•", "&bull;"), self.styles["Body2"]))
        e.append(Spacer(1, 6 * mm))

        # Recommandations : carences / excès / contraintes / risques
        e.append(Paragraph("5 · Constats & risques", self.styles["H2"]))

        def liste_box(titre, items, coul_bg, coul_txt):
            if not items:
                items = ["Aucun élément signalé."]
            cells = [[Paragraph(f'<b><font color="{coul_txt}">{titre}</font></b>', self.styles["Body2"])]]
            for it in items:
                cells.append([Paragraph(f"&bull; {it}", self.styles["Body2"])])
            tb = Table(cells, colWidths=[80 * mm])
            tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), coul_bg),
                                    ("BOX", (0, 0), (-1, -1), 0.6, coul_bg),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            return tb

        carences_box = liste_box("Carences identifiées", diag.get("carences", []), HexColor("#fbe6dc"), "#9a3318")
        exces_box = liste_box("Excès détectés", diag.get("exces", []), HexColor("#f8ecd1"), "#7a4a0e")
        contr_box = liste_box("Contraintes agronomiques", diag.get("contraintes", []), BLEU_CLAIR, "#0f4c75")
        risq_box = liste_box("Risques potentiels", diag.get("risques", []), HexColor("#f3e8d0"), "#6a4a10")

        grid = Table([[carences_box, exces_box], [contr_box, risq_box]],
                     colWidths=[82 * mm, 82 * mm])
        grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                  ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        e.append(grid)
        return e

    # ---- PAGE 4 : PLAN DE FERTILISATION + CULTURES + SIGNATURE ----
    def _page_plan_cultures_signature(self, diag, prod, numero, signature, date_gen, qr_contenu):
        e = []
        e.append(Paragraph("6 · Plan de fertilisation & actions correctives", self.styles["H2"]))
        actions = diag.get("actions_correctives", [])
        if not actions:
            e.append(Paragraph("Aucune correction majeure nécessaire. Maintenir les bonnes pratiques "
                               "(apport régulier de matière organique, rotation des cultures).", self.styles["Body2"]))
        else:
            for i, a in enumerate(actions, 1):
                cell = Table([[Paragraph(f'<b><font color="white">{i}</font></b>',
                                         ParagraphStyle("n", fontName="Helvetica-Bold", fontSize=11,
                                                        textColor=white, alignment=TA_CENTER)),
                               Paragraph(a, self.styles["Body2"])]],
                             colWidths=[9 * mm, 156 * mm])
                cell.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), VERT),
                                          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                          ("BACKGROUND", (1, 0), (1, 0), VERT_CLAIR),
                                          ("TOPPADDING", (0, 0), (-1, -1), 6),
                                          ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                          ("LEFTPADDING", (1, 0), (1, 0), 8)]))
                e.append(cell)
                e.append(Spacer(1, 2.5 * mm))
        e.append(Spacer(1, 5 * mm))

        # Cultures recommandées (puces vertes)
        e.append(Paragraph("7 · Cultures recommandées", self.styles["H2"]))
        cultures = diag.get("cultures_recommandees", [])
        if cultures:
            chips = []
            row = []
            for c in cultures:
                row.append(Paragraph(f'<font color="white"><b>{c}</b></font>',
                                     ParagraphStyle("c", fontName="Helvetica-Bold", fontSize=9.5,
                                                    textColor=white, alignment=TA_CENTER)))
            chip_tbl = Table([row], colWidths=[ (165 * mm) / max(1, len(row)) ] * len(row))
            sty = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]
            for i in range(len(row)):
                sty.append(("BACKGROUND", (i, 0), (i, 0), VERT if i % 2 == 0 else BLEU))
                sty.append(("LEFTPADDING", (i, 0), (i, 0), 3))
                sty.append(("RIGHTPADDING", (i, 0), (i, 0), 3))
            chip_tbl.setStyle(TableStyle(sty))
            e.append(chip_tbl)
        e.append(Spacer(1, 10 * mm))

        # Signature numérique + QR
        e.append(Paragraph("8 · Signature numérique AgroScan Pro", self.styles["H2"]))
        sig_left = [
            Paragraph(f'<b>Rapport authentifié</b> — {SOCIETE}', self.styles["Body2"]),
            Paragraph(f'N° unique : <b>{numero}</b>', self.styles["Body2"]),
            Paragraph(f'Date de génération : {date_gen}', self.styles["Body2"]),
            Paragraph(f'Signature (SHA-256) : <font face="Courier"><b>{signature}</b></font>', self.styles["Body2"]),
            Paragraph(f'Contact : {CONTACT}', self.styles["Body2"]),
            Spacer(1, 3 * mm),
            Paragraph("Scannez le QR code pour vérifier l'authenticité du rapport.", self.styles["Mini"]),
        ]
        sig_left_tbl = Table([[p] for p in sig_left], colWidths=[125 * mm])
        sig_left_tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                                          ("TOPPADDING", (0, 0), (-1, -1), 1),
                                          ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
        sig = Table([[sig_left_tbl, self._qr(qr_contenu, 34 * mm)]],
                    colWidths=[127 * mm, 38 * mm])
        sig.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GRIS_CLAIR),
                                 ("BOX", (0, 0), (-1, -1), 1, BLEU),
                                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                                 ("TOPPADDING", (0, 0), (-1, -1), 10),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        e.append(sig)
        e.append(Spacer(1, 6 * mm))
        e.append(Paragraph(diag.get("avertissement", ""), self.styles["Mini"]))
        return e
