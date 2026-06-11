"""
Rules Engine V1 — Catégorie IRRIGATION — Additions V2
+40 règles : complétion 20 cultures, ETP, stress hydrique.
"""

IRRIGATION_RULES_V2 = [

    # ═══════════════════════════════════════════════════════════
    # ARACHIDE  (IRR-ARA-002..003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-ARA-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique arachide — Floraison gynophore",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 15},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "meteo.etp", "op": "gte", "value": 5.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Stress hydrique critique arachide floraison",
                "message": "Gynophore en formation = phase la plus sensible. Manque d'eau = gousses vides. Irriguer immédiatement."}],
            "risque": {"score": 0.92, "libelle": "Stress gynophore"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation urgence gynophore arachide",
                "detail": "Apporter 30-40 mm. Maintenir humidité sol à 60-80% capacité de rétention.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-ARA-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Excès eau arachide — Fructification sol saturé",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification", "maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 85},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Excès eau arachide fructification",
                "message": "Sol saturé pendant fructification = pourriture gousses + aflatoxines. Drainer."}],
            "risque": {"score": 0.80, "libelle": "Pourriture gousses"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainage urgence arachide",
                "detail": "Creuser rigoles de drainage. Arrêter toute irrigation. Prévoir récolte précoce si nécessaire."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # SORGHO  (IRR-SOR-002..003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-SOR-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique sorgho — Epiaison floraison critique",
        "cultures": ["Sorgho"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["epiaison", "floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
            {"field": "meteo.temp_air", "op": "gte", "value": 33},
            {"field": "meteo.etp", "op": "gte", "value": 6.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Stress hydrique sorgho épiaison",
                "message": "Épiaison-floraison = fenêtre critique 10 jours. Stérilité du pollen si stress hydrique. Irriguer d'urgence."}],
            "risque": {"score": 0.88, "libelle": "Stérilité pollen"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation prioritaire sorgho épiaison",
                "detail": "20-25 mm immédiatement. Maintenir humidité sol >50% jusqu'à formation grains.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-SOR-003",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Besoin eau sorgho — Tallage formation tiges",
        "cultures": ["Sorgho"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["tallage", "montaison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 20},
            {"field": "meteo.etp", "op": "gte", "value": 5.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Déficit hydrique sorgho tallage",
                "message": "Tallage insuffisant si manque d'eau : moins de tiges → moins d'épis → rendement réduit."}],
            "risque": {"score": 0.72, "libelle": "Déficit tallage"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation sorgho tallage",
                "detail": "15-20 mm tous les 8-10 jours si pas de pluie."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # NIÉBÉ  (IRR-NIE-002..003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-NIE-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique niébé — Floraison nouaison",
        "cultures": ["Niébé"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
            {"field": "meteo.temp_air", "op": "gte", "value": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Stress hydrique niébé floraison",
                "message": "Manque d'eau à floraison : abscission florale. Perte rendement jusqu'à 80%. Irriguer si disponible."}],
            "risque": {"score": 0.88, "libelle": "Avortement floral"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation niébé floraison",
                "detail": "15-20 mm si possible. Niébé tolérant mais la floraison reste le point critique.",
                "urgence_jours": 2}],
        },
        "gravite": "critique", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-NIE-003",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Besoin eau niébé — Phase levée sèche",
        "cultures": ["Niébé"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "sol.humidite", "op": "lte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sol sec levée niébé",
                "message": "Sol trop sec à levée : germination irrégulière, manque à planter."}],
            "risque": {"score": 0.72, "libelle": "Levée irrégulière"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation légère levée niébé",
                "detail": "10 mm léger pour humidifier les 10 premiers cm. Ne pas inonder."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # SÉSAME  (IRR-SES-002..003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-SES-002",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Excès eau sésame — Engorgement mortel",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 80},
            {"field": "meteo.pluie_24h", "op": "gte", "value": 40},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Engorgement mortel sésame",
                "message": "Sésame = culture la plus sensible à l'eau stagnante. 24h engorgé = Fusarium + Phytophtora fatal."}],
            "risque": {"score": 0.92, "libelle": "Engorgement mortel"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainage urgence sésame",
                "detail": "Drainer immédiatement. Éviter toute irrigation supplémentaire. Billonner si non fait.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.92, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-SES-003",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Besoin eau sésame — Floraison capsules",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 15},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Déficit eau sésame floraison",
                "message": "Floraison = période de besoin modéré. Sec prolongé = avortement capsules."}],
            "risque": {"score": 0.70, "libelle": "Avortement capsules"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation légère sésame floraison",
                "detail": "10-15 mm tous les 10 jours si pas de pluie. Ne pas mouiller le collet."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MANIOC  (IRR-MAN-002..003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-MAN-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique manioc — Saison sèche prolongée",
        "cultures": ["Manioc"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "tuberisation"],
        "mois_applicables": [11, 12, 1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "meteo.temp_air", "op": "gte", "value": 33},
            {"field": "meteo.etp", "op": "gte", "value": 6.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Stress hydrique manioc saison sèche",
                "message": "Manioc tolérant mais prolonged drought > 3 mois = défoliation défensive + perte rendement 30%."}],
            "risque": {"score": 0.68, "libelle": "Stress saison sèche"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation d'appoint manioc",
                "detail": "20 mm/15 jours en saison sèche si possible. Couvre-sol mulch feuilles mortes."}],
        },
        "gravite": "elevee", "priorite": 6, "confiance": 0.68, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-MAN-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Engorgement manioc — Pourriture racinaire saison pluies",
        "cultures": ["Manioc"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [7, 8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 88},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 70},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Engorgement manioc saison pluies",
                "message": "Sol saturé > 2 semaines = Phytophtora drechsleri sur racines. Billonner et drainer."}],
            "risque": {"score": 0.75, "libelle": "Pourriture racinaire"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Billonnage manioc en sol plat",
                "detail": "Créer billons 30 cm hauteur si sol plat. Décollage des eaux de surface."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PIMENT  (IRR-PIM-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-PIM-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique piment — Floraison avortement",
        "cultures": ["Piment"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
            {"field": "meteo.temp_air", "op": "gte", "value": 33},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Stress hydrique piment floraison",
                "message": "Chaleur + sécheresse : avortement fleurs + BER fruits. Irriguer immédiatement."}],
            "risque": {"score": 0.88, "libelle": "Avortement fleurs + BER"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation régulière piment",
                "detail": "Goutte-à-goutte 15 mm/semaine. Éviter stress hydrique et réhumidification brutale (BER).",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-PIM-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Engorgement piment — Phytophtora collet",
        "cultures": ["Piment"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 82},
            {"field": "meteo.pluie_24h", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Excès eau piment",
                "message": "Sol saturé = Phytophthora capsici mortel sur collet piment. Drainage urgent."}],
            "risque": {"score": 0.82, "libelle": "Phytophtora capsici"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainage urgence piment",
                "detail": "Drainer. Métalaxyl préventif sur sol si terrain concerné.",
                "urgence_jours": 1}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # GOMBO  (IRR-GOM-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-GOM-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique gombo — ETP élevée",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.etp", "op": "gte", "value": 6.5},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "ETP élevée + sec = stress gombo",
                "message": "ETP > 6.5 mm/j avec peu de pluie : gombo stresse, capsules durcissent prématurément."}],
            "risque": {"score": 0.75, "libelle": "Stress ETP élevée"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation gombo selon ETP",
                "detail": "Apporter 70% ETP = 4-5 mm/j. Fréquence tous les 3 jours en chaleur."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-GOM-003",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Programme irrigation gombo — Cycle complet",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 15},
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Apport eau régulier gombo requis",
                "message": "Gombo à haute production nécessite 400-600 mm. Irrigation complémentaire requise."}],
            "risque": {"score": 0.65, "libelle": "Besoin eau production"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Programme irrigation gombo",
                "detail": "Levée: 1x/semaine. Végétation: 2x/semaine 15 mm. Floraison: 3x/semaine 10-15 mm."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.68, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # AUBERGINE  (IRR-AUB-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-AUB-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique aubergine — Fructification",
        "cultures": ["Aubergine"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 12},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Déficit eau aubergine fructification",
                "message": "Stress à fructification = fruits petits, déformés, calibre commercial insuffisant."}],
            "risque": {"score": 0.78, "libelle": "Qualité fruits réduite"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation régulière aubergine",
                "detail": "15-20 mm tous les 5-7 jours. Mulch sol recommandé pour réduire évaporation."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-AUB-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Excès eau aubergine — Verticilliose phytophtora",
        "cultures": ["Aubergine"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 85},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 55},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Excès eau aubergine",
                "message": "Sol détrempé = Verticillium dahliae + Phytophtora nicotianae. Flétrissement vasculaire."}],
            "risque": {"score": 0.78, "libelle": "Maladies sol humide"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainer parcelle aubergine",
                "detail": "Drainer. Réduire arrosage. Billonner si terrain plat."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CHOU  (IRR-CHO-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-CHO-002",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Besoin eau chou — Pommaison",
        "cultures": ["Chou"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["pommaison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 15},
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Eau insuffisante pommaison chou",
                "message": "Pommaison = phase critique : manque d'eau = petites têtes, fissures, qualité commerciale perdue."}],
            "risque": {"score": 0.82, "libelle": "Pommaison compromise"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation abondante pommaison",
                "detail": "20-25 mm tous les 5-7 jours. Chou consomme 400-500 mm sur cycle complet.",
                "urgence_jours": 2}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-CHO-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Excès eau chou — Pourriture collet hernia",
        "cultures": ["Chou"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 82},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Excès eau chou",
                "message": "Sol saturé = hernie (Plasmodiophora brassicae) + fonte semis (Rhizoctonia). Drainer."}],
            "risque": {"score": 0.78, "libelle": "Hernie + fonte"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainage + chaulage chou",
                "detail": "Drainer. Chaux vive 1 t/ha si hernie connue. pH >7 réduit Plasmodiophora."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CONCOMBRE  (IRR-CON-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-CON-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique concombre — Fructification",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.etp", "op": "gte", "value": 6.5},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Stress hydrique concombre fructification",
                "message": "ETP > 6.5 + peu de pluie : amertume, fruits recourbés, BER. Production commerciale compromise."}],
            "risque": {"score": 0.88, "libelle": "Qualité fruits déclassée"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Goutte-à-goutte concombre",
                "detail": "2-3 mm/jour par temps chaud. Concombre = 95% eau. Ne jamais laisser stresser.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-CON-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Excès eau concombre — Pourriture pédonculaire",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 85},
            {"field": "meteo.pluie_24h", "op": "gte", "value": 35},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Excès eau concombre",
                "message": "Sol saturé + contact feuilles humides = Pythium/Phytophtora. Pourriture pédonculaire rapide."}],
            "risque": {"score": 0.78, "libelle": "Pythium/Phytophtora"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainer + palissage concombre",
                "detail": "Élever les fruits du sol. Drainer. Arrêter arrosage foliaire."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PAPAYE  (IRR-PAP-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-PAP-002",
        "categorie": "irrigation", "sous_categorie": "stress_hydrique",
        "nom": "Stress hydrique papaye — Chute fruits",
        "cultures": ["Papaye"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "meteo.temp_air", "op": "gte", "value": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Stress hydrique papaye saison sèche",
                "message": "Papaye très sensible : 10 jours de stress = chute massive fruits non mûrs."}],
            "risque": {"score": 0.88, "libelle": "Chute prématurée fruits"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation régulière papaye saison sèche",
                "detail": "25-30 mm/semaine minimum. Mulch organique 10 cm = économise 30% eau.",
                "urgence_jours": 2}],
        },
        "gravite": "critique", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-PAP-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Engorgement papaye — Pourriture collet mortelle",
        "cultures": ["Papaye"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 82},
            {"field": "meteo.pluie_24h", "op": "gte", "value": 40},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Engorgement papaye — collet menacé",
                "message": "Papaye en sol saturé > 48h = Pythium mortel. Plante s'effondre en 3-5 jours."}],
            "risque": {"score": 0.92, "libelle": "Pourriture collet mortelle"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainage urgence papaye",
                "detail": "Drainage immédiat. Mound planting obligatoire en zones à pluies > 1500 mm.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.92, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # ANACARDE  (IRR-ANA-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-ANA-002",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Irrigation d'appoint anacarde — Floraison saison sèche",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": [1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 2},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sécheresse anacarde floraison",
                "message": "Anacarde fleurit en saison sèche. Stress à floraison = avortement inflorescences."}],
            "risque": {"score": 0.72, "libelle": "Avortement floral"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation appoint anacarde floraison",
                "detail": "10-15 mm/semaine si accessible. Arroser au pied, éviter feuilles. Mulch organique."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-ANA-003",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Besoin eau anacarde — Nouaison noix",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": [3, 4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "meteo.etp", "op": "gte", "value": 6.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "ETP élevée nouaison anacarde",
                "message": "Nouaison noix cajou = période critique. ETP > 6 + sec = noix avortées, petites."}],
            "risque": {"score": 0.70, "libelle": "Nouaison compromise"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation appoint nouaison anacarde",
                "detail": "10-20 mm/semaine si possible. Priorité aux jeunes vergers 1-3 ans."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.68, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # BANANE  (IRR-BAN-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-BAN-002",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Besoin eau banane — Plein été saison sèche",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
            {"field": "meteo.etp", "op": "gte", "value": 5.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Banane = forte consommatrice eau",
                "message": "Banane consomme 1500-2200 mm/an. Saison sèche sans irrigation = perte totale de récolte."}],
            "risque": {"score": 0.92, "libelle": "Arrêt croissance saison sèche"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation goutte-à-goutte banane",
                "detail": "4-6 L/h/plant. 6-8 h/jour si ETP > 5mm. Irrigation localisée au pied optimal.",
                "urgence_jours": 2}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.92, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-BAN-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Engorgement banane — Saison pluies zone basse",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [7, 8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 88},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Engorgement bananier saison pluies",
                "message": "Sol saturé > 5 jours = Fusarium oxysporum f.sp. cubense actif (Panama). Verse aussi possible."}],
            "risque": {"score": 0.80, "libelle": "Fusarium + verse"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Drainage urgence bananier",
                "detail": "Drains enterrés 1m profondeur. Sol drainant obligatoire pour bananier durable."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PASTÈQUE  (IRR-PAS-002..03)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-PAS-002",
        "categorie": "irrigation", "sous_categorie": "besoin_eau",
        "nom": "Besoin eau pastèque — Grossissement fruits",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 15},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Eau insuffisante pastèque fructification",
                "message": "Pastèque = 95% eau. Stress grossissement = fruits petits, éclatement ou BER."}],
            "risque": {"score": 0.82, "libelle": "Fruits petits/déformés"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation régulière pastèque",
                "detail": "25-30 mm/semaine. Réduire légèrement 10 jours avant récolte pour sucrer. Éviter irrégularité."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-PAS-003",
        "categorie": "irrigation", "sous_categorie": "exces_eau",
        "nom": "Excès eau pastèque — Fissuration éclatement fruits",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification", "maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 40},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},  # après sécheresse
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Réhumidification brutale pastèque",
                "message": "Forte pluie après sec = pression osmotique = éclatement fruits mûrs. Récolter immédiatement."}],
            "risque": {"score": 0.78, "libelle": "Éclatement fruits"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Récolte d'urgence fruits à maturité",
                "detail": "Récolter fruits mûrs dans les 48h après forte pluie pour éviter éclatement.",
                "urgence_jours": 1}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RÈGLES GÉNÉRALES IRRIGATION  (IRR-GEN-002..006)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "IRR-GEN-002",
        "categorie": "irrigation", "sous_categorie": "general",
        "nom": "ETP très élevée — Alerte stress toutes cultures",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [3, 4, 5, 11, 12],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.etp", "op": "gte", "value": 8.0},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "ETP extrême > 8 mm/j",
                "message": "Évapotranspiration > 8 mm/j : toutes cultures en stress potentiel. Irrigation prioritaire cultures sensibles."}],
            "risque": {"score": 0.92, "libelle": "ETP extrême"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Priorité irrigation ETP élevée",
                "detail": "Priorité: 1-Florales/fructification 2-Jeunes plants 3-Cultures valeur haute."}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-GEN-003",
        "categorie": "irrigation", "sous_categorie": "general",
        "nom": "Sécheresse prolongée — Déficit hydrique cumulé",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 2},
            {"field": "meteo.etp", "op": "gte", "value": 5.5},
            {"field": "meteo.temp_air", "op": "gte", "value": 32},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Déficit hydrique cumulé critique",
                "message": "Déficit > 35 mm/semaine. Stress hydrique généralisé imminent si pas d'irrigation."}],
            "risque": {"score": 0.85, "libelle": "Déficit hydrique cumulé"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Déclencher irrigation d'urgence",
                "detail": "Compenser 50-70% du déficit. Doses fractionnées tôt le matin pour limiter pertes évaporatoires."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-GEN-004",
        "categorie": "irrigation", "sous_categorie": "general",
        "nom": "Pluie prévue — Report irrigation conseillé",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Pluie significative — Reporter irrigation",
                "message": "Pluie récente ≥ 20 mm : reporter toute irrigation 2-3 jours pour éviter sur-irrigation."}],
            "risque": {"score": 0.40, "libelle": "Gaspillage eau"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Reporter irrigation 2-3 jours",
                "detail": "Surveiller humidité sol avant de reprendre l'irrigation."}],
        },
        "gravite": "faible", "priorite": 3, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-GEN-005",
        "categorie": "irrigation", "sous_categorie": "general",
        "nom": "Sol saturé généralisé — Drainage prioritaire",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "gte", "value": 90},
            {"field": "meteo.pluie_7j", "op": "gte", "value": 80},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Sol saturé — Drainage urgent",
                "message": "Humidité sol > 90% = asphyxie racinaire imminente. Toutes cultures menacées."}],
            "risque": {"score": 0.90, "libelle": "Asphyxie racinaire"},
            "recommandations": [{"priorite": 1, "type": "drainage",
                "titre": "Créer rigoles de drainage urgence",
                "detail": "Rigoles profondes 30 cm entre rangs. Pompage si nappe remontante.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "IRR-GEN-006",
        "categorie": "irrigation", "sous_categorie": "general",
        "nom": "Vent fort + chaleur — Stress combiné évapotranspiration",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "gte", "value": 30},
            {"field": "meteo.temp_air", "op": "gte", "value": 35},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Vent chaud + air sec — ETP explosive",
                "message": "Harmattan intense : ETP peut dépasser 10 mm/j. Irrigation 2x/jour jeunes plants si possible."}],
            "risque": {"score": 0.85, "libelle": "ETP explosive harmattan"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Doubler fréquence irrigation",
                    "detail": "Fractionnement: matin + fin après-midi. Mulch sol obligatoire."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Brise-vent si possible",
                    "detail": "Plantation rangées arbustes = réduit ETP de 20-30%."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "gratuit",
    },

]
