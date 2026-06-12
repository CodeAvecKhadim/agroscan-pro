"""
Tests unitaires — ndvi_to_message (Phase 4).
Vérifie toutes les branches NDVI + stress hydrique + source simulée.
"""
import pytest
from app.services.ndvi_message import ndvi_to_message


class TestNdviToMessage:

    def test_ndvi_none_retourne_orange(self):
        msg, col = ndvi_to_message(None)
        assert col == "orange"
        assert "non disponibles" in msg.lower() or "satellite" in msg.lower()

    def test_ndvi_eleve_retourne_vert(self):
        msg, col = ndvi_to_message(0.7)
        assert col == "vert"
        assert "très bien" in msg.lower() or "vigoureuse" in msg.lower()

    def test_ndvi_exactement_0_6_retourne_vert(self):
        _, col = ndvi_to_message(0.6)
        assert col == "vert"

    def test_ndvi_moyen_sans_stress_retourne_vert(self):
        msg, col = ndvi_to_message(0.5)
        assert col == "vert"
        assert "bon état" in msg.lower()

    def test_ndvi_moyen_avec_stress_eau_retourne_orange(self):
        msg, col = ndvi_to_message(0.5, ndwi=-0.2)
        assert col == "orange"
        assert "hydrique" in msg.lower() or "irrigation" in msg.lower()

    def test_ndwi_au_dessus_seuil_pas_stress(self):
        # ndwi = -0.10 < seuil -0.15 → pas stress
        _, col = ndvi_to_message(0.5, ndwi=-0.10)
        assert col == "vert"

    def test_ndvi_bas_sans_stress_retourne_orange(self):
        msg, col = ndvi_to_message(0.3)
        assert col == "orange"
        assert "vigueur" in msg.lower() or "baisse" in msg.lower()

    def test_ndvi_bas_avec_stress_eau_retourne_orange(self):
        msg, col = ndvi_to_message(0.3, ndwi=-0.25)
        assert col == "orange"
        assert "hydrique" in msg.lower()

    def test_ndvi_tres_bas_retourne_rouge(self):
        msg, col = ndvi_to_message(0.1)
        assert col == "rouge"
        assert "anomalie" in msg.lower() or "conseiller" in msg.lower()

    def test_ndvi_exactement_0_2_retourne_orange(self):
        _, col = ndvi_to_message(0.2)
        assert col == "orange"

    def test_ndvi_juste_sous_0_2_retourne_rouge(self):
        _, col = ndvi_to_message(0.19)
        assert col == "rouge"

    def test_source_simule_ajoute_note(self):
        msg, _ = ndvi_to_message(0.5, source="simule")
        assert "estimation" in msg.lower() or "saisonnière" in msg.lower()

    def test_source_simule_fallback_ajoute_note(self):
        msg, _ = ndvi_to_message(0.5, source="simule_fallback")
        assert "estimation" in msg.lower() or "saisonnière" in msg.lower()

    def test_source_sentinel2_pas_de_note(self):
        msg, _ = ndvi_to_message(0.5, source="sentinel-2")
        assert "estimation" not in msg.lower()

    def test_retourne_tuple_str_str(self):
        result = ndvi_to_message(0.5)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(v, str) for v in result)

    def test_couleur_valeurs_valides(self):
        valides = {"vert", "orange", "rouge"}
        for ndvi in [None, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            _, col = ndvi_to_message(ndvi)
            assert col in valides, f"Couleur invalide '{col}' pour NDVI={ndvi}"
