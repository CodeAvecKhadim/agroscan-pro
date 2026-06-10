"""Rules Engine V1 — Catégorie MÉTÉO (~60 règles)
Alertes climatiques transversales : chaleur extrême, vent, sécheresse, inondation.
"""

METEO_RULES = [

    # ═══════════════════════════════════════════════════════════════
    # CHALEUR EXTRÊME
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "MET-GEN-001", "categorie": "meteo", "sous_categorie": "chaleur",
        "nom": "Chaleur extrême >38°C — Cultures légumières",
        "cultures": ["Tomate", "Piment", "Aubergine", "Gombo", "Concombre"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [4, 5, 6, 10, 11],
        "conditions": {"field": "meteo.temp_air", "op": "gte", "value": 38},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Chaleur extrême >38°C — cultures légumières",
                "message": "T° >38°C : avortement fleurs, coup de soleil fruits, arrêt photosynthèse."}],
            "risque": {"score": 0.92, "libelle": "Stress thermique critique"},
            "recommandations": [
                {"priorite": 1, "type": "protection", "titre": "Ombrage 30-50% si disponible",
                    "detail": "Filet ombrage ou paillage blanc pour réfléchir chaleur."},
                {"priorite": 2, "type": "irrigation", "titre": "Irrigation matin avant 8h",
                    "dose": "15-20 mm", "urgence_jours": 1,
                    "detail": "Éviter irrigation en pleine chaleur — brûlures."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "MET-GEN-002", "categorie": "meteo", "sous_categorie": "chaleur",
        "nom": "Chaleur >35°C — Grandes cultures céréales",
        "cultures": ["Riz", "Maïs", "Mil", "Sorgho"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "epiaison"],
        "mois_applicables": None,
        "conditions": {"field": "meteo.temp_air", "op": "gte", "value": 35},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Chaleur >35°C à floraison céréales",
                "message": "T° >35°C à floraison : stérilité pollinique + dommages protéines grains."}],
            "risque": {"score": 0.85, "libelle": "Stress thermique floraison"},
            "recommandations": [{"priorite": 1, "type": "surveillance",
                "titre": "Surveiller taux de remplissage des épis/panicules",
                "detail": "Si >30% stérilité : noter pour choix variété saison prochaine."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "MET-GEN-003", "categorie": "meteo", "sous_categorie": "chaleur",
        "nom": "Vague chaleur prolongée >3j >36°C",
        "cultures": ["Tomate", "Piment", "Chou", "Oignon", "Pastèque"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 36},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "meteo.etp", "op": "gte", "value": 8},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Vague de chaleur prolongée",
                "message": "Chaleur + sécheresse + ETP élevée : stress hydro-thermique combiné. Pertes 30-60%."}],
            "risque": {"score": 0.90, "libelle": "Stress hydro-thermique"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Irrigations fréquentes matin/soir", "urgence_jours": 1},
                {"priorite": 2, "type": "protection", "titre": "Paillage mulch pour refroidir sol",
                    "detail": "Paille 10 cm réduit T° sol de 5-8°C."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # SÉCHERESSE
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "MET-SEC-001", "categorie": "meteo", "sous_categorie": "secheresse",
        "nom": "Sécheresse prolongée — Grandes cultures pluviales",
        "cultures": ["Mil", "Sorgho", "Arachide", "Niébé", "Maïs"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": ["bassin_arachidier", "senegal_oriental", "zone_sylvopastorale"],
        "stades_applicables": None,
        "mois_applicables": [7, 8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
            {"field": "meteo.pluie_24h", "op": "lte", "value": 2},
            {"field": "meteo.temp_air", "op": "gte", "value": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sécheresse prolongée — cultures pluviales",
                "message": ">10j sans pluie significative en hivernage : stress sévère. Surveiller flétrissement."}],
            "risque": {"score": 0.88, "libelle": "Sécheresse hivernage"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Sarclage pour réduire concurrence herbes",
                    "detail": "Sarclage conserve 20-30% humidité sol supplémentaire."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Paillage inter-rangs",
                    "detail": "Tiges de mil ou paille : réduit évaporation 30-40%."},
            ],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "MET-SEC-002", "categorie": "meteo", "sous_categorie": "secheresse",
        "nom": "Sécheresse saison sèche — Arbres fruitiers",
        "cultures": ["Mangue", "Anacarde", "Banane", "Papaye"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": None,
        "mois_applicables": [1, 2, 3, 4, 11, 12],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 2},
            {"field": "meteo.temp_air", "op": "gte", "value": 33},
            {"field": "meteo.etp", "op": "gte", "value": 7},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sécheresse saison sèche arbres fruitiers",
                "message": "ETP >7mm/j sans pluie : besoins en eau non couverts. Stress durable."}],
            "risque": {"score": 0.82, "libelle": "Stress hydrique arboriculture"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Irrigation localisée goutte-à-goutte",
                    "dose": "30-80 L/arbre/semaine selon âge"},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Paillage organique pied d'arbre",
                    "detail": "Couche 15 cm rayon 1 m autour du tronc."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "MET-SEC-003", "categorie": "meteo", "sous_categorie": "secheresse",
        "nom": "Début saison sèche — Alerte cultures sensibles",
        "cultures": ["Manioc", "Sésame", "Arachide"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": None,
        "mois_applicables": [10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 15},
            {"field": "meteo.pluie_24h", "op": "lte", "value": 3},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Début saison sèche — surveillance récolte",
                "message": "Transition vers saison sèche. Planifier récolte cultures arrivant à maturité."}],
            "risque": {"score": 0.65, "libelle": "Fin saison pluies"},
            "recommandations": [{"priorite": 1, "type": "planification",
                "titre": "Estimer date maturité + planifier récolte",
                "detail": "Arachide : arracher avant sol trop sec (risque gousses cassées)."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # PLUIES EXCESSIVES / INONDATIONS
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "MET-PLU-001", "categorie": "meteo", "sous_categorie": "inondation",
        "nom": "Pluies torrentielles >80mm/24h — Alerte inondation",
        "cultures": ["Tomate", "Piment", "Aubergine", "Papaye", "Sésame"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"field": "meteo.pluie_24h", "op": "gte", "value": 80},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Pluies torrentielles — risque inondation",
                "message": ">80mm/24h : asphyxie racinaire, lessivage engrais, maladies fongiques explosives."}],
            "risque": {"score": 0.92, "libelle": "Inondation + pathogènes sol"},
            "recommandations": [
                {"priorite": 1, "type": "drainage", "titre": "Drainage urgence avant 24h", "urgence_jours": 1},
                {"priorite": 2, "type": "traitement_phyto",
                    "titre": "Fongicide sol préventif après submersion",
                    "produit": "Métalaxyl 25WP", "dose": "2 kg/ha"},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "MET-PLU-002", "categorie": "meteo", "sous_categorie": "inondation",
        "nom": "Pluies abondantes 7j — Risque maladies fongiques généralisé",
        "cultures": ["Riz", "Maïs", "Tomate", "Piment", "Aubergine", "Chou"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 100},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 88},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pluies prolongées — Risque épidémie fongique",
                "message": "100mm+/7j + HR>88% : conditions épidémiques Mildiou, Phytophthora, Anthracnose."}],
            "risque": {"score": 0.88, "libelle": "Épidémie fongique multi-maladies"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Programme fongicide préventif multi-cibles",
                "produit": "Mancozèbe 80WP + Cymoxanil 4%", "dose": "2 kg/ha", "urgence_jours": 2}],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "MET-PLU-003", "categorie": "meteo", "sous_categorie": "pluie",
        "nom": "Pluie >30mm — Lessivage engrais récents",
        "cultures": ["Tomate", "Maïs", "Oignon", "Piment", "Chou"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"field": "meteo.pluie_24h", "op": "gte", "value": 30},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Lessivage engrais après forte pluie",
                "message": ">30mm : lixiviation N (nitrate) + perte 30-50% fertilisants récents."}],
            "risque": {"score": 0.72, "libelle": "Lessivage N"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Réapplication N fractionnée après drainage",
                "detail": "Attendre 3-5j drainage sol. Réapporter 30-50% dose N initiale."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # VENT
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "MET-VEN-001", "categorie": "meteo", "sous_categorie": "vent",
        "nom": "Vent fort >40 km/h — Maïs verse",
        "cultures": ["Maïs", "Sorgho", "Mil"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["montaison", "floraison", "remplissage_grains"],
        "mois_applicables": None,
        "conditions": {"field": "meteo.vent", "op": "gte", "value": 40},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Vent fort — Risque verse céréales",
                "message": "Vent >40km/h à montaison : verse possible si tiges faibles (excès azote)."}],
            "risque": {"score": 0.80, "libelle": "Verse céréales"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale",
                    "titre": "Inspecter après passage vent fort",
                    "detail": "Redresser plants versés dans 24h si encore verts."},
                {"priorite": 2, "type": "surveillance",
                    "titre": "Réduire N si tallage excessif pour la suite"},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "MET-VEN-002", "categorie": "meteo", "sous_categorie": "vent",
        "nom": "Vent fort >50 km/h — Arbres fruitiers bris branches",
        "cultures": ["Mangue", "Anacarde", "Banane", "Papaye"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"field": "meteo.vent", "op": "gte", "value": 50},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Vent violent — Bris branches fruitiers",
                "message": "Vent >50km/h : bris branches, chute fruits prématurés, blessures entrées maladies."}],
            "risque": {"score": 0.82, "libelle": "Bris mécaniques + infections"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_post_vent",
                    "titre": "Inspecter + protéger blessures",
                    "detail": "Couper bords nets + mastic cicatrisant sur toute coupe.", "urgence_jours": 1},
                {"priorite": 2, "type": "traitement_phyto",
                    "titre": "Cuivre sur blessures", "produit": "Bouillie bordelaise",
                    "dose": "1% badigeon"},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "MET-VEN-003", "categorie": "meteo", "sous_categorie": "vent",
        "nom": "Harmattan — Stress combiné vent sec froid",
        "cultures": ["Tomate", "Piment", "Oignon", "Chou", "Gombo"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": ["bassin_arachidier", "senegal_oriental", "zone_sylvopastorale"],
        "stades_applicables": None,
        "mois_applicables": [12, 1, 2],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 20},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 30},
            {"field": "meteo.temp_air", "op": "lte", "value": 22},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Harmattan — Dessèchement cultures",
                "message": "Vent sec froid <30% HR : dessèchement foliaire rapide + évaporation accrue."}],
            "risque": {"score": 0.72, "libelle": "Stress harmattan"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Augmenter fréquence irrigation",
                    "detail": "Arroser matin. ETP peut doubler avec harmattan."},
                {"priorite": 2, "type": "protection", "titre": "Brise-vent naturel ou filet",
                    "detail": "Rangées sorgho ou branchages en barrière vent dominant."},
            ],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # TEMPÉRATURES FROIDES — NUITS FRAÎCHES
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "MET-FRO-001", "categorie": "meteo", "sous_categorie": "froid",
        "nom": "Nuits fraîches <15°C — Cultures tropicales",
        "cultures": ["Tomate", "Piment", "Aubergine", "Papaye", "Concombre"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [12, 1, 2],
        "conditions": {"field": "meteo.temp_air", "op": "lte", "value": 15},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Nuits froides <15°C — cultures tropicales",
                "message": "T° <15°C la nuit : fructification ralentie, noircissement Papaye, stress Piment."}],
            "risque": {"score": 0.72, "libelle": "Stress froid cultures tropicales"},
            "recommandations": [
                {"priorite": 1, "type": "protection", "titre": "Voile de forçage si T° <12°C",
                    "detail": "Agrotextile P17 sur arceaux. Protège jusqu'à -3°C."},
                {"priorite": 2, "type": "fertilisation",
                    "titre": "Apport potassium + calcium pour renforcer parois cellulaires",
                    "produit": "Nitrate de calcium", "dose": "3 kg/ha foliaire"},
            ],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.72, "plan_requis": "gratuit",
    },
    {
        "code": "MET-FRO-002", "categorie": "meteo", "sous_categorie": "froid",
        "nom": "Nuits fraîches <12°C — Favorise Mildiou maraîchage",
        "cultures": ["Tomate", "Chou", "Oignon", "Piment"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": ["niayes"],
        "stades_applicables": None,
        "mois_applicables": [12, 1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "lte", "value": 12},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Nuit froide humide — Mildiou favori",
                "message": "Nuit <12°C + HR>85% : sporulation Phytophthora/Peronospora maximale."}],
            "risque": {"score": 0.85, "libelle": "Sporulation nocturne Mildiou"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Traitement anti-mildiou le matin",
                "produit": "Cymoxanil 4% + Mancozèbe 40%", "dose": "2 kg/ha", "urgence_jours": 2}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # HUMIDITÉ RELATIVE EXTRÊME
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "MET-HUM-001", "categorie": "meteo", "sous_categorie": "humidite",
        "nom": "Humidité très élevée >92% — Alerte maladies fongiques généralisée",
        "cultures": ["Riz", "Maïs", "Tomate", "Piment", "Chou", "Concombre", "Pastèque"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 92},
            {"field": "meteo.temp_air", "op": "between", "value": 18, "value2": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Humidité >92% — Alerte fongique généralisée",
                "message": "HR >92% prolongée : sporulation active pour tous pathogènes fongiques présents."}],
            "risque": {"score": 0.85, "libelle": "Conditions épidémiques"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Programme fongique préventif d'urgence",
                "produit": "Mancozèbe 80WP", "dose": "2,5 kg/ha", "urgence_jours": 2}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "MET-HUM-002", "categorie": "meteo", "sous_categorie": "humidite",
        "nom": "Humidité très basse <30% — Acariens + stress",
        "cultures": ["Tomate", "Piment", "Aubergine", "Manioc", "Papaye", "Pastèque"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [12, 1, 2, 3],
        "conditions": {"field": "meteo.humidite_rel", "op": "lte", "value": 30},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Air très sec <30% HR — Acariens + stress hydrique",
                "message": "HR <30% : explosions acariens rouges + dessèchement foliaire + ETP doublée."}],
            "risque": {"score": 0.85, "libelle": "Stress hydrique + acariens"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "Acaricide préventif",
                    "produit": "Abamectine 1.8EC", "dose": "0,5 L/ha", "urgence_jours": 5},
                {"priorite": 2, "type": "irrigation", "titre": "Augmenter fréquence irrigation 20-30%",
                    "urgence_jours": 2},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # ETP — ÉVAPOTRANSPIRATION
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "MET-ETP-001", "categorie": "meteo", "sous_categorie": "etp",
        "nom": "ETP très élevée >8mm/j — Stress toutes cultures",
        "cultures": ["Tomate", "Maïs", "Oignon", "Riz", "Piment", "Chou"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.etp", "op": "gte", "value": 8},
            {"field": "meteo.pluie_24h", "op": "lte", "value": 5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "ETP très élevée >8mm/j",
                "message": "Demande évaporatoire >8mm/j sans pluie : déficit hydrique 1-2 jours max."}],
            "risque": {"score": 0.85, "libelle": "Déficit hydrique rapide"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation compensatoire 0.8 × ETP",
                "dose": "6-8 mm/j", "urgence_jours": 1,
                "detail": "Coeff. cultural 0.8-1.1 selon stade."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "premium",
    },
    {
        "code": "MET-ETP-002", "categorie": "meteo", "sous_categorie": "etp",
        "nom": "ETP modérée + sol sec — Alerte précautionnelle",
        "cultures": ["Mil", "Sorgho", "Niébé", "Arachide", "Sésame"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "remplissage_grains"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.etp", "op": "between", "value": 5, "value2": 8},
            {"field": "sol.humidite", "op": "lte", "value": 35},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "ETP + sol sec — Stress imminent céréales",
                "message": "Bilan hydrique négatif 3-5 jours. Surveiller signes flétrissement."}],
            "risque": {"score": 0.75, "libelle": "Stress hydrique imminent"},
            "recommandations": [{"priorite": 1, "type": "surveillance",
                "titre": "Surveiller flétrissement matinal", "detail": "Si flétrissement à 8h : intervention immédiate."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # DÉBUT HIVERNAGE
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "MET-HIV-001", "categorie": "meteo", "sous_categorie": "saison",
        "nom": "Premières pluies hivernage — Alerte Pythium et fonte semis",
        "cultures": ["Mil", "Sorgho", "Maïs", "Niébé", "Arachide", "Sésame"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["semis", "levee"],
        "mois_applicables": [6, 7],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 20},
            {"field": "sol.humidite", "op": "gte", "value": 75},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Premières pluies — Risque fonte semis",
                "message": "Premières pluies intenses : sol froid puis chaud + humide = Pythium/Rhizoctonia actifs."}],
            "risque": {"score": 0.72, "libelle": "Fonte semis début hivernage"},
            "recommandations": [{"priorite": 1, "type": "traitement_semences",
                "titre": "Traitement semences préventif obligatoire",
                "produit": "Thirame 80WP + Métalaxyl 35FS", "dose": "3 g Thirame + 2 g Métalaxyl / kg semences"}],
        },
        "gravite": "moyenne", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

]
