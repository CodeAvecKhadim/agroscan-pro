"""
Factory SMS — retourne le bon provider selon SMS_PROVIDER dans settings.

Détection automatique par préfixe opérateur si SMS_PROVIDER="auto".

Mapping préfixes Sénégal (2024) :
  77, 78 → Orange
  76, 75 → Free
  70      → Expresso
  Autres  → provider par défaut
"""
import logging

from app.core.config import settings
from app.services.sms.base import SMSProvider

logger = logging.getLogger("agroscan.sms.factory")

# Préfixes opérateurs (2 premiers chiffres après +221)
_PREFIX_MAP = {
    "77": "orange",
    "78": "orange",
    "76": "free",
    "75": "free",
    "70": "expresso",
}


def detect_provider_for_phone(phone: str) -> str:
    """Détecte l'opérateur depuis le préfixe du numéro sénégalais."""
    p = phone.strip().replace(" ", "").replace("-", "")
    # Normaliser : enlever +221 ou 221
    for prefix in ("+221", "221"):
        if p.startswith(prefix):
            p = p[len(prefix):]
    if p.startswith("0"):
        p = p[1:]
    return _PREFIX_MAP.get(p[:2], settings.SMS_PROVIDER)


def get_sms_provider(phone: str | None = None) -> SMSProvider:
    """
    Retourne une instance du provider SMS configuré.

    Si SMS_PROVIDER="auto", détecte l'opérateur depuis le numéro.
    Si SMS_PROVIDER="mock" (ou ENV=development), utilise le mock.
    """
    provider_name = settings.SMS_PROVIDER.lower().strip()

    if provider_name == "auto" and phone:
        provider_name = detect_provider_for_phone(phone)
        logger.debug("Auto-detected provider '%s' for %s", provider_name, phone)

    # Imports tardifs pour éviter les imports circulaires
    if provider_name == "orange":
        from app.services.sms.orange import OrangeSMSProvider
        return OrangeSMSProvider()

    if provider_name == "free":
        from app.services.sms.free import FreeSMSProvider
        return FreeSMSProvider()

    if provider_name == "expresso":
        from app.services.sms.expresso import ExpressoSMSProvider
        return ExpressoSMSProvider()

    if provider_name in ("africas_talking", "at"):
        from app.services.sms.africas_talking import AfricasTalkingProvider
        return AfricasTalkingProvider()

    # Par défaut : mock (dev / aucune config)
    from app.services.sms.mock import MockSMSProvider
    if provider_name not in ("mock", ""):
        logger.warning("Provider SMS inconnu '%s', utilisation du mock", provider_name)
    return MockSMSProvider()
