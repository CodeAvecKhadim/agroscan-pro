"""
Génération du plan de traitement depuis les résultats de diagnostic.
Convertit les actions des règles déclenchées en sc_traitements.
Déduplique, trie par urgence, persiste en base.
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.sante import Consultation, Diagnostic, Traitement, TypeTraitement, StatutTraitement


def generer_plan(
    db: Session,
    consultation: Consultation,
    diagnostics: list[dict],
    regles_declenchees: list[dict],
) -> list[Traitement]:
    """
    Génère et insère sc_traitements depuis :
    - Les actions des règles déclenchées (source principale)
    - Les diagnostics classés (pour lier diagnostic_id)
    Retourne la liste des Traitement créés.
    """
    traitements_raw: list[dict] = []

    # 1. Extraire traitements des règles déclenchées
    # evaluate() retourne: alertes (list[str]), recommandations (list[str]), risque (str)
    for regle in regles_declenchees:
        code    = regle.get("code", "")
        gravite = regle.get("gravite", "faible")
        priorite = {"critique": 1, "elevee": 2, "moyenne": 3, "faible": 4}.get(gravite, 4)

        # Chaque recommandation → 1 traitement
        for reco in regle.get("recommandations", []):
            if not reco:
                continue
            traitements_raw.append({
                "type":          "mesure_culturale",
                "titre":         str(reco),
                "urgence_jours": 3 if gravite == "critique" else (7 if gravite == "elevee" else 14),
                "priorite":      priorite,
                "detail":        f"Règle {code} — gravité {gravite}",
            })

        # Alertes critiques → traitement surveillance
        for alerte in regle.get("alertes", []):
            if not alerte:
                continue
            traitements_raw.append({
                "type":          "surveillance",
                "titre":         str(alerte),
                "urgence_jours": 1 if gravite == "critique" else 3,
                "priorite":      1 if gravite == "critique" else priorite,
                "detail":        f"Alerte règle {code}",
            })

    # 2. Fallback : si rules engine vide, générer depuis diagnostics bibliothèque
    if not traitements_raw and diagnostics:
        traitements_raw = _traitements_from_diagnostics(db, diagnostics)

    # 3. Dédupliquer (même titre + même type)
    seen: set[str] = set()
    deduped: list[dict] = []
    for t in traitements_raw:
        key = f"{t['type']}|{t['titre'][:60]}"
        if key not in seen:
            seen.add(key)
            deduped.append(t)

    # 4. Trier : urgence_jours ASC (None → fin), priorite ASC
    deduped.sort(key=lambda x: (x.get("urgence_jours") or 999, x.get("priorite") or 5))

    # 5. Associer diagnostic_id (rang 1)
    diag_id_top = None
    if diagnostics:
        top = diagnostics[0]
        diag = (db.query(Diagnostic)
                .filter_by(consultation_id=consultation.id,
                           entite_id=top["entite_id"],
                           entite_type=top["entite_type"])
                .first())
        diag_id_top = diag.id if diag else None

    # 6. Insérer
    inserted: list[Traitement] = []
    for i, t in enumerate(deduped, start=1):
        obj = Traitement(
            consultation_id     = consultation.id,
            diagnostic_id       = diag_id_top if i == 1 else None,
            priorite            = t.get("priorite", i),
            type                = _map_type(t.get("type", "mesure_culturale")),
            titre               = t["titre"],
            produit             = t.get("produit"),
            dose                = t.get("dose"),
            frequence           = t.get("frequence"),
            delai_carence_jours = t.get("delai_carence_jours"),
            urgence_jours       = t.get("urgence_jours"),
            detail              = t.get("detail"),
            date_application    = _date_application(t.get("urgence_jours")),
            statut              = StatutTraitement.PLANIFIE,
        )
        db.add(obj)
        inserted.append(obj)

    db.commit()
    for obj in inserted:
        db.refresh(obj)
    return inserted


def _traitements_from_diagnostics(db: Session, diagnostics: list[dict]) -> list[dict]:
    """Fallback : crée un traitement générique depuis le diagnostic top."""
    if not diagnostics:
        return []
    top = diagnostics[0]
    return [{
        "type":     "surveillance",
        "titre":    f"Surveiller évolution : {top['entite_nom']}",
        "detail":   f"Diagnostic probable : {top['entite_nom']} "
                    f"(confiance {round(top['score_confiance']*100)}%). "
                    "Prendre photo et contacter technicien si aggravation.",
        "urgence_jours": 7,
        "priorite": 1,
    }]


def _map_type(type_str: str) -> TypeTraitement:
    mapping = {
        "traitement_phyto": TypeTraitement.TRAITEMENT_PHYTO,
        "fertilisation":    TypeTraitement.FERTILISATION,
        "irrigation":       TypeTraitement.IRRIGATION,
        "mesure_culturale": TypeTraitement.MESURE_CULTURALE,
        "recolte":          TypeTraitement.RECOLTE,
        "surveillance":     TypeTraitement.SURVEILLANCE,
        "alerte":           TypeTraitement.SURVEILLANCE,
        "conseil":          TypeTraitement.MESURE_CULTURALE,
    }
    return mapping.get(type_str.lower(), TypeTraitement.MESURE_CULTURALE)


def _date_application(urgence_jours: int | None) -> date | None:
    if urgence_jours is None:
        return None
    return date.today() + timedelta(days=urgence_jours)
