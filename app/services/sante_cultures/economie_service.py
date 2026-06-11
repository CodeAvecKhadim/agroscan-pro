"""
EconomieService — Réexporte _calcul_economie depuis orchestrateur.
Façade pour injection de dépendance + tests unitaires isolés.
"""
from app.services.sante_cultures.orchestrateur import (
    _calcul_economie as calcul_economie,
    _prix_marche as prix_marche,
    _PRIX_MARCHE as PRIX_MARCHE,
)

__all__ = ["calcul_economie", "prix_marche", "PRIX_MARCHE"]
