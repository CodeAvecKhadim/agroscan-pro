"""
Tests Santé des Cultures — 24 cas de test.
Couvre : indice_service, scoring_service, orchestrateur, carte_service.
Pas de DB requise (tests unitaires purs).
"""
import pytest


# ══════════════════════════════════════════════════════════════════════════════
# IndiceService — to_label() + traduire_tous()
# ══════════════════════════════════════════════════════════════════════════════

class TestToLabel:

    def test_ndvi_excellent(self):
        from app.services.sante_cultures.indice_service import to_label
        assert to_label("ndvi", 0.65) == "Excellent"

    def test_ndvi_bon(self):
        from app.services.sante_cultures.indice_service import to_label
        assert to_label("ndvi", 0.50) == "Bon"

    def test_ndvi_moyen(self):
        from app.services.sante_cultures.indice_service import to_label
        assert to_label("ndvi", 0.30) == "Moyen"

    def test_ndvi_faible(self):
        from app.services.sante_cultures.indice_service import to_label
        assert to_label("ndvi", 0.10) == "Faible"

    def test_ndvi_none_retourne_none(self):
        from app.services.sante_cultures.indice_service import to_label
        assert to_label("ndvi", None) is None

    def test_indice_inconnu_retourne_none(self):
        from app.services.sante_cultures.indice_service import to_label
        assert to_label("ndxxx", 0.5) is None

    def test_ndwi_positif_excellent(self):
        from app.services.sante_cultures.indice_service import to_label
        assert to_label("ndwi", 0.25) == "Excellent"

    def test_ndwi_tres_negatif_faible(self):
        from app.services.sante_cultures.indice_service import to_label
        assert to_label("ndwi", -0.5) == "Faible"

    def test_traduire_tous_complet(self):
        from app.services.sante_cultures.indice_service import traduire_tous
        raw = {"ndvi": 0.65, "ndre": 0.35, "savi": 0.4, "evi": 0.45, "msavi": 0.35, "ndwi": 0.1}
        labels = traduire_tous(raw)
        assert labels["ndvi_label"] == "Excellent"
        assert labels["ndre_label"] == "Bon"
        assert labels["ndwi_label"] == "Bon"
        assert len(labels) == 6

    def test_traduire_tous_valeurs_manquantes(self):
        from app.services.sante_cultures.indice_service import traduire_tous
        labels = traduire_tous({})
        assert all(v is None for v in labels.values())


# ══════════════════════════════════════════════════════════════════════════════
# ScoringService
# ══════════════════════════════════════════════════════════════════════════════

class TestScoringService:

    def test_poids_composite_somme_1(self):
        from app.services.sante_cultures.scoring_service import POIDS
        assert abs(sum(POIDS.values()) - 1.0) < 1e-9

    def test_score_depuis_ndvi_seuils(self):
        from app.services.sante_cultures.scoring_service import score_depuis_ndvi
        assert score_depuis_ndvi(0.65) == 100.0
        assert score_depuis_ndvi(0.50) == 75.0
        assert score_depuis_ndvi(0.30) == 45.0
        assert score_depuis_ndvi(0.10) == 15.0

    def test_score_depuis_ndvi_none_neutre(self):
        from app.services.sante_cultures.scoring_service import score_depuis_ndvi
        assert score_depuis_ndvi(None) == 50.0

    def test_score_risque_vide_100(self):
        from app.services.sante_cultures.scoring_service import score_risque
        assert score_risque([]) == 100.0

    def test_score_risque_plancher_20(self):
        from app.services.sante_cultures.scoring_service import score_risque
        # Beaucoup de règles critiques → plancher 20
        regles = [{"gravite": "critique", "confiance": 1.0}] * 10
        assert score_risque(regles) == 20.0

    def test_score_risque_1_critique(self):
        from app.services.sante_cultures.scoring_service import score_risque
        regles = [{"gravite": "critique", "confiance": 1.0}]
        # déduction = 40 * 1.0 = 40 → 100 - 40 = 60
        assert score_risque(regles) == 60.0

    def test_score_composite_poids(self):
        from app.services.sante_cultures.scoring_service import score_composite
        s = score_composite(80, 70, 90, 60, 50)
        expected = 80*0.30 + 70*0.25 + 90*0.20 + 60*0.15 + 50*0.10
        assert abs(s - expected) < 0.001

    def test_score_to_etat(self):
        from app.services.sante_cultures.scoring_service import score_to_etat
        assert score_to_etat(85) == "Excellent"
        assert score_to_etat(70) == "Bon"
        assert score_to_etat(50) == "Moyen"
        assert score_to_etat(30) == "Faible"


# ══════════════════════════════════════════════════════════════════════════════
# Orchestrateur — determine_niveau + calculs (sans DB)
# ══════════════════════════════════════════════════════════════════════════════

class TestOrchestrateurNiveau:

    def test_n1_sans_capteur(self):
        from app.services.sante_cultures.orchestrateur import determine_niveau
        from app.schemas.sante_cultures import AnalyseSanteRequest
        req = AnalyseSanteRequest(culture_nom="Riz", parcelle_id=1)
        assert determine_niveau(req) == 1

    def test_n2_capteur_partiel(self):
        from app.services.sante_cultures.orchestrateur import determine_niveau
        from app.schemas.sante_cultures import AnalyseSanteRequest, CapteurData
        req = AnalyseSanteRequest(
            culture_nom="Maïs", parcelle_id=1,
            capteur=CapteurData(sol_pH=6.5, sol_humidite=55.0),
        )
        assert determine_niveau(req) == 2

    def test_n3_npk_complet(self):
        from app.services.sante_cultures.orchestrateur import determine_niveau
        from app.schemas.sante_cultures import AnalyseSanteRequest, CapteurData
        req = AnalyseSanteRequest(
            culture_nom="Tomate", parcelle_id=1,
            capteur=CapteurData(sol_azote=45.0, sol_phosphore=18.0, sol_potassium=140.0),
        )
        assert determine_niveau(req) == 3

    def test_prevision_rendement_riz(self):
        from app.services.sante_cultures.orchestrateur import _calcul_prevision
        prev = _calcul_prevision("Riz", 80.0, 1, None)
        assert prev.rendement_potentiel == 6.0
        assert prev.rendement_estime > 0
        assert prev.confiance == 0.60

    def test_prevision_plancher_score_bas(self):
        from app.services.sante_cultures.orchestrateur import _calcul_prevision
        prev = _calcul_prevision("Riz", 20.0, 1, None)
        assert prev.rendement_estime > 0
        assert prev.ecart_performance < 0

    def test_economie_roi_positif(self):
        from app.services.sante_cultures.orchestrateur import _calcul_prevision, _calcul_economie
        prev = _calcul_prevision("Riz", 60.0, 1, None)
        eco = _calcul_economie("Riz", 2.0, prev)
        assert eco.superficie_ha == 2.0
        assert eco.roi_estime is not None


# ══════════════════════════════════════════════════════════════════════════════
# SatelliteService — coordonnees_to_bbox + fallback simulation
# ══════════════════════════════════════════════════════════════════════════════

class TestSatelliteService:

    def test_coordonnees_to_bbox(self):
        from app.services.sante_cultures.satellite_service import coordonnees_to_bbox
        coords = [
            {"lat": 14.70, "lon": -17.50},
            {"lat": 14.72, "lon": -17.48},
            {"lat": 14.71, "lon": -17.49},
        ]
        bbox = coordonnees_to_bbox(coords)
        assert bbox == (-17.50, 14.70, -17.48, 14.72)

    def test_coordonnees_to_bbox_vide_leve_erreur(self):
        from app.services.sante_cultures.satellite_service import coordonnees_to_bbox
        with pytest.raises(ValueError):
            coordonnees_to_bbox([])

    def test_simulation_hivernage(self):
        from app.services.sante_cultures.satellite_service import _indices_simules
        raw = _indices_simules(8, "Riz")   # août = hivernage
        assert raw["ndvi"] >= 0.5
        assert "ndwi" in raw
        assert raw["source"] == "simule"

    def test_simulation_saison_seche(self):
        from app.services.sante_cultures.satellite_service import _indices_simules
        raw = _indices_simules(1, "Arachide")   # janvier = saison sèche
        assert raw["ndvi"] < 0.4


# ══════════════════════════════════════════════════════════════════════════════
# CarteService
# ══════════════════════════════════════════════════════════════════════════════

class TestCarteService:

    _COORDS = [{"lat": 14.70, "lon": -17.50}, {"lat": 14.71, "lon": -17.49}]

    def test_carte_geojson_valide(self):
        from app.services.sante_cultures.carte_service import generer_carte
        carte = generer_carte("sante", 72.0, self._COORDS, 1.0)
        assert carte["type"] == "FeatureCollection"
        assert len(carte["features"]) > 0

    def test_carte_vide_sans_coordonnees(self):
        from app.services.sante_cultures.carte_service import generer_carte
        carte = generer_carte("sante", 72.0, [], 1.0)
        assert carte["_meta"]["nb_cellules"] == 0
        assert len(carte["features"]) == 0

    def test_toutes_cartes_4_types(self):
        from app.services.sante_cultures.carte_service import generer_toutes_cartes
        scores = {
            "composite": 72.0, "hydrique": 60.0,
            "fertilite": 80.0, "maladie": 85.0, "ravageur": 90.0,
        }
        cartes = generer_toutes_cartes(scores, self._COORDS, 1.0)
        assert set(cartes.keys()) == {"sante", "hydrique", "fertilite", "risques"}

    def test_feature_structure_geojson(self):
        from app.services.sante_cultures.carte_service import generer_carte
        carte = generer_carte("hydrique", 55.0, self._COORDS, 1.0)
        feat = carte["features"][0]
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "Polygon"
        props = feat["properties"]
        assert "score" in props
        assert "label" in props
        assert "couleur" in props
