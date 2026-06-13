"""
Provider SMS factice — développement et tests uniquement.
Affiche l'OTP dans les logs au lieu d'envoyer un vrai SMS.
"""
import logging

from app.services.sms.base import SMSProvider, SMSResult

logger = logging.getLogger("agroscan.sms.mock")


class MockSMSProvider(SMSProvider):
    """Simule l'envoi SMS. Ne jamais utiliser en production."""

    def send(self, phone: str, message: str) -> SMSResult:
        phone_norm = self.normalize_phone(phone)
        logger.warning(
            "[SMS MOCK] → %s | %s",
            phone_norm,
            message,
        )
        # Affiche aussi en stdout pour faciliter les tests
        print(f"\n{'='*50}")
        print(f"📱 SMS MOCK → {phone_norm}")
        print(f"   {message}")
        print(f"{'='*50}\n")
        return SMSResult(success=True, provider="mock", message_id="mock-0000")
