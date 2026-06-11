"""
Rules Engine V1 — Catégorie FERTILISATION — Additions V2
+45 règles : complétion 20 cultures, carences NPK, pH, matière organique.
"""

FERTILISATION_RULES_V2 = [

    # ═══════════════════════════════════════════════════════════
    # SÉSAME  (FER-SES-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-SES-002",
        "categorie": "fertilisation", "sous_categorie": "phosphore",
        "nom": "Carence phosphore sésame — Levée racinaire",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.phosphore", "op": "lte", "value": 15},
            {"field": "sol.pH", "op": "lte", "value": 6.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence phosphore sésame",
                "message": "P < 15 ppm sur sol acide : développement racinaire limité, anthèse réduite."}],
            "risque": {"score": 0.78, "libelle": "Carence P"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Triple Superphosphate sésame",
                "produit": "TSP 46% P2O5", "dose": "50 kg/ha en fond",
                "detail": "Incorporer avant semis. Améliore enracinement et floraison."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "FER-SES-003",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Carence potassium sésame — Fructification",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 0.20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence K sésame fructification",
                "message": "K+ insuffisant : remplissage graines incomplet, qualité huile réduite."}],
            "risque": {"score": 0.75, "libelle": "Carence K"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Chlorure de potassium sésame",
                "produit": "KCl 60% K2O", "dose": "30 kg/ha en couverture"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "FER-SES-004",
        "categorie": "fertilisation", "sous_categorie": "azote",
        "nom": "Apport azoté sésame — Faible teneur sol",
        "cultures": ["Sésame"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 0.8},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Azote faible sésame",
                "message": "N total < 0.8‰ : jaunissement interfoliaire anticipé. Croissance végétative compromise."}],
            "risque": {"score": 0.68, "libelle": "Carence N"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Urée fractionnée sésame",
                "produit": "Urée 46% N", "dose": "40 kg/ha : 20 kg semis + 20 kg floraison"}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.70, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # GOMBO  (FER-GOM-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-GOM-002",
        "categorie": "fertilisation", "sous_categorie": "azote",
        "nom": "Carence azote gombo — Jaunissement progressif",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 0.7},
            {"field": "obs.symptomes", "op": "contains", "value": "jaunissement"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence azote gombo",
                "message": "Jaunissement des vieilles feuilles + sol N< 0.7‰ : apport azoté urgent."}],
            "risque": {"score": 0.80, "libelle": "Carence N"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Urée en couverture gombo",
                "produit": "Urée 46% N", "dose": "30 kg/ha fractionnés",
                "urgence_jours": 5}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GOM-003",
        "categorie": "fertilisation", "sous_categorie": "phosphore",
        "nom": "Carence phosphore gombo — Floraison réduite",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.phosphore", "op": "lte", "value": 12},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Phosphore faible gombo",
                "message": "P assimilable faible : avortement floral et production capsules réduite."}],
            "risque": {"score": 0.68, "libelle": "Carence P floraison"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Phosphate naturel Tilemsi",
                "produit": "Phosphate naturel 28% P2O5", "dose": "100 kg/ha en fond"}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.68, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GOM-004",
        "categorie": "fertilisation", "sous_categorie": "micronutriment",
        "nom": "Carence calcium-magnésium gombo — Sol sableux lessivé",
        "cultures": ["Gombo"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "lte", "value": 5.5},
            {"field": "sol.matiere_organique", "op": "lte", "value": 0.8},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Carence Ca-Mg gombo",
                "message": "pH acide + faible MO : Ca et Mg bloqués. Pourriture apicale capsules possible."}],
            "risque": {"score": 0.65, "libelle": "Carence Ca-Mg"},
            "recommandations": [{"priorite": 1, "type": "amendement_sol",
                "titre": "Dolomite (Ca+Mg) gombo",
                "produit": "Dolomite 18% CaO + 9% MgO", "dose": "500 kg/ha",
                "detail": "Relève pH + apporte Ca+Mg simultanément."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.65, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CONCOMBRE  (FER-CON-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-CON-002",
        "categorie": "fertilisation", "sous_categorie": "calcium",
        "nom": "Carence calcium concombre — Pourriture apicale",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "pourriture_apicale"},
            {"field": "sol.conductivite", "op": "gte", "value": 3.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence Ca concombre",
                "message": "Pourriture apicale bout des fruits = carence calcique fonctionnelle. Liée à stress hydrique ou EC élevée."}],
            "risque": {"score": 0.80, "libelle": "BER (Blossom End Rot)"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Nitrate de calcium foliaire",
                "produit": "Nitrate de Ca 15%", "dose": "4 kg/ha en foliaire 2x/semaine",
                "detail": "Irrigation régulière simultanée — carence fonctionnelle."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "FER-CON-003",
        "categorie": "fertilisation", "sous_categorie": "azote",
        "nom": "Programme NPK concombre — Cycle complet",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 1.0},
            {"field": "sol.phosphore", "op": "lte", "value": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Programme NPK concombre recommandé",
                "message": "Sol pauvre en N et P : fertilisation NPK structurée nécessaire pour potentiel productif."}],
            "risque": {"score": 0.70, "libelle": "Carence NPK"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Programme NPK concombre",
                "detail": "Fond: DAP 100 kg/ha. J15: Urée 30 kg/ha. J30: KCl 30 kg/ha. Floraison: urée 20 kg/ha."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.70, "plan_requis": "gratuit",
    },
    {
        "code": "FER-CON-004",
        "categorie": "fertilisation", "sous_categorie": "micronutriment",
        "nom": "Carence magnésium concombre — Chlorose interfoliaire",
        "cultures": ["Concombre"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "chlorose_interfoliaire"},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Carence magnésium concombre",
                "message": "Chlorose entre nervures = Mg insuffisant. Fréquent sur sables après pluies lessivantes."}],
            "risque": {"score": 0.65, "libelle": "Carence Mg"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Sulfate de magnésium foliaire",
                "produit": "MgSO4 (Kieserite) 16% Mg", "dose": "2 kg/ha en foliaire",
                "urgence_jours": 7}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.65, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PAPAYE  (FER-PAP-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-PAP-002",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Carence potassium papaye — Qualité fruits",
        "cultures": ["Papaye"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 0.25},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence K papaye",
                "message": "K+ insuffisant en fructification : fruits petits, saveur réduite, sensibilité accrue anthracnose."}],
            "risque": {"score": 0.78, "libelle": "Carence K"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Sulfate de potassium papaye",
                "produit": "SOP K2SO4 50% K2O", "dose": "100 g/plant/mois",
                "detail": "Préférer SO4 à Cl pour papaye sensible au chlore."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "FER-PAP-003",
        "categorie": "fertilisation", "sous_categorie": "magnesium",
        "nom": "Carence magnésium papaye — Feuilles basses jaunies",
        "cultures": ["Papaye"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "lte", "value": 6.0},
            {"field": "obs.symptomes", "op": "contains", "value": "jaunissement_interfoliaire"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence Mg papaye",
                "message": "Jaunissement entre nervures feuilles âgées = Mg bloqué par pH bas ou excès K."}],
            "risque": {"score": 0.75, "libelle": "Carence Mg"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Kieserite en sol + foliaire",
                "produit": "Kieserite MgSO4 26% MgO", "dose": "200 g/plant sol + 2 kg/ha foliaire"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "FER-PAP-004",
        "categorie": "fertilisation", "sous_categorie": "azote",
        "nom": "Programme NPK mensuel papaye — Plantation jeune",
        "cultures": ["Papaye"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 1.0},
            {"field": "culture.jours_semis", "op": "lte", "value": 180},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "NPK mensuel papaye requis",
                "message": "Papaye jeune = besoins élevés. Programme mensuel recommandé pour rendement optimal."}],
            "risque": {"score": 0.70, "libelle": "Carence NPK"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Programme mensuel papaye (6 premiers mois)",
                "detail": "M1-M3: 50g urée + 50g TSP + 50g KCl/plant/mois. M4-M6: 100g urée + 50g KCl/plant/mois."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MANGUE  (FER-MAG-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-MAG-002",
        "categorie": "fertilisation", "sous_categorie": "phosphore",
        "nom": "Carence phosphore mangue — Enracinement plantin",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.phosphore", "op": "lte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Phosphore bas mangue",
                "message": "P assimilable < 10 ppm : enracinement insuffisant jeunes arbres, floraison différée."}],
            "risque": {"score": 0.72, "libelle": "Carence P"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "DAP en fond de trou plantation",
                "produit": "DAP 18-46-0", "dose": "200-500 g/arbre en fond de trou"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },
    {
        "code": "FER-MAG-003",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Potassium mangue — Qualité fruits sucrés",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 0.20},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Potassium faible avant fructification mangue",
                "message": "K+ bas : fruits petits, moins sucrés, moins colorés. Impact commercial direct."}],
            "risque": {"score": 0.68, "libelle": "Carence K fruits"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "SOP avant floraison mangue",
                "produit": "Sulfate potassium 50% K2O", "dose": "500 g-1 kg/arbre avant floraison"}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.70, "plan_requis": "gratuit",
    },
    {
        "code": "FER-MAG-004",
        "categorie": "fertilisation", "sous_categorie": "micronutriment",
        "nom": "Carence bore mangue — Déformation fleurs",
        "cultures": ["Mangue"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "avortement_floral"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Possible carence bore mangue",
                "message": "Avortement floral massif = carence B possible, surtout sols sableux pluvieux lessivants."}],
            "risque": {"score": 0.65, "libelle": "Carence Bore"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Borax foliaire mangue",
                "produit": "Borax 11% B", "dose": "0,3% en foliaire (3 kg/100L eau)",
                "detail": "2 applications : 2 semaines avant + pendant floraison."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.68, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # ANACARDE  (FER-ANA-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-ANA-002",
        "categorie": "fertilisation", "sous_categorie": "phosphore",
        "nom": "Carence phosphore anacarde — Enracinement jeunes plants",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.phosphore", "op": "lte", "value": 8},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "P bas anacarde",
                "message": "P < 8 ppm sur sol ferrallitique : carence P fréquente au Sénégal pour anacarde."}],
            "risque": {"score": 0.75, "libelle": "Carence P"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Phosphate naturel fond anacarde",
                "produit": "Phosphate de Thiès 28% P2O5", "dose": "500 g/arbre en fond de trou"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "FER-ANA-003",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Potassium anacarde — Remplissage noix",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification", "maturation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 0.15},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "K insuffisant anacarde fructification",
                "message": "K+ bas pendant remplissage noix : calibre et teneur huile réduits."}],
            "risque": {"score": 0.65, "libelle": "Carence K"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "SOP avant floraison anacarde",
                "produit": "K2SO4 50% K2O", "dose": "250-500 g/arbre selon âge"}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.65, "plan_requis": "gratuit",
    },
    {
        "code": "FER-ANA-004",
        "categorie": "fertilisation", "sous_categorie": "azote",
        "nom": "Azote anacarde jeune — Croissance végétative",
        "cultures": ["Anacarde"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 0.5},
            {"field": "culture.jours_semis", "op": "lte", "value": 365},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "N bas anacarde jeune",
                "message": "Anacarde <1 an : N suffisant nécessaire pour charpente arbre. Ne pas négliger."}],
            "risque": {"score": 0.65, "libelle": "Carence N jeune"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Urée anacarde jeune",
                "produit": "Urée 46% N", "dose": "50-100 g/plant en 2 fractions (saison pluies)"}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.65, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # BANANE  (FER-BAN-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-BAN-002",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Carence potassium banane — Nervures et fruits",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 0.30},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Carence K banane",
                "message": "Banane 1er consommateur K : K< 0.3 meq = fruit malformés, doigts courts, verse. Urgence."}],
            "risque": {"score": 0.88, "libelle": "Carence K critique"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "KCl ou SOP mensuel banane",
                "produit": "KCl 60% K2O", "dose": "300 g/plant/mois",
                "detail": "Banane exporte 400+ kg K2O/ha/an. Indispensable pour rendement."}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "FER-BAN-003",
        "categorie": "fertilisation", "sous_categorie": "magnesium",
        "nom": "Carence Mg banane — Chlorose Bluggoe",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "chlorose_banane"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence Mg banane",
                "message": "Jaunissement interfoliaire feuilles adultes = Mg déplacé par excès K. Apport Mg requis."}],
            "risque": {"score": 0.78, "libelle": "Carence Mg banane"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Kieserite sol + foliaire banane",
                "produit": "Kieserite 26% MgO", "dose": "200 g/plant/mois + foliaire 2 kg/ha"}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "FER-BAN-004",
        "categorie": "fertilisation", "sous_categorie": "azote",
        "nom": "Programme azoté banane — Tallage et montaison",
        "cultures": ["Banane"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 1.2},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Azote insuffisant banane",
                "message": "N < 1.2‰ : feuilles courtes, canopée réduite, cycle allongé."}],
            "risque": {"score": 0.78, "libelle": "Carence N"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Urée mensuel banane",
                "produit": "Urée 46% N", "dose": "150-200 g/plant/mois"}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PASTÈQUE  (FER-PAS-002..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-PAS-002",
        "categorie": "fertilisation", "sous_categorie": "azote",
        "nom": "Carence azote pastèque — Croissance végétative",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 0.8},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "N faible pastèque",
                "message": "Vigueur végétative insuffisante : feuilles petites, tiges courtes. Rendement compromis."}],
            "risque": {"score": 0.75, "libelle": "Carence N"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Urée fractionnée pastèque",
                "produit": "Urée 46% N", "dose": "50 kg/ha en 3 fractions (semis/J20/floraison)"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "FER-PAS-003",
        "categorie": "fertilisation", "sous_categorie": "calcium",
        "nom": "Carence calcium pastèque — Pourriture apex fruit",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "pourriture_apicale"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "BER pastèque (blossom end rot)",
                "message": "Bout de fleur pourri = carence Ca fonctionnelle. Stress hydrique + sol peu tamponné."}],
            "risque": {"score": 0.80, "libelle": "Carence Ca BER"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Nitrate calcium foliaire + irrigation constante",
                "produit": "Nitrate Ca 15%", "dose": "4 kg/ha foliaire 2x/semaine",
                "detail": "Irrigation goutte-à-goutte régulière = Ca conduit par transpiration."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "FER-PAS-004",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Potassium pastèque — Qualité fruit sucre",
        "cultures": ["Pastèque"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 0.20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "K insuffisant pastèque fructification",
                "message": "K+ < 0.2 meq : teneur en sucre (Brix) réduite, chair moins dense."}],
            "risque": {"score": 0.78, "libelle": "Carence K qualité"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "SOP en couverture pastèque",
                "produit": "K2SO4 50% K2O", "dose": "50 kg/ha à nouaison fruits"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # NIÉBÉ ajout  (FER-NIE-003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-NIE-003",
        "categorie": "fertilisation", "sous_categorie": "micronutriment",
        "nom": "Inoculant rhizobium niébé — Sols non-cultivés",
        "cultures": ["Niébé"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["semis"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.azote", "op": "lte", "value": 0.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Inoculant rhizobium recommandé niébé",
                "message": "Sol pauvre en N : inoculation Bradyrhizobium = fixation azotée 80-150 kg N/ha. ROI élevé."}],
            "risque": {"score": 0.80, "libelle": "Manque fixation N2"},
            "recommandations": [{"priorite": 1, "type": "traitement_semences",
                "titre": "Inoculant Bradyrhizobium sur semences",
                "produit": "Inoculant Bradyrhizobium japonicum (SEMIA 587)", "dose": "200 g/25 kg semences",
                "detail": "Humidifier semences légèrement + mélanger inoculant + sécher à l'ombre avant semis."}],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MANIOC ajout  (FER-MAN-003)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-MAN-003",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Potassium manioc — Tubérisation et rendement",
        "cultures": ["Manioc"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["tuberisation"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 0.20},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "K insuffisant manioc tubérisation",
                "message": "K+ faible : amyloplastes réduits, tubérosités petites, qualité amidon affectée."}],
            "risque": {"score": 0.75, "libelle": "Carence K tubérisation"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "KCl manioc en couverture",
                "produit": "KCl 60% K2O", "dose": "80-100 kg/ha en couverture M4-M6"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # PIMENT ajout  (FER-PIM-003..004)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-PIM-003",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Potassium piment — Qualité fruits capsaïcine",
        "cultures": ["Piment"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.potassium", "op": "lte", "value": 0.22},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "K faible piment fructification",
                "message": "K insuffisant : fruits ternes, moins piquants, sensibilité accrue aux maladies post-récolte."}],
            "risque": {"score": 0.75, "libelle": "Carence K piment"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Sulfate potassium piment",
                "produit": "SOP 50% K2O", "dose": "50 kg/ha en couverture"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "FER-PIM-004",
        "categorie": "fertilisation", "sous_categorie": "calcium",
        "nom": "Carence calcium piment — BER pointe fruits",
        "cultures": ["Piment"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "OR", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "pourriture_apicale"},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "BER piment (bout de fleur)",
                "message": "Pourriture apicale piment = carence Ca fonctionnelle. Irrigation irrégulière facteur majeur."}],
            "risque": {"score": 0.78, "libelle": "BER piment"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Chlorure calcium foliaire piment",
                "produit": "CaCl2 ou Nitrate Ca 15%", "dose": "3 kg/ha foliaire"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RÈGLES GÉNÉRALES FERTILISATION  (FER-GEN-003..010)
    # ═══════════════════════════════════════════════════════════
    {
        "code": "FER-GEN-003",
        "categorie": "fertilisation", "sous_categorie": "pH",
        "nom": "Acidification sol — Correction chaulage urgence",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "lte", "value": 5.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "pH sol critique < 5.0",
                "message": "pH < 5.0 : Al3+ et Mn2+ toxiques, P totalement bloqué, activité biologique stoppée."}],
            "risque": {"score": 0.92, "libelle": "Toxicité aluminium"},
            "recommandations": [{"priorite": 1, "type": "amendement_sol",
                "titre": "Chaulage urgence pH<5",
                "produit": "Chaux agricole CaCO3 90%", "dose": "2-3 t/ha",
                "detail": "Apporter 2-3 mois avant plantation. Viser pH cible 6.0-6.5."}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.95, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GEN-004",
        "categorie": "fertilisation", "sous_categorie": "pH",
        "nom": "Sol légèrement acide — Optimisation disponibilité nutriments",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "between", "value": 5.0, "value2": 5.8},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "pH suboptimal 5.0-5.8",
                "message": "P assimilable réduit de 30-60%. Chaulage modéré recommandé."}],
            "risque": {"score": 0.72, "libelle": "Blocage phosphore"},
            "recommandations": [{"priorite": 1, "type": "amendement_sol",
                "titre": "Chaulage modéré",
                "produit": "Chaux agricole 90%", "dose": "1-1.5 t/ha selon tampon"}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GEN-005",
        "categorie": "fertilisation", "sous_categorie": "matiere_organique",
        "nom": "Matière organique très basse — Tous sols",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.matiere_organique", "op": "lte", "value": 0.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Matière organique sol critique",
                "message": "MO < 0.5% : sol peu tamponné, rétention eau réduite, minéralisation azote très faible."}],
            "risque": {"score": 0.85, "libelle": "MO critique"},
            "recommandations": [
                {"priorite": 1, "type": "amendement_sol", "titre": "Fumier organique 10 t/ha",
                    "produit": "Fumier décomposé ou compost", "dose": "10-20 t/ha",
                    "detail": "Application annuelle pendant 3 ans pour remonter MO de 0.5 à 1.5%."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Enfouir résidus de culture",
                    "detail": "Ne pas bruler les pailles. Incorporation = +0.1-0.2% MO/an."},
            ],
        },
        "gravite": "elevee", "priorite": 9, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GEN-006",
        "categorie": "fertilisation", "sous_categorie": "salinite",
        "nom": "Salinité sol élevée — Stress salin cultures maraîchères",
        "cultures": [], "ravageurs": [],
        "zones_applicables": ["niayes", "vallee_fleuve"],
        "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.conductivite", "op": "gte", "value": 4.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Salinité sol critique EC>4",
                "message": "EC > 4 dS/m : stress osmotique sévère. Tomate/oignon rendement chutera >50%."}],
            "risque": {"score": 0.90, "libelle": "Stress salin"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Lessivage salin en profondeur",
                    "detail": "Irrigation excédentaire 1000 mm pour descendre EC < 2 dS/m. Drainage nécessaire."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Variétés tolérantes sel uniquement",
                    "detail": "Orge, betterave, date tolèrent EC 6-8. Tomate limite EC < 2.5."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GEN-007",
        "categorie": "fertilisation", "sous_categorie": "azote",
        "nom": "Carence azote généralisée — Observation jaunissement",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["croissance_vegetative", "floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "jaunissement"},
            {"field": "sol.azote", "op": "lte", "value": 0.8},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence azote observée",
                "message": "Jaunissement des vieilles feuilles + N bas = carence azote. Apport d'urgence."}],
            "risque": {"score": 0.82, "libelle": "Carence N"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Urée ou ammonitrate en couverture urgence",
                "produit": "Urée 46% N", "dose": "30-50 kg/ha selon culture",
                "urgence_jours": 5}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GEN-008",
        "categorie": "fertilisation", "sous_categorie": "phosphore",
        "nom": "Carence phosphore — Teintes pourpres feuilles",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "teinte_pourpre"},
            {"field": "sol.phosphore", "op": "lte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence phosphore — teintes anthocyanes",
                "message": "Teinte pourpre-violette face inférieure = phosphore bloqué (froid ou pH bas)."}],
            "risque": {"score": 0.80, "libelle": "Carence P"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "DAP ou TSP en couverture",
                "produit": "DAP 18-46-0", "dose": "50 kg/ha",
                "urgence_jours": 7}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GEN-009",
        "categorie": "fertilisation", "sous_categorie": "potassium",
        "nom": "Carence potassium — Bordures feuilles brunies",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "brulure_bordures"},
            {"field": "sol.potassium", "op": "lte", "value": 0.15},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence potassium — bordures foliaires",
                "message": "Brûlure marginale feuilles âgées = symptôme carence K classique. Fréquent sols sableux."}],
            "risque": {"score": 0.82, "libelle": "Carence K"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "KCl en couverture urgence",
                "produit": "KCl 60% K2O", "dose": "50 kg/ha",
                "urgence_jours": 7}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "FER-GEN-010",
        "categorie": "fertilisation", "sous_categorie": "micronutriment",
        "nom": "Carence zinc — Petites feuilles rosette",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs.symptomes", "op": "contains", "value": "petites_feuilles"},
            {"field": "sol.pH", "op": "gte", "value": 7.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence zinc probable",
                "message": "Petites feuilles + entrenœuds courts = carence Zn. Fréquent sols calcaires."}],
            "risque": {"score": 0.72, "libelle": "Carence Zn"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Sulfate de zinc foliaire",
                "produit": "ZnSO4 22% Zn", "dose": "0,5 kg/ha foliaire 2 fois"}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },

]
