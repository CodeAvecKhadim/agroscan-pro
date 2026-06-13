"""
Provider SMS — Orange Sénégal.

Protocole : Orange Business Services (OBS) OneAPI SMS REST
Documentation : https://developer.orange.com/apis/sms-sn/

Prérequis :
  - Compte développeur Orange Business
  - Clé API dans SMS_API_KEY (settings)
  - Numéro émetteur approuvé dans SMS_SENDER_ID (ex : "AgroScan")

Variables d'environnement :
  SMS_PROVIDER=orange
  SMS_API_KEY=<bearer_token_orange_obs>
  SMS_API_SECRET=<optionnel_selon_auth>
  SMS_SENDER_ID=AgroScan
  ORANGE_SMS_URL=https://api.orange.com/smsmessaging/v1
"""
import logging

import requests

from app.core.config import settings
from app.services.sms.base import SMSProvider, SMSResult

logger = logging.getLogger("agroscan.sms.orange")

# Préfixes Orange Sénégal (mise à jour 2024)
ORANGE_PREFIXES = {"77", "78", "76"}  # 76 = Free mais routé via Orange dans certains cas


class OrangeSMSProvider(SMSProvider):
    """
    Envoie des SMS via l'API Orange Business Services.

    L'API suit la norme OMA OneAPI SMS :
    POST /smsmessaging/v1/outbound/tel%3A%2B{sender}/requests
    """

    BASE_URL = getattr(settings, "ORANGE_SMS_URL", "https://api.orange.com/smsmessaging/v1")
    TIMEOUT = 10  # secondes

    def send(self, phone: str, message: str) -> SMSResult:
        phone_norm = self.normalize_phone(phone)
        sender = self.normalize_phone(settings.SMS_SENDER_ID) if settings.SMS_SENDER_ID.startswith("0") else settings.SMS_SENDER_ID

        url = f"{self.BASE_URL}/outbound/tel%3A%2B221{settings.SMS_SENDER_ID}/requests"
        headers = {
            "Authorization": f"Bearer {settings.SMS_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "outboundSMSMessageRequest": {
                "address": [f"tel:{phone_norm}"],
                "senderAddress": f"tel:+221{settings.SMS_SENDER_ID}",
                "outboundSMSTextMessage": {"message": message},
            }
        }

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=self.TIMEOUT)
            r.raise_for_status()
            data = r.json()
            msg_id = (
                data.get("outboundSMSMessageRequest", {})
                    .get("resourceURL", "")
                    .split("/")[-1]
            )
            logger.info("Orange SMS envoyé → %s (id=%s)", phone_norm, msg_id)
            return SMSResult(success=True, provider="orange", message_id=msg_id)
        except requests.exceptions.HTTPError as e:
            logger.error("Orange SMS HTTP error %s → %s : %s", r.status_code, phone_norm, r.text)
            return SMSResult(success=False, provider="orange", error=f"HTTP {r.status_code}: {r.text[:200]}")
        except requests.exceptions.RequestException as e:
            logger.error("Orange SMS network error → %s : %s", phone_norm, str(e))
            return SMSResult(success=False, provider="orange", error=str(e))
