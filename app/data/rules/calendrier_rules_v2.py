"""
Rules Engine V1 — Catégorie CALENDRIER CULTURAL — Additions V2
+42 règles : stades critiques, fenêtres semis, alertes phénologiques.
"""

CALENDRIER_RULES_V2 = [

    # ═══════════════════════════════════════════════════════════
    # ARACHIDE — calendrier détaillé
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-ARA-003",
        "categorie": "calendrier", "sous_categorie": "semis",
        "nom": "Fenêtre optimale semis arachide hâtif",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [6, 7],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 25},
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 33},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Fenêtre optimale semis arachide",
                "message": "Pluies installées + T 25-33°C = fenêtre idéale semis arachide. Cycle 90-110 jours pour maturité avant fin hivernage."}],
            "risque": {"score": 0.20, "libelle": "Opportunité semis"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Semer arachide maintenant — variétés 90j",
                "detail": "Variétés 90j : Fleur 11, 73-33. Densité 165,000 plants/ha (40×15 cm). Traitement semences Thirame."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-ARA-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Arachide — Stade gynophore (35-45 JAL)",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": [7, 8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Stade gynophore arachide — Actions requises",
                "message": "Gynophore formé = phase critique. Ne pas travailler sol. Humidité sol obligatoire."}],
            "risque": {"score": 0.50, "libelle": "Phase gynophore"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Arrêter travaux sol sous arachide",
                    "detail": "Zéro sarclage profond après gynophore. Binage superficiel max. Sol meuble obligatoire."},
                {"priorite": 2, "type": "fertilisation", "titre": "Apport Ca gynophore",
                    "detail": "20-30 kg/ha gypse ou CaCO3 si Ca sol < 3 meq/100g. Critique pour remplissage gousses."},
            ],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # SORGHO — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-SOR-003",
        "categorie": "calendrier", "sous_categorie": "semis",
        "nom": "Semis sorgho — Fenêtre optimale hivernage",
        "cultures": ["Sorgho"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [6, 7],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Fenêtre semis sorgho",
                "message": "Pluies installées. Sorgho : semis dès 20mm cumulé sur 7j. Variétés 90-120 jours selon zone."}],
            "risque": {"score": 0.20, "libelle": "Opportunité semis"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Semer sorgho en ligne",
                "detail": "Sorgho : 75×25 cm, 2-3 graines/poquet, éclaircissage à 2 plants/poquet à 15 JAL. 5-8 kg/ha semences."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-SOR-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Sorgho — Épiaison (60-70 JAL) stade zéro tolérance",
        "cultures": ["Sorgho"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["epiaison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Épiaison sorgho — protection active requise",
                "message": "Épiaison sorgho = stade zéro tolérance stress + oiseaux granivores (Quelea). Surveiller intensément."}],
            "risque": {"score": 0.75, "libelle": "Stade vulnérable"},
            "recommandations": [
                {"priorite": 1, "type": "surveillance", "titre": "Surveillance quotidienne oiseaux épiaison",
                    "detail": "Dès épiaison : gardiennage, fils brillants, repulsifs. Quelea = perte totale en 48h."},
                {"priorite": 2, "type": "irrigation", "titre": "Priorité irrigation épiaison",
                    "detail": "20-25 mm si pluie < 10mm/7j. Critique pour remplissage grains."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # NIÉBÉ — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-NIE-003",
        "categorie": "calendrier", "sous_categorie": "semis",
        "nom": "Semis niébé — Dérobé après céréale",
        "cultures": ["Niébé"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 15},
            {"field": "meteo.temp_air", "op": "gte", "value": 27},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Fenêtre semis niébé dérobé",
                "message": "Août-sept = niébé dérobé après mil/sorgho. Variétés 60-75 jours pour récolte avant fin hivernage."}],
            "risque": {"score": 0.20, "libelle": "Opportunité semis dérobé"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Semer niébé 60j comme dérobée",
                "detail": "IT90K-372-1-2 ou IT97K-556-6 (60-65j). 75×25 cm, 2 plants/poquet. Ne pas dépasser fin août."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-NIE-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Niébé — Floraison 30-40 JAL protection insectes",
        "cultures": ["Niébé"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Floraison niébé — Insectes piqueurs-suceurs",
                "message": "Floraison niébé = attaque thrips + punaises (Clavigralla). Protection insecticide requise."}],
            "risque": {"score": 0.78, "libelle": "Insectes floraison"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Traitement insecticide floraison niébé",
                "detail": "Lambda-cyhalothrine 0.3 L/ha ou Dimethoate 0.5 L/ha. Traiter soir (préserver pollinisateurs)."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # SÉSAME — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-SES-003",
        "categorie": "calendrier", "sous_categorie": "semis",
        "nom": "Semis sésame — Fenêtre stricte début hivernage",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [6, 7],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
            {"field": "meteo.temp_air", "op": "between", "value": 27, "value2": 35},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Fenêtre semis sésame — Semer immédiatement",
                "message": "Sésame = fenêtre semis courte juin-juillet. Semis tardif (août+) = cycle non terminé avant fin pluies."}],
            "risque": {"score": 0.25, "libelle": "Risque semis tardif"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Semis sésame en lignes espacées",
                "detail": "30×15 cm. Graines superficielles 1-2 cm. 3-5 kg/ha. Ne pas enfouir profond. Sol meuble impératif."}],
        },
        "gravite": "faible", "priorite": 3, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-SES-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Sésame — Récolte avant déhiscence capsules",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["maturation"],
        "mois_applicables": [10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "lte", "value": 50},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sésame — Récolte urgente anti-déhiscence",
                "message": "Sésame mûr + temps sec chaud = capsules s'ouvrent = pertes 30-50%. Récolter quand 2/3 des capsules jaunes."}],
            "risque": {"score": 0.82, "libelle": "Pertes déhiscence capsules"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Récolte sésame à maturité 2/3",
                "detail": "Couper base, botter, laisser sécher en bottes debout 5-7 jours. Battre sur bâche.",
                "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.82, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # GOMBO — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-GOM-003",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Gombo — Récolte capsules tous les 2-3 jours",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Gombo — Récolter tous les 2-3 jours",
                "message": "Capsule gombo devient fibreuse en 3-4 jours par temps chaud. Récolte quotidienne = qualité prime."}],
            "risque": {"score": 0.72, "libelle": "Déclassement capsules fibreuses"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Programme récolte gombo 2-3j",
                "detail": "Récolter quand capsule 5-8 cm (avant lignification). T chaud > 30°C = récolte tous les 2 jours."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CHOU — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-CHO-003",
        "categorie": "calendrier", "sous_categorie": "semis",
        "nom": "Pépinière chou — Saison fraîche obligatoire",
        "cultures": ["Chou"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [10, 11, 12],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_min", "op": "lte", "value": 22},
            {"field": "meteo.temp_air", "op": "lte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Fenêtre pépinière chou (saison fraîche)",
                "message": "Saison fraîche = conditions optimales chou. Démarrer pépinière maintenant pour transplantation 3 semaines."}],
            "risque": {"score": 0.20, "libelle": "Opportunité pépinière"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Pépinière chou sous ombrage",
                "detail": "Semis en pépinière sous 30% ombrage. Substrat enrichi. Transplanter à 4-5 feuilles vraies. Arroser 2x/jour."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-CHO-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Chou — Pommaison stade décisif rendement",
        "cultures": ["Chou"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["pommaison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "lte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pommaison chou — Actions décisives",
                "message": "Pommaison = 3-4 semaines décisives. Tout stress ici = petite tête. Eau + engrais K + protection Teigne."}],
            "risque": {"score": 0.72, "libelle": "Tête petite si stress"},
            "recommandations": [
                {"priorite": 1, "type": "fertilisation", "titre": "Engrais K pommaison chou",
                    "detail": "KCl 60 kg/ha en couronne. Potassium = qualité tête, densité, conservation."},
                {"priorite": 2, "type": "traitement", "titre": "Surveiller Teigne Plutella pommaison",
                    "detail": "Inspection hebdomadaire cœur chou. BT ou spinosad si chenilles présentes."},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CONCOMBRE — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-CON-003",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Concombre — Récolte précoce anti-jaunissement",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Concombre — Récolter avant jaunissement",
                "message": "Concombre laissé sur pied après maturité = jaunit en 2 jours + stoppe production. Récolte tous les 2 jours."}],
            "risque": {"score": 0.70, "libelle": "Arrêt production si non récolté"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Récolte concombre 2x/semaine",
                "detail": "Récolter quand fruit atteint calibre commercial (15-20 cm). Enlever tous fruits jaunes."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PAPAYE — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-PAP-003",
        "categorie": "calendrier", "sous_categorie": "semis",
        "nom": "Pépinière papaye — Présaison sèche",
        "cultures": ["Papaye"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 26},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Fenêtre pépinière papaye — Oct-Nov",
                "message": "Pépinière papaye oct-nov = transplantation jan-fév = premières fleurs juillet. Cycle 8-10 mois."}],
            "risque": {"score": 0.20, "libelle": "Opportunité pépinière"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Pépinière papaye en sachet",
                "detail": "3 graines/sachet. Germination 15-20 jours. Conserver 1 plant/sachet. Transplanter à 25-30 cm hauteur."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-PAP-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Papaye — Détermination sexe à 4-6 feuilles",
        "cultures": ["Papaye"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 26},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Sélection sexe papaye à 4-6 feuilles",
                "message": "À 4-6 feuilles vraies: visibles fleurs au collet. Conserver 1 femelle + 1 mâle/10 plants."}],
            "risque": {"score": 0.50, "libelle": "Sex ratio critique"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Sélection plants papaye 4-6 feuilles",
                "detail": "Identifier sexe. Arracher mâles sauf 1/10. Hermaphrodite (Solo) = conserver tous. Couper excédents."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.82, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PASTÈQUE — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-PAS-003",
        "categorie": "calendrier", "sous_categorie": "semis",
        "nom": "Semis pastèque — Saison fraîche contre-saison",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [10, 11, 12],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "lte", "value": 32},
            {"field": "meteo.temp_min", "op": "gte", "value": 18},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Fenêtre semis pastèque contre-saison",
                "message": "Oct-déc = pastèque contre-saison possible avec irrigation. T < 32°C = qualité optimale fruits."}],
            "risque": {"score": 0.20, "libelle": "Opportunité semis contre-saison"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Semis pastèque avec paillage",
                "detail": "Poquet 200×100 cm. 2-3 graines/poquet. Paillage plastique multigolve. Irriguer 2x/semaine."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-PAS-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Pastèque — Taille filet et limitation fruits",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 26},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Taille pastèque — limiter à 2-3 fruits/plant",
                "message": "Sans taille : 10+ fruits petits. Avec taille à 2-3 fruits : calibre XL valeur export."}],
            "risque": {"score": 0.55, "libelle": "Fruits trop petits sans taille"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Limitation fruits pastèque",
                "detail": "Conserver 2-3 fruits/plant sur tige principale. Supprimer tiges latérales excédentaires à 2-3 feuilles."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # ANACARDE — calendrier perennial
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-ANA-003",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Anacarde — Taille formation après récolte",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [5, 6, 7],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Taille formation anacarde juin-juil",
                "message": "Post-récolte = fenêtre taille anacarde. Tailler tiges mortes, branches mal formées, crosses."}],
            "risque": {"score": 0.40, "libelle": "Entretien productivité"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Taille entretien anacardier",
                "detail": "Supprimer branches mortes, gourmands, branches < 1.5 m sol. Cicatriser coupes avec bouillie bordelaise."}],
        },
        "gravite": "moyenne", "priorite": 4, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-ANA-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Anacarde — Fertilisation pré-floraison (oct-nov)",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 5},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Anacarde — Fertiliser avant floraison",
                "message": "Oct-nov = dernières pluies = fenêtre fertilisation de fond avant floraison (janv-fév)."}],
            "risque": {"score": 0.50, "libelle": "Floraison sans réserves nutritives"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Fertilisation anacardier pré-floraison",
                "detail": "NPK 10-10-20 ou fumure organique 20 kg/arbre en couronne. Couvrir zone racinaire."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # BANANE — calendrier pérenne
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-BAN-003",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Banane — Gaine florale émergence",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Gaine florale bananier — Actions urgentes",
                "message": "Émergence régime = stade critique. Enfumer fleur pour protéger. Tuteur si vent > 30 km/h prévu."}],
            "risque": {"score": 0.70, "libelle": "Dommages régime"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Ensachage régime banane",
                    "detail": "Sac plastique bleu UV sur régime dès émergence = +15% calibre, protection insectes/froid."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Écimage inflorescence mâle",
                    "detail": "Couper bourgeon mâle après dernière main = économie photosynthèse vers fruits."},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-BAN-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Banane — Rejets sélection monoculme",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 24},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Gestion rejets bananier — Sélection",
                "message": "Bananier produit 8-15 rejets/an. Sans sélection = compétition = régimes petits. Conserver 1-2 rejets/cépée."}],
            "risque": {"score": 0.55, "libelle": "Compétition rejets"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Éliminer rejets excédentaires",
                "detail": "Conserver 1 rejet sword-sucker tous les 4-5 mois. Couper autres à la base (bêche profonde)."}],
        },
        "gravite": "moyenne", "priorite": 4, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MANGUE — calendrier pérenne
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-MAG-003",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Mangue — Induction florale stress hydrique contrôlé",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [10, 11, 12],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "meteo.temp_min", "op": "lte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Stress sec + froid = induction florale mangue",
                "message": "Sec + nuits fraîches = induction florale naturelle. Ne pas irriguer 4-6 semaines. Floraison prévue janv-fév."}],
            "risque": {"score": 0.20, "libelle": "Induction florale normale"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Arrêt irrigation induction florale mangue",
                "detail": "Arrêt total arrosage oct-nov. Stimule induction florale. Reprendre à l'ouverture des boutons."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-MAG-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Mangue — Thinning manuel grossissement fruits",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": [3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Thinning fruits mangue — Qualité export",
                "message": "Limiter à 2-3 fruits/panicule = mangues calibre export. Sans thinning = 15+ petits fruits."}],
            "risque": {"score": 0.55, "libelle": "Fruits sous-calibrés"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Thinning mangue à noix pois",
                "detail": "Au stade 'petite noix' (2-3 cm) = conserver 2-3 fruits/panicule. Calibre >350g = valeur marchande."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.72, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # RIZ — calendrier détaillé
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-RIZ-003",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Riz — Repiquage timing précis",
        "cultures": ["Riz"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [7, 8],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
            {"field": "meteo.temp_air", "op": "gte", "value": 27},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Fenêtre repiquage riz — 21-25 JAL",
                "message": "Repiquage optimal à 21-25 jours après semis pépinière. Au-delà 30j = perte tallage potentiel."}],
            "risque": {"score": 0.60, "libelle": "Retard repiquage"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Repiquer riz avant 25 JAL",
                "detail": "2-3 talles/poquet. Profondeur 2-3 cm. Espacement 20×20 cm. Ne pas repiquer > 30 JAL."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-RIZ-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Riz — Retrait eau 10 jours avant récolte",
        "cultures": ["Riz"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 26},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Retrait eau riz — J-10 avant récolte",
                "message": "Retirer eau 10-14 jours avant récolte = sol portant pour machines + grains mûrs uniformément."}],
            "risque": {"score": 0.60, "libelle": "Récolte sol portant"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Arrêt irrigation riz maturation",
                "detail": "Fermer arrivée eau 10-14 jours avant récolte estimée. Ressuyage sol = qualité grains + efficacité récolte."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.82, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MAÏS — calendrier
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-MAI-003",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Maïs — Éclaircissage et démariage",
        "cultures": ["Maïs"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Démariage maïs — 10-15 JAL",
                "message": "Maïs doit être démarié à 10-15 JAL. Conserver 1 plant vigoureux/poquet. Au-delà = concurrence racines."}],
            "risque": {"score": 0.68, "libelle": "Compétition plants"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Démariage maïs 10-15 JAL",
                "detail": "Conserver 1 plant/poquet (75×25 cm) ou 2 plants/poquet (75×40 cm). Conserver le plus vigoureux."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-MAI-004",
        "categorie": "calendrier", "sous_categorie": "stade_critique",
        "nom": "Maïs — Buttage contre verse",
        "cultures": ["Maïs"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["tallage"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Buttage maïs — stade 5-7 feuilles",
                "message": "Butter maïs à 5-7 feuilles = stabilité contre verse + favorise racines adventives."}],
            "risque": {"score": 0.68, "libelle": "Verse si non butté"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Butter maïs avec terre de labour",
                "detail": "Ramener terre au pied 8-10 cm hauteur. Combiner avec 2e apport urée. Outil : daba ou buttoir tracteur."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RÈGLES GÉNÉRALES CALENDRIER
    # ═══════════════════════════════════════════════════════════
    {
        "code": "CAL-GEN-003",
        "categorie": "calendrier", "sous_categorie": "general",
        "nom": "Retard semis > 4 semaines — Perte potentiel rendement",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 10},
            {"field": "meteo.temp_air", "op": "gte", "value": 27},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Retard semis — Fenêtre se ferme",
                "message": "Août = fenêtre semis qui se ferme. Chaque semaine de retard = -5-10% potentiel rendement céréales."}],
            "risque": {"score": 0.72, "libelle": "Retard fenêtre semis"},
            "recommandations": [{"priorite": 1, "type": "semis",
                "titre": "Semer maintenant variétés précoces",
                "detail": "Variétés 75-90 jours obligatoires si semis après mi-août. Ne pas dépasser 15 août pour mil/sorgho principal."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-GEN-004",
        "categorie": "calendrier", "sous_categorie": "general",
        "nom": "Rotation annuelle — Rappel anti-répétition culture",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "culture_precedent", "op": "eq", "value": "present"},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Rotation — Éviter même famille",
                "message": "Répétition même culture ou même famille = accumulation pathogènes sols. Rotation minimum 2 ans conseillée."}],
            "risque": {"score": 0.55, "libelle": "Pathogènes sol par répétition"},
            "recommandations": [{"priorite": 1, "type": "planification",
                "titre": "Rotation recommandée",
                "detail": "Alterner: Légumineuses → Céréales → Maraîchers. Solanées max 1/3 ans. Niébé enrichit sol N."}],
        },
        "gravite": "moyenne", "priorite": 4, "confiance": 0.72, "plan_requis": "gratuit",
    },
    {
        "code": "CAL-GEN-005",
        "categorie": "calendrier", "sous_categorie": "general",
        "nom": "Association culturale — Complémentarité nutritive",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": [6, 7],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Association culturale recommandée",
                "message": "Petite exploitation = associer Maïs + Niébé ou Sorgho + Arachide = complémentarité N + couverture sol."}],
            "risque": {"score": 0.25, "libelle": "Opportunité association"},
            "recommandations": [{"priorite": 1, "type": "planification",
                "titre": "Associations productives AgroScan",
                "detail": "Maïs + Niébé (1:1) : Niébé fixe N, ombrage réduit adventices. Sorgho + Arachide : même logique."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.72, "plan_requis": "gratuit",
    },

]
