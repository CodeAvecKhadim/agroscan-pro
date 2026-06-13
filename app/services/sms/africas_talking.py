"""
Provider SMS — Africa's Talking (agrégateur multi-opérateur).

Recommandé pour la production Sénégal : couvre Orange, Free, Expresso via
un seul contrat. Support officiel AT pour le Sénégal.

Documentation : https://africastalking.com/sms
Sandbox : https://sandbox.africastalking.com/

Variables d'environnement :
  SMS_PROVIDER=africas_talking
  SMS_API_KEY=<api_key_africastalking>
  SMS_USERNAME=<username_at>  (ex : "agroscan" ou "sandbox" pour tests)
  SMS_SENDER_ID=AgroScan
"""
import logging

import requests

from app.core.config import settings
from app.services.sms.base import SMSProvider, SMSResult

logger = logging.getLogger("agroscan.sms.africas_talking")

AT_LIVE_URL = "https://api.africastalking.com/version1/messaging"
AT_SANDBOX_URL = "https://api.sandbox.africastalking.com/version1/messaging"


class AfricasTalkingProvider(SMSProvider):
    """
    Envoie des SMS via Africa's Talking (supporte Orange/Free/Expresso Sénégal).

    SMS_USERNAME="sandbox" → utilise l'environnement de test AT.
    SMS_USERNAME=<votre_username> → production.
    """

    TIMEOUT = 15

    def send(self, phone: str, message: str) -> SMSResult:
        phone_norm = self.normalize_phone(phone)
        is_sandbox = settings.SMS_USERNAME == "sandbox"
        url = AT_SANDBOX_URL if is_sandbox else AT_LIVE_URL

        headers = {
            "apiKey": settings.SMS_API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "username": settings.SMS_USERNAME,
            "to": phone_norm,
            "message": message,
        }
        if settings.SMS_SENDER_ID and not is_sandbox:
            data["from"] = settings.SMS_SENDER_ID

        try:
            r = requests.post(url, data=data, headers=headers, timeout=self.TIMEOUT)
            r.raise_for_status()
            resp = r.json()
            recipients = resp.get("SMSMessageData", {}).get("Recipients", [])
            if recipients and recipients[0].get("status") == "Success":
                msg_id = recipients[0].get("messageId", "")
                logger.info("AT SMS envoyé → %s (id=%s)", phone_norm, msg_id)
                return SMSResult(success=True, provider="africas_talking", message_id=msg_id)
            else:
                err = recipients[0].get("status", "unknown") if recipients else "no recipients"
                logger.error("AT SMS refusé → %s : %s", phone_norm, err)
                return SMSResult(success=False, provider="africas_talking", error=err)
        except requests.exceptions.HTTPError:
            logger.error("AT SMS HTTP error %s → %s", r.status_code, phone_norm)
            return SMSResult(success=False, provider="africas_talking", error=f"HTTP {r.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error("AT SMS network error → %s : %s", phone_norm, str(e))
            return SMSResult(success=False, provider="africas_talking", error=str(e))
