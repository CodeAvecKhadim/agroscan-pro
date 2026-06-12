"""
Tests i18n — ndvi_to_message (français uniquement pour l'instant).
Vérifie que les messages sont corrects et que le fichier fr.json est intact.
"""
import pytest
from app.services.ndvi_message import ndvi_to_message


class TestNdviMessageFr:
    """ndvi_to_message retourne messages cohérents en français."""

    def test_ndvi_eleve_vert(self):
        msg, col = ndvi_to_message(0.7)
        assert col == "vert"
        assert len(msg) > 5

    def test_ndvi_rouge(self):
        msg, col = ndvi_to_message(0.05)
        assert col == "rouge"
        assert len(msg) > 5

    def test_ndvi_none_orange(self):
        msg, col = ndvi_to_message(None)
        assert col == "orange"
        assert len(msg) > 5

    def test_stress_eau_orange(self):
        _, col = ndvi_to_message(0.5, ndwi=-0.25)
        assert col == "orange"

    def test_estimation_simule(self):
        msg, _ = ndvi_to_message(0.5, source="simule")
        assert "estimation" in msg.lower() or "saisonnière" in msg.lower()

    def test_lang_inconnue_retourne_fr(self):
        msg_fr, col_fr = ndvi_to_message(0.7, lang="fr")
        msg_unk, col_unk = ndvi_to_message(0.7, lang="xx")
        assert col_unk == col_fr
        assert msg_unk == msg_fr

    def test_retourne_tuple_str_str(self):
        result = ndvi_to_message(0.5)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(v, str) for v in result)

    def test_couleur_valeurs_valides(self):
        valides = {"vert", "orange", "rouge"}
        for ndvi in [None, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            _, col = ndvi_to_message(ndvi)
            assert col in valides


class TestI18nFichierFr:
    """Vérifie l'intégrité du fichier fr.json."""

    def _load_json(self) -> dict:
        import json, os
        path = os.path.join(os.path.dirname(__file__), "../app/static/i18n/fr.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_fichier_json_valide(self):
        data = self._load_json()
        assert isinstance(data, dict)
        assert "_meta" in data

    def test_meta_lang_fr(self):
        data = self._load_json()
        assert data["_meta"]["lang"] == "fr"

    def test_sections_requises_presentes(self):
        data = self._load_json()
        for s in ["nav", "parcelle", "satellite", "auth", "commun"]:
            assert s in data

    def test_oui_non_presents(self):
        data = self._load_json()
        assert data["commun"]["oui"] == "Oui"
        assert data["commun"]["non"] == "Non"
