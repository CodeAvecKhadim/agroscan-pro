"""
PrevisionService — Réexporte _calcul_prevision depuis orchestrateur.
Façade pour injection de dépendance + tests unitaires isolés.
"""
from app.services.sante_cultures.orchestrateur import (
    _calcul_prevision as calcul_prevision,
    _RENDEMENTS_REF as RENDEMENTS_REF,
)

__all__ = ["calcul_prevision", "RENDEMENTS_REF"]
