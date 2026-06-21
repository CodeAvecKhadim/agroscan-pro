"""
Moteur de diagnostic de sol — AgroScan Pro / Social Technologie.
Pour une culture donnée, compare les 8 mesures aux seuils optimaux ISRA/CDH
et produit un statut par paramètre + un score /8.

- Diagnostic SIMPLIFIÉ (plan gratuit) : statut + plage optimale.
- Diagnostic AVANCÉ (premium/coop)    : ajoute la recommandation agronomique chiffrée.

Les 29 cultures du référentiel sont chargées (seuils par culture).
Les recommandations avancées sont génériques par paramètre (valables pour toutes
les cultures) et adaptées au contexte sénégalais (urée, DAP/phosphate de Thiès, KCl…).
"""
from typing import Dict, List, Any

PARAMS = ["Température", "Humidité", "CE", "pH", "Azote", "Phosphore", "Potassium", "Salinité"]

# ----------------------------------------------------------------------------
#  SEUILS [min, max] par culture — référentiel complet (29 cultures)
# ----------------------------------------------------------------------------
SEUILS = {
    "Riz": {"pH": [5, 7], "Humidité": [70, 100], "Température": [20, 35], "CE": [300, 1000], "Azote": [80, 200], "Phosphore": [40, 100], "Potassium": [100, 250], "Salinité": [0, 500]},
    "Mil": {"pH": [5.5, 7.5], "Humidité": [20, 60], "Température": [25, 38], "CE": [100, 1000], "Azote": [30, 100], "Phosphore": [20, 60], "Potassium": [60, 150], "Salinité": [0, 800]},
    "Maïs": {"pH": [5.8, 7], "Humidité": [50, 80], "Température": [18, 32], "CE": [200, 1500], "Azote": [80, 200], "Phosphore": [50, 120], "Potassium": [100, 250], "Salinité": [0, 600]},
    "Sorgho": {"pH": [5.5, 7.5], "Humidité": [25, 70], "Température": [22, 36], "CE": [150, 1200], "Azote": [40, 120], "Phosphore": [25, 70], "Potassium": [70, 180], "Salinité": [0, 800]},
    "Arachide": {"pH": [5.8, 7], "Humidité": [40, 70], "Température": [22, 32], "CE": [200, 1500], "Azote": [50, 150], "Phosphore": [30, 80], "Potassium": [80, 200], "Salinité": [0, 600]},
    "Sésame": {"pH": [5.5, 7.5], "Humidité": [25, 60], "Température": [25, 38], "CE": [100, 1200], "Azote": [30, 100], "Phosphore": [20, 60], "Potassium": [60, 150], "Salinité": [0, 700]},
    "Coton": {"pH": [6, 7.5], "Humidité": [40, 75], "Température": [22, 35], "CE": [200, 1500], "Azote": [60, 180], "Phosphore": [40, 100], "Potassium": [80, 200], "Salinité": [0, 700]},
    "Oignon": {"pH": [6, 7.5], "Humidité": [50, 75], "Température": [18, 30], "CE": [300, 1500], "Azote": [80, 200], "Phosphore": [50, 120], "Potassium": [100, 250], "Salinité": [0, 600]},
    "Tomate": {"pH": [6, 7], "Humidité": [60, 80], "Température": [18, 30], "CE": [300, 2000], "Azote": [100, 250], "Phosphore": [60, 150], "Potassium": [150, 300], "Salinité": [0, 800]},
    "Carotte": {"pH": [6, 7], "Humidité": [55, 75], "Température": [15, 25], "CE": [200, 1500], "Azote": [80, 180], "Phosphore": [50, 120], "Potassium": [100, 200], "Salinité": [0, 500]},
    "Chou": {"pH": [6, 7.5], "Humidité": [60, 80], "Température": [15, 25], "CE": [250, 2000], "Azote": [100, 250], "Phosphore": [60, 150], "Potassium": [150, 300], "Salinité": [0, 700]},
    "Piment": {"pH": [5.5, 7], "Humidité": [55, 80], "Température": [22, 32], "CE": [200, 1500], "Azote": [80, 180], "Phosphore": [50, 120], "Potassium": [120, 250], "Salinité": [0, 700]},
    "Gombo": {"pH": [5.8, 7], "Humidité": [50, 75], "Température": [22, 35], "CE": [150, 1500], "Azote": [60, 150], "Phosphore": [40, 100], "Potassium": [80, 200], "Salinité": [0, 700]},
    "Aubergine amère": {"pH": [5.5, 7], "Humidité": [55, 80], "Température": [22, 32], "CE": [150, 1500], "Azote": [80, 180], "Phosphore": [50, 120], "Potassium": [120, 250], "Salinité": [0, 700]},
    "Mangue": {"pH": [5.5, 7.5], "Humidité": [40, 75], "Température": [24, 38], "CE": [150, 1500], "Azote": [40, 120], "Phosphore": [30, 80], "Potassium": [80, 200], "Salinité": [0, 800]},
    "Pastèque": {"pH": [6, 7], "Humidité": [50, 80], "Température": [24, 35], "CE": [200, 1500], "Azote": [60, 150], "Phosphore": [40, 100], "Potassium": [100, 200], "Salinité": [0, 700]},
    "Melon": {"pH": [6, 7], "Humidité": [50, 80], "Température": [24, 35], "CE": [200, 1500], "Azote": [60, 150], "Phosphore": [40, 100], "Potassium": [100, 200], "Salinité": [0, 600]},
    "Banane": {"pH": [5.5, 7], "Humidité": [70, 90], "Température": [22, 32], "CE": [300, 1500], "Azote": [100, 250], "Phosphore": [60, 150], "Potassium": [150, 350], "Salinité": [0, 800]},
    "Papaye": {"pH": [5.5, 7], "Humidité": [60, 85], "Température": [22, 34], "CE": [200, 1500], "Azote": [80, 200], "Phosphore": [50, 120], "Potassium": [120, 250], "Salinité": [0, 700]},
    "Bisap": {"pH": [5.5, 7.5], "Humidité": [30, 70], "Température": [22, 38], "CE": [100, 1200], "Azote": [30, 100], "Phosphore": [20, 60], "Potassium": [60, 150], "Salinité": [0, 700]},
    "Concombre": {"pH": [6, 7], "Humidité": [60, 80], "Température": [18, 32], "CE": [200, 1500], "Azote": [80, 180], "Phosphore": [50, 120], "Potassium": [100, 200], "Salinité": [0, 600]},
    "Courgette": {"pH": [6, 7], "Humidité": [55, 80], "Température": [18, 32], "CE": [200, 1500], "Azote": [80, 180], "Phosphore": [50, 120], "Potassium": [100, 200], "Salinité": [0, 600]},
    "Laitue": {"pH": [6, 7], "Humidité": [60, 80], "Température": [15, 25], "CE": [200, 1500], "Azote": [80, 180], "Phosphore": [50, 120], "Potassium": [100, 200], "Salinité": [0, 500]},
    "Manioc": {"pH": [5.5, 7], "Humidité": [40, 80], "Température": [22, 32], "CE": [100, 1200], "Azote": [30, 100], "Phosphore": [20, 60], "Potassium": [80, 200], "Salinité": [0, 700]},
    "Navet chinois": {"pH": [6, 7], "Humidité": [55, 75], "Température": [15, 28], "CE": [200, 1500], "Azote": [70, 160], "Phosphore": [40, 100], "Potassium": [80, 180], "Salinité": [0, 500]},
    "Patate douce": {"pH": [5.5, 7], "Humidité": [50, 80], "Température": [22, 32], "CE": [150, 1200], "Azote": [50, 150], "Phosphore": [30, 80], "Potassium": [80, 200], "Salinité": [0, 600]},
    "Poivron": {"pH": [6, 7], "Humidité": [60, 80], "Température": [18, 30], "CE": [200, 1500], "Azote": [80, 200], "Phosphore": [50, 120], "Potassium": [120, 250], "Salinité": [0, 700]},
    "Pomme de terre": {"pH": [5.5, 7], "Humidité": [55, 80], "Température": [15, 25], "CE": [200, 1500], "Azote": [80, 200], "Phosphore": [50, 120], "Potassium": [100, 250], "Salinité": [0, 500]},
    "Jaxatu": {"pH": [5.5, 7], "Humidité": [55, 80], "Température": [22, 35], "CE": [150, 1500], "Azote": [80, 180], "Phosphore": [50, 120], "Potassium": [100, 200], "Salinité": [0, 700]},
}


# ----------------------------------------------------------------------------
#  RECOMMANDATIONS AVANCÉES — génériques par paramètre (bas / ok / haut)
#  Valables pour toutes les cultures ; adaptées au Sénégal.
# ----------------------------------------------------------------------------
RECOS_PARAM = {
    "pH": {
        "bas": "Sol acide. Apporter de la chaux agricole (1 à 3 t/ha) 4 à 6 semaines avant le semis. "
               "L'acidité bloque le phosphore (fréquent en Casamance).",
        "ok":  "pH favorable. Maintenir avec des apports réguliers de matière organique.",
        "haut":"Sol basique : risque de blocage du fer et du zinc. Apporter du soufre agricole "
               "et de la matière organique pour faire baisser le pH.",
    },
    "Salinité": {
        "bas": "Salinité faible : pas de problème.",
        "ok":  "Salinité maîtrisée.",
        "haut":"Salinité élevée (fréquente dans les Niayes et le Delta). Améliorer le drainage, "
               "lessiver à l'eau douce, et choisir des variétés tolérantes.",
    },
    "CE": {
        "bas": "Conductivité faible : sol peu chargé, surveiller la fertilité.",
        "ok":  "Conductivité correcte.",
        "haut":"Conductivité élevée : risque de salinité. Drainer et lessiver à l'eau douce.",
    },
    "Azote": {
        "bas": "Carence en azote. Apporter de l'urée (100 à 200 kg/ha, fractionné en 2-3 fois) "
               "ou de la matière organique compostée.",
        "ok":  "Azote suffisant. Maintenir les bonnes pratiques.",
        "haut":"Excès d'azote : risque de feuillage excessif et de maladies. Réduire les apports azotés.",
    },
    "Phosphore": {
        "bas": "Carence en phosphore : impact sur l'enracinement. Apporter du DAP (18-46-0) "
               "ou du phosphate de Thiès (100 à 200 kg/ha) au semis.",
        "ok":  "Phosphore suffisant pour un bon enracinement.",
        "haut":"Phosphore élevé : pas d'apport supplémentaire ; surveiller le blocage du zinc.",
    },
    "Potassium": {
        "bas": "Carence en potassium : impact sur le calibre et la qualité des fruits/tubercules. "
               "Apporter du KCl ou du sulfate de potassium (100 à 200 kg/ha).",
        "ok":  "Potassium suffisant pour la qualité des récoltes.",
        "haut":"Excès de potassium : peut bloquer le magnésium. Apporter du sulfate de magnésium si symptômes.",
    },
    "Humidité": {
        "bas": "Sol trop sec pour cette culture. Irriguer avant le semis/plantation, de préférence tôt le matin.",
        "ok":  "Humidité du sol adaptée.",
        "haut":"Sol trop humide : vérifier le drainage pour éviter l'asphyxie des racines.",
    },
    "Température": {
        "bas": "Sol froid : la germination peut être ralentie. Attendre un réchauffement ou pailler.",
        "ok":  "Température du sol favorable.",
        "haut":"Sol chaud : arroser tôt le matin ou en soirée, pailler pour limiter l'évaporation.",
    },
}


def diagnose(culture: str, measurements: Dict[str, float], advanced: bool = False) -> Dict[str, Any]:
    """Calcule le diagnostic complet pour une culture et un jeu de mesures."""
    seuils = SEUILS.get(culture)
    if not seuils:
        return {"error": f"Culture inconnue : {culture}", "score": 0, "verdict": "\u2014", "detail": []}

    detail, score, filled = [], 0, 0
    for p in PARAMS:
        val = measurements.get(p)
        rng = seuils.get(p, [None, None])
        mn, mx = rng[0], rng[1]
        if val is None:
            status = "wait"
        elif mn is not None and val < mn:
            status = "bas"
        elif mx is not None and val > mx:
            status = "haut"
        else:
            status = "ok"
        if status != "wait":
            filled += 1
        if status == "ok":
            score += 1

        row = {"parametre": p, "valeur": val, "min": mn, "max": mx, "statut": status}
        if advanced and status in ("bas", "ok", "haut"):
            reco = RECOS_PARAM.get(p)
            if reco:
                row["recommandation"] = reco[status]
        detail.append(row)

    verdict = _verdict(score, filled)
    return {"score": score, "filled": filled, "verdict": verdict, "detail": detail}


def cultures_disponibles() -> List[str]:
    """Liste des cultures du référentiel."""
    return list(SEUILS.keys())


def _verdict(score: int, filled: int) -> str:
    if filled == 0:
        return "En attente"
    if score == 8:
        return "Excellent"
    if score >= 6:
        return "Bon"
    if score >= 4:
        return "Moyen"
    return "\u00c0 corriger"
