"""
Rules Engine V1 — Catégorie RENDEMENT — Additions V2
+45 règles : prévision récolte, pertes stockage, qualité grains, valorisation.
"""

RENDEMENT_RULES_V2 = [

    # ═══════════════════════════════════════════════════════════
    # ARACHIDE
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-ARA-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement arachide — Conditions favorables",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["maturation"],
        "mois_applicables": [10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "between", "value": 10, "value2": 25},
            {"field": "meteo.temp_air", "op": "between", "value": 26, "value2": 32},
            {"field": "sol.pH", "op": "between", "value": 5.8, "value2": 6.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Conditions favorables rendement arachide",
                "message": "Conditions actuelles bonnes pour remplissage gousses. Rendement estimé 1.5-2 t/ha sans pertes."}],
            "risque": {"score": 0.20, "libelle": "Rendement correct attendu"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Préparer logistique récolte arachide",
                "detail": "Rendement attendu 1.5-2 t/ha en sec. Prévoir main d'oeuvre arrachage + séchage solaire 4-5 jours."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.72, "plan_requis": "premium",
    },
    {
        "code": "REN-ARA-004",
        "categorie": "rendement", "sous_categorie": "perte_qualite",
        "nom": "Récolte tardive arachide — Aflatoxines + germination",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["maturation"],
        "mois_applicables": [10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 70},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 15},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Retard récolte arachide = aflatoxines",
                "message": "Arachide mûre sous pluie = Aspergillus flavus → aflatoxines B1. Invendable. Récolter immédiatement."}],
            "risque": {"score": 0.90, "libelle": "Contamination aflatoxines"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Récolte urgence arachide",
                "detail": "Arracher + sécher dans les 48h. Séchage < 8% humidité. Triage visuel gousses décolorées.",
                "urgence_jours": 2}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # SORGHO
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-SOR-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement sorgho — Grains en formation",
        "cultures": ["Sorgho"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "between", "value": 15, "value2": 40},
            {"field": "meteo.temp_air", "op": "between", "value": 27, "value2": 33},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Remplissage grains sorgho normal",
                "message": "Conditions pluie + T acceptables pour remplissage. Rendement estimé 1.5-2.5 t/ha selon variété."}],
            "risque": {"score": 0.20, "libelle": "Rendement attendu correct"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Prévoir logistique battage sorgho",
                "detail": "Rendement estimé 1.5-2.5 t/ha. Prévoir séchage panicules 10-14 jours avant battage."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },
    {
        "code": "REN-SOR-004",
        "categorie": "rendement", "sous_categorie": "perte_stockage",
        "nom": "Stockage sorgho — Moisissures grain humide",
        "cultures": ["Sorgho"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Risque stockage sorgho humide",
                "message": "Grain > 14% humidité en stockage = Aspergillus + Fusarium. Sécher à < 12% avant stockage."}],
            "risque": {"score": 0.78, "libelle": "Moisissure stockage"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Séchage sorgho avant stockage",
                "detail": "Séchage solaire sur bâche 5-7 jours. Tester humidité grains. Magasin aéré, surélevé."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # NIÉBÉ
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-NIE-003",
        "categorie": "rendement", "sous_categorie": "perte_stockage",
        "nom": "Niébé stockage — Bruche Callosobruchus maculatus",
        "cultures": ["Niébé"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.humidite_rel", "op": "between", "value": 50, "value2": 75},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Bruche niébé — traitement stockage urgent",
                "message": "T > 28°C + HR 50-75% = conditions parfaites Callosobruchus maculatus. 100% perte en 6 mois sans protection."}],
            "risque": {"score": 0.92, "libelle": "Bruche stockage"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Protection grains niébé stockage",
                    "detail": "Huile végétale 5 ml/kg (suffoquer insectes). Ou hermétique (silo métallique). Ou N-SanKam.",
                    "urgence_jours": 1},
                {"priorite": 2, "type": "traitement", "titre": "Phosphine si attaque sévère",
                    "detail": "Phosphine (fumigation) si infestation > 10 insectes/kg. Professionnel uniquement."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.92, "plan_requis": "gratuit",
    },
    {
        "code": "REN-NIE-004",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement niébé — Gousses en formation",
        "cultures": ["Niébé"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 27, "value2": 34},
            {"field": "meteo.pluie_7j", "op": "between", "value": 10, "value2": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Conditions normales niébé fructification",
                "message": "Gousses en formation dans bonnes conditions. Rendement attendu 0.6-1.2 t/ha graine sèche."}],
            "risque": {"score": 0.20, "libelle": "Rendement normal"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Récolte niébé 2-3 passages",
                "detail": "Récolter en 2-3 passages quand gousses jaunissent. Éviter attendre toutes mûres = déhiscence."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # SÉSAME
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-SES-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement sésame — Capsules formées",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 27, "value2": 35},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Sésame — capsules en formation",
                "message": "Capsules bien formées. Rendement attendu 400-700 kg/ha graine selon variété."}],
            "risque": {"score": 0.20, "libelle": "Rendement attendu"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Préparation récolte sésame",
                "detail": "À 2/3 capsules jaunies = couper. Bottes debout 5j. Battre sur bâche. Rendement décortiqué × 0.97."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.68, "plan_requis": "premium",
    },
    {
        "code": "REN-SES-004",
        "categorie": "rendement", "sous_categorie": "qualite",
        "nom": "Sésame — Qualité huile (teneur > 50%)",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "between", "value": 5.5, "value2": 7.0},
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Conditions favorables qualité huile sésame",
                "message": "T > 28°C + pH sol neutre = teneur huile optimale (51-56%). Récolte pas trop tardive pour couleur claire."}],
            "risque": {"score": 0.20, "libelle": "Qualité huile bonne"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Séchage rapide pour sésame qualité export",
                "detail": "Séchage rapide < 6% humidité = qualité blanc premium. Éviter contact sol = couleur foncée déclassée."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.68, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # MANIOC
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-MAN-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement manioc — Maturation 12-18 mois",
        "cultures": ["Manioc"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["tuberisation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 34},
            {"field": "sol.pH", "op": "between", "value": 5.5, "value2": 7.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Conditions normales manioc tubérisation",
                "message": "Tubérisation active. Rendement 15-25 t/ha attendu à 12 mois selon variété."}],
            "risque": {"score": 0.20, "libelle": "Tubérisation normale"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Plan récolte manioc échelonnée",
                "detail": "Manioc = récolte possible 8-24 mois. Récolter par plots pour étaler commercialisation."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },
    {
        "code": "REN-MAN-004",
        "categorie": "rendement", "sous_categorie": "perte_recolte",
        "nom": "Manioc — Pertes post-récolte détérioration 48h",
        "cultures": ["Manioc"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 70},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Manioc récolté — Détérioration 24-48h",
                "message": "Racines manioc = périt en 24-48h après récolte. Vendre ou transformer immédiatement."}],
            "risque": {"score": 0.90, "libelle": "Détérioration post-récolte rapide"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Transformer manioc dans les 24h",
                    "detail": "Gari, attiéké, farine, chips = transformer dans les 24h. Trempage eau = 48h max.",
                    "urgence_jours": 1},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Cirage racines si délai",
                    "detail": "Paraffine ou huile végétale sur racines = +5 jours conservation."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # GOMBO
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-GOM-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement gombo — Production continue",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 28, "value2": 36},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Rendement gombo — production continue possible",
                "message": "Conditions thermiques idéales gombo. Production 8-12 t/ha/cycle sur 4-5 mois récolte continue."}],
            "risque": {"score": 0.20, "libelle": "Production normale"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Plan commercialisation gombo",
                "detail": "Récolte continue = marché local frais ou transformation (séchage). Gombo séché × 8 = valeur ajoutée."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # PIMENT
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-PIM-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement piment — Fructification normale",
        "cultures": ["Piment"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 32},
            {"field": "meteo.pluie_7j", "op": "between", "value": 10, "value2": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Conditions piment fructification correctes",
                "message": "Piment en bonnes conditions. Rendement attendu 8-15 t/ha selon variété et conduite."}],
            "risque": {"score": 0.20, "libelle": "Rendement normal"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Préparer commercialisation piment",
                "detail": "Piment frais = marché local. Piment rouge séché = valeur ×3. Prévoir séchoir solaire."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },
    {
        "code": "REN-PIM-004",
        "categorie": "rendement", "sous_categorie": "qualite",
        "nom": "Piment — Calibre et teneur capsaïcine",
        "cultures": ["Piment"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Chaleur sèche = capsaïcine élevée piment",
                "message": "T > 30°C + faible HR = piment plus fort (capsaïcine élevée). Valeur marchande piment fort supérieure."}],
            "risque": {"score": 0.20, "libelle": "Qualité capsaïcine favorable"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Valoriser piment fort en saison sèche",
                "detail": "Piment séché saison sèche = teneur capsaïcine max. Marché export possible (poudre piment)."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.65, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # ANACARDE
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-ANA-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement anacarde — Maturation noix",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": [3, 4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 28, "value2": 36},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Anacarde — noix en formation",
                "message": "Conditions sèches normales maturation anacarde. Rendement 500-800 kg/ha noix brutes attendu."}],
            "risque": {"score": 0.20, "libelle": "Rendement normal"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Récolte anacarde au sol dès chute",
                "detail": "Ramasser quotidiennement dès chute. Ne pas laisser > 3 jours sol (champignons). Sécher 3-5 jours."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },
    {
        "code": "REN-ANA-004",
        "categorie": "rendement", "sous_categorie": "qualite",
        "nom": "Anacarde — Outturn (KOR) qualité export",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "lte", "value": 50},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Séchage anacarde — qualité KOR optimal",
                "message": "Séchage bien = KOR (Kernel Output Ratio) > 47 = prime export. Séchage < 3 jours = KOR bas."}],
            "risque": {"score": 0.20, "libelle": "Qualité export"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Séchage anacarde 3-5 jours soleil",
                "detail": "Humidité 8-10% = KOR optimal. Test: bonne noix flotte pas dans eau. Stocker sur palette."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # BANANE
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-BAN-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement banane — Régime 75-120 jours",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 33},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Conditions croissance banane normales",
                "message": "T 25-33°C + eau disponible = croissance optimale. Régime = 25-40 kg/plant selon variété."}],
            "risque": {"score": 0.20, "libelle": "Rendement normal"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Suivi mûrissement banane 75-120j",
                "detail": "Du bourgeon mâle à récolte = 75-120 jours. Récolter quand angles des doigts s'arrondissent."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },
    {
        "code": "REN-BAN-004",
        "categorie": "rendement", "sous_categorie": "perte_recolte",
        "nom": "Banane — Pertes post-récolte mûrissement rapide",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Banane — Mûrissement accéléré T > 32°C",
                "message": "> 32°C = banane verte mûrit en 2-3 jours. Logistique vente/transport urgente."}],
            "risque": {"score": 0.78, "libelle": "Pertes post-récolte chaleur"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Récolter banane légèrement verte",
                    "detail": "Récolter avant maturité commerciale si transport > 2 jours. Chambre fraîche si possible.",
                    "urgence_jours": 2},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PASTÈQUE
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-PAS-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement pastèque — Grossissement",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 28, "value2": 36},
            {"field": "meteo.pluie_7j", "op": "between", "value": 10, "value2": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Pastèque en grossissement normal",
                "message": "Conditions favorables grossissement. Rendement 25-35 t/ha selon conduite."}],
            "risque": {"score": 0.20, "libelle": "Rendement normal"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Indicateurs maturité pastèque",
                "detail": "Vrille sèche + son creux au tapotage + pédoncule brunissant = maturité. Brix > 10 = qualité premium."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # MANGUE
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-MAG-003",
        "categorie": "rendement", "sous_categorie": "perte_qualite",
        "nom": "Mangue — Attaques mouches + anthracnose post-récolte",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": [4, 5, 6],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Mouches fruits + anthracnose mangue post-récolte",
                "message": "Ceratitis cosyra + Colletotrichum = pertes 30-60% après récolte. Traitements bagging/trempage."}],
            "risque": {"score": 0.82, "libelle": "Pertes mouches + anthracnose"},
            "recommandations": [
                {"priorite": 1, "type": "traitement", "titre": "Ensachage mangue ou trempage post-récolte",
                    "detail": "Bagging plastique (eau-savon) empêche ponte. Après récolte: trempage eau chaude 50°C/5min anti-anthracnose.",
                    "urgence_jours": 3},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "REN-MAG-004",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement mangue — Floraison abondante",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["floraison"],
        "mois_applicables": [1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 23, "value2": 31},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Floraison mangue — conditions favorables",
                "message": "T 23-31°C + sec = pollinisation optimale mangue. Bon nouage = récolte 3-4 mois."}],
            "risque": {"score": 0.20, "libelle": "Bon potentiel récolte"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Estimer récolte mangue 90-120 jours",
                "detail": "Floraison → récolte = 90-120 jours selon variété. Kent: 110j. Amélie: 90j. Keitt: 120j."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # RIZ
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-RIZ-003",
        "categorie": "rendement", "sous_categorie": "perte_recolte",
        "nom": "Riz — Pertes récolte tardive égrenage",
        "cultures": ["Riz"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 50},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Riz mûr + vent = égrenage",
                "message": "Riz à maturité + vent > 30 km/h + sec = égrenage spontané. Perdre 20-30% récolte en 3-5 jours."}],
            "risque": {"score": 0.80, "libelle": "Égrenage récolte tardive"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Récolte riz urgence — ne pas attendre",
                "detail": "Couper quand 85% des grains mûrs (couleur dorée). Ne pas attendre 100% = pertes."},
            ],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "REN-RIZ-004",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement riz — Remplissage grains",
        "cultures": ["Riz"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 32},
            {"field": "meteo.pluie_7j", "op": "between", "value": 15, "value2": 40},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Remplissage grains riz normal",
                "message": "Conditions favorables remplissage. Rendement estimé 4-6 t/ha paddy selon variété et conduite."}],
            "risque": {"score": 0.20, "libelle": "Rendement paddy attendu"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Estimer production paddy par parcelle",
                "detail": "Compter 4-6 panicules/m² × 150-200 grains/panicule × 30g/1000grains = estimation."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # MAÏS
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-MAI-003",
        "categorie": "rendement", "sous_categorie": "perte_stockage",
        "nom": "Maïs stockage — Sitophilus zeamais charançon",
        "cultures": ["Maïs"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 27},
            {"field": "meteo.humidite_rel", "op": "between", "value": 55, "value2": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Charançon maïs — Conditions stockage actives",
                "message": "T > 27°C + HR 55-80% = Sitophilus zeamais actif. 1 femelle = 300 descendants. 50% perte en 6 mois."}],
            "risque": {"score": 0.90, "libelle": "Charançon stockage maïs"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Protection maïs stockage",
                    "detail": "Sécher à < 12% humidité avant stockage. Silo hermétique ou traitement Actellic 2%. Durée max 6 mois.",
                    "urgence_jours": 2},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "REN-MAI-004",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement maïs — Remplissage épis",
        "cultures": ["Maïs"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 26, "value2": 33},
            {"field": "meteo.pluie_7j", "op": "between", "value": 15, "value2": 40},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Maïs — remplissage épis normal",
                "message": "Conditions remplissage grains maïs normales. Rendement 2.5-4 t/ha selon variété."}],
            "risque": {"score": 0.20, "libelle": "Rendement attendu"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Indicateurs maturité maïs",
                "detail": "Grain à lait → pâteux → vitreux = maturité. Couche noire base grain = maturité physiologique atteinte."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # MIL
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-MIL-003",
        "categorie": "rendement", "sous_categorie": "prevision",
        "nom": "Prévision rendement mil — Chandelle formation",
        "cultures": ["Mil"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["epiaison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 27, "value2": 35},
            {"field": "meteo.pluie_7j", "op": "between", "value": 10, "value2": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Chandelle mil en formation normale",
                "message": "Épiaison mil dans bonnes conditions. Rendement estimé 800-1500 kg/ha selon pluviométrie."}],
            "risque": {"score": 0.20, "libelle": "Rendement normal"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Récolte mil 90-100 JAL",
                "detail": "Couper chandelles à 85-90% grains mûrs. Sécher 7-10 jours. Battre quand grain dur à ongle."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.70, "plan_requis": "premium",
    },
    {
        "code": "REN-MIL-004",
        "categorie": "rendement", "sous_categorie": "perte_stockage",
        "nom": "Mil — Humidité stockage + mites Sitotroga",
        "cultures": ["Mil"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 65},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Mil stockage — Sitotroga + humidité",
                "message": "T > 28°C + HR > 65% = Sitotroga cerealella (mite) + moisissures. Grain > 12% humidité = risque."}],
            "risque": {"score": 0.78, "libelle": "Insectes stockage + moisissures"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Sécher mil avant grenier",
                "detail": "Sécher chandelles sur aire 10-12 jours. Stocker grains battus < 12% HR. Grenier ventilé surélevé."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RÈGLES GÉNÉRALES RENDEMENT
    # ═══════════════════════════════════════════════════════════
    {
        "code": "REN-GEN-003",
        "categorie": "rendement", "sous_categorie": "general",
        "nom": "Déficit combiné N+eau — Perte rendement systématique",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 0.05},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Double stress N + eau = perte rendement -30 à -50%",
                "message": "Carence N + stress hydrique simultanés = perte rendement 30-50% inévitable. Lever un des deux en priorité."}],
            "risque": {"score": 0.90, "libelle": "Double stress N+eau"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Lever stress hydrique en premier",
                    "detail": "Irrigation avant fertilisation. Urée sans eau = brûlure + volatilisation.",
                    "urgence_jours": 1},
                {"priorite": 2, "type": "fertilisation", "titre": "Urée après retour eau",
                    "detail": "30-50 kg/ha urée dès que sol humide. Enfoui légèrement."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "REN-GEN-004",
        "categorie": "rendement", "sous_categorie": "general",
        "nom": "Pertes post-récolte généralisées — Mauvais séchage",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Mauvaises conditions séchage récoltes",
                "message": "HR > 75% + pluies = séchage impossible en plein air. Grains humides = moisissures + perte valeur."}],
            "risque": {"score": 0.80, "libelle": "Conditions séchage défavorables"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Séchage artificiel ou étaler attente",
                    "detail": "Séchoir amélioré ou étaler sur béton sous abri. Tourner 2x/jour. Humidité cible < 12%."},
                {"priorite": 2, "type": "planification", "titre": "Reporter transformation si possible",
                    "detail": "Si stock peut attendre, reporter jusqu'au temps sec. Sinon : séchoir à bois urgence."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "REN-GEN-005",
        "categorie": "rendement", "sous_categorie": "general",
        "nom": "Estimation pertes adventices non désherbées",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": [7, 8],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
            {"field": "meteo.temp_air", "op": "gte", "value": 26},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Adventices saison pluies — Pertes rendement -20-40%",
                "message": "Saison pluies + chaleur = explosion adventices. Sans désherbage 30-45 JAL = perte 20-40% rendement."}],
            "risque": {"score": 0.82, "libelle": "Pertes adventices non contrôlées"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Désherbage manuel ou herbicide 15-25 JAL",
                "detail": "Désherber avant 25 JAL = critique. 2e passage 45 JAL si besoin. Herbicides: Pendiméthaline + Gramoxone.",
                "urgence_jours": 5}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "REN-GEN-006",
        "categorie": "rendement", "sous_categorie": "general",
        "nom": "Estimateur rendement global parcelle — Contexte favorable",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "between", "value": 10, "value2": 50},
            {"field": "meteo.temp_air", "op": "between", "value": 24, "value2": 33},
            {"field": "sol.pH", "op": "between", "value": 5.5, "value2": 7.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Contexte général favorable à la production",
                "message": "Pluie, T et pH sol dans plages optimales. Conditions générales favorables. Anticiper récolte dans les délais."}],
            "risque": {"score": 0.20, "libelle": "Conditions générales favorables"},
            "recommandations": [{"priorite": 1, "type": "prevision",
                "titre": "Planifier logistique récolte selon estimation",
                "detail": "Prévoir main d'oeuvre, transport, stockage selon rendement attendu par culture."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.68, "plan_requis": "premium",
    },

]
