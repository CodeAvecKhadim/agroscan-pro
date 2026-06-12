"""
Tests du nouveau modèle économique AgroScan Pro (juin 2026).

GRATUIT   : 2 parcelles, 3 ha/parcelle, 3 IA/jour, 1 satellite/semaine
PREMIUM   : 14 900 FCFA/campagne (90 jours), ∞ tout
COOPERATIVE: 25 000 FCFA/mois ou 250 000 FCFA/an, 25 ha inclus

Tests structurés en 3 catégories :
  - TestPlanMatrix / TestPriceTTC : purs tests unitaires sans DB
  - TestSubscriptionService : service subscription avec vraie DB
  - TestBillingAPI : endpoints HTTP
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import PlanType, SubStatus
from app.services.plans import features_for, price_ttc, PLAN_FEATURES, COOP_HA_EXTENSIONS
from app.core.deps import _today_str, _current_week_str

client = TestClient(app)


def _login(email, password="test1234"):
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    return r.json().get("access_token") if r.status_code == 200 else None


# ── Tests matrice plans (unitaires, sans DB) ──────────────────────────────────

class TestPlanMatrix:
    def test_gratuit_max_parcelles(self):
        assert features_for(PlanType.GRATUIT)["max_parcelles"] == 2

    def test_gratuit_max_ha(self):
        assert features_for(PlanType.GRATUIT)["max_ha_per_parcelle"] == 3.0

    def test_gratuit_daily_ai(self):
        assert features_for(PlanType.GRATUIT)["daily_ai_analyses"] == 3

    def test_gratuit_weekly_satellite(self):
        assert features_for(PlanType.GRATUIT)["weekly_satellite"] == 1

    def test_gratuit_no_pdf(self):
        assert features_for(PlanType.GRATUIT)["pdf_reports"] is False

    def test_gratuit_no_ai_assistant(self):
        assert features_for(PlanType.GRATUIT)["ai_assistant"] is False

    def test_premium_price_14900(self):
        assert features_for(PlanType.PREMIUM)["price_ht"] == 14900

    def test_premium_duration_90_days(self):
        assert features_for(PlanType.PREMIUM)["duration_days"] == 90

    def test_premium_unlimited_ai(self):
        assert features_for(PlanType.PREMIUM)["daily_ai_analyses"] is None

    def test_premium_unlimited_satellite(self):
        assert features_for(PlanType.PREMIUM)["weekly_satellite"] is None

    def test_premium_max_ha_20(self):
        assert features_for(PlanType.PREMIUM)["max_ha_per_parcelle"] == 20.0

    def test_premium_unlimited_parcelles(self):
        assert features_for(PlanType.PREMIUM)["max_parcelles"] is None

    def test_premium_all_features(self):
        feats = features_for(PlanType.PREMIUM)
        for key in ("pdf_reports", "ai_assistant", "ndvi_satellite", "historical_data",
                    "activities_management", "farm_management"):
            assert feats[key] is True, f"Premium manque: {key}"

    def test_coop_monthly_price_25000(self):
        assert features_for(PlanType.COOPERATIVE)["price_ht"] == 25000

    def test_coop_annual_price_250000(self):
        assert features_for(PlanType.COOPERATIVE)["price_ht_annual"] == 250000

    def test_coop_included_ha_25(self):
        assert features_for(PlanType.COOPERATIVE)["included_ha"] == 25

    def test_coop_advisor_dashboard(self):
        assert features_for(PlanType.COOPERATIVE)["advisor_dashboard"] is True

    def test_coop_multi_farmer(self):
        assert features_for(PlanType.COOPERATIVE)["multi_farmer"] is True

    def test_ha_extensions_three_tiers(self):
        assert len(COOP_HA_EXTENSIONS) == 3

    def test_ha_extensions_values(self):
        assert COOP_HA_EXTENSIONS[0] == {"ha": 25, "price_monthly": 25000, "price_annual": 250000}
        assert COOP_HA_EXTENSIONS[1] == {"ha": 50, "price_monthly": 40000, "price_annual": 400000}
        assert COOP_HA_EXTENSIONS[2] == {"ha": 100, "price_monthly": 60000, "price_annual": 600000}

    def test_three_plans_defined(self):
        assert len(PLAN_FEATURES) == 3


# ── Tests calcul prix TTC (unitaires) ─────────────────────────────────────────

class TestPriceTTC:
    def test_gratuit_free(self):
        p = price_ttc(PlanType.GRATUIT)
        assert p["ht"] == 0 and p["ttc"] == 0

    def test_premium_ht(self):
        p = price_ttc(PlanType.PREMIUM)
        assert p["ht"] == 14900

    def test_premium_ttc_includes_vat(self):
        p = price_ttc(PlanType.PREMIUM)
        expected_ttc = 14900 + round(14900 * 0.18)
        assert p["ttc"] == expected_ttc

    def test_premium_billing_is_campaign(self):
        assert price_ttc(PlanType.PREMIUM)["billing"] == "campaign"

    def test_coop_monthly_ht(self):
        p = price_ttc(PlanType.COOPERATIVE, billing="monthly")
        assert p["ht"] == 25000 and p["billing"] == "monthly"

    def test_coop_annual_ht(self):
        p = price_ttc(PlanType.COOPERATIVE, billing="annual")
        assert p["ht"] == 250000 and p["billing"] == "annual"

    def test_premium_daily_under_170(self):
        p = price_ttc(PlanType.PREMIUM)
        assert p["ht"] / 90 < 170

    def test_coop_annual_saving_vs_monthly(self):
        monthly_year = price_ttc(PlanType.COOPERATIVE, billing="monthly")["ht"] * 12
        annual = price_ttc(PlanType.COOPERATIVE, billing="annual")["ht"]
        assert annual < monthly_year, "Annuel doit coûter moins que 12 × mensuel"

    def test_currency_is_fcfa(self):
        assert price_ttc(PlanType.PREMIUM)["currency"] == "FCFA"


# ── Tests helpers deps ──────────────────────────────────────────────────────────

class TestDepsHelpers:
    def test_today_str_format(self):
        today = _today_str()
        parts = today.split("-")
        assert len(parts) == 3 and len(parts[0]) == 4

    def test_week_str_format(self):
        week = _current_week_str()
        assert "-W" in week
        year, w = week.split("-W")
        assert len(year) == 4 and 1 <= int(w) <= 53


# ── Tests API plans (public, sans authentification) ────────────────────────────

class TestBillingPlansAPI:
    def test_plans_status_200(self):
        r = client.get("/api/billing/plans")
        assert r.status_code == 200

    def test_plans_three_entries(self):
        data = client.get("/api/billing/plans").json()
        assert len(data["plans"]) == 3

    def test_plans_currency_fcfa(self):
        data = client.get("/api/billing/plans").json()
        assert data["currency"] == "FCFA"

    def test_plans_vat_18_percent(self):
        data = client.get("/api/billing/plans").json()
        assert data["vat_rate"] == 0.18

    def test_plans_marketing_tagline(self):
        mkt = client.get("/api/billing/plans").json()["marketing"]
        assert "14 900" in mkt["premium_tagline"]
        assert "campagne" in mkt["premium_tagline"].lower()

    def test_plans_marketing_daily_cost(self):
        mkt = client.get("/api/billing/plans").json()["marketing"]
        assert "170" in mkt["premium_daily"]

    def test_plans_premium_price_14900(self):
        plans = client.get("/api/billing/plans").json()["plans"]
        premium = next(p for p in plans if p["plan"] == "premium")
        assert premium["pricing_monthly"]["ht"] == 14900

    def test_plans_premium_duration_days(self):
        plans = client.get("/api/billing/plans").json()["plans"]
        premium = next(p for p in plans if p["plan"] == "premium")
        assert premium["pricing_monthly"]["duration_days"] == 90

    def test_plans_coop_ha_extensions(self):
        plans = client.get("/api/billing/plans").json()["plans"]
        coop = next(p for p in plans if p["plan"] == "cooperative")
        assert "ha_extensions" in coop
        assert coop["included_ha"] == 25

    def test_plans_gratuit_limits(self):
        plans = client.get("/api/billing/plans").json()["plans"]
        gratuit = next(p for p in plans if p["plan"] == "gratuit")
        assert gratuit["max_parcelles"] == 2
        assert gratuit["max_ha_per_parcelle"] == 3.0
        assert gratuit["daily_ai_analyses"] == 3
        assert gratuit["weekly_satellite"] == 1

    def test_plans_premium_unlimited(self):
        plans = client.get("/api/billing/plans").json()["plans"]
        premium = next(p for p in plans if p["plan"] == "premium")
        assert premium["max_parcelles"] is None
        assert premium["daily_ai_analyses"] is None
        assert premium["weekly_satellite"] is None


# ── Tests API authentification requise ──────────────────────────────────────

class TestBillingAuthRequired:
    def test_me_requires_auth(self):
        assert client.get("/api/billing/me").status_code == 401

    def test_usage_requires_auth(self):
        assert client.get("/api/billing/usage").status_code == 401

    def test_change_requires_auth(self):
        r = client.post("/api/billing/change", json={"plan": "premium"})
        assert r.status_code == 401
