"""
Calendrier cultural — AgroScan Pro / Social Technologie.

À partir d'une culture et d'une date de semis, génère les grandes étapes
indicatives jusqu'à la récolte (semis, repiquage, fertilisation, surveillance,
récolte), calculées en proportion du cycle de la culture.

⚠️ DONNÉES INDICATIVES — à valider par un agronome (ISRA/ANCAR).
Les dates réelles varient selon la variété, la zone et la saison. Ce calendrier
est un repère général, pas un itinéraire technique officiel.
"""
from datetime import date, timedelta
from typing import List, Dict, Any

from app.services.infos_cultures import info_culture, AVERTISSEMENT


def _etapes_pour_cycle(cycle_min: int, cycle_max: int, semis_direct: bool) -> List[Dict[str, Any]]:
    """
    Construit les étapes en proportion du cycle (en jours après semis).
    Pour une culture pérenne (cycle 0), renvoie des étapes adaptées.
    """
    if cycle_max <= 0:
        # Culture pérenne (arbre) : pas de cycle semis→récolte classique
        return [
            {"jour": 0,   "titre": "Plantation", "icone": "🌱",
             "detail": "Mettre en terre le plant/la bouture. Arroser abondamment à la reprise."},
            {"jour": 30,  "titre": "Reprise & arrosage", "icone": "💧",
             "detail": "Surveiller la reprise. Maintenir un arrosage régulier les premières semaines."},
            {"jour": 90,  "titre": "Premier entretien", "icone": "✂️",
             "detail": "Désherbage, paillage, première fertilisation organique au pied."},
            {"jour": 180, "titre": "Suivi sanitaire", "icone": "🦠",
             "detail": "Surveiller maladies et ravageurs. Tailler si nécessaire."},
            {"jour": 365, "titre": "Entrée en production", "icone": "🍎",
             "detail": "Selon l'espèce, première production entre 1 et 5 ans. Fertilisation régulière."},
        ]

    cyc = (cycle_min + cycle_max) // 2   # cycle moyen
    etapes = []

    if semis_direct:
        etapes.append({"jour": 0, "titre": "Semis direct", "icone": "🌱",
                       "detail": "Semer directement au champ en lignes. Garder le sol humide jusqu'à la levée."})
        etapes.append({"jour": max(7, int(cyc * 0.07)), "titre": "Levée & démariage", "icone": "🌿",
                       "detail": "Après la levée, éclaircir (démarier) pour garder les plants les plus vigoureux."})
    else:
        etapes.append({"jour": 0, "titre": "Semis en pépinière", "icone": "🌱",
                       "detail": "Semer en pépinière à l'abri. Arroser en pluie fine matin et soir."})
        etapes.append({"jour": max(21, int(cyc * 0.22)), "titre": "Repiquage au champ", "icone": "🌿",
                       "detail": "Repiquer les jeunes plants au champ, de préférence en fin de journée."})

    # Fertilisation (vers 1/3 du cycle)
    etapes.append({"jour": int(cyc * 0.35), "titre": "Apport d'engrais", "icone": "💊",
                   "detail": "Premier apport de fond / d'entretien (selon l'analyse de sol). Fractionner l'azote."})
    # Surveillance sanitaire (vers la moitié)
    etapes.append({"jour": int(cyc * 0.55), "titre": "Surveillance sanitaire", "icone": "🦠",
                   "detail": "Surveiller maladies et ravageurs. Utiliser le diagnostic photo d'AgroScan au moindre doute."})
    # Besoin en eau maximal (vers 2/3)
    etapes.append({"jour": int(cyc * 0.70), "titre": "Phase critique en eau", "icone": "💧",
                   "detail": "Période de forte demande en eau (floraison/grossissement). Ne pas laisser le sol se dessécher."})
    # Récolte (fenêtre min-max)
    etapes.append({"jour": cycle_min, "titre": "Début de récolte possible", "icone": "🧺",
                   "detail": f"La récolte peut commencer autour du jour {cycle_min}, selon la variété."})
    if cycle_max != cycle_min:
        etapes.append({"jour": cycle_max, "titre": "Fin de récolte estimée", "icone": "✅",
                       "detail": f"Récolte généralement terminée vers le jour {cycle_max}."})
    return etapes


# Cultures semées en direct (pas de pépinière/repiquage)
_SEMIS_DIRECT = {"Riz", "Mil", "Maïs", "Sorgho", "Arachide", "Sésame", "Coton",
                 "Carotte", "Gombo", "Pastèque", "Melon", "Bisap", "Concombre",
                 "Courgette", "Navet chinois", "Manioc", "Patate douce", "Pomme de terre"}


def generer_calendrier(culture: str, date_semis: date) -> Dict[str, Any]:
    """
    Renvoie le calendrier cultural d'une culture à partir d'une date de semis.
    """
    fiche = info_culture(culture)
    if not fiche:
        return {"error": f"Culture inconnue : {culture}"}

    cmin, cmax = fiche["cycle_jours"][0], fiche["cycle_jours"][1]
    semis_direct = culture in _SEMIS_DIRECT
    etapes_brutes = _etapes_pour_cycle(cmin, cmax, semis_direct)

    # Convertit les "jours après semis" en vraies dates
    etapes = []
    for e in etapes_brutes:
        d = date_semis + timedelta(days=e["jour"])
        etapes.append({
            "jour": e["jour"],
            "date": d.isoformat(),
            "titre": e["titre"],
            "icone": e["icone"],
            "detail": e["detail"],
        })

    return {
        "culture": culture,
        "date_semis": date_semis.isoformat(),
        "cycle_jours": fiche["cycle_jours"],
        "etapes": etapes,
        "avertissement": AVERTISSEMENT,
    }
