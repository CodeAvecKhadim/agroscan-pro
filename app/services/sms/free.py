"""
Provider SMS — Free Sénégal (via passerelle HTTP).

Protocole : API HTTP REST Free Sénégal Business
Documentation : Contacter Free Sénégal Entreprises pour l'accès API

Prérequis :
  - Compte Free Sénégal Business (SMS en masse)
  - Clé API + identifiant dans settings
  - Numéro émetteur (Sender ID) approuvé

Variables d'environnement :
  SMS_PROVIDER=free
  SMS_API_KEY=<api_key_free>
  SMS_API_SECRET=<api_secret_free>
  SMS_SENDER_ID=AgroScan
  FREE_SMS_URL=https://sms.free.sn/api/v1   (URL officielle à confirmer avec Free)
"""
import logging

import requests

from app.core.config import settings
from app.services.sms.base import SMSProvider, SMSResult

logger = logging.getLogger("agroscan.sms.free")

# Préfixes Free Sénégal
FREE_PREFIXES = {"76", "75"}


class FreeSMSProvider(SMSProvider):
    """
    Envoie des SMS via l'API Free Sénégal Business.

    Protocole HTTP POST standard (formulaire ou JSON selon config Free).
    Contacter Free Entreprises (+221 33 869 XX XX) pour l'accès API.
    """

    BASE_URL = getattr(settings, "FREE_SMS_URL", "https://sms.free.sn/api/v1")
    TIMEOUT = 10

    def send(self, phone: str, message: str) -> SMSResult:
        phone_norm = self.normalize_phone(phone)
        headers = {
            "X-Api-Key": settings.SMS_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "to": phone_norm,
            "from": settings.SMS_SENDER_ID,
            "text": message,
        }
        # Certaines API Free utilisent form-encoded
        if getattr(settings, "FREE_SMS_FORM_ENCODED", False):
            payload_alt = {
                "to": phone_norm,
                "sender": settings.SMS_SENDER_ID,
                "message": message,
                "username": settings.SMS_USERNAME,
                "password": settings.SMS_API_SECRET,
            }
            try:
                r = requests.post(self.BASE_URL + "/send", data=payload_alt, timeout=self.TIMEOUT)
            except requests.exceptions.RequestException as e:
                return SMSResult(success=False, provider="free", error=str(e))
        else:
            try:
                r = requests.post(self.BASE_URL + "/messages", json=payload, headers=headers, timeout=self.TIMEOUT)
            except requests.exceptions.RequestException as e:
                logger.error("Free SMS network error → %s : %s", phone_norm, str(e))
                return SMSResult(success=False, provider="free", error=str(e))

        try:
            r.raise_for_status()
            data = r.json()
            msg_id = str(data.get("id", data.get("messageId", "")))
            logger.info("Free SMS envoyé → %s (id=%s)", phone_norm, msg_id)
            return SMSResult(success=True, provider="free", message_id=msg_id)
        except requests.exceptions.HTTPError:
            logger.error("Free SMS HTTP error %s → %s", r.status_code, phone_norm)
            return SMSResult(success=False, provider="free", error=f"HTTP {r.status_code}: {r.text[:200]}")
