"""
Rules Engine V1 — Catégorie MALADIES — Additions V2
+65 règles : approfondissement maladies manquantes, conditions sol, phases critiques.
"""

MALADIES_RULES_V2 = [

    # ═══════════════════════════════════════════════════════════
    # RIZ — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-RIZ-005",
        "categorie": "maladie", "sous_categorie": "bacteriose",
        "nom": "Bactériose bandes brunes riz Xanthomonas oryzicola",
        "cultures": ["Riz"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["tallage", "montaison"],
        "mois_applicables": [7, 8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 33},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
            {"field": "meteo.vent", "op": "gte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Bactériose bandes brunes riz",
                "message": "Vent + chaleur + humidité = X. oryzicola. Stries brunes sur feuilles, eau laiteuse possible."}],
            "risque": {"score": 0.78, "libelle": "Bactériose foliaire"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Cuivre + éviter blessures riz",
                "detail": "Sulfate de cuivre 1 kg/ha. Réduire excès N. Éviter irrigation par aspersion si symptômes."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-RIZ-006",
        "categorie": "maladie", "sous_categorie": "helminthosporiose",
        "nom": "Helminthosporiose riz Bipolaris oryzae",
        "cultures": ["Riz"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 0.06},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Helminthosporiose riz — carence N + humidité",
                "message": "Bipolaris oryzae favorisé par carence N + humidité. Taches brunes ovales sur feuilles."}],
            "risque": {"score": 0.75, "libelle": "Helminthosporiose"},
            "recommandations": [
                {"priorite": 1, "type": "fertilisation", "titre": "Apport N urgence helminthosporiose",
                    "detail": "30 kg/ha urée immédiatement. Carence N = immunité faible riz."},
                {"priorite": 2, "type": "traitement", "titre": "Fongicide Bipolaris",
                    "detail": "Tricyclazole ou Propiconazole si attaque sévère > 25% feuilles touchées."},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MAÏS — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-MAI-005",
        "categorie": "maladie", "sous_categorie": "bacteriose",
        "nom": "Pourriture bactérienne tige maïs Erwinia chrysanthemi",
        "cultures": ["Maïs"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["montaison"],
        "mois_applicables": [7, 8],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.pluie_24h", "op": "gte", "value": 30},
            {"field": "sol.humidite", "op": "gte", "value": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pourriture tige maïs bactérienne",
                "message": "Feuilles internes molles, odeur fétide = Erwinia. Sol saturé + chaleur = milieu parfait."}],
            "risque": {"score": 0.75, "libelle": "Pourriture bactérienne tige"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainer + éviter excès N",
                "detail": "Drainage prioritaire. Excès N = tiges tendres = sensibilité Erwinia. Réduire densité future."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-MAI-006",
        "categorie": "maladie", "sous_categorie": "virose",
        "nom": "Mosaïque maïs MDMV vecteur pucerons",
        "cultures": ["Maïs"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 32},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Mosaïque maïs — virus MDMV pucerons vecteurs",
                "message": "Temps chaud sec = pucerons vecteurs actifs. Mosaïque MDMV : feuilles rayées jaune-vert. Irréversible."}],
            "risque": {"score": 0.72, "libelle": "Mosaïque MDMV"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Contrôle pucerons vecteurs",
                    "detail": "Imidaclopride 0.2 L/ha. Traiter tôt avant symptômes. Arracher plants malades."},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # ARACHIDE — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-ARA-005",
        "categorie": "maladie", "sous_categorie": "pourridies",
        "nom": "Flétrissement Sclerotium rolfsii arachide sol chaud",
        "cultures": ["Arachide"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": [7, 8],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.temperature", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
            {"field": "sol.matiere_organique", "op": "lte", "value": 1.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sclerotium rolfsii arachide — sol chaud",
                "message": "Sol chaud > 30°C + MO basse = Sclerotium rolfsii. Collet blanc cotonneux, tige morte. Tache qui s'étend."}],
            "risque": {"score": 0.80, "libelle": "Sclerotium collet"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Fongicide Sclerotium arachide",
                    "detail": "PCNB (Terraclor) en traitement sol ou Tebuconazole 0.5 L/ha. Éliminer résidus infestés."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Chaulage sol acide",
                    "detail": "pH < 6 favorise Sclerotium. Chaulage 1 t/ha si pH < 5.8."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-ARA-006",
        "categorie": "maladie", "sous_categorie": "rouille",
        "nom": "Rouille arachide Puccinia arachidis",
        "cultures": ["Arachide"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": [8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 22, "value2": 28},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Rouille arachide — pustules orangées",
                "message": "Temps frais + humide = Puccinia arachidis. Pustules orangées face inférieure feuilles. Défoliation."}],
            "risque": {"score": 0.80, "libelle": "Rouille Puccinia"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide anti-rouille arachide",
                "detail": "Propiconazole 0.5 L/ha ou Mancozèbe 2 kg/ha. Programme 14 jours."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MIL — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-MIL-005",
        "categorie": "maladie", "sous_categorie": "ergot",
        "nom": "Ergot du mil Claviceps fusiformis",
        "cultures": ["Mil"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["floraison"],
        "mois_applicables": [8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "meteo.temp_air", "op": "between", "value": 20, "value2": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Ergot du mil — miellée sucrée",
                "message": "Floraison humide + fraîche = Claviceps fusiformis. Miellée sucrée sur chandelle = ergot. Toxique animaux."}],
            "risque": {"score": 0.78, "libelle": "Ergot Claviceps"},
            "recommandations": [
                {"priorite": 1, "type": "surveillance", "titre": "Inspecter miellée chandelles mil",
                    "detail": "Inspecter à floraison. Chandelles avec miellée = couper et brûler. Ne pas donner aux animaux."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-MIL-006",
        "categorie": "maladie", "sous_categorie": "helminthosporiose",
        "nom": "Helminthosporiose mil Exserohilum turcicum",
        "cultures": ["Mil"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": [8],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
            {"field": "meteo.temp_air", "op": "between", "value": 20, "value2": 28},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Helminthosporiose mil — taches foliaires grises",
                "message": "Grandes taches gris-olive elliptiques feuilles mil = E. turcicum. Se propage en conditions humides."}],
            "risque": {"score": 0.72, "libelle": "Helminthosporiose foliaire"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide contact mil helminthosporiose",
                "detail": "Mancozèbe 2 kg/ha ou Chlorothalonil. Variétés tolérantes si parcelle récurrente."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # SORGHO — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-SOR-005",
        "categorie": "maladie", "sous_categorie": "charbon",
        "nom": "Charbon couvert sorgho Sporisorium sorghi",
        "cultures": ["Sorgho"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["epiaison"],
        "mois_applicables": [9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
            {"field": "meteo.temp_air", "op": "between", "value": 20, "value2": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Charbon couvert sorgho à l'épiaison",
                "message": "Épis noirs à sortie = Sporisorium sorghi. Sol infesté spores + humidité. Traitement semences obligatoire futur."}],
            "risque": {"score": 0.78, "libelle": "Charbon couvert sorgho"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Arracher épis charbonnés",
                    "detail": "Couper et brûler avant libération spores. Ne pas laisser au sol."},
                {"priorite": 2, "type": "traitement", "titre": "Traitement semences prochain cycle",
                    "detail": "Thirame 3 g/kg semence ou Carboxine 2 g/kg. Essentiel pour prochain semis."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-SOR-006",
        "categorie": "maladie", "sous_categorie": "rouille",
        "nom": "Rouille sorgho Puccinia purpurea",
        "cultures": ["Sorgho"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["montaison", "floraison"],
        "mois_applicables": [9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 78},
            {"field": "meteo.temp_air", "op": "between", "value": 20, "value2": 26},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Rouille sorgho pustules pourpres",
                "message": "Pustules pourpres-brunes face inférieure = Puccinia purpurea. Fin de cycle humide favorisant."}],
            "risque": {"score": 0.72, "libelle": "Rouille Puccinia purpurea"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide anti-rouille sorgho",
                "detail": "Propiconazole 0.4 L/ha ou Tebuconazole 0.5 L/ha si attaque sévère > 30% feuilles."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # GOMBO — maladies
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-GOM-003",
        "categorie": "maladie", "sous_categorie": "virose",
        "nom": "Yellow Vein Mosaic Virus YVMV gombo",
        "cultures": ["Gombo"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 65},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "YVMV gombo — mosaïque jaune nervures",
                "message": "Mosaïque jaune sur nervures gombo = YVMV (Begomovirus), vecteur aleurodes. Perte 50-80%. Irréversible."}],
            "risque": {"score": 0.88, "libelle": "YVMV Begomovirus"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Contrôle aleurodes vecteurs YVMV",
                    "detail": "Imidaclopride 0.3 L/ha. Arracher plants malades. Filet insect-proof pépinière."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Variétés tolérantes YVMV",
                    "detail": "Variété IARI-selection ou Clemson Spineless = tolérance YVMV. Rotation nécessaire."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-GOM-004",
        "categorie": "maladie", "sous_categorie": "fusariose",
        "nom": "Flétrissement Fusarium oxysporum gombo",
        "cultures": ["Gombo"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.temperature", "op": "gte", "value": 28},
            {"field": "sol.humidite", "op": "gte", "value": 70},
            {"field": "sol.pH", "op": "lte", "value": 6.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Fusarium oxysporum gombo — flétrissement",
                "message": "Sol chaud + acide + humide = Fusarium vasculaire gombo. Flétrissement unilatéral + brunissement tige."}],
            "risque": {"score": 0.80, "libelle": "Fusarium vasculaire gombo"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Chaulage + Trichoderma sol gombo",
                    "detail": "Chaux pour remonter pH > 6.5. Trichoderma harzianum en sol = bio-contrôle Fusarium."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # SÉSAME — maladies
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-SES-005",
        "categorie": "maladie", "sous_categorie": "bacteriose",
        "nom": "Bactériose Pseudomonas syringae sésame",
        "cultures": ["Sésame"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
            {"field": "meteo.temp_air", "op": "between", "value": 22, "value2": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Bactériose sésame taches angulaires",
                "message": "Taches angulaires limitées nervures + halo jaune = P. syringae. Contagion par éclaboussures."}],
            "risque": {"score": 0.72, "libelle": "Bactériose sésame"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Cuivre bactériose sésame",
                "detail": "Bouillie bordelaise 1%. Éviter arrosage par aspersion. Écartement suffisant pour ventilation."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-SES-006",
        "categorie": "maladie", "sous_categorie": "cercosporiose",
        "nom": "Cercospora sesami sésame feuilles",
        "cultures": ["Sésame"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative", "floraison"],
        "mois_applicables": [8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 78},
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Cercospora sesami taches foliaires",
                "message": "Taches circulaires brun-rougeâtre centre gris = Cercospora sesami. Défol progressive si humidité persiste."}],
            "risque": {"score": 0.72, "libelle": "Cercospora sesami"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Chlorothalonil Cercospora sésame",
                "detail": "Chlorothalonil 1.5 kg/ha ou Mancozèbe 2 kg/ha. Viser face inférieure feuilles."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # NIÉBÉ — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-NIE-005",
        "categorie": "maladie", "sous_categorie": "virose",
        "nom": "Cowpea Mosaic Virus CMV niébé",
        "cultures": ["Niébé"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 26},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 65},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "CMV niébé — mosaïque vecteur pucerons",
                "message": "Temps chaud sec = pucerons vecteurs CMV actifs. Mosaïque + nanisme niébé. Perte 40-60%."}],
            "risque": {"score": 0.80, "libelle": "CMV niébé"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Insecticide pucerons CMV",
                    "detail": "Imidaclopride 0.2 L/ha dès levée. Arracher plants très malades."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Variétés tolérantes CMV",
                    "detail": "IT90K-272-2 = tolérant CMV. Éviter semis tardif (pucerons plus actifs)."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-NIE-006",
        "categorie": "maladie", "sous_categorie": "sclerotiniose",
        "nom": "Sclerotinia sclerotiorum niébé sol froid",
        "cultures": ["Niébé"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": [11, 12, 1],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "lte", "value": 22},
            {"field": "sol.humidite", "op": "gte", "value": 75},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sclerotinia niébé — saison fraîche",
                "message": "T < 22°C + sol humide = Sclerotinia. Tiges molles eau + duvet blanc. Sclerotes noirs."}],
            "risque": {"score": 0.72, "libelle": "Sclerotinia sclerotiorum"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Iprodione Sclerotinia niébé",
                "detail": "Iprodione 0.5 kg/ha. Drainage prioritaire. Rotation légumineuses 3 ans."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # AUBERGINE — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-AUB-005",
        "categorie": "maladie", "sous_categorie": "cercosporiose",
        "nom": "Cercospora solani aubergine",
        "cultures": ["Aubergine"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "meteo.temp_air", "op": "between", "value": 24, "value2": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Cercosporiose aubergine — taches blanches",
                "message": "Taches circulaires blanches entourées de brun foncé = Cercospora. Défoliation progressive."}],
            "risque": {"score": 0.72, "libelle": "Cercospora solani"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide Cercospora aubergine",
                "detail": "Mancozèbe 2 kg/ha ou Chlorothalonil 1.5 kg/ha. Appliquer tôt matin."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-AUB-006",
        "categorie": "maladie", "sous_categorie": "stemphylium",
        "nom": "Stemphylium lycopersici aubergine",
        "cultures": ["Aubergine"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 78},
            {"field": "meteo.temp_air", "op": "between", "value": 22, "value2": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Stemphylium aubergine — taches nécrotiques",
                "message": "Taches nécrotiques brunes irrégulières = Stemphylium lycopersici. Favorable temps doux humide."}],
            "risque": {"score": 0.70, "libelle": "Stemphylium foliaire"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Iprodione + Chlorothalonil aubergine",
                "detail": "Iprodione 0.5 kg/ha + Chlorothalonil 1 kg/ha. Améliorer ventilation rangs."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CONCOMBRE — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-CON-005",
        "categorie": "maladie", "sous_categorie": "oïdium",
        "nom": "Oïdium Podosphaera xanthii concombre",
        "cultures": ["Concombre"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 20, "value2": 28},
            {"field": "meteo.humidite_rel", "op": "between", "value": 50, "value2": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Oïdium concombre — poudre blanche feuilles",
                "message": "Poudre blanche face supérieure feuilles = Podosphaera xanthii. Temps tiède + humidité modérée = parfait."}],
            "risque": {"score": 0.82, "libelle": "Oïdium P. xanthii"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Soufre mouillable ou Myclobutanil oïdium",
                "detail": "Soufre 3 kg/ha ou Myclobutanil 0.3 L/ha. Ne pas appliquer par T > 32°C (brûlures)."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-CON-006",
        "categorie": "maladie", "sous_categorie": "anthracnose",
        "nom": "Anthracnose Colletotrichum lagenarium concombre",
        "cultures": ["Concombre"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
            {"field": "meteo.temp_air", "op": "between", "value": 22, "value2": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Anthracnose concombre — taches eau fruits",
                "message": "Taches aqueuses s'enfonçant sur fruits + feuilles = Colletotrichum lagenarium. Perte commerciale."}],
            "risque": {"score": 0.78, "libelle": "Anthracnose Colletotrichum"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Mancozèbe + Chlorothalonil anthracnose concombre",
                "detail": "Mancozèbe 2 kg/ha tous les 10 jours. Éviter contact eau-sol avec fruits."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CHOU — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-CHO-005",
        "categorie": "maladie", "sous_categorie": "mildiou",
        "nom": "Mildiou chou Peronospora parasitica",
        "cultures": ["Chou"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": [11, 12, 1],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
            {"field": "meteo.temp_air", "op": "between", "value": 10, "value2": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Mildiou chou saison fraîche",
                "message": "T 10-20°C + HR > 85% = Peronospora parasitica. Duvet gris face inférieure + taches jaunes."}],
            "risque": {"score": 0.80, "libelle": "Mildiou Peronospora"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Métalaxyl-M chou mildiou",
                "detail": "Métalaxyl-M + Mancozèbe 2 kg/ha. Appliquer tôt matin. Répéter 7 jours."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-CHO-006",
        "categorie": "maladie", "sous_categorie": "bacteriose",
        "nom": "Pourriture noire chou Xanthomonas campestris pv. campestris",
        "cultures": ["Chou"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 33},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 78},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pourriture noire chou Xanthomonas",
                "message": "Bord feuilles jaunit en V + nervures noires = X. campestris. Irréversible. Contamination rapide."}],
            "risque": {"score": 0.82, "libelle": "Pourriture noire Xanthomonas"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Cuivre anti-Xanthomonas chou",
                    "detail": "Bouillie bordelaise 1% dès symptômes. Arracher plants très atteints. Pas d'arrosage sur feuilles."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Rotation 2 ans sans brassicacées",
                    "detail": "Sol contaminé = rotation 2-3 ans. Semences certifiées."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PAPAYE — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-PAP-005",
        "categorie": "maladie", "sous_categorie": "virose",
        "nom": "Papaya Ring Spot Virus PRSV papaye",
        "cultures": ["Papaye"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 27},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 65},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "PRSV papaye — mosaïque destructrice",
                "message": "PRSV = virus le plus destructeur papaye. Tâches anneaux sur fruits + mosaïque feuilles. Vecteur pucerons."}],
            "risque": {"score": 0.90, "libelle": "PRSV Papaya Ringspot"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Arracher plants PRSV papaye",
                    "detail": "Pas de traitement curatif. Arracher + brûler. Garder isolement spatial 100m du reste."},
                {"priorite": 2, "type": "traitement", "titre": "Contrôle pucerons prévention PRSV",
                    "detail": "Huile minérale 2% sur jeunes plants = réduit inoculation par pucerons."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-PAP-006",
        "categorie": "maladie", "sous_categorie": "anthracnose",
        "nom": "Anthracnose Colletotrichum gloeosporioides papaye",
        "cultures": ["Papaye"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "meteo.pluie_24h", "op": "gte", "value": 15},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Anthracnose fruits papaye",
                "message": "Taches aqueuses s'enfonçant sur fruits papaye = Colletotrichum. Pluie + humidité. Fruits invendables."}],
            "risque": {"score": 0.80, "libelle": "Anthracnose fruit"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Mancozèbe papaye anti-anthracnose",
                "detail": "Mancozèbe 2 kg/ha ou Carbendazime 0.5 kg/ha. Post-récolte: trempage Carbendazime 500 ppm."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PASTÈQUE — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-PAS-005",
        "categorie": "maladie", "sous_categorie": "fusariose",
        "nom": "Flétrissement Fusarium oxysporum f.sp. niveum pastèque",
        "cultures": ["Pastèque"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.temperature", "op": "gte", "value": 25},
            {"field": "sol.pH", "op": "lte", "value": 6.5},
            {"field": "sol.humidite", "op": "gte", "value": 65},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Fusarium pastèque — flétrissement vasculaire",
                "message": "Flétrissement subit = F.o. f.sp. niveum. Tige sectionnée = brunissement vasculaire. Sol persistant 10 ans."}],
            "risque": {"score": 0.88, "libelle": "Fusarium vasculaire pastèque"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Greffe porte-greffe résistant",
                    "detail": "Greffe sur courge Cucurbita ficifolia = résistance totale Fusarium. Solution durable."},
                {"priorite": 2, "type": "traitement", "titre": "Rotation longue + Trichoderma",
                    "detail": "Rotation 5+ ans sans cucurbitacées. Trichoderma harzianum en sol."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-PAS-006",
        "categorie": "maladie", "sous_categorie": "anthracnose",
        "nom": "Anthracnose Colletotrichum lagenarium pastèque",
        "cultures": ["Pastèque"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Anthracnose pastèque — taches noires fruits",
                "message": "Taches concentriques noires sur fruits + taches foliaires = Colletotrichum. Fruits invendables."}],
            "risque": {"score": 0.80, "libelle": "Anthracnose pastèque"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Programme fongicide anthracnose pastèque",
                "detail": "Chlorothalonil 1.5 kg/ha + Mancozèbe 2 kg/ha. Dès début floraison, tous les 10 jours."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # BANANE — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-BAN-005",
        "categorie": "maladie", "sous_categorie": "cercosporiose",
        "nom": "Cercospora noire Mycosphaerella fijiensis (Black Sigatoka)",
        "cultures": ["Banane"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 30},
            {"field": "meteo.temp_air", "op": "between", "value": 24, "value2": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Black Sigatoka bananier — maladie la plus grave",
                "message": "Stries noires → taches jaunes → nécrose = M. fijiensis. Défoliation 75-80% = mûrissement prématuré."}],
            "risque": {"score": 0.92, "libelle": "Black Sigatoka catastrophique"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Programme fongicide Black Sigatoka",
                    "detail": "Triadimefon ou Epoxiconazole alternés. 21 jours. Effeuillage feuilles atteintes."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Effeuillage prophylactique",
                    "detail": "Couper feuilles > 50% atteintes. Brûler. Hygiene plantation capitale."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-BAN-006",
        "categorie": "maladie", "sous_categorie": "fusariose",
        "nom": "Maladie Panama Fusarium oxysporum f.sp. cubense TR4",
        "cultures": ["Banane"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "lte", "value": 6.5},
            {"field": "sol.humidite", "op": "gte", "value": 70},
            {"field": "meteo.temp_air", "op": "gte", "value": 26},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Panama Disease TR4 — Fusarium catastrophique",
                "message": "Flétrissement unilateral + brunissement vasculaire = F.o. cubense TR4. Pas de traitement. Maladie de quarantaine."}],
            "risque": {"score": 0.95, "libelle": "Panama Disease TR4"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Alerte autorités phytosanitaires",
                    "detail": "Signaler immédiatement DAPSA/DPVC. Quarantaine parcelle. Aucun plant ni sol hors zone."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Arracher + incinérer plants malades",
                    "detail": "Arracher. Brûler sur place. Désinfecter outils. Variétés TR4-R à planter uniquement."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # ANACARDE — maladies
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-ANA-005",
        "categorie": "maladie", "sous_categorie": "anthracnose",
        "nom": "Anthracnose Colletotrichum gloeosporioides anacarde",
        "cultures": ["Anacarde"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["floraison"],
        "mois_applicables": [1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
            {"field": "meteo.pluie_24h", "op": "gte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Anthracnose anacarde floraison",
                "message": "Pluie floraison = Colletotrichum. Inflorescences noircissent. Perte totale noix possible."}],
            "risque": {"score": 0.88, "libelle": "Anthracnose floraison"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Mancozèbe + Carbendazime anacardier floraison",
                "detail": "Mancozèbe 2 kg/ha + Carbendazime 0.5 kg/ha. 2 applications à 7 jours si pluie persiste.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MANIOC — maladies complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-MAN-005",
        "categorie": "maladie", "sous_categorie": "bacteriose",
        "nom": "Bactériose manioc Xanthomonas axonopodis pv. manihotis",
        "cultures": ["Manioc"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 32},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
            {"field": "meteo.vent", "op": "gte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Bactériose manioc — taches angulaires tige",
                "message": "Taches foliaires angulaires + exsudat gomme sur tige + dépérissement = X. axonopodis."}],
            "risque": {"score": 0.78, "libelle": "Bactériose vasculaire manioc"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Cuivre + couper tige malades",
                    "detail": "Couper et brûler tiges malades. Cuivre 1% en pulvérisation. Boutures saines uniquement."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RÈGLES GÉNÉRALES MALADIES
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MAL-GEN-003",
        "categorie": "maladie", "sous_categorie": "general",
        "nom": "Sol acide pH<5.0 — Amplification maladies telluriques",
        "cultures": [], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "lt", "value": 5.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Sol très acide = amplification Fusarium/Sclerotium",
                "message": "pH < 5.0 = Fusarium, Sclerotium, nématodes amplifiés. Action corrective avant toute plantation."}],
            "risque": {"score": 0.88, "libelle": "Amplification pathogènes sol acide"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Chaulage urgent pH < 5.0",
                "detail": "Chaux agricole 2-3 t/ha. Incorporer avant plantation. Remonter pH 6.0-6.5 = idéal.",
                "urgence_jours": 14}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-GEN-004",
        "categorie": "maladie", "sous_categorie": "general",
        "nom": "Humidité prolongée + stagnation — Botrytis généralisé",
        "cultures": [], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [7, 8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 88},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 50},
            {"field": "meteo.temp_air", "op": "between", "value": 18, "value2": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Conditions Botrytis généralisé — toutes cultures",
                "message": "HR > 88% + T fraîche = Botrytis cinerea actif sur toutes cultures. Moisissures grises fleurs/fruits."}],
            "risque": {"score": 0.85, "libelle": "Botrytis généralisé"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Iprodione + ventilation urgence",
                "detail": "Iprodione 0.5 kg/ha. Écimer + ventilation entre rangs. Éliminer fleurs sèches stade sensible."}],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "MAL-GEN-005",
        "categorie": "maladie", "sous_categorie": "general",
        "nom": "Excès azote — Sensibilité maladies fongiques augmentée",
        "cultures": [], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "gte", "value": 0.25},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Excès N + humidité = sensibilité fongique",
                "message": "Excès N = tissus tendres, riches, succulents = mildiou/Botrytis/rouilles plus sévères."}],
            "risque": {"score": 0.75, "libelle": "Sensibilité accrue excès N"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Réduire N et augmenter K",
                "detail": "Arrêt apports N. Apporter K2O 30-50 kg/ha = renforce parois cellulaires + résistance."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

]
