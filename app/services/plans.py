"""
Matrice des plans AgroScan Pro — source unique de vérité.

Nouveau modèle économique (juin 2026) :
  GRATUIT      : 0 FCFA — 2 parcelles, 3 ha/parcelle, 3 analyses IA/jour, 1 satellite/semaine
  PREMIUM      : 14 900 FCFA/campagne (90 jours) — jusqu'à 20 ha, toutes fonctionnalités
  COOPERATIVE  : 25 000 FCFA/mois ou 250 000 FCFA/an — 25 ha inclus, extensions disponibles
"""
from app.models import PlanType
from app.core.config import settings

PLAN_FEATURES = {
    PlanType.GRATUIT: {
        "label": "Gratuit",
        # Limites quantitatives
        "max_parcelles": settings.FREE_MAX_PARCELLES,           # 2
        "max_ha_per_parcelle": settings.FREE_MAX_HA_PER_PARCELLE,  # 3.0 ha
        "daily_ai_analyses": settings.FREE_DAILY_AI_ANALYSES,  # 3/jour
        "weekly_satellite": settings.FREE_WEEKLY_SATELLITE,    # 1/semaine
        "max_seats": 1,
        # Tarification
        "price_ht": 0,
        "duration_days": None,
        "price_ht_annual": None,
        # Fonctionnalités
        "precision_agriculture": False,
        "ndvi_satellite": True,          # limité à 1/semaine
        "ai_assistant": False,
        "soil_analysis": False,
        "crop_health_advanced": False,
        "pdf_reports": False,
        "historical_data": False,
        "activities_management": False,
        "farm_management": False,
        "advisor_dashboard": False,
        "multi_farmer": False,
        "consolidated_reports": False,
        "alerts": False,
        # Compat legacy deps.py
        "monthly_analyses": settings.FREE_DAILY_AI_ANALYSES,
        "history_days": settings.FREE_HISTORY_DAYS,
        "advanced_reco": False,
        "whatsapp_support": False,
        "multi_user": False,
        "multi_farm": False,
        "collab_dashboard": False,
    },
    PlanType.PREMIUM: {
        "label": "Producteur Premium",
        # Limites quantitatives
        "max_parcelles": None,           # illimité
        "max_ha_per_parcelle": 20.0,     # 20 ha max par parcelle
        "daily_ai_analyses": None,       # illimité
        "weekly_satellite": None,        # illimité
        "max_seats": 1,
        # Tarification
        "price_ht": settings.PRICE_PREMIUM_HT,           # 14 900 FCFA / campagne
        "duration_days": settings.PRICE_PREMIUM_DURATION_DAYS,  # 90 jours
        "price_ht_annual": None,
        # Fonctionnalités
        "precision_agriculture": True,
        "ndvi_satellite": True,
        "ai_assistant": True,
        "soil_analysis": True,
        "crop_health_advanced": True,
        "pdf_reports": True,
        "historical_data": True,
        "activities_management": True,
        "farm_management": True,
        "advisor_dashboard": False,
        "multi_farmer": False,
        "consolidated_reports": False,
        "alerts": True,
        # Compat legacy
        "monthly_analyses": None,
        "history_days": None,
        "advanced_reco": True,
        "whatsapp_support": True,
        "multi_user": False,
        "multi_farm": True,
        "collab_dashboard": False,
    },
    PlanType.COOPERATIVE: {
        "label": "Coopérative",
        # Limites quantitatives
        "max_parcelles": None,           # illimité
        "max_ha_per_parcelle": None,     # selon extension
        "daily_ai_analyses": None,       # illimité (1/jour/parcelle recommandé)
        "weekly_satellite": None,        # illimité
        "max_seats": 50,
        "included_ha": settings.COOP_INCLUDED_HA,  # 25 ha inclus
        # Tarification
        "price_ht": settings.PRICE_COOP_HT,               # 25 000 FCFA/mois
        "duration_days": None,
        "price_ht_annual": settings.PRICE_COOP_HT_ANNUAL,  # 250 000 FCFA/an
        # Fonctionnalités
        "precision_agriculture": True,
        "ndvi_satellite": True,
        "ai_assistant": True,
        "soil_analysis": True,
        "crop_health_advanced": True,
        "pdf_reports": True,
        "historical_data": True,
        "activities_management": True,
        "farm_management": True,
        "advisor_dashboard": True,
        "multi_farmer": True,
        "consolidated_reports": True,
        "alerts": True,
        # Compat legacy
        "monthly_analyses": None,
        "history_days": None,
        "advanced_reco": True,
        "whatsapp_support": True,
        "multi_user": True,
        "multi_farm": True,
        "collab_dashboard": True,
    },
}

# Grille extensions hectares coopérative (FCFA/mois)
COOP_HA_EXTENSIONS = [
    {"ha": 25,  "price_monthly": 25000,  "price_annual": 250000},
    {"ha": 50,  "price_monthly": 40000,  "price_annual": 400000},
    {"ha": 100, "price_monthly": 60000,  "price_annual": 600000},
]


def features_for(plan: PlanType) -> dict:
    """Renvoie le dictionnaire de droits pour un plan donné."""
    return PLAN_FEATURES[plan]


def price_ttc(plan: PlanType, billing: str = "monthly") -> dict:
    """Calcule le prix TTC (TVA 18 %) en FCFA.

    Pour PREMIUM : billing ignoré — prix par campagne.
    Pour COOPERATIVE : billing = 'monthly' | 'annual'.
    """
    feats = PLAN_FEATURES[plan]
    if billing == "annual" and feats.get("price_ht_annual"):
        ht = feats["price_ht_annual"]
    else:
        ht = feats["price_ht"]
    vat = round(ht * settings.VAT_RATE)
    return {
        "ht": ht,
        "vat": vat,
        "ttc": ht + vat,
        "currency": settings.CURRENCY,
        "billing": billing if plan == PlanType.COOPERATIVE else "campaign",
        "duration_days": feats.get("duration_days"),
    }
