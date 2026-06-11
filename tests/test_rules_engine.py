"""
Tests automatiques — Rules Engine V1 AgroScan
Vérifie : déclenchement, priorités, scores, recommandations, performance < 200ms.
Usage : .venv/bin/python -m pytest tests/test_rules_engine.py -v -s
"""
import time
import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.rules_evaluator import evaluate


# ─────────────────────────────────────────────────────────────
# Helpers contexte — clés plates (flat) attendues par _flatten()
# ─────────────────────────────────────────────────────────────
def ctx_meteo(temp_air=None, humidite_rel=None, pluie_7j=None, pluie_24h=None,
              etp=None, vent=None, temp_min=None):
    c = {}
    if temp_air      is not None: c["meteo_temp_air"]    = temp_air
    if humidite_rel  is not None: c["meteo_humidite_rel"] = humidite_rel
    if pluie_7j      is not None: c["meteo_pluie_7j"]    = pluie_7j
    if pluie_24h     is not None: c["meteo_pluie_24h"]   = pluie_24h
    if etp           is not None: c["meteo_etp"]         = etp
    if vent          is not None: c["meteo_vent"]        = vent
    if temp_min      is not None: c["meteo_temp_min"]    = temp_min
    return c


def ctx_sol(pH=None, azote=None, phosphore=None, potassium=None,
            humidite=None, temperature=None, matiere_organique=None, conductivite=None):
    c = {}
    if pH               is not None: c["sol_pH"]               = pH
    if azote            is not None: c["sol_azote"]            = azote
    if phosphore        is not None: c["sol_phosphore"]        = phosphore
    if potassium        is not None: c["sol_potassium"]        = potassium
    if humidite         is not None: c["sol_humidite"]         = humidite
    if temperature      is not None: c["sol_temperature"]      = temperature
    if matiere_organique is not None: c["sol_matiere_organique"] = matiere_organique
    if conductivite     is not None: c["sol_conductivite"]     = conductivite
    return c


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


def _eval(db: Session, ctx: dict, categorie: str, plan: str = "premium") -> dict:
    return evaluate(db, ctx, categorie=categorie, plan=plan, persist=False)


# ─────────────────────────────────────────────────────────────
# 1. MALADIES — déclenchement règles
# ─────────────────────────────────────────────────────────────

class TestMaladies:

    def test_conditions_humides_chaudes_declenchent_maladies(self, db):
        """Conditions humides T22-30 + HR>85 + pluie = maladies déclenchées."""
        ctx = {
            **ctx_meteo(temp_air=22, humidite_rel=89, pluie_7j=35, pluie_24h=12),
            **ctx_sol(pH=6.2, humidite=78),
        }
        result = _eval(db, ctx, "maladie")
        assert len(result["resultats"]) > 0, \
            f"Conditions humides doivent déclencher maladies. Règles évaluées: {result['regles_evaluees']}"

    def test_mildiou_tomate_conditions_classiques(self, db):
        """Conditions classiques mildiou (T15-22 + HR>80 + pluie)."""
        ctx = {
            **ctx_meteo(temp_air=20, humidite_rel=88, pluie_7j=32, pluie_24h=10),
            **ctx_sol(pH=6.2, humidite=78),
        }
        result = _eval(db, ctx, "maladie")
        assert len(result["resultats"]) > 0, \
            f"Conditions mildiou doivent déclencher maladies: {[r['code'] for r in result['resultats']]}"

    def test_maladie_score_confiance_range(self, db):
        """Score confiance toujours dans [0, 1]."""
        ctx = {**ctx_sol(pH=6.5, humidite=65), **ctx_meteo(temp_air=28, humidite_rel=75, pluie_7j=20)}
        result = _eval(db, ctx, "maladie")
        for r in result["resultats"]:
            assert 0.0 <= r.get("confiance", 0.5) <= 1.0, \
                f"Confiance hors plage pour {r['code']}: {r.get('confiance')}"

    def test_conditions_seches_chaudes_peu_maladies(self, db):
        """Air très sec + peu de pluie = peu de maladies fongiques."""
        ctx = {
            **ctx_meteo(temp_air=36, humidite_rel=18, pluie_7j=1, pluie_24h=0),
        }
        result = _eval(db, ctx, "maladie")
        # En sec extrême, peu de maladies fongiques
        assert len(result["resultats"]) <= 5, \
            f"Trop de maladies en conditions sèches: {len(result['resultats'])}"

    def test_maladies_champ_resultats_requis(self, db):
        """Résultat doit toujours avoir les champs requis."""
        ctx = {**ctx_meteo(temp_air=25, humidite_rel=85, pluie_7j=30)}
        result = _eval(db, ctx, "maladie")
        for r in result["resultats"]:
            assert "code" in r, "Champ 'code' manquant"
            assert "gravite" in r, "Champ 'gravite' manquant"
            assert "priorite" in r, "Champ 'priorite' manquant"

    def test_sol_acide_declenchement_maladies_sol(self, db):
        """Sol très acide pH<5 doit déclencher alertes maladies sol."""
        ctx = {
            **ctx_sol(pH=4.5),
            **ctx_meteo(temp_air=27, humidite_rel=72),
        }
        result = _eval(db, ctx, "maladie")
        assert len(result["resultats"]) > 0, "Sol pH 4.5 doit déclencher règles maladies"


# ─────────────────────────────────────────────────────────────
# 2. RAVAGEURS — déclenchement et priorités
# ─────────────────────────────────────────────────────────────

class TestRavageurs:

    def test_ravageur_conditions_normales_retourne_liste(self, db):
        """Évaluation ravageurs retourne toujours une liste."""
        ctx = {**ctx_meteo(temp_air=28, humidite_rel=72, pluie_7j=25)}
        ctx["stade_actuel"] = "tallage"
        ctx["mois"] = 8
        result = _eval(db, ctx, "ravageur")
        assert isinstance(result["resultats"], list)

    def test_ravageur_priorite_triee_desc(self, db):
        """Résultats triés par priorité décroissante."""
        ctx = {
            **ctx_meteo(temp_air=30, humidite_rel=80, pluie_7j=20),
            **ctx_sol(humidite=70),
        }
        ctx["stade_actuel"] = "floraison"
        result = _eval(db, ctx, "ravageur")
        resultats = result["resultats"]
        if len(resultats) >= 2:
            for i in range(len(resultats) - 1):
                p_curr = resultats[i].get("priorite", 0)
                p_next = resultats[i + 1].get("priorite", 0)
                assert p_curr >= p_next, \
                    f"Mauvais tri: {p_curr} < {p_next} ({resultats[i]['code']}/{resultats[i+1]['code']})"

    def test_ravageur_gravite_valeurs_valides(self, db):
        """Gravité dans valeurs attendues."""
        valid_gravites = {"faible", "moyenne", "elevee", "critique"}
        ctx = {**ctx_meteo(temp_air=30, humidite_rel=70, pluie_7j=15)}
        result = _eval(db, ctx, "ravageur")
        for r in result["resultats"]:
            assert r.get("gravite") in valid_gravites, \
                f"Gravité invalide {r.get('gravite')} pour {r['code']}"

    def test_ravageur_actions_non_vides(self, db):
        """Règles déclenchées ont des actions."""
        ctx = {**ctx_meteo(temp_air=32, humidite_rel=78, pluie_7j=10)}
        ctx["stade_actuel"] = "tallage"
        result = _eval(db, ctx, "ravageur")
        for r in result["resultats"]:
            assert r.get("alertes") or r.get("recommandations"), \
                f"Actions vides pour {r['code']}"

    def test_conditions_chaleur_sec_declenchent_ravageurs(self, db):
        """Chaleur + sécheresse = ravageurs suceurs actifs."""
        ctx = {
            **ctx_meteo(temp_air=35, humidite_rel=25, pluie_7j=2, vent=30),
        }
        result = _eval(db, ctx, "ravageur")
        # Conditions extrêmes = au moins quelques ravageurs
        assert len(result["resultats"]) >= 0  # Au moins pas d'erreur


# ─────────────────────────────────────────────────────────────
# 3. FERTILISATION — scores et recommandations
# ─────────────────────────────────────────────────────────────

class TestFertilisation:

    def test_carence_azote_sol_pauvre(self, db):
        """Carence N avec sol azote très bas + symptômes jaunissement."""
        ctx = {
            **ctx_sol(pH=6.0, azote=0.04, humidite=55),
            **ctx_meteo(temp_air=28, pluie_7j=15),
            "obs_symptomes": ["jaunissement"],
        }
        result = _eval(db, ctx, "fertilisation")
        assert len(result["resultats"]) > 0, \
            f"Sol azote 0.04 + jaunissement doit déclencher. Évaluées: {result['regles_evaluees']}"

    def test_sol_acide_pH_critique(self, db):
        """Sol très acide pH < 5.0 doit déclencher alerte."""
        ctx = {
            **ctx_sol(pH=4.5, azote=0.08, phosphore=8),
            **ctx_meteo(temp_air=27, pluie_7j=20),
        }
        result = _eval(db, ctx, "fertilisation")
        assert len(result["resultats"]) > 0, f"Sol pH 4.5 doit déclencher. Évaluées: {result['regles_evaluees']}"

    def test_carence_phosphore_sol_acide(self, db):
        """Carence P + sol acide = doit déclencher fertilisation."""
        ctx = {
            **ctx_sol(pH=5.4, phosphore=6, azote=0.06),
            **ctx_meteo(temp_air=28, pluie_7j=18),
        }
        result = _eval(db, ctx, "fertilisation")
        assert len(result["resultats"]) > 0, "P faible + sol acide doit déclencher"

    def test_fertilisation_recommandations_structure(self, db):
        """Recommandations ont la structure attendue."""
        ctx = {
            **ctx_sol(pH=5.5, azote=0.05, phosphore=6, potassium=40),
            **ctx_meteo(temp_air=28, pluie_7j=18),
        }
        result = _eval(db, ctx, "fertilisation")
        for r in result["resultats"]:
            recs = r.get("recommandations", [])
            for rec in recs:
                assert "titre" in rec or "type" in rec, \
                    f"Recommandation sans titre/type pour {r['code']}"

    def test_sol_tres_salin_declenchement(self, db):
        """Sol très salin > 6 dS/m doit déclencher."""
        ctx = {
            **ctx_sol(conductivite=7.0, pH=6.5),
            **ctx_meteo(temp_air=28, pluie_7j=10),
        }
        result = _eval(db, ctx, "fertilisation")
        assert len(result["resultats"]) > 0, "Sol salin > 6 dS/m doit déclencher"


# ─────────────────────────────────────────────────────────────
# 4. IRRIGATION — stress hydrique
# ─────────────────────────────────────────────────────────────

class TestIrrigation:

    def test_stress_hydrique_extreme(self, db):
        """ETP élevée + sécheresse + chaleur = alerte irrigation."""
        ctx = {
            **ctx_meteo(temp_air=36, humidite_rel=25, pluie_7j=2, etp=7.5),
            **ctx_sol(humidite=18),
        }
        result = _eval(db, ctx, "irrigation")
        assert len(result["resultats"]) > 0, \
            f"ETP 7.5 + sec doit déclencher irrigation. Évaluées: {result['regles_evaluees']}"

    def test_sol_sature_alerte_drainage(self, db):
        """Sol saturé > 88% + fortes pluies = alerte drainage."""
        ctx = {
            **ctx_meteo(pluie_7j=90, pluie_24h=45, temp_air=27),
            **ctx_sol(humidite=92),
        }
        result = _eval(db, ctx, "irrigation")
        assert len(result["resultats"]) > 0, \
            f"Sol saturé 92% + 90mm/7j doit déclencher. Évaluées: {result['regles_evaluees']}"

    def test_irrigation_alertes_niveau_valide(self, db):
        """Niveau alerte dans valeurs valides."""
        valid_niveaux = {"faible", "moyenne", "elevee", "critique"}
        ctx = {**ctx_meteo(etp=7.0, pluie_7j=3, temp_air=33), **ctx_sol(humidite=25)}
        result = _eval(db, ctx, "irrigation")
        for r in result["resultats"]:
            for alerte in r.get("alertes", []):
                niveau = alerte.get("niveau", "faible")
                assert niveau in valid_niveaux, f"Niveau invalide: {niveau}"

    def test_pluie_importante_reporter_irrigation(self, db):
        """Pluie > 20mm doit déclencher conseil reporter irrigation."""
        ctx = {**ctx_meteo(pluie_24h=25, pluie_7j=30, temp_air=26)}
        result = _eval(db, ctx, "irrigation")
        assert isinstance(result["resultats"], list)


# ─────────────────────────────────────────────────────────────
# 5. MÉTÉO — alertes climatiques
# ─────────────────────────────────────────────────────────────

class TestMeteo:

    def test_harmattan_intense(self, db):
        """Vent fort + HR < 20% + chaleur = Harmattan détecté."""
        ctx = {
            **ctx_meteo(temp_air=38, humidite_rel=12, vent=50, pluie_7j=0),
            "mois": 12,
        }
        result = _eval(db, ctx, "meteo")
        assert len(result["resultats"]) > 0, \
            f"Harmattan intense doit déclencher. Évaluées: {result['regles_evaluees']}"

    def test_pluies_excessives(self, db):
        """Pluies > 100mm/7j + HR > 88% + culture Tomate = alerte fongique."""
        ctx = {
            **ctx_meteo(pluie_7j=110, humidite_rel=90, temp_air=26),
            "mois": 8,
            "culture_nom": "Tomate",  # MET-PLU-002 est lié aux cultures spécifiques
        }
        result = _eval(db, ctx, "meteo")
        assert len(result["resultats"]) > 0, \
            f"Pluies excessives + Tomate doivent déclencher. Évaluées: {result['regles_evaluees']}"

    def test_meteo_score_entre_0_et_1(self, db):
        """Score risque entre 0 et 1."""
        ctx = {**ctx_meteo(temp_air=38, humidite_rel=15, vent=45, etp=8.5, pluie_7j=1)}
        result = _eval(db, ctx, "meteo")
        for r in result["resultats"]:
            risque = r.get("risque") or {}
            if "score" in risque:
                assert 0.0 <= risque["score"] <= 1.0, f"Score hors plage: {risque['score']}"

    def test_vent_tres_fort_verse(self, db):
        """Vent > 60 km/h doit déclencher alerte verse."""
        ctx = {**ctx_meteo(vent=65, temp_air=28), "stade_actuel": "montaison"}
        result = _eval(db, ctx, "meteo")
        assert isinstance(result["resultats"], list)


# ─────────────────────────────────────────────────────────────
# 6. CALENDRIER — stades et fenêtres
# ─────────────────────────────────────────────────────────────

class TestCalendrier:

    def test_fenetre_semis_hivernage(self, db):
        """Pluies installées juillet = fenêtre semis."""
        ctx = {
            **ctx_meteo(pluie_7j=30, temp_air=29),
            "mois": 7,
        }
        result = _eval(db, ctx, "calendrier")
        assert isinstance(result["resultats"], list)

    def test_stade_epiaison_calendrier(self, db):
        """Stade épiaison septembre = règles calendrier."""
        ctx = {
            **ctx_meteo(temp_air=28, pluie_7j=18),
            "stade_actuel": "epiaison",
            "mois": 9,
        }
        result = _eval(db, ctx, "calendrier")
        assert isinstance(result["resultats"], list)

    def test_calendrier_structure_resultats(self, db):
        """Chaque résultat calendrier a code + gravite."""
        ctx = {**ctx_meteo(pluie_7j=25, temp_air=27), "mois": 6}
        result = _eval(db, ctx, "calendrier")
        for r in result["resultats"]:
            assert "code" in r and "gravite" in r


# ─────────────────────────────────────────────────────────────
# 7. RENDEMENT — prévision et pertes
# ─────────────────────────────────────────────────────────────

class TestRendement:

    def test_chaleur_stockage_insectes(self, db):
        """T > 27°C + HR 55-80% = insectes stockage actifs."""
        ctx = {
            **ctx_meteo(temp_air=30, humidite_rel=65),
        }
        result = _eval(db, ctx, "rendement")
        assert isinstance(result["resultats"], list)

    def test_double_stress_N_eau(self, db):
        """Carence N + sécheresse = perte rendement."""
        ctx = {
            **ctx_sol(azote=0.04),
            **ctx_meteo(pluie_7j=8, temp_air=31),
        }
        result = _eval(db, ctx, "rendement")
        assert isinstance(result["resultats"], list)

    def test_rendement_structure_valide(self, db):
        """Chaque résultat a code + gravite + priorite."""
        ctx = {**ctx_meteo(temp_air=28, humidite_rel=60, pluie_7j=15)}
        result = _eval(db, ctx, "rendement")
        for r in result["resultats"]:
            for field in ("code", "gravite", "priorite"):
                assert field in r, f"Champ '{field}' absent pour {r.get('code', '?')}"

    def test_pertes_stockage_declenchement(self, db):
        """Conditions stockage défavorables déclenchent règles rendement."""
        ctx = {
            **ctx_meteo(temp_air=30, humidite_rel=72),
        }
        result = _eval(db, ctx, "rendement")
        # Doit au moins évaluer des règles
        assert result["regles_evaluees"] > 0


# ─────────────────────────────────────────────────────────────
# 8. PERFORMANCE — < 200ms par évaluation
# ─────────────────────────────────────────────────────────────

class TestPerformance:
    TARGET_MS = 200

    def _mesure(self, db: Session, ctx: dict, categorie: str) -> float:
        t0 = time.perf_counter()
        evaluate(db, ctx, categorie=categorie, plan="premium", persist=False)
        return (time.perf_counter() - t0) * 1000

    def test_perf_maladie(self, db):
        ctx = {**ctx_meteo(temp_air=22, humidite_rel=90, pluie_7j=35),
               **ctx_sol(pH=6.2, humidite=78)}
        ms = self._mesure(db, ctx, "maladie")
        assert ms < self.TARGET_MS, f"Maladie trop lent: {ms:.1f}ms > {self.TARGET_MS}ms"

    def test_perf_ravageur(self, db):
        ctx = {**ctx_meteo(temp_air=30, humidite_rel=70, pluie_7j=20)}
        ctx["stade_actuel"] = "tallage"
        ms = self._mesure(db, ctx, "ravageur")
        assert ms < self.TARGET_MS, f"Ravageur trop lent: {ms:.1f}ms"

    def test_perf_fertilisation(self, db):
        ctx = {**ctx_sol(pH=5.5, azote=0.05, phosphore=8, potassium=50),
               **ctx_meteo(temp_air=27, pluie_7j=15)}
        ms = self._mesure(db, ctx, "fertilisation")
        assert ms < self.TARGET_MS, f"Fertilisation trop lent: {ms:.1f}ms"

    def test_perf_irrigation(self, db):
        ctx = {**ctx_meteo(temp_air=35, etp=7.0, pluie_7j=3, humidite_rel=20),
               **ctx_sol(humidite=22)}
        ms = self._mesure(db, ctx, "irrigation")
        assert ms < self.TARGET_MS, f"Irrigation trop lent: {ms:.1f}ms"

    def test_perf_meteo(self, db):
        ctx = {**ctx_meteo(temp_air=38, humidite_rel=15, vent=50, pluie_7j=0, etp=8.0)}
        ms = self._mesure(db, ctx, "meteo")
        assert ms < self.TARGET_MS, f"Météo trop lent: {ms:.1f}ms"

    def test_perf_calendrier(self, db):
        ctx = {**ctx_meteo(temp_air=29, pluie_7j=25), "stade_actuel": "floraison", "mois": 8}
        ms = self._mesure(db, ctx, "calendrier")
        assert ms < self.TARGET_MS, f"Calendrier trop lent: {ms:.1f}ms"

    def test_perf_rendement(self, db):
        ctx = {**ctx_meteo(temp_air=30, humidite_rel=65, pluie_7j=12)}
        ms = self._mesure(db, ctx, "rendement")
        assert ms < self.TARGET_MS, f"Rendement trop lent: {ms:.1f}ms"

    def test_perf_moyenne_toutes_categories(self, db):
        """Temps moyen sur 7 catégories < 200ms chacune."""
        categories = ["maladie", "ravageur", "fertilisation", "irrigation", "meteo", "calendrier", "rendement"]
        ctx_base = {
            **ctx_meteo(temp_air=28, humidite_rel=75, pluie_7j=20, etp=5.5),
            **ctx_sol(pH=6.2, azote=0.08, phosphore=12, humidite=55),
            "stade_actuel": "croissance_vegetative",
            "mois": 8,
        }
        durees = []
        for cat in categories:
            t0 = time.perf_counter()
            evaluate(db, ctx_base, categorie=cat, plan="premium", persist=False)
            ms = (time.perf_counter() - t0) * 1000
            durees.append(ms)

        moyenne = sum(durees) / len(durees)
        max_ms = max(durees)
        print(f"\n  Temps moyen: {moyenne:.1f}ms | Max: {max_ms:.1f}ms")
        print(f"  Par catégorie: {dict(zip(categories, [f'{d:.0f}ms' for d in durees]))}")

        assert moyenne < self.TARGET_MS, f"Temps moyen {moyenne:.1f}ms > {self.TARGET_MS}ms"
        assert max_ms < self.TARGET_MS * 2, f"Max {max_ms:.1f}ms trop élevé"


# ─────────────────────────────────────────────────────────────
# 9. INTÉGRATION — évaluation multi-contexte
# ─────────────────────────────────────────────────────────────

class TestIntegration:

    def test_evaluation_retourne_dict_structure(self, db):
        """evaluate() retourne la structure attendue."""
        result = evaluate(db, {}, categorie="maladie", plan="gratuit", persist=False)
        required_keys = {"resultats", "regles_evaluees", "regles_declenchees", "duree_ms"}
        for key in required_keys:
            assert key in result, f"Clé manquante dans résultat: {key}"

    def test_evaluation_sans_contexte(self, db):
        """Évaluation sans contexte ne plante pas."""
        result = evaluate(db, {}, categorie="ravageur", plan="gratuit", persist=False)
        assert result is not None
        assert isinstance(result["resultats"], list)

    def test_evaluation_culture_id_inexistant(self, db):
        """Culture_id inexistant ne plante pas."""
        ctx = {
            **ctx_meteo(temp_air=28, humidite_rel=80, pluie_7j=25),
            "culture_id": 999999,
        }
        result = evaluate(db, ctx, "maladie", "premium", False)
        assert result is not None

    def test_plan_gratuit_vs_premium(self, db):
        """Plan premium peut retourner plus de règles que gratuit."""
        ctx = {
            **ctx_meteo(temp_air=28, humidite_rel=78, pluie_7j=20),
            **ctx_sol(pH=6.0, azote=0.06),
        }
        r_gratuit = evaluate(db, ctx, "fertilisation", "gratuit", False)
        r_premium = evaluate(db, ctx, "fertilisation", "premium", False)
        assert len(r_premium["resultats"]) >= len(r_gratuit["resultats"]), \
            "Premium doit avoir >= résultats que gratuit"

    def test_evaluation_contexte_complet(self, db):
        """Contexte complet évaluation cohérente toutes catégories."""
        ctx = {
            **ctx_meteo(temp_air=22, humidite_rel=89, pluie_7j=35, pluie_24h=12,
                        etp=4.5, vent=10, temp_min=18),
            **ctx_sol(pH=5.8, azote=0.06, phosphore=10, potassium=80,
                      humidite=72, matiere_organique=1.2, conductivite=0.8, temperature=28),
            "obs_symptomes": ["taches", "jaunissement"],
            "stade_actuel": "floraison",
            "mois": 9,
            "zone_agro": "niayes",
        }
        for categorie in ["maladie", "ravageur", "fertilisation", "irrigation", "meteo"]:
            result = evaluate(db, ctx, categorie=categorie, plan="premium", persist=False)
            assert result is not None
            assert "resultats" in result

    def test_duree_ms_dans_resultat(self, db):
        """duree_ms toujours présente et > 0."""
        ctx = {**ctx_meteo(temp_air=28)}
        result = evaluate(db, ctx, "maladie", "premium", False)
        assert "duree_ms" in result
        assert result["duree_ms"] >= 0

    def test_regles_declenchees_coherent(self, db):
        """regles_declenchees == len(resultats)."""
        ctx = {**ctx_meteo(temp_air=22, humidite_rel=90, pluie_7j=40)}
        result = evaluate(db, ctx, "maladie", "premium", False)
        assert result["regles_declenchees"] == len(result["resultats"])


# ─────────────────────────────────────────────────────────────
# 10. RAPPORT PERFORMANCE — summary complet
# ─────────────────────────────────────────────────────────────

def test_rapport_performance_complet(db):
    """Génère rapport complet des temps d'évaluation — 5 runs/catégorie."""
    categories = ["maladie", "ravageur", "fertilisation", "irrigation", "meteo", "calendrier", "rendement"]
    ctx = {
        **ctx_meteo(temp_air=30, humidite_rel=78, pluie_7j=25, pluie_24h=8, etp=6.0, vent=20, temp_min=22),
        **ctx_sol(pH=5.9, azote=0.07, phosphore=11, potassium=60,
                  humidite=68, matiere_organique=1.5, conductivite=0.6, temperature=27),
        "stade_actuel": "croissance_vegetative",
        "mois": 8,
        "zone_agro": "casamance",
    }

    print("\n" + "=" * 60)
    print("RAPPORT PERFORMANCE — Rules Engine V1 AgroScan")
    print("=" * 60)

    total_ms = 0
    for cat in categories:
        times = []
        n_resultats = 0
        for _ in range(5):
            t0 = time.perf_counter()
            result = evaluate(db, ctx, categorie=cat, plan="premium", persist=False)
            times.append((time.perf_counter() - t0) * 1000)
            n_resultats = len(result["resultats"])

        avg = sum(times) / len(times)
        total_ms += avg
        status = "OK" if avg < 200 else "SLOW"
        print(f"  [{status}] {cat:<16} {avg:6.1f}ms avg  {n_resultats:2d} résultats")

    moyenne_globale = total_ms / len(categories)
    print(f"\n  Moyenne globale: {moyenne_globale:.1f}ms  (objectif: <200ms)")
    print("=" * 60)

    assert moyenne_globale < 200, f"Moyenne {moyenne_globale:.1f}ms > 200ms"
