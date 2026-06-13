"""
Interface abstraite SMS — tous les providers l'implémentent.
Permet de changer de carrier sans toucher au code métier.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SMSResult:
    success: bool
    provider: str
    message_id: str = ""
    error: str = ""


class SMSProvider(ABC):
    """Contrat de base pour tous les providers SMS."""

    @abstractmethod
    def send(self, phone: str, message: str) -> SMSResult:
        """
        Envoie un SMS.

        Args:
            phone: numéro au format international (+221XXXXXXXXX)
            message: texte du SMS (max 160 caractères)

        Returns:
            SMSResult avec success=True si l'envoi est confirmé.
        """
        ...

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalise un numéro sénégalais au format E.164.

        Exemples :
          "776543210"    → "+221776543210"
          "0776543210"   → "+221776543210"
          "+221776543210"→ "+221776543210"
        """
        p = phone.strip().replace(" ", "").replace("-", "")
        if p.startswith("+221"):
            return p
        if p.startswith("221"):
            return "+" + p
        if p.startswith("0"):
            p = p[1:]
        return "+221" + p
