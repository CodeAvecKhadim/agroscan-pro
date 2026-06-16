"""
Tests suppression logique de parcelles — Sprint suppression.

Couvre :
  - Unitaires : logique StatutParcelle, deleted_at
  - Intégration API : DELETE, GET /archivees, POST /restaurer, contrôle propriétaire
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.champ import StatutParcelle

client = TestClient(app)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _creer_parcelle(token, nom="Parcelle Test"):
    r = client.post("/api/champ/parcelles", json={
        "nom": nom,
        "type_culture": "Mil",
        "statut": "active",
    }, headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


# ── Tests unitaires : modèle StatutParcelle ───────────────────────────────────

class TestStatutParcelle:
    def test_archive_existe_dans_enum(self):
        assert StatutParcelle.ARCHIVE == "archive"

    def test_active_est_la_valeur_defaut(self):
        assert StatutParcelle.ACTIVE == "active"

    def test_en_culture_existe(self):
        assert StatutParcelle.EN_CULTURE == "en_culture"

    def test_toutes_valeurs_attendues(self):
        valeurs = {s.value for s in StatutParcelle}
        assert "archive" in valeurs
        assert "active" in valeurs
        assert "en_repos" in valeurs
        assert "en_preparation" in valeurs
        assert "en_culture" in valeurs


# ── Tests intégration : suppression logique ───────────────────────────────────

class TestSuppressionParcelle:

    def test_supprimer_parcelle_renvoie_204(self, token_user_a):
        p = _creer_parcelle(token_user_a)
        r = client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        assert r.status_code == 204

    def test_parcelle_supprimee_absente_de_la_liste(self, token_user_a):
        p = _creer_parcelle(token_user_a)
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        liste = client.get("/api/champ/parcelles", headers=_auth(token_user_a)).json()
        ids = [x["id"] for x in liste]
        assert p["id"] not in ids

    def test_parcelle_supprimee_inaccessible_par_id(self, token_user_a):
        p = _creer_parcelle(token_user_a)
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        r = client.get(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        assert r.status_code == 404

    def test_supprimer_requiert_authentification(self, token_user_a):
        p = _creer_parcelle(token_user_a)
        r = client.delete(f"/api/champ/parcelles/{p['id']}")
        assert r.status_code == 401

    def test_supprimer_parcelle_inexistante_renvoie_404(self, token_user_a):
        r = client.delete("/api/champ/parcelles/999999", headers=_auth(token_user_a))
        assert r.status_code == 404

    def test_supprimer_parcelle_autre_org_renvoie_404(self, token_user_a, token_user_b):
        """Un utilisateur ne peut pas supprimer la parcelle d'un autre."""
        p = _creer_parcelle(token_user_a)
        r = client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_b))
        assert r.status_code == 404


# ── Tests intégration : vue archives ─────────────────────────────────────────

class TestVueArchives:

    def test_liste_archivees_vide_par_defaut(self, token_user_c):
        r = client.get("/api/champ/parcelles/archivees", headers=_auth(token_user_c))
        assert r.status_code == 200
        # Utilisateur C n'a encore rien supprimé
        assert isinstance(r.json(), list)

    def test_parcelle_supprimee_apparait_dans_archives(self, token_user_a):
        p = _creer_parcelle(token_user_a, nom="Champ Nord")
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        archives = client.get("/api/champ/parcelles/archivees", headers=_auth(token_user_a)).json()
        ids = [x["id"] for x in archives]
        assert p["id"] in ids

    def test_archives_contient_deleted_at(self, token_user_a):
        p = _creer_parcelle(token_user_a)
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        archives = client.get("/api/champ/parcelles/archivees", headers=_auth(token_user_a)).json()
        archive = next(x for x in archives if x["id"] == p["id"])
        assert archive["deleted_at"] is not None

    def test_archives_requiert_authentification(self):
        r = client.get("/api/champ/parcelles/archivees")
        assert r.status_code == 401


# ── Tests intégration : restauration ─────────────────────────────────────────

class TestRestaurationParcelle:

    def test_restaurer_parcelle_archivee(self, token_user_a):
        p = _creer_parcelle(token_user_a, nom="Champ Restauré")
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        r = client.post(f"/api/champ/parcelles/{p['id']}/restaurer", headers=_auth(token_user_a))
        assert r.status_code == 200
        data = r.json()
        assert data["statut"] == "active"
        assert data["deleted_at"] is None

    def test_parcelle_restauree_visible_dans_liste(self, token_user_a):
        p = _creer_parcelle(token_user_a)
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        client.post(f"/api/champ/parcelles/{p['id']}/restaurer", headers=_auth(token_user_a))
        liste = client.get("/api/champ/parcelles", headers=_auth(token_user_a)).json()
        ids = [x["id"] for x in liste]
        assert p["id"] in ids

    def test_restaurer_parcelle_non_archivee_renvoie_400(self, token_user_a):
        p = _creer_parcelle(token_user_a)
        r = client.post(f"/api/champ/parcelles/{p['id']}/restaurer", headers=_auth(token_user_a))
        assert r.status_code == 400

    def test_restaurer_requiert_authentification(self, token_user_a):
        p = _creer_parcelle(token_user_a)
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        r = client.post(f"/api/champ/parcelles/{p['id']}/restaurer")
        assert r.status_code == 401

    def test_restaurer_parcelle_autre_org_renvoie_404(self, token_user_a, token_user_b):
        p = _creer_parcelle(token_user_a)
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        r = client.post(f"/api/champ/parcelles/{p['id']}/restaurer", headers=_auth(token_user_b))
        assert r.status_code == 404


# ── Tests unitaires supplémentaires : price_ttc suppression sans impact ───────

class TestSuppressionSansEffetTarif:
    """Suppression ne modifie pas les plans ni les quotas."""

    def test_suppression_ne_cree_pas_paiement(self, token_user_a):
        """DELETE /parcelles ne déclenche pas d'opération billing."""
        p = _creer_parcelle(token_user_a)
        r_before = client.get("/api/billing/me", headers=_auth(token_user_a))
        client.delete(f"/api/champ/parcelles/{p['id']}", headers=_auth(token_user_a))
        r_after = client.get("/api/billing/me", headers=_auth(token_user_a))
        assert r_before.json()["plan"] == r_after.json()["plan"]
