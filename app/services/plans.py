"""
Matrice des plans : LA source unique de vérité pour les droits de chaque abonnement.
Bonne pratique SaaS : centraliser ici toutes les limites et fonctionnalités, pour que
le contrôle d'accès (decorators/dépendances) lise toujours le même tableau.

Pour changer une offre commerciale, on modifie UNIQUEMENT ce fichier.
"""
from app.models import PlanType
from app.core.config import settings

PLAN_FEATURES = {
    PlanType.GRATUIT: {
        "label": "Gratuit",
        "monthly_analyses": settings.FREE_MONTHLY_ANALYSES,   # 3 / mois
        "history_days": settings.FREE_HISTORY_DAYS,           # 30 jours
        "advanced_reco": False,    # diagnostic simplifié uniquement
        "pdf_reports": False,
        "whatsapp_support": False,
        "multi_user": False,
        "multi_farm": False,
        "collab_dashboard": False,
        "max_seats": 1,
        "price_ht": 0,
    },
    PlanType.PREMIUM: {
        "label": "Premium",
        "monthly_analyses": None,   # None = illimité
        "history_days": None,       # historique complet
        "advanced_reco": True,      # recommandations agronomiques avancées
        "pdf_reports": True,
        "whatsapp_support": True,
        "multi_user": False,
        "multi_farm": True,
        "collab_dashboard": False,
        "max_seats": 1,
        "price_ht": settings.PRICE_PREMIUM_HT,
    },
    PlanType.COOPERATIVE: {
        "label": "Coopérative",
        "monthly_analyses": None,
        "history_days": None,
        "advanced_reco": True,
        "pdf_reports": True,
        "whatsapp_support": True,
        "multi_user": True,         # plusieurs comptes
        "multi_farm": True,         # plusieurs exploitations
        "collab_dashboard": True,   # tableau de bord collaboratif
        "max_seats": 50,
        "price_ht": settings.PRICE_COOP_HT,
    },
}


def features_for(plan: PlanType) -> dict:
    """Renvoie le dictionnaire de droits pour un plan donné."""
    return PLAN_FEATURES[plan]


def price_ttc(plan: PlanType) -> dict:
    """Calcule le prix TTC (TVA 18 %) d'un plan, en FCFA."""
    ht = PLAN_FEATURES[plan]["price_ht"]
    vat = round(ht * settings.VAT_RATE)
    return {"ht": ht, "vat": vat, "ttc": ht + vat, "currency": settings.CURRENCY}
