"""
Constructeur de contexte agricole — agrège tous les modules pour l'IA.
Mon Champ + Santé + Ferme + Météo + Rules Engine → snapshot structuré.
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import User
from app.models.champ import Parcelle, AnalyseSol
from app.models.agronomie import Culture
from app.models.sante import Consultation, Diagnostic, StatutConsultation
from app.models.ferme import Activite, StatutActivite
from app.models.meteo import Alerte, ConditionMeteo, NiveauAlerte
from app.models.ia import ConfigIA
from app.schemas.ia import ContexteAgro
from app.services.ia.quota import limites

log = logging.getLogger(__name__)


def build_contexte(
    db: Session,
    org_id: int,
    user_id: int,
    plan: str,
    config: Optional[ConfigIA] = None,
    parcelle_id: Optional[int] = None,
) -> ContexteAgro:
    """
    Construit le contexte complet du producteur.
    plan=gratuit  : top 2 parcelles, météo seule parcelle principale
    plan=premium  : toutes parcelles, météo complète, historique 90j
    """
    lim = limites(plan)
    now = datetime.now(timezone.utc)
    horizon_jours = 90 if plan != "gratuit" else 30

    # ── Producteur ────────────────────────────────────────────────────────────
    user = db.query(User).filter_by(id=user_id).first()
    from app.models import Subscription
    sub = db.query(Subscription).filter_by(org_id=org_id).first()

    producteur = {
        "nom": user.full_name if user else "Producteur",
        "plan": plan,
        "org_id": org_id,
    }

    # ── Parcelles ─────────────────────────────────────────────────────────────
    from app.models.champ import StatutParcelle
    q_parc = db.query(Parcelle).filter(Parcelle.org_id == org_id)
    if parcelle_id:
        # Scope explicite : toujours inclure la parcelle demandée
        q_parc = q_parc.filter(Parcelle.id == parcelle_id)
    else:
        q_parc = q_parc.filter(Parcelle.statut == StatutParcelle.ACTIVE)

    parcelles_db = q_parc.order_by(Parcelle.id).all()
    max_parc = 2 if plan == "gratuit" else len(parcelles_db)
    parcelles_db = parcelles_db[:max_parc]

    parcelles_ctx = []
    for p in parcelles_db:
        culture_nom = None
        if p.culture_id:
            c = db.query(Culture).filter_by(id=p.culture_id).first()
            culture_nom = c.nom if c else None

        # Dernière analyse sol
        sol_info = {}
        sol = (db.query(AnalyseSol)
               .filter_by(parcelle_id=p.id)
               .order_by(AnalyseSol.id.desc())
               .first())
        if sol:
            if sol.pH_eau:       sol_info["pH"] = round(sol.pH_eau, 1)
            if sol.azote_total:  sol_info["azote_g_kg"] = round(sol.azote_total, 1)
            if sol.phosphore_assim: sol_info["phosphore_mg_kg"] = round(sol.phosphore_assim, 1)
            if sol.texture:      sol_info["texture"] = sol.texture.value if hasattr(sol.texture, 'value') else str(sol.texture)
            if sol.matiere_organique: sol_info["matiere_organique_pct"] = round(sol.matiere_organique, 1)

        parcelles_ctx.append({
            "id":          p.id,
            "nom":         p.nom,
            "culture":     culture_nom,
            "zone_agro":   p.zone_agro,
            "superficie_ha": p.superficie_ha,
            "sol":         sol_info,
        })

    # ── Santé des cultures ────────────────────────────────────────────────────
    sante_ctx: dict = {"consultations_recentes": [], "diagnostics_actifs": []}
    if not config or config.inclure_historique_sante:
        depuis = now - timedelta(days=30)
        for p in parcelles_db:
            consults = (db.query(Consultation)
                        .filter(Consultation.parcelle_id == p.id,
                                Consultation.created_at >= depuis)
                        .order_by(Consultation.created_at.desc())
                        .limit(3)
                        .all())
            for c in consults:
                diagnostics = (db.query(Diagnostic)
                               .filter_by(consultation_id=c.id)
                               .order_by(Diagnostic.score_confiance.desc())
                               .limit(2)
                               .all())
                # symptomes stockés dans contexte JSONB ou resume
                symptomes = (c.resume or
                             (c.contexte or {}).get("symptomes_principaux") or
                             (c.contexte or {}).get("stade_actuel") or "")
                sante_ctx["consultations_recentes"].append({
                    "parcelle":    p.nom,
                    "date":        c.created_at.date().isoformat(),
                    "statut":      c.statut.value,
                    "symptomes":   symptomes,
                    "diagnostics": [
                        {
                            "nom": d.entite_nom,
                            "confiance": round((d.score_confiance or 0) * 100),
                            "statut": d.statut.value,
                        }
                        for d in diagnostics
                    ],
                })

    # ── Gestion de ferme ──────────────────────────────────────────────────────
    ferme_ctx: dict = {"activites_recentes": [], "activites_planifiees": [], "cout_mois_fcfa": 0}
    if not config or config.inclure_couts:
        depuis_ferme = now - timedelta(days=7)
        debut_mois   = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        parc_ids     = [p.id for p in parcelles_db]

        if parc_ids:
            activites = (db.query(Activite)
                         .filter(Activite.org_id == org_id,
                                 Activite.parcelle_id.in_(parc_ids),
                                 Activite.date_prevue >= depuis_ferme.date())
                         .order_by(Activite.date_prevue.desc())
                         .limit(10)
                         .all())

            for a in activites:
                cout = sum(c.montant_total_fcfa or 0 for c in a.couts) + \
                       sum(m.montant_total_fcfa or 0 for m in a.main_oeuvre)
                entry = {
                    "type":   a.type.value,
                    "titre":  a.titre,
                    "date":   a.date_prevue.isoformat() if a.date_prevue else None,
                    "statut": a.statut.value,
                    "cout_fcfa": cout,
                }
                if a.statut == StatutActivite.PLANIFIE:
                    ferme_ctx["activites_planifiees"].append(entry)
                else:
                    ferme_ctx["activites_recentes"].append(entry)

            # Coût mois courant
            from app.models.ferme import Cout, MainOeuvre
            from sqlalchemy import func
            for model_cls in (Cout, MainOeuvre):
                result = (db.query(func.sum(model_cls.montant_total_fcfa))
                          .join(Activite, model_cls.activite_id == Activite.id)
                          .filter(Activite.org_id == org_id,
                                  Activite.date_prevue >= debut_mois.date())
                          .scalar())
                ferme_ctx["cout_mois_fcfa"] += int(result or 0)

    # ── Météo ─────────────────────────────────────────────────────────────────
    meteo_ctx: dict = {"conditions": {}, "alertes_actives": [], "previsions_3j": []}
    if not config or config.inclure_meteo:
        # Conditions dernière parcelle principale
        if parcelles_db:
            p_principale = parcelles_db[0]
            cond = (db.query(ConditionMeteo)
                    .filter_by(org_id=org_id, parcelle_id=p_principale.id)
                    .order_by(ConditionMeteo.id.desc())
                    .first())
            if cond:
                meteo_ctx["conditions"] = {
                    "temp_c":      cond.temp_actuelle,
                    "humidite_pct": cond.humidite_rel,
                    "pluie_mm":    cond.pluie_mm,
                    "vent_kmh":    cond.vent_kmh,
                    "description": cond.description_fr,
                    "zone":        cond.zone_agro,
                }

            # Prévisions 3j
            from app.models.meteo import Prevision
            prev = (db.query(Prevision)
                    .filter_by(org_id=org_id, parcelle_id=p_principale.id)
                    .order_by(Prevision.id.desc())
                    .first())
            if prev and prev.donnees:
                for j in prev.donnees[:3]:
                    meteo_ctx["previsions_3j"].append({
                        "date":      j.get("date"),
                        "temp_max":  j.get("temp_max"),
                        "pluie_mm":  j.get("pluie_mm"),
                        "vent_kmh":  j.get("vent_kmh"),
                    })

        # Alertes actives
        alertes = (db.query(Alerte)
                   .filter_by(org_id=org_id, lu=False)
                   .filter(Alerte.niveau.in_([NiveauAlerte.CRITIQUE, NiveauAlerte.AVERTISSEMENT]))
                   .order_by(Alerte.created_at.desc())
                   .limit(5)
                   .all())
        for a in alertes:
            meteo_ctx["alertes_actives"].append({
                "niveau":     a.niveau.value,
                "titre":      a.titre,
                "type":       a.type_alerte.value,
                "sous_type":  a.sous_type,
            })

    # ── Rules Engine ──────────────────────────────────────────────────────────
    regles_ctx: dict = {"declenchees": []}
    if not config or config.inclure_regles:
        try:
            from app.models.rules_engine import RegleDeclenchement, RegleMoteur
            depuis_regles = now - timedelta(days=7)
            declenchements = (
                db.query(RegleDeclenchement)
                .filter(RegleDeclenchement.org_id == org_id,
                        RegleDeclenchement.created_at >= depuis_regles)
                .order_by(RegleDeclenchement.created_at.desc())
                .limit(10)
                .all()
            )
            for d in declenchements:
                r = db.query(RegleMoteur).filter_by(id=d.regle_id).first()
                if r:
                    actions = r.actions or {}
                    regles_ctx["declenchees"].append({
                        "code":      r.code,
                        "nom":       r.nom,
                        "categorie": r.categorie,
                        "gravite":   r.gravite,
                        "alertes":   actions.get("alertes", [])[:2],
                        "reco":      (actions.get("recommandations") or [])[:1],
                        "date":      d.created_at.date().isoformat(),
                    })
        except Exception as e:
            log.debug("Rules historique non disponible: %s", e)

    # ── Estimation tokens ─────────────────────────────────────────────────────
    import json
    contenu_estime = json.dumps({
        "producteur": producteur,
        "parcelles": parcelles_ctx,
        "sante": sante_ctx,
        "ferme": ferme_ctx,
        "meteo": meteo_ctx,
        "regles": regles_ctx,
    }, ensure_ascii=False)
    tokens_estimes = len(contenu_estime) // 4  # ~4 chars/token

    return ContexteAgro(
        producteur=producteur,
        parcelles=parcelles_ctx,
        sante=sante_ctx,
        ferme=ferme_ctx,
        meteo=meteo_ctx,
        regles=regles_ctx,
        date_contexte=now.date().isoformat(),
        tokens_estimes=tokens_estimes,
    )


def contexte_to_texte(ctx: ContexteAgro, max_chars: int = 8000) -> str:
    """Convertit le contexte en bloc texte pour injection dans le system prompt."""
    lignes = []

    p = ctx.producteur
    lignes.append(f"Producteur : {p.get('nom')} | Plan : {p.get('plan','gratuit').upper()}")

    # Parcelles
    if ctx.parcelles:
        lignes.append(f"\n--- PARCELLES ({len(ctx.parcelles)}) ---")
        for parc in ctx.parcelles:
            sol = parc.get("sol", {})
            sol_str = ", ".join(f"{k} {v}" for k, v in sol.items()) if sol else "non analysé"
            lignes.append(
                f"• {parc['nom']} — {parc.get('culture','?')} — "
                f"{parc.get('superficie_ha','?')} ha — {parc.get('zone_agro','?')}"
            )
            if sol:
                lignes.append(f"  Sol : {sol_str}")

    # Météo
    if ctx.meteo.get("conditions"):
        cond = ctx.meteo["conditions"]
        lignes.append(f"\n--- MÉTÉO ACTUELLE ({cond.get('zone','')}) ---")
        lignes.append(
            f"Temp : {cond.get('temp_c','?')}°C | "
            f"Humidité : {cond.get('humidite_pct','?')}% | "
            f"Vent : {cond.get('vent_kmh','?')} km/h | "
            f"Pluie : {cond.get('pluie_mm','?')} mm/j | "
            f"{cond.get('description','')}"
        )
    if ctx.meteo.get("previsions_3j"):
        lignes.append("Prévisions 3j : " + " | ".join(
            f"{j.get('date','')} Tmax {j.get('temp_max','?')}°C pluie {j.get('pluie_mm',0)}mm"
            for j in ctx.meteo["previsions_3j"]
        ))
    if ctx.meteo.get("alertes_actives"):
        lignes.append("⚠ Alertes météo actives :")
        for a in ctx.meteo["alertes_actives"]:
            lignes.append(f"  [{a['niveau'].upper()}] {a['titre']}")

    # Santé
    consults = ctx.sante.get("consultations_recentes", [])
    if consults:
        lignes.append(f"\n--- SANTÉ DES CULTURES ---")
        for c in consults[:3]:
            diags = c.get("diagnostics", [])
            diag_str = ", ".join(
                f"{d['nom']} ({d['confiance']}%)" for d in diags
            ) if diags else "en cours"
            lignes.append(
                f"• {c['parcelle']} le {c['date']} : {c.get('symptomes','?')} → {diag_str}"
            )

    # Ferme
    if ctx.ferme.get("activites_recentes") or ctx.ferme.get("activites_planifiees"):
        lignes.append(f"\n--- ACTIVITÉS FERME ---")
        for a in ctx.ferme.get("activites_recentes", [])[:4]:
            lignes.append(f"• {a['date']} {a['type']} — {a['titre']} ({a['cout_fcfa']:,} FCFA)")
        for a in ctx.ferme.get("activites_planifiees", [])[:3]:
            lignes.append(f"• PLANIFIÉ {a['date']} {a['type']} — {a['titre']}")
        if ctx.ferme.get("cout_mois_fcfa"):
            lignes.append(f"Coûts mois : {ctx.ferme['cout_mois_fcfa']:,} FCFA")

    # Rules déclenchées
    if ctx.regles.get("declenchees"):
        lignes.append(f"\n--- ALERTES AGRONOMIQUES RÉCENTES ---")
        for r in ctx.regles["declenchees"][:5]:
            lignes.append(
                f"• [{r.get('code','')}] {r.get('nom','')} "
                f"({r.get('gravite','')}) — {r.get('date','')}"
            )
            if r.get("reco"):
                lignes.append(f"  → {r['reco'][0]}")

    texte = "\n".join(lignes)
    # Tronquer si trop long
    if len(texte) > max_chars:
        texte = texte[:max_chars] + "\n[...contexte tronqué]"
    return texte
