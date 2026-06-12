"""
Service de notifications AgroScan Pro.

Envoi de notifications via webhook HTTP (Wave/Orange Money callback, Slack, n8n, etc.).
Extensible vers SMS (Twilio/Africa's Talking) en ajoutant le provider dans .env.

Configuration dans .env :
  NOTIFICATION_WEBHOOK_URL=https://hooks.example.com/agroscan
  NOTIFICATION_SECRET=mon_secret
  SMS_PROVIDER=           # vide = désactivé | africastalking | twilio
  SMS_API_KEY=
  SMS_SENDER_ID=AgroScan
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

# ── Schéma interne d'une notification ────────────────────────────────────────

def _build_payload(
    event: str,
    parcelle_id: Optional[int] = None,
    org_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "app": "agroscan-pro",
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parcelle_id": parcelle_id,
        "org_id": org_id,
        "data": data or {},
    }


def _sign(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


# ── Webhook ──────────────────────────────────────────────────────────────────

async def send_webhook(
    event: str,
    parcelle_id: Optional[int] = None,
    org_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """Envoie une notification webhook. Retourne True si succès."""
    url = getattr(settings, "NOTIFICATION_WEBHOOK_URL", "")
    if not url:
        return False

    payload = _build_payload(event, parcelle_id, org_id, data)
    body = json.dumps(payload).encode()

    secret = getattr(settings, "NOTIFICATION_SECRET", "")
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-AgroScan-Signature"] = _sign(body, secret)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, content=body, headers=headers)
        if r.status_code >= 400:
            log.warning("Webhook %s répondu %s", event, r.status_code)
            return False
        return True
    except Exception as exc:
        log.error("Webhook %s erreur: %s", event, exc)
        return False


# ── SMS via Africa's Talking ─────────────────────────────────────────────────

async def send_sms(phone: str, message: str) -> bool:
    """Envoie un SMS. Retourne True si succès."""
    provider = getattr(settings, "SMS_PROVIDER", "")
    api_key = getattr(settings, "SMS_API_KEY", "")
    sender = getattr(settings, "SMS_SENDER_ID", "AgroScan")

    if not provider or not api_key:
        log.debug("SMS désactivé (SMS_PROVIDER ou SMS_API_KEY absent)")
        return False

    if provider == "africastalking":
        username = getattr(settings, "SMS_USERNAME", "sandbox")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    "https://api.africastalking.com/version1/messaging",
                    headers={
                        "Accept": "application/json",
                        "apiKey": api_key,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={
                        "username": username,
                        "to": phone,
                        "message": message,
                        "from": sender,
                    },
                )
            if r.status_code == 201:
                return True
            log.warning("SMS AT status %s: %s", r.status_code, r.text[:200])
            return False
        except Exception as exc:
            log.error("SMS AT erreur: %s", exc)
            return False

    log.warning("SMS provider inconnu: %s", provider)
    return False


# ── Événements métier ─────────────────────────────────────────────────────────

async def notifier_anomalie_satellite(
    parcelle_id: int, org_id: int, culture: str, ndvi: float, message: str,
    phone: Optional[str] = None,
) -> None:
    """Déclenche webhook + SMS si anomalie satellite (NDVI rouge)."""
    data = {"culture": culture, "ndvi": ndvi, "message_simple": message}
    await send_webhook("anomalie_satellite", parcelle_id=parcelle_id, org_id=org_id, data=data)
    if phone:
        sms = f"AgroScan - Alerte {culture}: {message[:100]}"
        await send_sms(phone, sms)


async def notifier_activite_retard(
    parcelle_id: int, org_id: int, activite: str, jours_retard: int,
    phone: Optional[str] = None,
) -> None:
    """Déclenche webhook + SMS si activité en retard."""
    data = {"activite": activite, "jours_retard": jours_retard}
    await send_webhook("activite_retard", parcelle_id=parcelle_id, org_id=org_id, data=data)
    if phone:
        sms = f"AgroScan - {activite} en retard de {jours_retard}j. Vérifiez votre calendrier."
        await send_sms(phone, sms)
