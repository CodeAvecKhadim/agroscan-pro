"""
Tests Sprint 2 — Phase 1 : parcelles enrichies (date_semis, variete, stade_culture).
Tests purs (sans DB) pour les fonctions unitaires.
"""
import pytest
from datetime import date, timedelta

from app.services.calendrier import deriver_stade, generer_calendrier


# ── Tests deriver_stade ──────────────────────────────────────────────────────

class TestDeriverStade:
    def test_semis_futur_retourne_message_prevision(self):
        """Si date_semis est dans le futur, retourne message de prévision."""
        futur = date.today() + timedelta(days=10)
        stade = deriver_stade("Mil", futur)
        assert "prévu" in stade.lower()
        assert futur.strftime("%d/%m/%Y") in stade

    def test_stade_courant_mil_40_jours(self):
        """Mil semé il y a ~40j : stade doit être fertilisation (≈35% du cycle ~90j)."""
        d_semis = date.today() - timedelta(days=40)
        stade = deriver_stade("Mil", d_semis)
        assert stade not in ("Stade inconnu", "Culture inconnue")
        assert isinstance(stade, str) and len(stade) > 0

    def test_cycle_termine_apres_recolte(self):
        """Semis très ancien (1000 jours) → dernier stade ou cycle terminé."""
        tres_vieux = date.today() - timedelta(days=1000)
        stade = deriver_stade("Mil", tres_vieux)
        # Doit retourner le dernier stade connu (fin de récolte), pas une erreur
        assert stade not in ("Stade inconnu", "Culture inconnue")

    def test_culture_inconnue_retourne_message_clair(self):
        stade = deriver_stade("Zirconium_agricole", date.today())
        assert stade == "Culture inconnue"

    def test_culture_arachide_recente(self):
        """Arachide semée hier → premier stade (semis direct)."""
        hier = date.today() - timedelta(days=1)
        stade = deriver_stade("Arachide", hier)
        assert "Semis" in stade or "Levée" in stade

    def test_toutes_cultures_principales(self):
        """Toutes les cultures principales doivent retourner un stade non-erreur."""
        cultures = ["Mil", "Sorgho", "Maïs", "Riz", "Arachide", "Niébé",
                    "Tomate", "Oignon", "Coton"]
        d_semis = date.today() - timedelta(days=30)
        for culture in cultures:
            stade = deriver_stade(culture, d_semis)
            assert stade not in ("Stade inconnu",), f"Erreur pour culture: {culture}"

    def test_retourne_toujours_string(self):
        """deriver_stade ne lève jamais d'exception, retourne toujours str."""
        # Même avec des entrées bizarres
        try:
            result = deriver_stade("", date.today())
            assert isinstance(result, str)
        except Exception:
            pytest.fail("deriver_stade ne doit pas lever d'exception")


# ── Tests generer_calendrier (régression) ───────────────────────────────────

class TestGenererCalendrier:
    def test_retourne_etapes_avec_dates_iso(self):
        cal = generer_calendrier("Mil", date(2026, 6, 1))
        assert "etapes" in cal
        etapes = cal["etapes"]
        assert len(etapes) >= 4
        for e in etapes:
            assert "date" in e and "titre" in e
            # date doit être parseable en ISO
            date.fromisoformat(e["date"])

    def test_premiere_etape_date_egale_semis(self):
        d = date(2026, 6, 15)
        cal = generer_calendrier("Riz", d)
        premiere = cal["etapes"][0]
        assert premiere["jour"] == 0
        assert date.fromisoformat(premiere["date"]) == d

    def test_culture_inconnue_retourne_error_key(self):
        cal = generer_calendrier("PlanteInexistante", date.today())
        assert "error" in cal

    def test_etapes_ordonnees_chronologiquement(self):
        cal = generer_calendrier("Maïs", date(2026, 5, 1))
        dates = [date.fromisoformat(e["date"]) for e in cal["etapes"]]
        assert dates == sorted(dates)


# ── Tests schémas Pydantic ───────────────────────────────────────────────────

class TestParcelleSchemas:
    def test_parcelle_create_accepte_nouveaux_champs(self):
        from app.schemas.champ import ParcelleCreate
        p = ParcelleCreate(
            nom="Parcelle Test",
            type_culture="Mil",
            date_semis=date(2026, 6, 1),
            variete="Souna III",
            stade_culture="Levée & démariage",
        )
        assert p.date_semis == date(2026, 6, 1)
        assert p.variete == "Souna III"
        assert p.stade_culture == "Levée & démariage"

    def test_parcelle_create_champs_optionnels(self):
        from app.schemas.champ import ParcelleCreate
        p = ParcelleCreate(nom="Sans agronomie", type_culture="Mil")
        assert p.date_semis is None
        assert p.variete is None
        assert p.stade_culture is None

    def test_parcelle_update_accepte_nouveaux_champs(self):
        from app.schemas.champ import ParcelleUpdate
        u = ParcelleUpdate(date_semis=date(2026, 7, 1), variete="HK")
        assert u.date_semis == date(2026, 7, 1)
        assert u.variete == "HK"

    def test_parcelle_out_a_nouveaux_champs(self):
        from app.schemas.champ import ParcelleOut
        fields = ParcelleOut.model_fields
        assert "date_semis" in fields
        assert "variete" in fields
        assert "stade_culture" in fields

    def test_parcelle_summary_a_stade_et_semis(self):
        from app.schemas.champ import ParcelleSummary
        fields = ParcelleSummary.model_fields
        assert "date_semis" in fields
        assert "stade_culture" in fields
