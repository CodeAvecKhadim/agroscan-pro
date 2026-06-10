"""Rules Engine V1 — Catégorie RENDEMENT (~40 règles)
Prédiction risque rendement : combinaisons sol + météo + stade.
"""

RENDEMENT_RULES = [

    # ═══════════════════════════════════════════════════════════════
    # GRANDES CULTURES
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "REN-RIZ-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Riz — Risque rendement élevé — Multiple stress",
        "cultures": ["Riz"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["tallage", "montaison", "epiaison"],
        "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"operator": "AND", "clauses": [
                {"field": "sol.pH", "op": "lte", "value": 5.5},
                {"field": "sol.azote", "op": "lte", "value": 80},
            ]},
            {"operator": "AND", "clauses": [
                {"field": "sol.humidite", "op": "lte", "value": 40},
                {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
            ]},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Risque rendement riz — actions correctrices urgentes",
                "message": "Combinaison de facteurs limitants : rendement potentiel réduit de 30-50%."}],
            "risque": {"score": 0.85, "libelle": "Rendement réduit riz"},
            "recommandations": [
                {"priorite": 1, "type": "fertilisation", "titre": "Corriger N + chaulage si pH<5.5"},
                {"priorite": 2, "type": "irrigation", "titre": "Irrigation d'urgence si stress hydrique"},
            ],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.82, "plan_requis": "premium",
    },
    {
        "code": "REN-RIZ-002", "categorie": "rendement", "sous_categorie": "optimisation",
        "nom": "Riz — Conditions optimales rendement maximum",
        "cultures": ["Riz"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["tallage", "montaison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "between", "value": 6.0, "value2": 7.0},
            {"field": "sol.azote", "op": "gte", "value": 100},
            {"field": "sol.phosphore", "op": "gte", "value": 15},
            {"field": "sol.humidite", "op": "gte", "value": 70},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Conditions optimales riz — Maintenir",
                "message": "Sol et eau en conditions idéales. Maintenir programme actuel."}],
            "risque": {"score": 0.20, "libelle": "Risque faible"},
            "recommandations": [{"priorite": 1, "type": "surveillance",
                "titre": "Maintenir surveillance maladies uniquement",
                "detail": "Sol OK. Focus sur Pyriculariose en tallage."}],
        },
        "gravite": "faible", "priorite": 3, "confiance": 0.85, "plan_requis": "premium",
    },
    {
        "code": "REN-MAI-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Maïs — Risque rendement — Carence N + stress eau floraison",
        "cultures": ["Maïs"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 80},
            {"field": "sol.humidite", "op": "lte", "value": 45},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Double stress maïs floraison — Risque récolte très faible",
                "message": "Carence N + stress hydrique simultanés à floraison : rendement <50% potentiel."}],
            "risque": {"score": 0.92, "libelle": "Rendement maïs très bas"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Irrigation immédiate 40-50mm", "urgence_jours": 1},
                {"priorite": 2, "type": "fertilisation", "titre": "Urée foliaire 2% si sol trop sec pour incorporer"},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "premium",
    },
    {
        "code": "REN-MIL-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Mil — Risque rendement — Striga + sol pauvre",
        "cultures": ["Mil"], "maladies": [], "ravageurs": [],
        "zones_applicables": ["bassin_arachidier", "senegal_oriental"],
        "stades_applicables": None,
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "striga"},
            {"field": "sol.phosphore", "op": "lte", "value": 8},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Mil — Striga + carence P = récolte quasi nulle",
                "message": "Striga + sol très pauvre : rendement <200 kg/ha possible. Intervention radicale."}],
            "risque": {"score": 0.92, "libelle": "Rendement quasi nul"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Arracher Striga AVANT floraison", "urgence_jours": 3},
                {"priorite": 2, "type": "fertilisation", "titre": "DAP en microdosage urgence", "produit": "DAP 18-46-0",
                    "dose": "1 cuillère/poquet"},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "REN-ARA-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Arachide — Risque rendement — Aflatoxine gousses",
        "cultures": ["Arachide"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification", "maturation"],
        "mois_applicables": [9, 10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 70},
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Arachide — Risque aflatoxine élevé",
                "message": "Chaud + humide à fructification : Aspergillus flavus produit aflatoxines. Valorisation commerciale à risque."}],
            "risque": {"score": 0.85, "libelle": "Aflatoxine rendement commercial"},
            "recommandations": [
                {"priorite": 1, "type": "recolte", "titre": "Récolter dès maturité sans délai", "urgence_jours": 7},
                {"priorite": 2, "type": "post_recolte", "titre": "Séchage rapide <12% humidité",
                    "detail": "Délai max 48h entre arrachage et séchage."},
            ],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "REN-SOR-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Sorgho — Risque rendement — Cécidomyie + pluie floraison",
        "cultures": ["Sorgho"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": [8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
            {"field": "obs.ravageurs", "op": "contains", "value": "cecidomyie"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Cécidomyie + humidité floraison sorgho",
                "message": "Combinaison Cécidomyie + conditions humides : pertes grains jusqu'à 100% sur panicule."}],
            "risque": {"score": 0.90, "libelle": "Rendement grains nul"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Malathion début floraison urgence",
                "produit": "Malathion 57EC", "dose": "1,5 L/ha", "urgence_jours": 2}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "REN-NIE-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Niébé — Risque rendement — Bruche + stockage",
        "cultures": ["Niébé"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 26},
            {"field": "meteo.humidite_rel", "op": "between", "value": 60, "value2": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Risque Bruche niébé — Perte stockage",
                "message": "Callosobruchus maculatus : 100% graines trouées en 3 mois si non traité."}],
            "risque": {"score": 0.90, "libelle": "Perte totale stockage"},
            "recommandations": [{"priorite": 1, "type": "post_recolte",
                "titre": "Traitement stockage Phosphine OU huile neem",
                "produit": "Phosphure d'aluminium", "dose": "3 comprimés/tonne", "urgence_jours": 5}],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # CULTURES MARAÎCHÈRES
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "REN-TOM-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Tomate — Risque rendement — BER + Mildiou + stress eau",
        "cultures": ["Tomate"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 60},
            {"field": "sol.humidite", "op": "lte", "value": 45},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Tomate — Triple stress fructification",
                "message": "Carence K + stress hydrique + humidité élevée = BER + Mildiou + chute fleurs simultanés."}],
            "risque": {"score": 0.92, "libelle": "Perte récolte tomate"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Irrigation régulière urgence", "urgence_jours": 1},
                {"priorite": 2, "type": "fertilisation", "titre": "K₂SO₄ + nitrate calcium foliaire"},
                {"priorite": 3, "type": "traitement_phyto", "titre": "Fongicide Mildiou", "urgence_jours": 2},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "premium",
    },
    {
        "code": "REN-OIG-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Oignon — Risque rendement — Bulbes petits conservation faible",
        "cultures": ["Oignon"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["bulbaison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 60},
            {"field": "sol.azote", "op": "lte", "value": 60},
            {"field": "sol.humidite", "op": "lte", "value": 45},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Oignon — Carence NPK + stress hydrique bulbaison",
                "message": "Bulbaison compromettante : calibre réduit + conservation <2 mois."}],
            "risque": {"score": 0.85, "libelle": "Faible rendement commercial oignon"},
            "recommandations": [
                {"priorite": 1, "type": "fertilisation", "titre": "K₂SO₄ + irrigation compensatoire urgence"},
                {"priorite": 2, "type": "irrigation", "titre": "Irrigation 4-5 mm/j maintenant", "urgence_jours": 1},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "premium",
    },
    {
        "code": "REN-PIM-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Piment — Risque rendement — Chaleur + Virus + Thrips",
        "cultures": ["Piment"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 35},
            {"field": "obs.ravageurs", "op": "contains", "value": "thrips"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Piment — Chaleur + Thrips = chute récolte",
                "message": "Chaleur >35°C + Thrips : avortement fleurs + transmission TSWV. Risque zéro récolte."}],
            "risque": {"score": 0.88, "libelle": "Perte récolte piment"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "Abamectine anti-thrips urgent",
                    "produit": "Abamectine 1.8EC", "dose": "0,5 L/ha", "urgence_jours": 2},
                {"priorite": 2, "type": "irrigation", "titre": "Irrigation matin tôt pour rafraîchir", "urgence_jours": 1},
            ],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.85, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════════
    # ARBRES FRUITIERS
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "REN-MAG-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Mangue — Risque récolte faible — Oïdium + pluies floraison",
        "cultures": ["Mangue"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": [2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 10},
            {"field": "obs.symptomes", "op": "contains", "value": "oidium"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Mangue — Oïdium + pluies floraison = récolte compromise",
                "message": "Oïdium actif + pluies à floraison : perte 50-80% inflorescences possible."}],
            "risque": {"score": 0.92, "libelle": "Perte récolte mangue"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Soufre + fongicide curatif floraison",
                "produit": "Soufre 80WP + Tebuconazole 25EC",
                "dose": "3 kg Soufre + 0,5 L Tebu/ha", "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "REN-ANA-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Anacarde — Risque rendement noix — Anthracnose + pluies",
        "cultures": ["Anacarde"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "nouaison"],
        "mois_applicables": [3, 4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 40},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Anthracnose anacarde + pluies = pertes noix",
                "message": "Pluies prolongées à nouaison : Colletotrichum cause chute noix jusqu'à 60%."}],
            "risque": {"score": 0.85, "libelle": "Perte noix cajou"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Carbendazime + cuivre anti-Anthracnose",
                "produit": "Carbendazime 50WP", "dose": "1 kg/ha", "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "REN-BAN-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Banane — Risque rendement — Sigatoka noire sévère",
        "cultures": ["Banane"], "maladies": [], "ravageurs": [],
        "zones_applicables": ["casamance"],
        "stades_applicables": None,
        "mois_applicables": [7, 8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "sigatoka"},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 50},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Sigatoka noire active + pluies = mûrissement prématuré",
                "message": "Sigatoka sévère : défoliation >50% = régimes mûrissent 4-6 semaines trop tôt."}],
            "risque": {"score": 0.92, "libelle": "Rendement commercial nul"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Programme fongicide intensif", "produit": "Propiconazole 25EC",
                "dose": "0,8 L/ha", "urgence_jours": 2}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "premium",
    },
    {
        "code": "REN-PAP-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Papaye — PRSV = perte totale production",
        "cultures": ["Papaye"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "ringspot"},
            {"field": "obs.symptomes", "op": "contains", "value": "mosaique_papaye"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "PRSV papaye — Perte production totale",
                "message": "PRSV actif : production nulle sur plants infectés. Contamination rapide voisins."}],
            "risque": {"score": 0.98, "libelle": "Perte totale production papaye"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale",
                    "titre": "Arracher TOUS les plants infectés",
                    "detail": "Quarantaine parcelle. Informer producteurs voisins.", "urgence_jours": 1},
                {"priorite": 2, "type": "planification",
                    "titre": "Replanter variétés tolérantes PRSV",
                    "detail": "Maradol rouge, Sunrise Solo si disponibles."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.95, "plan_requis": "gratuit",
    },
    {
        "code": "REN-MAN-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Manioc — CMD + qualité tubercules",
        "cultures": ["Manioc"], "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "mosaique_manioc"},
            {"field": "obs.ravageurs", "op": "contains", "value": "acarien_vert"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Manioc — CMD + Acarien vert = rendement nul",
                "message": "Mosaïque + Acarien vert simultanés : perte rendement 80-100%."}],
            "risque": {"score": 0.95, "libelle": "Perte rendement manioc critique"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Arracher plants malades", "urgence_jours": 1},
                {"priorite": 2, "type": "traitement_phyto", "titre": "Abamectine anti-acarien",
                    "produit": "Abamectine 1.8EC", "dose": "0,5 L/ha", "urgence_jours": 3},
                {"priorite": 3, "type": "mesure_culturale", "titre": "Replanter boutures certifiées CMD-résistantes"},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.92, "plan_requis": "gratuit",
    },
    {
        "code": "REN-SES-001", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Sésame — Risque rendement nul — égrenage avant récolte",
        "cultures": ["Sésame"], "maladies": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 30},
            {"field": "culture.stade", "op": "eq", "value": "maturation"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Sésame mûr + vent fort = RÉCOLTER IMMÉDIATEMENT",
                "message": "Vent >30km/h sur sésame mûr : ouverture capsules + égrenage = pertes 100% en 1 jour."}],
            "risque": {"score": 0.95, "libelle": "Perte totale égrenage"},
            "recommandations": [{"priorite": 1, "type": "recolte",
                "titre": "Couper tiges AUJOURD'HUI — urgence absolue",
                "detail": "Couper à la base. Lier en gerbes immédiatement. Battre dans 48h.", "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.95, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════════
    # RENDEMENT POSITIF — CONDITIONS OPTIMALES
    # ═══════════════════════════════════════════════════════════════
    {
        "code": "REN-GEN-001", "categorie": "rendement", "sous_categorie": "optimisation",
        "nom": "Conditions optimales sol — Rendement maximum possible",
        "cultures": ["Tomate", "Maïs", "Riz", "Oignon"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "between", "value": 6.0, "value2": 7.0},
            {"field": "sol.azote", "op": "gte", "value": 100},
            {"field": "sol.phosphore", "op": "gte", "value": 20},
            {"field": "sol.potassium", "op": "gte", "value": 100},
            {"field": "sol.matiere_organique", "op": "gte", "value": 2.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Excellentes conditions sol — Rendement optimal",
                "message": "Sol en conditions idéales. Facteur limitant = phytosanitaire uniquement."}],
            "risque": {"score": 0.15, "libelle": "Risque rendement faible"},
            "recommandations": [{"priorite": 1, "type": "surveillance",
                "titre": "Programme prophylactique maladies/ravageurs uniquement",
                "detail": "Sol non limitant. Concentrer efforts sur protection phytosanitaire."}],
        },
        "gravite": "faible", "priorite": 3, "confiance": 0.85, "plan_requis": "premium",
    },
    {
        "code": "REN-GEN-002", "categorie": "rendement", "sous_categorie": "risque_rendement",
        "nom": "Sol très dégradé — Rendement faible garanti",
        "cultures": ["Mil", "Sorgho", "Arachide", "Niébé", "Maïs"],
        "maladies": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.matiere_organique", "op": "lte", "value": 0.5},
            {"field": "sol.phosphore", "op": "lte", "value": 6},
            {"field": "sol.azote", "op": "lte", "value": 40},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sol très dégradé — Rendement <50% potentiel garanti",
                "message": "Triple carence P + N + MO <0.5% : même avec bonnes pluies, rendement sera faible."}],
            "risque": {"score": 0.88, "libelle": "Sol dégradé rendement bas"},
            "recommandations": [
                {"priorite": 1, "type": "amendement_organique",
                    "titre": "Compost 10t/ha avant plantation",
                    "produit": "Fumier composté", "dose": "10 t/ha"},
                {"priorite": 2, "type": "fertilisation",
                    "titre": "Programme NPK complet + microdosage",
                    "produit": "DAP 18-46-0 + Urée 46%",
                    "dose": "50 kg DAP + 40 kg Urée/ha fractionnés"},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.88, "plan_requis": "gratuit",
    },

]
