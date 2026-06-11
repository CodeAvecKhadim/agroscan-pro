"""
Rules Engine V1 — Règles générales transversales
+40 règles : diagnostics intégrés, alertes multi-risques, gestion sol.
"""

GENERAL_RULES = [

    # ═══════════════════════════════════════════════════════════
    # SOL — gestion qualité
    # ═══════════════════════════════════════════════════════════
    {
        "code": "GEN-SOL-001",
        "categorie": "fertilisation", "sous_categorie": "sol_general",
        "nom": "Sol salin — Réduction rendement all crops",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.conductivite", "op": "gte", "value": 6.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Sol très salin > 6 dS/m",
                "message": "CE > 6 dS/m = rendement réduit 50-100% selon culture. Lessivage + gypse + drainage obligatoire."}],
            "risque": {"score": 0.90, "libelle": "Salinité critique"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Lessivage sel sol salin",
                    "detail": "Irrigation abondante 150-200 mm/ha pour lessiver sel en profondeur. Drain nécessaire."},
                {"priorite": 2, "type": "fertilisation", "titre": "Gypse sol sodique",
                    "detail": "Gypse 2-4 t/ha si Na échangeable. Remplacement Na par Ca favorise floculation."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-SOL-002",
        "categorie": "fertilisation", "sous_categorie": "sol_general",
        "nom": "MO sol très faible — Dégradation structure",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.matiere_organique", "op": "lte", "value": 0.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "MO sol < 0.5% — Dégradation sévère",
                "message": "MO < 0.5% = sol fragile, peu de rétention eau, faible activité biologique. Agroforesterie + compost urgent."}],
            "risque": {"score": 0.82, "libelle": "Dégradation sol avancée"},
            "recommandations": [
                {"priorite": 1, "type": "fertilisation", "titre": "Apport compost/fumier urgent",
                    "detail": "10-20 t/ha fumier ou compost bien décomposé. Incorporer avant semis."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Couverture végétale permanente",
                    "detail": "Résidus de récolte au sol + légumineuses couvertes inter-saison."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-SOL-003",
        "categorie": "fertilisation", "sous_categorie": "sol_general",
        "nom": "Compaction sol — Tassement profond",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.texture", "op": "in", "value": ["argileuse", "argilo_limoneuse", "argilo_limoneux"]},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Risque compaction sol argileux sec",
                "message": "Sol argileux sec + passages engins = compaction durée. Racines bloquées = rendement -20-40%."}],
            "risque": {"score": 0.72, "libelle": "Compaction sol argileux"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Éviter passages sur sol sec argileux",
                "detail": "Travailler sol après pluie légère. Sous-solage 1/3 ans si compaction historique."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.72, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # IRRIGATION — efficience eau
    # ═══════════════════════════════════════════════════════════
    {
        "code": "GEN-IRR-001",
        "categorie": "irrigation", "sous_categorie": "efficience",
        "nom": "Stress hydrique cumulé — Score DSI > 4",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "lte", "value": 5},
            {"field": "meteo.etp", "op": "gte", "value": 5.5},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
            {"field": "sol.humidite", "op": "lte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Déficit stress combiné — Irrigation urgente",
                "message": "4 indicateurs simultanés = stress hydrique extrême. Irrigation d'urgence toutes cultures actives."}],
            "risque": {"score": 0.92, "libelle": "Stress quadruple indicateurs"},
            "recommandations": [{"priorite": 1, "type": "irrigation",
                "titre": "Irrigation priorité maximale",
                "detail": "Toute culture en phase végétative/floraison doit être irriguée dans les 12-24h.",
                "urgence_jours": 1}],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.90, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-IRR-002",
        "categorie": "irrigation", "sous_categorie": "efficience",
        "nom": "Nappe souterraine basse — Restriction eau",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [3, 4, 5],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.etp", "op": "gte", "value": 7.0},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 2},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Saison sèche — restriction eau potentielle",
                "message": "ETP > 7 + quasi pas de pluie = nappe descendante. Prioriser eau cultures haute valeur."}],
            "risque": {"score": 0.80, "libelle": "Restriction ressource eau"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Irrigation localisée goutte-à-goutte",
                    "detail": "Goutte-à-goutte = 40-60% économie eau vs aspersion. Priorité saison sèche."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Mulch organique obligatoire",
                    "detail": "10 cm mulch = réduit ETP sol de 30%. Paille, résidus, feuilles mortes."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # MÉTÉO — alertes intégrées
    # ═══════════════════════════════════════════════════════════
    {
        "code": "GEN-MET-001",
        "categorie": "meteo", "sous_categorie": "alerte_integree",
        "nom": "Triple stress thermique-hydrique-salin",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 36},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 3},
            {"field": "sol.conductivite", "op": "gte", "value": 3.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Triple stress chaleur+sécheresse+salinité",
                "message": "T > 36°C + sec + sol salin = triple stress = perte rendement 60-80%. Actions d'urgence multiples."}],
            "risque": {"score": 0.95, "libelle": "Triple stress catastrophique"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Irrigation fractionnée urgence",
                    "detail": "Petites doses fréquentes pour ne pas aggraver salinité. Eau < 1 dS/m si possible."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Ombrage d'urgence",
                    "detail": "Filet ombrage 50% + mulch sol. Cultures annuelles: envisager abandon partiel."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-MET-002",
        "categorie": "meteo", "sous_categorie": "alerte_integree",
        "nom": "Alerte ravageurs migrateurs — Saison propice",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [5, 6, 10, 11],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.vent", "op": "between", "value": 15, "value2": 40},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 60},
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 35},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Conditions propices ravageurs migrateurs",
                "message": "Vent 15-40 km/h + T + humidité = arrivée noctuelles, acridiens migrateurs possible. Surveiller."}],
            "risque": {"score": 0.60, "libelle": "Ravageurs migrateurs possibles"},
            "recommandations": [{"priorite": 1, "type": "surveillance",
                "titre": "Surveillance ravageurs migrateurs",
                "detail": "Inspection matinale. Alerter DGPV/DAPSA si criquet pèlerin ou noctuelle de l'armée observés."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.62, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RAVAGEURS — alertes générales complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "GEN-RAV-001",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Pullulation insectes fleur — Pollinisateurs-nuisibles coexistence",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "between", "value": 25, "value2": 35},
            {"field": "meteo.humidite_rel", "op": "between", "value": 50, "value2": 75},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Floraison — Traiter soir pas pendant floraison",
                "message": "Pollinisateurs actifs en journée. Tout insecticide pendant floraison = perte pollinisateurs = moins de fruits."}],
            "risque": {"score": 0.55, "libelle": "Pollinisateurs floraison"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Traitement insecticide soir uniquement",
                "detail": "Traiter exclusivement après 18h ou avant 7h du matin. Jamais pendant pleine floraison."}],
        },
        "gravite": "moyenne", "priorite": 4, "confiance": 0.85, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-RAV-002",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Résistance insecticides — Rotation molécules",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Prévention résistance insecticides",
                "message": "Même molécule > 2x/cycle = risque résistance accéléré. Rotation groupes chimiques recommandée."}],
            "risque": {"score": 0.40, "libelle": "Risque résistance"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Rotation insecticides groupes différents",
                "detail": "OP → Pyrethroïde → Neonicotinoïde → rotation. Jamais même groupe 2 traitements consécutifs."}],
        },
        "gravite": "faible", "priorite": 3, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-RAV-003",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Nématodes sol — Galles racines cultures maraîchères",
        "cultures": ["Tomate", "Aubergine", "Gombo", "Oignon", "Piment"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.temperature", "op": "gte", "value": 25},
            {"field": "sol.texture", "op": "in", "value": ["sableuse", "sablo_limoneuse"]},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Nématodes galles — Sol sableux chaud",
                "message": "Sol sableux + T > 25°C = Meloidogyne actif. Galles racines = blocage eau+nutriments."}],
            "risque": {"score": 0.80, "libelle": "Nématodes Meloidogyne"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Solarisation sol anti-nématodes",
                    "detail": "Plastique transparent sur sol humide 4-6 semaines = T > 50°C = mort nématodes."},
                {"priorite": 2, "type": "traitement", "titre": "Fosthiazate ou Carbofuran nématicides",
                    "detail": "Fosthiazate (Nemathorin) 5 kg/ha ou Carbofuran 5G si solarisation impossible."},
            ],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-RAV-004",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Oiseaux granivores — Protection épiaison universelle",
        "cultures": ["Mil", "Sorgho", "Riz", "Maïs"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["epiaison", "maturation"],
        "mois_applicables": [9, 10],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Oiseaux granivores épiaison — Protection urgente",
                "message": "Quelea quelea + Estrilda + tourterelles actifs à épiaison. Perte 100% en 48h si pas protégé."}],
            "risque": {"score": 0.90, "libelle": "Oiseaux granivores"},
            "recommandations": [
                {"priorite": 1, "type": "mesure_culturale", "titre": "Gardiennage continu épiaison",
                    "detail": "Gardiennage dès 6h-18h. Fils nylon brillant + épouvantails + pétards = combinaison efficace."},
                {"priorite": 2, "type": "mesure_culturale", "titre": "Filet oiseaux si petit champ",
                    "detail": "Filet polyéthylène < 1 ha = solution fiable. Investissement rentabilisé en 1-2 saisons."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-RAV-005",
        "categorie": "ravageur", "sous_categorie": "general",
        "nom": "Termites — Dégâts semis et racines saison sèche",
        "cultures": ["Maïs", "Sorgho", "Mil", "Arachide", "Manioc"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["levee"],
        "mois_applicables": [3, 4, 5, 11, 12, 1, 2],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.humidite", "op": "lte", "value": 25},
            {"field": "meteo.temp_air", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Termites actifs — Sol sec chaud",
                "message": "Sol sec + chaleur = termites actifs. Semences ou racines attaquées. Manque à lever."}],
            "risque": {"score": 0.75, "libelle": "Dégâts termites semis"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Insecticide sol contre termites",
                "detail": "Imidaclopride 70WS en traitement semences (5 ml/kg). Ou chlorpyrifos sol 1 L/ha."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # CALENDRIER — règles intégrées
    # ═══════════════════════════════════════════════════════════
    {
        "code": "GEN-CAL-001",
        "categorie": "calendrier", "sous_categorie": "general",
        "nom": "Désherbage chimique pré-levée — Fenêtre application",
        "cultures": ["Maïs", "Sorgho", "Mil", "Arachide", "Niébé"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["semis"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "between", "value": 5, "value2": 20},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Fenêtre herbicide pré-levée après pluie légère",
                "message": "Pluie légère = sol humide = herbicide pré-levée efficace. Traiter dans les 3 jours post-semis."}],
            "risque": {"score": 0.25, "libelle": "Opportunité herbicide pré-levée"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Pendiméthaline pré-levée",
                "detail": "Pendiméthaline 1.5 L/ha ou Atrazine 1 kg/ha (maïs). Sol humide, pas séché. < 3 jours post-semis."}],
        },
        "gravite": "faible", "priorite": 3, "confiance": 0.78, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-CAL-002",
        "categorie": "calendrier", "sous_categorie": "general",
        "nom": "Traitement semences — Rappel systématique",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["semis"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 25},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Traitement semences avant semis",
                "message": "Traitement semences = investissement minimal + protection maximale levée. ROI 1:10."}],
            "risque": {"score": 0.30, "libelle": "Semences non traitées"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Programme traitement semences",
                "detail": "Thirame 3g/kg (fongicide) + Imidaclopride 5ml/kg (insecticide). Mélanger avant semis."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-CAL-003",
        "categorie": "calendrier", "sous_categorie": "general",
        "nom": "Récolte matinale — Qualité maximale fruits",
        "cultures": ["Tomate", "Concombre", "Piment", "Aubergine", "Gombo"], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 28},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Récolter tôt matin — Qualité + conservation",
                "message": "Récolte avant 10h = température fruits basse = moins d'éthylène = 2x plus longue conservation."}],
            "risque": {"score": 0.20, "libelle": "Qualité récolte"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Récolte 6h-9h matin",
                "detail": "Récolter avant les heures chaudes. Stocker à l'ombre immédiatement. Ne pas exposer au soleil."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.82, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # RENDEMENT — alertes générales
    # ═══════════════════════════════════════════════════════════
    {
        "code": "GEN-REN-001",
        "categorie": "rendement", "sous_categorie": "general",
        "nom": "Attaque multiple simultanée — Réduction synergique",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs_ravageurs", "op": "not_null"},
            {"field": "obs_symptomes", "op": "not_null"},
            {"field": "meteo.pluie_7j", "op": "lte", "value": 10},
        ]},
        "actions": {
            "alertes": [{"niveau": "critique", "titre": "Attaques multiples simultanées",
                "message": "Ravageur + maladie + sécheresse = synergie destructive. Pertes peuvent être totales (80-100%)."}],
            "risque": {"score": 0.92, "libelle": "Attaques multiples synergiques"},
            "recommandations": [
                {"priorite": 1, "type": "irrigation", "titre": "Lever stress hydrique en premier",
                    "detail": "Plante stressée = immunité nulle. Irriguer avant tout traitement."},
                {"priorite": 2, "type": "traitement", "titre": "Traitement intégré ravageur + maladie",
                    "detail": "Tank-mix insecticide + fongicide si pas de contre-indication. Réduire nb passages."},
            ],
        },
        "gravite": "critique", "priorite": 10, "confiance": 0.88, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-REN-002",
        "categorie": "rendement", "sous_categorie": "general",
        "nom": "Stade végétatif critique — Protection maximale",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["floraison", "fructification"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_air", "op": "gte", "value": 27},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Stade floraison-fructification — Vigilance renforcée",
                "message": "Floraison et fructification = fenêtre 10-20 jours. Tout stress ici = perte définitive rendement."}],
            "risque": {"score": 0.60, "libelle": "Stade critique tous stress"},
            "recommandations": [{"priorite": 1, "type": "surveillance",
                "titre": "Inspection quotidienne stade critique",
                "detail": "Inspecter matin + soir. Résoudre tout stress sous 48h : eau, ravageurs, maladies."}],
        },
        "gravite": "moyenne", "priorite": 6, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-REN-003",
        "categorie": "rendement", "sous_categorie": "general",
        "nom": "Variétés améliorées vs locales — Gain potentiel",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": ["semis"], "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 15},
        ]},
        "actions": {
            "alertes": [{"niveau": "faible", "titre": "Variétés améliorées = +30-50% rendement potentiel",
                "message": "Variétés certifiées améliorées = rendement 30-50% supérieur aux variétés locales selon cultures."}],
            "risque": {"score": 0.20, "libelle": "Sous-performance variétés locales"},
            "recommandations": [{"priorite": 1, "type": "planification",
                "titre": "Essayer variétés améliorées sur 20% surface",
                "detail": "Tester 20% surface en variétés certifiées. Conserver 80% en variétés connues pour sécurité."}],
        },
        "gravite": "faible", "priorite": 2, "confiance": 0.75, "plan_requis": "premium",
    },

    # ═══════════════════════════════════════════════════════════
    # MALADIES — alertes générales complémentaires
    # ═══════════════════════════════════════════════════════════
    {
        "code": "GEN-MAL-001",
        "categorie": "maladie", "sous_categorie": "general",
        "nom": "Symptômes chlorose générale — Carence ou maladie",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "obs_symptomes", "op": "not_null"},
            {"field": "sol.pH", "op": "lte", "value": 5.5},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Chlorose = sol acide probable",
                "message": "Chlorose + sol acide = carence Fe/Mn/Zn amplifiée par pH bas OU maladie racinaire favorisée."}],
            "risque": {"score": 0.75, "libelle": "Chlorose double cause"},
            "recommandations": [
                {"priorite": 1, "type": "fertilisation", "titre": "Chaulage + microéléments foliaires",
                    "detail": "Chaux pour remonter pH. Sulfate de zinc 2 kg/ha + sulfate de fer 1 kg/ha foliaire."},
            ],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.75, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-MAL-002",
        "categorie": "maladie", "sous_categorie": "general",
        "nom": "Résidus pathogènes — Rotation obligatoire",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None,
        "mois_applicables": [11, 12, 1],
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "between", "value": 5.0, "value2": 7.0},
            {"field": "sol.humidite", "op": "gte", "value": 40},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Inter-saison — Gestion résidus pathogènes",
                "message": "Résidus cultures laissés au sol = inoculum maladies saison suivante. Enfouir ou brûler."}],
            "risque": {"score": 0.60, "libelle": "Inoculum résidus"},
            "recommandations": [{"priorite": 1, "type": "mesure_culturale",
                "titre": "Enfouissement résidus inter-saison",
                "detail": "Labourer profond 25-30 cm pour enfouir résidus. Ou brûler si maladie sévère saison passée."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.72, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-MAL-003",
        "categorie": "maladie", "sous_categorie": "general",
        "nom": "Chaleur + humidité nuit — Maladies fongiques nocturnes",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.temp_min", "op": "gte", "value": 22},
            {"field": "meteo.humidite_rel", "op": "gte", "value": 85},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Nuits chaudes et humides — Explosion fongique",
                "message": "T nuit > 22°C + HR > 85% = sporulation massive pendant la nuit. Symptômes visibles au matin."}],
            "risque": {"score": 0.82, "libelle": "Sporulation nocturne"},
            "recommandations": [{"priorite": 1, "type": "traitement",
                "titre": "Traitement préventif coucher soleil",
                "detail": "Traitement fongicide en fin d'après-midi (16-18h) couvre la nuit = fenêtre optimale."}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.80, "plan_requis": "gratuit",
    },

    # ═══════════════════════════════════════════════════════════
    # FERTILISATION — règles systémiques
    # ═══════════════════════════════════════════════════════════
    {
        "code": "GEN-FER-001",
        "categorie": "fertilisation", "sous_categorie": "general",
        "nom": "Fertilisation sous pluie — Volatilisation urée",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_24h", "op": "gte", "value": 30},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Pluie forte — Ne pas fertiliser",
                "message": "Pluie > 30 mm = lessivage N + volatilisation urée = gaspillage. Reporter fertilisation 2-3 jours."}],
            "risque": {"score": 0.60, "libelle": "Pertes fertilisant pluie"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Reporter fertilisation après pluie",
                "detail": "Attendre 2-3 jours après pluie forte. Sol ressuyé = incorporation optimale. Enfoui léger si urée."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-FER-002",
        "categorie": "fertilisation", "sous_categorie": "general",
        "nom": "Fertilisation fractionnée — Efficience azote",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None, "stades_applicables": None, "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "meteo.pluie_7j", "op": "gte", "value": 20},
            {"field": "sol.texture", "op": "in", "value": ["sableuse", "sablo_limoneuse"]},
        ]},
        "actions": {
            "alertes": [{"niveau": "moyenne", "titre": "Sol sableux — Fractionner azote",
                "message": "Sol sableux = faible rétention N. 1 apport unique = 30-40% lessivé. Fractionner en 2-3 applications."}],
            "risque": {"score": 0.62, "libelle": "Lessivage N sol sableux"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Programme N fractionné 3x",
                "detail": "33% levée + 33% tallage + 33% montaison. Chaque dose après pluie légère."}],
        },
        "gravite": "moyenne", "priorite": 5, "confiance": 0.80, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-FER-003",
        "categorie": "fertilisation", "sous_categorie": "general",
        "nom": "Feuilles violacées — Carence phosphore généralisée",
        "cultures": [], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.phosphore", "op": "lte", "value": 10},
            {"field": "sol.pH", "op": "lte", "value": 5.8},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Carence P probable — Teintes violacées",
                "message": "P sol < 10 ppm + pH acide = carence P. Nervures et tiges violacées = anthocyanine stress P."}],
            "risque": {"score": 0.80, "libelle": "Carence phosphore"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Triple super phosphate + chaulage",
                "detail": "TSP 50 kg/ha. pH acide bloque P : chaulage d'abord pour libérer P existant.",
                "urgence_jours": 7}],
        },
        "gravite": "elevee", "priorite": 8, "confiance": 0.82, "plan_requis": "gratuit",
    },
    {
        "code": "GEN-FER-004",
        "categorie": "fertilisation", "sous_categorie": "general",
        "nom": "Carence Zn — Nanisme petites feuilles",
        "cultures": ["Maïs", "Riz", "Sorgho", "Mil"], "ravageurs": [],
        "zones_applicables": None,
        "stades_applicables": ["levee", "croissance_vegetative"],
        "mois_applicables": None,
        "conditions": {"operator": "AND", "clauses": [
            {"field": "sol.pH", "op": "gte", "value": 7.5},
            {"field": "sol.matiere_organique", "op": "lte", "value": 1.0},
        ]},
        "actions": {
            "alertes": [{"niveau": "elevee", "titre": "Sol alcalin + MO basse = carence Zn",
                "message": "pH > 7.5 + MO basse = Zn bloqué = nanisme des jeunes feuilles (petites, en rosette)."}],
            "risque": {"score": 0.78, "libelle": "Carence Zn sol alcalin"},
            "recommandations": [{"priorite": 1, "type": "fertilisation",
                "titre": "Sulfate de zinc correcteur",
                "detail": "Sulfate de zinc 5 kg/ha au sol ou 0.5% foliaire 2 applications à 10 jours."}],
        },
        "gravite": "elevee", "priorite": 7, "confiance": 0.78, "plan_requis": "gratuit",
    },

]
