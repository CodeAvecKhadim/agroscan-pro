"""
Rules Engine V1 — Catégorie RAVAGEURS — Additions V2
+40 règles pour compléter la couverture 20 cultures.
"""

RAVAGEURS_RULES_V2 = [

    # ═══════════════════════════════════════════════════════════
    # ANACARDE  (RAV-ANA-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-ANA-002",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Thrips anacarde — Floraison inflorescence",
        "cultures": ["Anacarde"], "ravageurs": ["Thrips (Selenothrips rubrocinctus)"],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": [2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Thrips anacarde actif",
                "message": "Saison sèche + chaleur : thrips envahissent les inflorescences, réduisant la nouaison de 20-40%."}],
            "risque": {"score": 0.78, "libelle": "Thrips floraison"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Insecticide contact thrips anacarde",
                "produit": "Lambda-cyhalothrine 2.5EC", "dose": "0,5 L/ha",
                "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-ANA-003",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Cochenille anacarde — Tiges et feuilles",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "cochenille"},
            {"field": "obs.symptomes", "op": "contains", "value": "fumagine"},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Cochenille anacarde détectée",
                "message": "Fumagine noire sur feuilles = cochenilles actives. Réduire la vigueur de 15%."}],
            "risque": {"score": 0.62, "libelle": "Cochenilles"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Huile blanche + insecticide",
                "produit": "Huile de paraffine 1% + Acétamipride 20SP",
                "dose": "0,5 L + 0,3 kg/ha", "urgence_jours": 5}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.70, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-ANA-004",
        "categorie": "ravageur", "sous_categorie": "insecte_foreur",
        "nom": "Foreur tige anacarde — Saison sèche",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "sciure"},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Foreur tige anacarde",
                "message": "Sciure visible = galerie en cours. Risque de casse de branches fruitières."}],
            "risque": {"score": 0.65, "libelle": "Foreur tige"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Injecter insecticide dans galerie",
                    "detail": "Coton imbibé d'acétate d'éthyle ou chlorpyrifos + obturer galerie."},
            ],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.65, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # AUBERGINE  (RAV-AUB-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-AUB-002",
        "categorie": "ravageur", "sous_categorie": "acarien",
        "nom": "Acarien tétranyque aubergine — Saison sèche",
        "cultures": ["Aubergine"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 50},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Acariens tétranyques aubergine",
                "message": "Temps chaud et sec : prolifération rapide de Tetranychus urticae sur face inférieure."}],
            "risque": {"score": 0.80, "libelle": "Tetranychus urticae"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Acaricide contact aubergine",
                "produit": "Abamectine 1.8EC", "dose": "0,5 L/ha",
                "delai_carence_jours": 7, "urgence_jours": 5}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-AUB-003",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Aleurodes aubergine — Vecteur virus + miellat",
        "cultures": ["Aubergine"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "aleurode"},
            {"field": "obs.ravageurs", "op": "contains", "value": "mouche_blanche"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Aleurodes aubergine",
                "message": "Bemisia tabaci = vecteur TYLCV + fumagine. Contrôle urgent."}],
            "risque": {"score": 0.82, "libelle": "Aleurodes + virus"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Insecticide systémique aleurodes",
                "produit": "Thiamethoxam 25WG", "dose": "0,15 kg/ha", "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-AUB-004",
        "categorie": "ravageur", "sous_categorie": "insecte_perforateur",
        "nom": "Perforateur fruits aubergine — Leucinodes orbonalis",
        "cultures": ["Aubergine"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification", "maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "galerie_fruit"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Perforateur fruits aubergine",
                "message": "Leucinodes orbonalis : larves creusent galeries dans fruits. Perte 60-80% sans traitement."}],
            "risque": {"score": 0.88, "libelle": "Leucinodes orbonalis"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "Spinosad ou Bacillus thuringiensis",
                    "produit": "Spinosad 48SC", "dose": "0,25 L/ha",
                    "delai_carence_jours": 3, "urgence_jours": 2},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Récolter fruits perforés et détruire"},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # BANANE  (RAV-BAN-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-BAN-002",
        "categorie": "ravageur", "sous_categorie": "insecte_foreur",
        "nom": "Charançon du bananier — Cosmopolites sordidus",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "charancon"},
            {"field": "obs.symptomes", "op": "contains", "value": "galerie_rhizome"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Charançon du bananier détecté",
                "message": "Cosmopolites sordidus : larves détruisent le rhizome. Causes de dépérissement et verse. Perte potentielle >50%."}],
            "risque": {"score": 0.90, "libelle": "Charançon bananier"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "Endosulfan ou Chlorpyrifos sol",
                    "produit": "Chlorpyrifos 20EC", "dose": "4 L/ha",
                    "detail": "Traitement sol au pied des rejets.", "urgence_jours": 5},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Pièges à pseudotiges",
                    "detail": "Déposer pseudo-tige coupée en tronçons → attire adultes → collecter et détruire."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-BAN-003",
        "categorie": "ravageur", "sous_categorie": "nematode",
        "nom": "Nématodes bananier — Pratylenchus / Radopholus",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "nanisme"},
            {"field": "sol.pH", "op": "between", "value": 5.5, "value2": 7.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Nématodes bananier suspects",
                "message": "Nanisme + racines nécrosées = nématodes endoparasites. Analyse sol recommandée."}],
            "risque": {"score": 0.75, "libelle": "Nématodes racinaires"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Utiliser rejets sains (macropropagation)",
                    "detail": "Traitement eau chaude 55°C / 20 min sur rejets avant plantation."},
                {"priorite": 2, "type": "amendement_sol", "titre": "Matière organique + rotation",
                    "detail": "Fumure organique 20 t/ha améliore biodiversité sol et réduit nématodes."},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.70, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-BAN-004",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Thrips bananier — Chaetanaphothrips orchidii",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 70},
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Thrips bananier sur régimes",
                "message": "Thrips entrainent cicatrices et nécrose sur peau banane. Impact commercial."}],
            "risque": {"score": 0.62, "libelle": "Thrips bananier"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Gainer les régimes en floraison",
                "detail": "Gainette polyéthylène percée = protection mécanique efficace."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.68, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CONCOMBRE  (RAV-CON-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-CON-002",
        "categorie": "ravageur", "sous_categorie": "acarien",
        "nom": "Acarien rouge concombre — Saison sèche chaude",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 55},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Acariens rouges concombre",
                "message": "Chaleur + sécheresse : multiplication explosive de Tetranychus urticae."}],
            "risque": {"score": 0.82, "libelle": "Acariens"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Acaricide tétranyques concombre",
                "produit": "Abamectine 1.8EC", "dose": "0,4 L/ha",
                "delai_carence_jours": 7, "urgence_jours": 4}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-CON-003",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Puceron concombre — Colonie sur jeunes pousses",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "puceron"},
            {"field": "obs.symptomes", "op": "contains", "value": "feuilles_enroulees"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pucerons concombre",
                "message": "Aphis gossypii : vecteur CMV + Potyviruses. Colonies sur apex."}],
            "risque": {"score": 0.80, "libelle": "Pucerons + virus"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Insecticide puceron concombre",
                "produit": "Pirimicarbe 50WG", "dose": "0,4 kg/ha",
                "delai_carence_jours": 3, "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-CON-004",
        "categorie": "ravageur", "sous_categorie": "insecte_foreur",
        "nom": "Mouche du fruit concombre — Bactrocera cucurbitae",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": [7, 8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Mouche du fruit cucurbitacées",
                "message": "Bactrocera cucurbitae pontes dans fruits verts → pourriture + chute."}],
            "risque": {"score": 0.88, "libelle": "Mouche du fruit"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "Pièges à phéromone + appât protéiné",
                    "produit": "Methyl Eugenol piège + Malathion appât", "dose": "5 pièges/ha"},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Récolter fruits régulièrement",
                    "detail": "Fruits laissés mûrs = sites de ponte. Enfouir fruits tombés."},
            ],
        },
        "gravite": "critique", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # GOMBO  (RAV-GOM-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-GOM-002",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Pucerons gombo — Aphis gossypii sur jeunes plants",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "puceron"},
            {"field": "obs.symptomes", "op": "contains", "value": "miellat_gombo"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pucerons gombo",
                "message": "Aphis gossypii sur jeunes plants : malformation + vecteur de virus (OKRV)."}],
            "risque": {"score": 0.78, "libelle": "Pucerons + virus"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Insecticide puceron gombo",
                "produit": "Imidaclopride 200SL", "dose": "0,4 L/ha",
                "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-GOM-003",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Aleurodes gombo — Bemisia tabaci",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 60},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Aleurodes gombo — saison sèche",
                "message": "Temps sec et chaud : explosion de Bemisia tabaci sur gombo. Fumagine + virus."}],
            "risque": {"score": 0.80, "libelle": "Aleurodes"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Spirotétramate contre aleurodes",
                "produit": "Spirotétramate 150OD", "dose": "0,8 L/ha",
                "urgence_jours": 4}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-GOM-004",
        "categorie": "ravageur", "sous_categorie": "insecte_foreur",
        "nom": "Perceur de la capsule gombo — Earias insulana",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "capsule_percee"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Earias insulana sur gombo",
                "message": "Larves perforent tiges et capsules. Perte qualité commerciale."}],
            "risque": {"score": 0.85, "libelle": "Earias insulana"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Pyréthrinoïde sur capsules",
                "produit": "Cypermethrine 10EC", "dose": "0,5 L/ha",
                "delai_carence_jours": 5, "urgence_jours": 3}],
        },
        "gravite": "critique", "priorite": 9, "confiance": 0.85, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # SÉSAME  (RAV-SES-002..003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-SES-002",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Punaise tigre sésame — Sésame saison humide",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification", "maturation"],
        "mois_applicables": [8, 9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "gte", "value": 70},
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Punaise tigre sésame",
                "message": "Punaises actives sur capsules : succion graines en formation. Perte qualitative."}],
            "risque": {"score": 0.65, "libelle": "Punaises capsules"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Endosulfan sur capsules sésame",
                "produit": "Endosulfan 35EC", "dose": "1,5 L/ha",
                "urgence_jours": 5}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.65, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-SES-003",
        "categorie": "ravageur", "sous_categorie": "acarien",
        "nom": "Acarien sésame — Polyphagotarsonemus latus",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 55},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Acarien large sésame",
                "message": "Polyphagotarsonemus latus : déformation jeunes feuilles en saison sèche."}],
            "risque": {"score": 0.60, "libelle": "Acarien large"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Dicofol ou soufre mouillable",
                "produit": "Soufre mouillable 80WP", "dose": "3 kg/ha",
                "urgence_jours": 5}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.62, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PASTÈQUE  (RAV-PAS-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-PAS-002",
        "categorie": "ravageur", "sous_categorie": "insecte_foreur",
        "nom": "Mouche du fruit pastèque — Bactrocera cucurbitae",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": [5, 6, 7, 8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 55},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Mouche du fruit pastèque",
                "message": "Bactrocera cucurbitae : pontes dans jeunes fruits = pourriture interne totale."}],
            "risque": {"score": 0.90, "libelle": "Mouche du fruit"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "Piège + appât protéiné pastèque",
                    "produit": "Spinosad 0.02% appât + Methyl eugenol piège", "dose": "5 pièges/ha"},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Récolter à maturité sans délai",
                    "detail": "Fruits laissés au sol = foyers de reproduction. Détruire fruits infestés."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-PAS-003",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Puceron pastèque — Aphis gossypii",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "puceron"},
            {"field": "obs.symptomes", "op": "contains", "value": "enroulement_apical"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Pucerons pastèque",
                "message": "Aphis gossypii vecteur WMV2 et CMV sur pastèque. Traitement urgent vecteur."}],
            "risque": {"score": 0.82, "libelle": "Puceron + virus"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Pirimicarbe contre pucerons pastèque",
                "produit": "Pirimicarbe 50WG", "dose": "0,3 kg/ha",
                "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-PAS-004",
        "categorie": "ravageur", "sous_categorie": "acarien",
        "nom": "Acarien rouge pastèque — Temps sec prolongé",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 32},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 45},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Acariens rouges pastèque",
                "message": "Extrême sécheresse : Tetranychus urticae explose sur feuilles. Brunissement foliaire."}],
            "risque": {"score": 0.78, "libelle": "Tetranychus urticae"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Acaricide pastèque",
                "produit": "Spiromesifen 240SC", "dose": "0,4 L/ha",
                "urgence_jours": 4}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # ARACHIDE ajout  (RAV-ARA-004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-ARA-004",
        "categorie": "ravageur", "sous_categorie": "insecte_foreur",
        "nom": "Termites arachide — Sol sableux saison sèche",
        "cultures": ["Arachide"], "ravageurs": [],
        "zones_applicables": ["bassin_arachidier", "soudano_sahelien"],
        "stades_applicables": None,
        "mois_applicables": [10, 11, 12],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "lte", "value": 20},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Termites arachide saison sèche",
                "message": "Sol sec = colonisation termites. Attaquent gousses et tiges : perte qualitative importante."}],
            "risque": {"score": 0.75, "libelle": "Termites"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Insecticide sol termites arachide",
                "produit": "Chlorpyrifos 40EC", "dose": "2 L/ha (sol)"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MIL ajout  (RAV-MIL-004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-MIL-004",
        "categorie": "ravageur", "sous_categorie": "plante_parasite",
        "nom": "Striga — Mil Sorgho zones sèches",
        "cultures": ["Mil", "Sorgho"], "ravageurs": [],
        "zones_applicables": ["soudano_sahelien", "sahel"],
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": [7, 8, 9],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "striga"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Striga détecté",
                "message": "Striga hermonthica — plante parasite racinaire. Réduit rendement 30-80% selon infestation."}],
            "risque": {"score": 0.90, "libelle": "Striga hermonthica"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Arracher Striga avant floraison",
                    "detail": "Avant fleur rouge = avant dispersion graines. 500 graines/plant = infestation persistante 20 ans."},
                {"priorite": 2, "type": "traitement_semences", "titre": "Traitement semences Imazapyr",
                    "produit": "Imazapyr 0.5% (Imazapyr-IR)", "dose": "10 g/kg semences"},
                {"priorite": 3, "type": "mesure_culturale", "titre": "Rotation légumineuses + fumier",
                    "detail": "Niébé ou arachide avant mil + fumier 2 t/ha réduit émergence Striga."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MANGUE ajout  (RAV-MAG-003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-MAG-003",
        "categorie": "ravageur", "sous_categorie": "insecte_foreur",
        "nom": "Mouche du fruit mangue — Ceratitis cosyra",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification", "maturation"],
        "mois_applicables": [4, 5, 6, 7],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 55},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Mouche du fruit mangue",
                "message": "Ceratitis cosyra principal ravageur mangue Afrique. Pertes 30-80%. Piqûre sur fruits verts-jaunes."}],
            "risque": {"score": 0.90, "libelle": "Cératite de la mangue"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "Piège + appât protéiné mangue",
                    "produit": "Spinosad 0.02% appât + piège Cue-lure", "dose": "5 pièges/ha + 8 appâts/ha"},
                {"priorite": 2, "type": "traitement_phyto", "titre": "Malathion ULV couverture",
                    "produit": "Malathion 50EC + Sucre 10%", "dose": "Taches 1 L/arbre", "urgence_jours": 7},
                {"priorite": 3, "type": "mesure_culturale", "titre": "Ramasser fruits tombés quotidiennement",
                    "detail": "Fruits tombés = foyers de ponte. Enfouir à 50 cm ou immerger."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CHOU ajout  (RAV-CHO-003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-CHO-003",
        "categorie": "ravageur", "sous_categorie": "insecte_foreur",
        "nom": "Teigne des crucifères — Plutella xylostella",
        "cultures": ["Chou"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "teigne_chou"},
            {"field": "obs.symptomes", "op": "contains", "value": "fenestration_feuilles"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Teigne crucifères chou",
                "message": "Plutella xylostella : ravageur #1 du chou mondial. Résistances nombreuses aux insecticides. Larves vert pâle."}],
            "risque": {"score": 0.92, "libelle": "Plutella xylostella"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "BT ou Spinosad vs teigne",
                    "produit": "Bacillus thuringiensis subsp. kurstaki", "dose": "1 kg/ha",
                    "detail": "Alterner avec Spinosad 48SC (0.3 L/ha) pour éviter résistances.", "urgence_jours": 2},
                {"priorite": 2, "type": "traitement_phyto", "titre": "Chlorantraniliprole systémique",
                    "produit": "Chlorantraniliprole 18.5SC", "dose": "0,3 L/ha",
                    "delai_carence_jours": 14, "urgence_jours": 3},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.92, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # OIGNON ajout  (RAV-OIG-003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-OIG-003",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Thrips oignon — Thrips tabaci forte pression",
        "cultures": ["Oignon"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "bulbaison"],
        "mois_applicables": [11, 12, 1, 2, 3],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.humidite_rel", "op": "lte", "value": 50},
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "obs.ravageurs", "op": "contains", "value": "thrips"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Thrips oignon — forte pression",
                "message": "Thrips tabaci population élevée : rugosité + blanchiment feuilles + transmission IYSV."}],
            "risque": {"score": 0.88, "libelle": "Thrips forte pression"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Abamectine + Imidaclopride alternés",
                "produit": "Abamectine 1.8EC + Imidaclopride 200SL", "dose": "0,5 L + 0,3 L/ha",
                "detail": "Alterner familles pour éviter résistances.", "urgence_jours": 2}],
        },
        "gravite": "critique", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PIMENT ajout  (RAV-PIM-003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-PIM-003",
        "categorie": "ravageur", "sous_categorie": "acarien",
        "nom": "Acarien large piment — Polyphagotarsonemus latus",
        "cultures": ["Piment"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 55},
            {"field": "obs.symptomes", "op": "contains", "value": "bronzing_apex"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Acarien large piment",
                "message": "P. latus : apex déformés en saison sèche. Ressemble à une carence. Loupe nécessaire."}],
            "risque": {"score": 0.78, "libelle": "Polyphagotarsonemus latus"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Abamectine contre acarien large",
                "produit": "Abamectine 1.8EC", "dose": "0,5 L/ha",
                "urgence_jours": 4}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RIZ ajout  (RAV-RIZ-005)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-RIZ-005",
        "categorie": "ravageur", "sous_categorie": "insecte_piqueur",
        "nom": "Cigale d'eau — Riz irrigation début saison",
        "cultures": ["Riz"], "ravageurs": [],
        "zones_applicables": ["vallee_fleuve"],
        "stades_applicables": ["levee", "tallage"],
        "mois_applicables": [4, 5, 6],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
            {"field": "obs.symptomes", "op": "contains", "value": "brunissement_racines"},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Cigale d'eau riz",
                "message": "Belostoma/Nepidae : sucent racines dans eau chaude. Tallage affaibli."}],
            "risque": {"score": 0.62, "libelle": "Cigale d'eau"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Vider et refaire lame d'eau",
                "detail": "Renouveler eau + Chlorpyrifos granulés si nécessaire."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.65, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MANIOC ajout  (RAV-MAN-003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-MAN-003",
        "categorie": "ravageur", "sous_categorie": "acarien",
        "nom": "Acarien vert manioc — Mononychellus tanajoa",
        "cultures": ["Manioc"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 50},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Acarien vert manioc saison sèche",
                "message": "Mononychellus tanajoa : lobes déformés en saison sèche. Pertes 30-80% si non traité."}],
            "risque": {"score": 0.80, "libelle": "Acarien vert"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_phyto", "titre": "Acaricide manioc",
                    "produit": "Dicofol 18.5EC ou Abamectine 1.8EC", "dose": "1 L/ha"},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Lâcher Typhlodromalus aripo",
                    "detail": "Acarien prédateur introduit en Afrique. Demander IITA / CSRS."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RÈGLES GÉNÉRALES RAVAGEURS  (RAV-GEN-001..005)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "RAV-GEN-001",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Explosion ravageurs — Chaleur extrême + sécheresse",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1, 2, 3, 4],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 35},
            {"field": "meteo.humidite_rel", "op": "lte", "value": 40},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 2},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Conditions favorables explosion ravageurs",
                "message": "Temps très sec et chaud : acariens + aleurodes + pucerons en prolifération exponentielle."}],
            "risque": {"score": 0.75, "libelle": "Ravageurs saison sèche"},
            "recommandations": [{"priorite": 1, "type": "surveillance",
                "titre": "Inspection face inférieure des feuilles 2x/semaine"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-GEN-002",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Invasion acridienne — Criquet pèlerin zone sahel",
        "cultures": [], "ravageurs": [],
        "zones_applicables": ["soudano_sahelien", "sahel"],
        "stades_applicables": None,
        "mois_applicables": [8, 9, 10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "criquet"},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Invasion acridienne",
                "message": "Schistocerca gregaria : alerte critique. Contacter services phytosanitaires DGPV immédiatement."}],
            "risque": {"score": 0.98, "libelle": "Criquet pèlerin"},
            "recommandations": [
                {"priorite": 1, "type": "alerte_institutionnelle",
                    "titre": "URGENCE — Contacter DGPV Sénégal : +221 33 889 10 85",
                    "detail": "Signalement obligatoire. Traitement aérien national coordonné (Fipronil ULV)."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.98, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-GEN-003",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Nématodes polyvalents — Sol sableux acide",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "lte", "value": 5.5},
            {"field": "obs.symptomes", "op": "contains", "value": "galles_racinaires"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Nématodes galligènes détectés",
                "message": "Meloidogyne spp. : galles sur racines. Sol acide et sableux = conditions optimales."}],
            "risque": {"score": 0.82, "libelle": "Nématodes à galles"},
            "recommandations": [
                {"priorite": 1, "type": "traitement_sol", "titre": "Nématicide sol",
                    "produit": "Cadusafos 10GR ou Oxamyl 10GR", "dose": "10-15 kg/ha"},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Solarisation sol pépinière",
                    "detail": "Film plastique transparent 6 semaines = 80% réduction nématodes."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-GEN-004",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Noctuelles terricoles — Semis levée sol humide",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["semis", "levee"],
        "mois_applicables": [6, 7, 8],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 20},
            {"field": "meteo.temp_air", "op": "gte", "value": 24},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Risque noctuelles terricoles",
                "message": "Après forte pluie chaude : Agrotis/Spodoptera actifs la nuit, coupent collets jeunes plants."}],
            "risque": {"score": 0.65, "libelle": "Noctuelles terricoles"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Insecticide sol granulé ou bait",
                "produit": "Chlorpyrifos 10GR", "dose": "15 kg/ha au sol"}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.65, "plan_requis": "gratuit",
    },
    {
        "code": "RAV-GEN-005",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Punaises phytophages — Floraison toutes cultures",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.ravageurs", "op": "contains", "value": "punaise"},
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Punaises phytophages en floraison",
                "message": "Succion fleurs et jeunes fruits = avortement floral + stigmates piqûres commerciales."}],
            "risque": {"score": 0.72, "libelle": "Punaises floraison"},
            "recommandations": [{"priorite": 1, "type": "traitement_phyto",
                "titre": "Pyréthrinoïde contact + ingestion",
                "produit": "Lambda-cyhalothrine 2.5EC", "dose": "0,5 L/ha",
                "urgence_jours": 3}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },

]
