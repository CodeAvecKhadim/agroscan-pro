"""
Rules Engine V1 — Catégorie MÉTÉO — Additions V2
+42 règles : alertes climatiques, Harmattan, vents forts, événements extrêmes.
"""

METEO_RULES_V2 = [

    # ═══════════════════════════════════════════════════════════
    # VAGUE DE CHALEUR — cultures sensibles
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-CAL-002",
        "categorie": "meteo", "sous_categorie": "vague_chaleur",
        "nom": "Vague chaleur extrême >38°C — tomate piment aubergine",
        "cultures": ["Tomate", "Piment", "Aubergine"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": [3, 4, 5, 11, 12],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 38},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Vague chaleur > 38°C solanées",
                "message": ">38°C + air sec : pollen stérile, avortement floral massif tomate/piment/aubergine. Ombrage d'urgence."}],
            "risque": {"score": 0.92, "libelle": "Stérilité pollen chaleur"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Ombrage filet 30% solanées",
                    "detail": "Filet ombrage 30-50%. Irrigation 2x/jour matin + soir. Arrêter fertilisation N."},
                {"priorite": 2, "type": "irrigation", "titre": "Irrigation fraîche solanées chaleur",
                    "detail": "Eau fraîche matin + soir. Évite stress thermique racinaire."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "MET-CAL-003",
        "categorie": "meteo", "sous_categorie": "vague_chaleur",
        "nom": "Chaleur >40°C — Riz stérilité pollen",
        "cultures": ["Riz"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 35},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 50},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Chaleur floraison riz critique",
                "message": ">35°C à floraison riz = spikelet stérilité. 1°C de trop peut faire -10% rendement."}],
            "risque": {"score": 0.88, "libelle": "Spikelet stérilité"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation fraîche floraison riz",
                "detail": "Maintenir lame d'eau 5-10 cm pour refroidir canopée. Irrigation nocturne si possible."}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "MET-CAL-004",
        "categorie": "meteo", "sous_categorie": "vague_chaleur",
        "nom": "Chaleur >36°C — Maïs floraison soie",
        "cultures": ["Maïs"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 36},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 40},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Chaleur + sécheresse floraison maïs",
                "message": "T > 36°C + air sec = pollen maïs déshydraté en 1-2h. Soie non fécondée = épis incomplets."}],
            "risque": {"score": 0.90, "libelle": "Pollen stérile maïs"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation urgence floraison maïs",
                "detail": "Irrigation immédiate. Arrosage léger matin sur feuilles pour augmenter HR locale si possible.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "MET-CAL-005",
        "categorie": "meteo", "sous_categorie": "vague_chaleur",
        "nom": "Chaleur nuit >25°C — Respiration nocturne cultures céréales",
        "cultures": ["Riz", "Maïs", "Sorgho", "Mil"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [3, 4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_min", "op": "gte", "value": 25},
            {"field": "meteo.temp_air", "op": "gte", "value": 35},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Nuits chaudes — respiration augmentée céréales",
                "message": "Nuits > 25°C = respiration nocturne intense = pertes glucides accumulés. -5 à -15% rendement potentiel."}],
            "risque": {"score": 0.72, "libelle": "Perte rendement nuits chaudes"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Adapter densité semis saison chaude",
                "detail": "Réduire densité 10-15% en saison chaude pour diminuer compétition + température canopée."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # HARMATTAN — vent chaud sec
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-HAR-001",
        "categorie": "meteo", "sous_categorie": "harmattan",
        "nom": "Harmattan intense — Toutes cultures",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 40},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 20},
            {"field": "meteo.temp_air", "op": "gte", "value": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Harmattan intense — ETP extrême",
                "message": "Vent > 40 km/h + HR < 20% + T > 32°C = ETP potentielle >10 mm/j. Toutes cultures en stress sévère."}],
            "risque": {"score": 0.92, "libelle": "ETP extrême Harmattan"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Doubler arrosages Harmattan",
                    "detail": "Irrigation 2x/jour minimum. Mulch sol 10 cm. Abri si jeunes plants."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Brise-vent d'urgence",
                    "detail": "Écrans vent temporaires (bâches, paillage vertical) côté vent dominant."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "MET-HAR-002",
        "categorie": "meteo", "sous_categorie": "harmattan",
        "nom": "Harmattan modéré — Cultures maraîchères sensibles",
        "cultures": ["Tomate", "Oignon", "Chou", "Laitue", "Concombre"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 25},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Harmattan maraîchers — déshydratation feuilles",
                "message": "Vent chaud sec = nécrose bords feuilles, fruit déclassé. Filet brise-vent et arrosage plus fréquent."}],
            "risque": {"score": 0.78, "libelle": "Déshydratation foliaire"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation fractionnée Harmattan maraîchers",
                "detail": "3 arrosages/jour si possible. Brise-vent latéral 1,5 m hauteur."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "MET-HAR-003",
        "categorie": "meteo", "sous_categorie": "harmattan",
        "nom": "Harmattan — Propagation maladies cryptogamiques ralentie",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "lte", "value": 25},
            {"field": "meteo.vent", "op": "gte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Harmattan inhibe champignons foliaires",
                "message": "Air sec < 25% HR = mildiou/botrytis stoppés. Risque fongique faible. Mais vecteurs acariens actifs."}],
            "risque": {"score": 0.30, "libelle": "Risque fongique réduit"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Réduire fongicides, surveiller acariens",
                "detail": "Pause fongicides possible. Augmenter surveillance acariens (araignées rouges actives par temps sec)."}],
        },
        "gravite": "faible", "priorite": 3, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PLUIES EXCESSIVES — maladies fongiques
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-PLU-001",
        "categorie": "meteo", "sous_categorie": "pluies_excessives",
        "nom": "Pluies prolongées >100mm/7j — Maladies fongiques généralisées",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [6, 7, 8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 100},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Pluies intenses > 100mm/semaine",
                "message": "> 100 mm/7j + HR > 80% = explosion Phytophthora, Alternaria, Botrytis, Cercospora. Traitement préventif urgent."}],
            "risque": {"score": 0.90, "libelle": "Explosion maladies fongiques"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide préventif après pluies intenses",
                "detail": "Mancozèbe ou cuivre après pluie. Répéter tous les 7 jours si pluies continuent.",
                "urgence_jours": 2}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "MET-PLU-002",
        "categorie": "meteo", "sous_categorie": "pluies_excessives",
        "nom": "Pluie intense >50mm/24h — Risque lessivage engrais",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 50},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pluie > 50mm/24h — lessivage N",
                "message": "> 50 mm/24h = lessivage nitrates, ruissellement engrais. Ré-apporter N/K dans 7-10 jours."}],
            "risque": {"score": 0.78, "libelle": "Lessivage N-K"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Ré-apport N après forte pluie",
                "detail": "Attendre 5-7 jours (sol ressuyé). Urée 30-40 kg/ha ou nitrate ammonium calcique."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "MET-PLU-003",
        "categorie": "meteo", "sous_categorie": "pluies_excessives",
        "nom": "Pluie modérée après sécheresse — Réhumidification rapide",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 25},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Réhumidification après sécheresse",
                "message": "Humidité après sec = activation champignons dormants + maladies bactériennes. Surveiller 5-7 jours."}],
            "risque": {"score": 0.65, "libelle": "Activation pathogènes sol"},
            "recommandations": [{"priorite": 1, "type": "surveillance",
                "titre": "Surveillance accrue après retour pluies",
                "detail": "Inspecter bases tiges, collets, feuilles basses dans les 5 jours. BER tomates/pastèques."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.68, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # TEMPÉRATURES BASSES — risques gel/fraîcheur
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-GEL-001",
        "categorie": "meteo", "sous_categorie": "froid",
        "nom": "Températures basses <15°C — Cultures tropicales",
        "cultures": ["Tomate", "Aubergine", "Piment", "Concombre", "Papaye"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [12, 1, 2],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_min", "op": "lte", "value": 15},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Froid nocturne < 15°C solanées/cucurbitacées",
                "message": "T < 15°C nuit = ralentissement drastique. T < 10°C = dommages irréversibles solanées/papaye."}],
            "risque": {"score": 0.78, "libelle": "Stress froid tropical"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Protection anti-froid",
                    "detail": "Voiles de forçage nuit. Paillage pour conserver chaleur sol. Reporter transplantation."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "MET-GEL-002",
        "categorie": "meteo", "sous_categorie": "froid",
        "nom": "Nuits froides <12°C — Riz blocage photosynthèse",
        "cultures": ["Riz"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "tallage"],
        "mois_applicables": [12, 1, 2],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_min", "op": "lte", "value": 12},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Froid nocturne < 12°C — Riz",
                "message": "T < 12°C = blocage photosynthèse + tallage réduit. Cycle se rallonge 10-15 jours."}],
            "risque": {"score": 0.72, "libelle": "Ralentissement riz froid"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Augmenter lame eau riz froid",
                "detail": "Augmenter lame eau 10-15 cm (tampon thermique). Proscrire urée par temps froid."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # BROUILLARD / HUMIDITÉ NOCTURNE
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-BRO-001",
        "categorie": "meteo", "sous_categorie": "brouillard_humidite",
        "nom": "HR >90% nuit prolongée — Botrytis mildiou",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 90},
            {"field": "meteo.pluie_24h", "op": "gte", "value": 5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "HR > 90% — Botrytis/Mildiou imminent",
                "message": "HR > 90% + pluie légère = conditions optimales Botrytis cinerea + Phytophthora infestans."}],
            "risque": {"score": 0.82, "libelle": "Botrytis/Mildiou actif"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide préventif HR élevée",
                "detail": "Iprodione (Botrytis) ou Mancozèbe/Métalaxyl (Mildiou). Appliquer fenêtre sèche.",
                "urgence_jours": 2}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "MET-BRO-002",
        "categorie": "meteo", "sous_categorie": "brouillard_humidite",
        "nom": "Rosée matinale prolongée — Cercospora Alternaria",
        "cultures": ["Arachide", "Maïs", "Tomate", "Oignon"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "floraison"],
        "mois_applicables": [7, 8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
            {"field": "meteo.temp_air", "op": "between", "value": 22, "value2": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Rosée prolongée + chaleur — Cercospora",
                "message": "HR > 85% + T 22-30°C = rosée matinale = Cercospora arachidicola + Alternaria alternata actifs."}],
            "risque": {"score": 0.78, "libelle": "Cercospora/Alternaria"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide Cercospora arachide",
                "detail": "Chlorothalonil 1.5 kg/ha ou Tebuconazole 0.5 L/ha. Appliquer tôt matin ou soir sans vent.",
                "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # GRÊLE / VENT FORT
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-VEN-001",
        "categorie": "meteo", "sous_categorie": "vent_fort",
        "nom": "Vent très fort >60km/h — Verse maïs sorgho",
        "cultures": ["Maïs", "Sorgho"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["montaison", "floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Vent > 60km/h — Verse imminente maïs/sorgho",
                "message": "Vent > 60 km/h à montaison/floraison = verse (lodging). Maïs > 1.5m particulièrement vulnérable."}],
            "risque": {"score": 0.88, "libelle": "Verse vent fort"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Buttage préventif anti-verse",
                    "detail": "Butter plantes si pas encore fait. Éviter excès N (tiges fragiles)."},
                {"priorite": 2, "type": "surveillance", "titre": "Inspecter après tempête",
                    "detail": "Relever plantes versées dans les 48h. Plante versée avant floraison = récupérable."},
            ],
        },
        "gravite": "critique", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "MET-VEN-002",
        "categorie": "meteo", "sous_categorie": "vent_fort",
        "nom": "Vent fort >50km/h — Banane verse",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 50},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Vent > 50km/h — Verse bananier",
                "message": "Bananier très vulnérable > 50 km/h. Sol détrempé + vent = verse totale de la parcelle."}],
            "risque": {"score": 0.90, "libelle": "Verse bananier"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Tuteurage bananier",
                    "detail": "Tuteurs bambou si plants < 1.5 m. Enlever régimes exposés au vent si maturité proche."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Drainage avant saison cyclones",
                    "detail": "Sol bien drainé = tenue mécanique meilleure."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "MET-VEN-003",
        "categorie": "meteo", "sous_categorie": "vent_fort",
        "nom": "Vent chaud + sec — Propagation bactéries foliaires",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 35},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Vent chaud-sec = propagation bactéries",
                "message": "Vent > 30km/h + air sec : propagation bactéries sur blessures + micro-déchirures foliaires. Surveiller."}],
            "risque": {"score": 0.60, "libelle": "Bactérioses vent"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Cuivre préventif après vent fort",
                "detail": "Sulfate cuivre 1% après passage vent fort pour couvrir blessures mécaniques."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.62, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # ALERTES SAISON — début / fin hivernage
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-SAI-001",
        "categorie": "meteo", "sous_categorie": "saison",
        "nom": "Début hivernage — Premières pluies (juin-juillet)",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [6, 7],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 30},
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Début hivernage — fenêtre de semis",
                "message": "Premières pluies significatives. Confirmer hivernage installé avant semis définitif."}],
            "risque": {"score": 0.50, "libelle": "Risque faux départ hivernage"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Attendre 2e pluie significative pour semer",
                "detail": "Stratégie : attendre 2 pluies ≥ 20mm à 7j intervalle avant semis mil/sorgho/maïs."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.70, "plan_requis": "gratuit",
    },
    {
        "code": "MET-SAI-002",
        "categorie": "meteo", "sous_categorie": "saison",
        "nom": "Fin hivernage précoce — Sécheresse terminaison culture",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "meteo.etp", "op": "gte", "value": 6.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Fin hivernage précoce probable",
                "message": "Pluies en baisse rapide sept-oct = fin hivernage. Cultures tardives en danger si non matures."}],
            "risque": {"score": 0.80, "libelle": "Cultures non matures fin hivernage"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Évaluer maturité cultures tardives",
                    "detail": "Estimer jours avant maturité. Si > 30 jours = irrigation complémentaire nécessaire."},
                {"priorite": 2, "type": "irrigation", "titre": "Irrigation appoint fin hivernage",
                    "detail": "10-15 mm/semaine pour sécuriser maturation si cultures pas matures."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "MET-SAI-003",
        "categorie": "meteo", "sous_categorie": "saison",
        "nom": "Pluies hors saison — Maladies inattendues",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [1, 2, 11, 12],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 15},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Pluie hors saison — Risque maladies inattendu",
                "message": "Pluie en saison sèche = cultures non préparées. Maladies fongiques sur cultures sensibles."}],
            "risque": {"score": 0.65, "libelle": "Maladies hors saison"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide préventif pluie hors saison",
                "detail": "Surveillance accrue 5 jours après pluie hors saison. Fongicide si cultures sensibles."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.65, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # INDICES COMBINÉS — ETP + Pluie + Temp
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-IDX-001",
        "categorie": "meteo", "sous_categorie": "indice_combine",
        "nom": "Indice FOEW favorable mildiou (T15-20 + HR>80)",
        "cultures": ["Tomate", "Pomme de terre", "Oignon"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 15, "value2": 22},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Conditions FOEW favorables au mildiou",
                "message": "T 15-22°C + HR > 80% + pluies = fenêtre Phytophtora infestans optimale. Traiter préventivement."}],
            "risque": {"score": 0.85, "libelle": "Mildiou FOEW optimal"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide systémique mildiou",
                "detail": "Métalaxyl-M + Mancozèbe. Répéter 7 jours. Si déjà présent : Dimethomorph.",
                "urgence_jours": 2}],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "MET-IDX-002",
        "categorie": "meteo", "sous_categorie": "indice_combine",
        "nom": "Indice favorable Stemphylium oignon (T20-26 + humidité)",
        "cultures": ["Oignon"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 20, "value2": 26},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 78},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 15},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Conditions Stemphylium/Botrytis oignon",
                "message": "T 20-26 + HR > 78% + pluies = Stemphylium vesicarium + Botrytis allii favorables."}],
            "risque": {"score": 0.80, "libelle": "Stemphylium/Botrytis oignon"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide oignon temps humide",
                "detail": "Chlorothalonil + Iprodione. Ne pas retarder avec symptômes. 7-10 jours intervalle.",
                "urgence_jours": 2}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "MET-IDX-003",
        "categorie": "meteo", "sous_categorie": "indice_combine",
        "nom": "Indice Cercospora arachide (T25-30 + humidité nuit)",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "floraison"],
        "mois_applicables": [8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 30},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Conditions optimales Cercospora arachide",
                "message": "T 25-30°C + HR > 80% = conditions parfaites Cercospora arachidicola (cerco précoce)."}],
            "risque": {"score": 0.82, "libelle": "Cercospora arachidicola actif"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Programme fongicide Cercospora",
                "detail": "Chlorothalonil 1.5 kg/ha à 30 JAL si non fait, puis tous les 14 jours."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "MET-IDX-004",
        "categorie": "meteo", "sous_categorie": "indice_combine",
        "nom": "Conditions explosion pyriculariose riz (T20-28 + HR>90)",
        "cultures": ["Riz"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["tallage", "montaison", "floraison"],
        "mois_applicables": [7, 8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 20, "value2": 28},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 90},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Pyriculariose riz — conditions explosives",
                "message": "T 20-28°C + HR > 90% + pluies = Magnaporthe oryzae (Blast) en pleine activité. Traitement urgent."}],
            "risque": {"score": 0.90, "libelle": "Blast riz conditions optimales"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide anti-Blast riz urgence",
                "detail": "Tricyclazole 0.6 kg/ha ou Isoprothiolane 1.5 L/ha. Épiaison: traiter absolument.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # ALERTES SPÉCIALES PAR CULTURE
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-SPE-001",
        "categorie": "meteo", "sous_categorie": "special_culture",
        "nom": "Brume sèche + froid — Anacarde avortement floral",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": [1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "lte", "value": 25},
            {"field": "meteo.temp_min", "op": "lte", "value": 18},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Brume sèche + froid anacarde",
                "message": "Harmattan froid (<18°C nuit + < 25% HR) à floraison anacarde = anthracnose + avortement. Surveillance."}],
            "risque": {"score": 0.75, "libelle": "Anthracnose + avortement floral"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Fongicide anthracnose anacarde",
                "detail": "Mancozèbe 2 kg/ha à floraison. Répéter à 10 jours si Harmattan persiste."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },
    {
        "code": "MET-SPE-002",
        "categorie": "meteo", "sous_categorie": "special_culture",
        "nom": "Pluie floraison mangue — Anthracnose",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": [1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 10},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Pluie floraison mangue — Anthracnose",
                "message": "Pluie + humidité à floraison mangue = Colletotrichum gloeosporioides. Perte 50-100% récolte."}],
            "risque": {"score": 0.90, "libelle": "Anthracnose mangue floraison"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Traitement fongicide mangue floraison",
                "detail": "Mancozèbe + Myclobutanil à l'ouverture des boutons. Répéter 7 jours si pluies continuent.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "MET-SPE-003",
        "categorie": "meteo", "sous_categorie": "special_culture",
        "nom": "Forte pluie récolte manioc — Report obligatoire",
        "cultures": ["Manioc"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 30},
            {"field": "sol.humidite", "op": "gte", "value": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Sol détrempé — Reporter récolte manioc",
                "message": "Sol saturé = racines cassent à l'arrachage. Attendre ressuyage 3-5 jours. Qualité amidon non affectée."}],
            "risque": {"score": 0.55, "libelle": "Dommages mécaniques récolte"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Attendre ressuyage sol 3-5 jours",
                "detail": "Reporter récolte. Tracteur inutilisable sol gorgé. Perte qualité = non."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.68, "plan_requis": "gratuit",
    },
    {
        "code": "MET-SPE-004",
        "categorie": "meteo", "sous_categorie": "special_culture",
        "nom": "Pluie récolte arachide — Report séchage",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["maturation"],
        "mois_applicables": [10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 15},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 75},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pluie récolte arachide — Aflatoxines",
                "message": "Humidité à récolte + stockage humide = Aspergillus flavus → aflatoxines. Problème santé public."}],
            "risque": {"score": 0.82, "libelle": "Aflatoxines récolte humide"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Séchage arachide immédiat",
                    "detail": "Sécher gousses < 8% humidité avant stockage. Séchage solaire 3-5 jours min.",
                    "urgence_jours": 2},
            ],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # VARIABILITÉ INTERANNUELLE
    # ═══════════════════════════════════════════════════════════
    {
        "code": "MET-VAR-001",
        "categorie": "meteo", "sous_categorie": "variabilite",
        "nom": "El Niño annoncé — Déficit pluies anticipé",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [4, 5, 6],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "meteo.temp_air", "op": "gte", "value": 32},
            {"field": "meteo.etp", "op": "gte", "value": 7.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Indicateurs saison sèche prolongée",
                "message": "Indicateurs début saison défavorables. Préférer variétés précoces. Prévoir irrigation."}],
            "risque": {"score": 0.72, "libelle": "Saison déficitaire anticipée"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Adapter choix variétés",
                    "detail": "Variétés précoces 75-80 jours (mil, sorgho). Densité réduite. Mulch préventif."},
                {"priorite": 2, "type": "irrigation", "titre": "Sécuriser source eau saison",
                    "detail": "Inventorier disponibilité eau. Priorité aux cultures à haute valeur économique."},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.68, "plan_requis": "premium",
    },

]
