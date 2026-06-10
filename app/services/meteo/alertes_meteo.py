"""
Alertes météo pures — basées sur seuils config : pluie, vent, chaleur, sécheresse, ETP.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.meteo import Alerte, ConditionMeteo, ConfigAlertes, NiveauAlerte, TypeAlerte

log = logging.getLogger(__name__)

_SEUILS_DEFAUT = {
    "pluie_forte_mm": 30,
    "pluie_extreme_mm": 60,
    "chaleur_max_c": 38,
    "chaleur_extreme_c": 42,
    "vent_fort_kmh": 40,
    "vent_extreme_kmh": 70,
    "secheresse_jours": 7,
    "secheresse_critique_jours": 14,
    "etp_elevee_mm": 8,
}


def generer_alertes_meteo(
    db: Session,
    org_id: int,
    conditions: ConditionMeteo,
    previsions_raw: list[dict],
    config: Optional[ConfigAlertes] = None,
    parcelle_id: Optional[int] = None,
    culture_id: Optional[int] = None,
) -> list[Alerte]:
    """Génère alertes météo pour une parcelle/zone selon seuils config."""
    seuils = _SEUILS_DEFAUT.copy()
    if config and config.seuils:
        seuils.update(config.seuils)

    nouvelles: list[Alerte] = []

    # ── 1. Pluie forte / prévue ───────────────────────────────────────────────
    for jour in previsions_raw[:7]:
        pluie = jour.get("pluie_mm") or 0.0
        d = jour.get("date", "?")
        if pluie >= seuils["pluie_extreme_mm"]:
            if not _existe_recente(db, org_id, parcelle_id, "pluie_extreme"):
                nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                    TypeAlerte.METEO, "pluie_extreme", NiveauAlerte.CRITIQUE,
                    f"Pluies extrêmes prévues le {d}",
                    f"Précipitations prévues : {pluie:.0f} mm. Risque d'inondation et de perte de récolte.",
                    {"valeur_mm": pluie, "date": d, "seuil_mm": seuils["pluie_extreme_mm"]},
                ))
            break
        elif pluie >= seuils["pluie_forte_mm"]:
            if not _existe_recente(db, org_id, parcelle_id, "pluie_forte"):
                nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                    TypeAlerte.METEO, "pluie_forte", NiveauAlerte.AVERTISSEMENT,
                    f"Fortes pluies prévues le {d}",
                    f"Précipitations prévues : {pluie:.0f} mm. Éviter traitements et récoltes.",
                    {"valeur_mm": pluie, "date": d, "seuil_mm": seuils["pluie_forte_mm"]},
                ))
            break

    # ── 2. Chaleur ────────────────────────────────────────────────────────────
    for jour in previsions_raw[:7]:
        tmax = jour.get("temp_max")
        if tmax is None:
            continue
        d = jour.get("date", "?")
        if tmax >= seuils["chaleur_extreme_c"]:
            if not _existe_recente(db, org_id, parcelle_id, "chaleur_extreme"):
                nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                    TypeAlerte.METEO, "chaleur_extreme", NiveauAlerte.CRITIQUE,
                    f"Chaleur extrême prévue le {d} ({tmax:.0f}°C)",
                    f"Température max prévue : {tmax:.0f}°C. Risque de brûlures foliaires et stress thermique sévère.",
                    {"valeur_c": tmax, "date": d, "seuil_c": seuils["chaleur_extreme_c"]},
                ))
            break
        elif tmax >= seuils["chaleur_max_c"]:
            if not _existe_recente(db, org_id, parcelle_id, "chaleur"):
                nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                    TypeAlerte.METEO, "chaleur", NiveauAlerte.AVERTISSEMENT,
                    f"Forte chaleur prévue le {d} ({tmax:.0f}°C)",
                    f"Température max prévue : {tmax:.0f}°C. Augmenter fréquence d'irrigation.",
                    {"valeur_c": tmax, "date": d, "seuil_c": seuils["chaleur_max_c"]},
                ))
            break

    # ── 3. Vent fort ──────────────────────────────────────────────────────────
    for jour in previsions_raw[:7]:
        vent = jour.get("vent_kmh")
        if vent is None:
            continue
        d = jour.get("date", "?")
        if vent >= seuils["vent_extreme_kmh"]:
            if not _existe_recente(db, org_id, parcelle_id, "vent_extreme"):
                nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                    TypeAlerte.METEO, "vent_extreme", NiveauAlerte.CRITIQUE,
                    f"Vents extrêmes prévus le {d} ({vent:.0f} km/h)",
                    f"Vent max prévu : {vent:.0f} km/h. Risque de verse. Protéger structures.",
                    {"valeur_kmh": vent, "date": d, "seuil_kmh": seuils["vent_extreme_kmh"]},
                ))
            break
        elif vent >= seuils["vent_fort_kmh"]:
            if not _existe_recente(db, org_id, parcelle_id, "vent_fort"):
                nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                    TypeAlerte.METEO, "vent_fort", NiveauAlerte.AVERTISSEMENT,
                    f"Vents forts prévus le {d} ({vent:.0f} km/h)",
                    f"Vent max prévu : {vent:.0f} km/h. Éviter pulvérisations (risque dérive).",
                    {"valeur_kmh": vent, "date": d, "seuil_kmh": seuils["vent_fort_kmh"]},
                ))
            break

    # ── 4. Sécheresse ─────────────────────────────────────────────────────────
    jours_sans_pluie = _compter_jours_sans_pluie(previsions_raw, seuil_mm=1.0)
    if jours_sans_pluie >= seuils["secheresse_critique_jours"]:
        if not _existe_recente(db, org_id, parcelle_id, "secheresse"):
            nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                TypeAlerte.METEO, "secheresse", NiveauAlerte.CRITIQUE,
                f"Sécheresse critique : {jours_sans_pluie} jours sans pluie prévus",
                f"{jours_sans_pluie} jours consécutifs sans précipitations prévues. Irrigation d'urgence recommandée.",
                {"jours_sans_pluie": jours_sans_pluie, "seuil": seuils["secheresse_critique_jours"]},
            ))
    elif jours_sans_pluie >= seuils["secheresse_jours"]:
        if not _existe_recente(db, org_id, parcelle_id, "secheresse"):
            nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                TypeAlerte.METEO, "secheresse", NiveauAlerte.AVERTISSEMENT,
                f"Risque sécheresse : {jours_sans_pluie} jours sans pluie prévus",
                f"{jours_sans_pluie} jours sans précipitations prévues. Surveiller humidité sol.",
                {"jours_sans_pluie": jours_sans_pluie, "seuil": seuils["secheresse_jours"]},
            ))

    # ── 5. ETP élevée (stress hydrique) ──────────────────────────────────────
    for jour in previsions_raw[:3]:
        etp = jour.get("etp_mm")
        if etp and etp >= seuils["etp_elevee_mm"]:
            d = jour.get("date", "?")
            if not _existe_recente(db, org_id, parcelle_id, "etp_elevee"):
                nouvelles.append(_creer(org_id, parcelle_id, culture_id,
                    TypeAlerte.METEO, "etp_elevee", NiveauAlerte.INFO,
                    f"Évapotranspiration élevée le {d} ({etp:.1f} mm/j)",
                    f"ETP prévue : {etp:.1f} mm/j. Besoins en eau élevés. Vérifier disponibilité irrigation.",
                    {"valeur_mm": etp, "date": d, "seuil_mm": seuils["etp_elevee_mm"]},
                ))
            break

    for a in nouvelles:
        db.add(a)
    if nouvelles:
        db.commit()

    return nouvelles


# ── Helpers ───────────────────────────────────────────────────────────────────

def _creer(
    org_id, parcelle_id, culture_id,
    type_alerte, sous_type, niveau,
    titre, message, details=None,
) -> Alerte:
    return Alerte(
        org_id=org_id,
        parcelle_id=parcelle_id,
        culture_id=culture_id,
        type_alerte=type_alerte,
        sous_type=sous_type,
        niveau=niveau,
        titre=titre,
        message=message,
        details=details,
        valable_du=datetime.now(timezone.utc),
    )


def _existe_recente(
    db: Session, org_id: int, parcelle_id: Optional[int], sous_type: str,
    heures: int = 24,
) -> bool:
    """Évite doublons : retourne True si alerte identique < heures."""
    from datetime import timedelta
    seuil = datetime.now(timezone.utc) - timedelta(hours=heures)
    q = db.query(Alerte).filter(
        Alerte.org_id == org_id,
        Alerte.sous_type == sous_type,
        Alerte.created_at >= seuil,
    )
    if parcelle_id is not None:
        q = q.filter(Alerte.parcelle_id == parcelle_id)
    return q.first() is not None


def _compter_jours_sans_pluie(previsions: list[dict], seuil_mm: float = 1.0) -> int:
    count = 0
    for j in previsions:
        if (j.get("pluie_mm") or 0) < seuil_mm:
            count += 1
        else:
            break
    return count
