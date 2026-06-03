"""
Fiches agronomiques enrichies — AgroScan Pro / Social Technologie.

Pour chaque culture : durée du cycle (semis → récolte), période de semis
indicative au Sénégal, besoin en eau, maladies/ravageurs courants, et un
conseil clé.

⚠️ IMPORTANT — STATUT DES DONNÉES :
Ces informations sont INDICATIVES, issues de connaissances agronomiques
générales. Elles doivent être VALIDÉES par un agronome (ISRA / ANCAR) avant
d'être considérées comme officielles. Les valeurs réelles varient selon la
zone agro-écologique (Niayes, Casamance, Vallée du Fleuve…), la variété et
la saison. Ne pas les présenter comme des recommandations officielles.

Champs :
- cycle_jours : [min, max] durée semis → récolte (jours)
- semis        : période(s) de semis indicative(s) au Sénégal
- eau          : besoin en eau global (Faible / Moyen / Élevé)
- maladies     : maladies et ravageurs les plus fréquents
- conseil      : un repère pratique
"""

# Mention à afficher partout où ces données sont utilisées
AVERTISSEMENT = ("Données indicatives — à valider par un agronome (ISRA/ANCAR). "
                 "Les valeurs varient selon la zone, la variété et la saison.")

INFOS_CULTURE = {
    "Riz": {
        "cycle_jours": [90, 150], "semis": "Hivernage (juin–août) ou contre-saison irriguée (déc.–févr.)",
        "eau": "Élevé", "maladies": "Pyriculariose, foreurs de tiges, oiseaux granivores",
        "conseil": "Maintenir une lame d'eau régulière ; repiquer des plants de 3–4 semaines.",
    },
    "Mil": {
        "cycle_jours": [75, 110], "semis": "Début hivernage (juin–juillet)",
        "eau": "Faible", "maladies": "Mildiou, charbon, chenilles mineuses, oiseaux",
        "conseil": "Culture rustique adaptée aux zones sèches ; démarier après levée.",
    },
    "Maïs": {
        "cycle_jours": [90, 120], "semis": "Hivernage (juin–juillet) ; irrigué en contre-saison",
        "eau": "Moyen", "maladies": "Foreurs de tiges, chenille légionnaire d'automne, helminthosporiose",
        "conseil": "Surveiller la chenille légionnaire dès la levée ; fractionner l'azote.",
    },
    "Sorgho": {
        "cycle_jours": [100, 130], "semis": "Hivernage (juin–juillet)",
        "eau": "Faible", "maladies": "Charbon, anthracnose, foreurs, oiseaux",
        "conseil": "Très résistant à la sécheresse ; bon précédent pour les légumineuses.",
    },
    "Arachide": {
        "cycle_jours": [90, 120], "semis": "Début hivernage (juin–juillet)",
        "eau": "Moyen", "maladies": "Cercosporiose, rosette, rouille, pourriture du collet",
        "conseil": "Légumineuse : enrichit le sol en azote ; apport localisé NPK 6-20-10.",
    },
    "Sésame": {
        "cycle_jours": [90, 120], "semis": "Hivernage (juillet)",
        "eau": "Faible", "maladies": "Flétrissement, pucerons, punaises",
        "conseil": "Récolter avant déhiscence complète des capsules pour limiter les pertes.",
    },
    "Coton": {
        "cycle_jours": [150, 180], "semis": "Début hivernage (juin)",
        "eau": "Moyen", "maladies": "Bactériose, chenilles de la capsule, pucerons, jassides",
        "conseil": "Surveiller les ravageurs de la capsule ; respecter les rotations.",
    },
    "Oignon": {
        "cycle_jours": [90, 150], "semis": "Saison fraîche (oct.–déc.), repiquage 6–8 sem.",
        "eau": "Moyen", "maladies": "Mildiou, thrips, pourriture du collet, alternariose",
        "conseil": "Culture phare des Niayes ; stopper l'irrigation avant récolte pour la conservation.",
    },
    "Tomate": {
        "cycle_jours": [90, 120], "semis": "Saison fraîche (oct.–janv.), repiquage 4–5 sem.",
        "eau": "Moyen", "maladies": "Mildiou, flétrissement bactérien, nématodes, mouche blanche, Tuta absoluta",
        "conseil": "Tuteurer ; arroser au pied, jamais sur le feuillage, pour limiter le mildiou.",
    },
    "Carotte": {
        "cycle_jours": [90, 120], "semis": "Saison fraîche (oct.–janv.), semis direct",
        "eau": "Moyen", "maladies": "Alternariose, nématodes, mouche de la carotte",
        "conseil": "Sol meuble et profond, sans cailloux ni fumier frais (racines fourchues sinon).",
    },
    "Chou": {
        "cycle_jours": [70, 110], "semis": "Saison fraîche (oct.–janv.), repiquage 4 sem.",
        "eau": "Élevé", "maladies": "Teigne des crucifères, chenilles, fonte des semis, hernie",
        "conseil": "Surveiller les chenilles ; arrosage régulier pour une bonne pommaison.",
    },
    "Piment": {
        "cycle_jours": [100, 150], "semis": "Saison fraîche à chaude, repiquage 5–6 sem.",
        "eau": "Moyen", "maladies": "Anthracnose, flétrissement, pucerons, acariens, viroses",
        "conseil": "Récoltes échelonnées ; éviter l'excès d'azote (trop de feuilles, peu de fruits).",
    },
    "Gombo": {
        "cycle_jours": [50, 90], "semis": "Hivernage et saison chaude, semis direct",
        "eau": "Moyen", "maladies": "Oïdium, viroses (jaunisse), pucerons, nématodes",
        "conseil": "Récolter les capsules jeunes et tendres tous les 2–3 jours.",
    },
    "Aubergine amère": {
        "cycle_jours": [90, 130], "semis": "Toute l'année (irrigué), repiquage 5 sem.",
        "eau": "Moyen", "maladies": "Flétrissement bactérien, doryphores, pucerons, nématodes",
        "conseil": "Culture locale rustique ; récoltes étalées sur plusieurs semaines.",
    },
    "Mangue": {
        "cycle_jours": [0, 0], "semis": "Plantation pérenne (arbre) ; greffage recommandé",
        "eau": "Moyen", "maladies": "Mouche des fruits, anthracnose, oïdium, cochenilles",
        "conseil": "Arbre pérenne (production en 3–5 ans) ; lutte contre la mouche des fruits essentielle.",
    },
    "Pastèque": {
        "cycle_jours": [75, 100], "semis": "Saison sèche chaude (févr.–mai), semis direct",
        "eau": "Moyen", "maladies": "Oïdium, mildiou, mouche des fruits, pucerons",
        "conseil": "Besoin de chaleur et d'espace ; réduire l'eau en fin de cycle (fruits plus sucrés).",
    },
    "Melon": {
        "cycle_jours": [80, 110], "semis": "Saison sèche chaude, semis direct",
        "eau": "Moyen", "maladies": "Oïdium, fusariose, pucerons, mouche des fruits",
        "conseil": "Limiter l'arrosage à l'approche de la maturité pour le sucre.",
    },
    "Banane": {
        "cycle_jours": [0, 0], "semis": "Plantation pérenne (rejets) ; production continue",
        "eau": "Élevé", "maladies": "Cercosporiose (maladie des raies), charançon, nématodes",
        "conseil": "Forte demande en eau et potassium ; protéger du vent.",
    },
    "Papaye": {
        "cycle_jours": [0, 0], "semis": "Plantation pérenne ; 1re récolte en 8–11 mois",
        "eau": "Moyen", "maladies": "Anthracnose, oïdium, virose (mosaïque), cochenilles",
        "conseil": "Sol bien drainé impératif (sensible à l'excès d'eau au collet).",
    },
    "Bisap": {
        "cycle_jours": [120, 180], "semis": "Début hivernage (juin–juillet)",
        "eau": "Faible", "maladies": "Pucerons, nématodes, pourriture des racines",
        "conseil": "Récolter les calices à pleine maturité ; culture peu exigeante.",
    },
    "Concombre": {
        "cycle_jours": [50, 75], "semis": "Saison fraîche à chaude, semis direct ou repiquage",
        "eau": "Élevé", "maladies": "Oïdium, mildiou, mouche blanche, pucerons",
        "conseil": "Cycle court ; récoltes fréquentes pour stimuler la production.",
    },
    "Courgette": {
        "cycle_jours": [50, 70], "semis": "Saison fraîche à chaude, semis direct",
        "eau": "Moyen", "maladies": "Oïdium, viroses, pucerons, mouche blanche",
        "conseil": "Cycle très court ; récolter jeune tous les 2–3 jours.",
    },
    "Laitue": {
        "cycle_jours": [40, 70], "semis": "Saison fraîche (oct.–févr.), repiquage 3–4 sem.",
        "eau": "Élevé", "maladies": "Mildiou, fonte des semis, pucerons, limaces",
        "conseil": "Cycle court ; arrosages légers et fréquents ; éviter la chaleur (montée en graines).",
    },
    "Manioc": {
        "cycle_jours": [240, 365], "semis": "Début hivernage, bouturage de tiges",
        "eau": "Faible", "maladies": "Mosaïque africaine, cochenille farineuse, bactériose",
        "conseil": "Culture longue mais rustique ; planter des boutures saines et certifiées.",
    },
    "Navet chinois": {
        "cycle_jours": [45, 70], "semis": "Saison fraîche, semis direct",
        "eau": "Moyen", "maladies": "Altises, chenilles, fonte des semis",
        "conseil": "Cycle court ; éclaircir tôt pour de beaux bulbes.",
    },
    "Patate douce": {
        "cycle_jours": [100, 150], "semis": "Hivernage et contre-saison, bouturage",
        "eau": "Moyen", "maladies": "Charançon de la patate douce, viroses, alternariose",
        "conseil": "Butter les lignes ; la variété à chair orange est riche en vitamine A.",
    },
    "Poivron": {
        "cycle_jours": [100, 140], "semis": "Saison fraîche, repiquage 5–6 sem.",
        "eau": "Moyen", "maladies": "Anthracnose, flétrissement, pucerons, acariens, viroses",
        "conseil": "Sensible aux coups de chaleur ; ombrage léger possible en saison chaude.",
    },
    "Pomme de terre": {
        "cycle_jours": [90, 120], "semis": "Saison fraîche (nov.–janv.), plants/tubercules",
        "eau": "Moyen", "maladies": "Mildiou, alternariose, teigne, nématodes",
        "conseil": "Butter régulièrement ; utiliser des plants certifiés indemnes de maladies.",
    },
    "Jaxatu": {
        "cycle_jours": [90, 130], "semis": "Toute l'année (irrigué), repiquage 5 sem.",
        "eau": "Moyen", "maladies": "Flétrissement bactérien, pucerons, nématodes, doryphores",
        "conseil": "Aubergine locale (Gilo) très prisée ; récoltes étalées sur plusieurs semaines.",
    },
}


def info_culture(culture: str) -> dict:
    """Renvoie la fiche enrichie d'une culture, ou None si absente."""
    return INFOS_CULTURE.get(culture)
