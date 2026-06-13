"""
Provider SMS — Expresso Sénégal (via passerelle HTTP).

Protocole : API HTTP REST Expresso Business
Documentation : Contacter Expresso Entreprises pour l'accès API

Prérequis :
  - Compte Expresso Business (SMS en masse)
  - Clé API dans settings
  - Sender ID approuvé

Variables d'environnement :
  SMS_PROVIDER=expresso
  SMS_API_KEY=<api_key_expresso>
  SMS_API_SECRET=<secret_expresso>
  SMS_SENDER_ID=AgroScan
  EXPRESSO_SMS_URL=https://sms.expresso.sn/api   (URL officielle à confirmer)
"""
import logging

import requests

from app.core.config import settings
from app.services.sms.base import SMSProvider, SMSResult

logger = logging.getLogger("agroscan.sms.expresso")

# Préfixes Expresso Sénégal
EXPRESSO_PREFIXES = {"70"}


class ExpressoSMSProvider(SMSProvider):
    """
    Envoie des SMS via l'API Expresso Sénégal Business.

    Contacter Expresso Entreprises (+221 33 839 XX XX) pour l'accès API.
    """

    BASE_URL = getattr(settings, "EXPRESSO_SMS_URL", "https://sms.expresso.sn/api")
    TIMEOUT = 10

    def send(self, phone: str, message: str) -> SMSResult:
        phone_norm = self.normalize_phone(phone)
        headers = {
            "Authorization": f"Bearer {settings.SMS_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "to": phone_norm,
            "sender": settings.SMS_SENDER_ID,
            "message": message,
            "type": "text",
        }

        try:
            r = requests.post(self.BASE_URL + "/send", json=payload, headers=headers, timeout=self.TIMEOUT)
            r.raise_for_status()
            data = r.json()
            msg_id = str(data.get("id", data.get("msgId", "")))
            logger.info("Expresso SMS envoyé → %s (id=%s)", phone_norm, msg_id)
            return SMSResult(success=True, provider="expresso", message_id=msg_id)
        except requests.exceptions.HTTPError:
            logger.error("Expresso SMS HTTP error %s → %s", r.status_code, phone_norm)
            return SMSResult(success=False, provider="expresso", error=f"HTTP {r.status_code}: {r.text[:200]}")
        except requests.exceptions.RequestException as e:
            logger.error("Expresso SMS network error → %s : %s", phone_norm, str(e))
            return SMSResult(success=False, provider="expresso", error=str(e))
