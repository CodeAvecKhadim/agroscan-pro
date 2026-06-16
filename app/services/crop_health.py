"""
Service de reconnaissance de maladie par photo — API Kindwise crop.health.

La clé API reste côté serveur (jamais exposée au navigateur).
Doc : https://crop.kindwise.com/docs
"""
import base64
import io
import logging
from typing import List, Optional

import requests
from PIL import Image

from app.core.config import settings

log = logging.getLogger(__name__)

API_URL   = "https://crop.kindwise.com/api/v1/identification"
USAGE_URL = "https://crop.kindwise.com/api/v1/usage_info"
_CREDITS_ALERTE = 50
_MAX_PX = 1024


class CropHealthError(Exception):
    """Erreur lors de l'appel à l'API crop.health."""
    pass


def _resize(image_bytes: bytes) -> bytes:
    """Redimensionne l'image si la plus grande dimension dépasse _MAX_PX."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        fmt = (img.format or "JPEG").upper()
        if fmt == "JPG":
            fmt = "JPEG"
        if max(img.size) > _MAX_PX:
            img.thumbnail((_MAX_PX, _MAX_PX), Image.LANCZOS)
            log.debug("Image redimensionnée → %s", img.size)
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=85, optimize=True)
        return buf.getvalue()
    except Exception as e:
        log.warning("Resize impossible, image brute envoyée : %s", e)
        return image_bytes


def get_remaining_credits() -> int:
    """Retourne les crédits Kindwise restants (-1 si indisponible). Log alerte si bas."""
    cle = settings.CROP_HEALTH_API_KEY
    if not cle:
        return -1
    try:
        r = requests.get(USAGE_URL, headers={"Api-Key": cle}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Structure réelle : {"remaining": {"total": 58.0}, "used": {...}}
            remaining_raw = data.get("remaining", {}).get("total", -1)
            if remaining_raw is not None and remaining_raw >= 0:
                remaining = int(remaining_raw)
                if remaining < _CREDITS_ALERTE:
                    log.warning(
                        "KINDWISE CRÉDITS BAS : %d restant(s) — renouveler la clé API.",
                        remaining,
                    )
                return remaining
    except Exception as e:
        log.debug("Usage info Kindwise indisponible : %s", e)
    return -1


def identifier_maladie(
    images_bytes: List[bytes],
    langue: str = "fr",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> dict:
    """
    Envoie jusqu'à 5 images à crop.health et renvoie un diagnostic normalisé.

    Retourne :
      {
        "disponible": bool,
        "maladies": [{"nom", "certitude", "symptomes", "cause", "traitement"}],
        "credits_restants": int,
      }
    """
    cle = settings.CROP_HEALTH_API_KEY
    if not cle:
        raise CropHealthError("Clé API crop.health absente (CROP_HEALTH_API_KEY).")

    credits_restants = get_remaining_credits()

    # Redimensionner + encoder (max 5 images)
    images_b64 = [
        base64.b64encode(_resize(img)).decode("ascii")
        for img in images_bytes[:5]
    ]

    payload: dict = {"images": images_b64}
    if latitude is not None and longitude is not None:
        payload["latitude"] = latitude
        payload["longitude"] = longitude

    params = {
        "details": "common_names,description,treatment",
        "language": langue,
    }
    headers = {
        "Content-Type": "application/json",
        "Api-Key": cle,
    }

    try:
        r = requests.post(API_URL, params=params, json=payload, headers=headers, timeout=30)
    except requests.RequestException as e:
        raise CropHealthError(f"Connexion à crop.health impossible : {e}")

    if r.status_code in (401, 403):
        raise CropHealthError("Clé API crop.health invalide ou non autorisée.")
    if r.status_code == 429:
        raise CropHealthError("Quota crop.health dépassé (crédits épuisés).")
    if r.status_code >= 500:
        raise CropHealthError(f"Erreur serveur crop.health ({r.status_code}). Réessayez ultérieurement.")
    if r.status_code >= 400:
        raise CropHealthError(f"crop.health a renvoyé une erreur {r.status_code}.")

    try:
        data = r.json()
    except ValueError:
        raise CropHealthError("Réponse crop.health illisible (JSON invalide).")

    if not data:
        return {"disponible": False, "maladies": [], "credits_restants": credits_restants}

    result = _normaliser(data)
    result["credits_restants"] = credits_restants
    return result


def _normaliser(data: dict) -> dict:
    """Transforme la réponse brute crop.health en format AgroScan."""
    maladies = []
    try:
        suggestions = (
            data.get("result", {})
                .get("disease", {})
                .get("suggestions", [])
        )
    except AttributeError:
        suggestions = []

    for s in suggestions[:3]:
        details = s.get("details", {}) or {}
        symptomes = None
        traitement = None

        desc = details.get("description")
        if isinstance(desc, dict):
            symptomes = desc.get("value")
        elif isinstance(desc, str):
            symptomes = desc

        trait = details.get("treatment")
        if isinstance(trait, dict):
            parts = []
            for cle_t in ("prevention", "biological", "chemical"):
                v = trait.get(cle_t)
                if isinstance(v, list):
                    parts.extend(v)
                elif isinstance(v, str):
                    parts.append(v)
            traitement = " ".join(parts) if parts else None
        elif isinstance(trait, str):
            traitement = trait

        maladies.append({
            "nom": s.get("name", "Inconnu"),
            "certitude": round(float(s.get("probability", 0)) * 100),
            "symptomes": symptomes,
            "cause": None,
            "traitement": traitement,
        })

    return {"disponible": len(maladies) > 0, "maladies": maladies}
