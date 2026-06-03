"""
Service de reconnaissance de maladie par photo — API Kindwise crop.health.

La photo (encodée en base64) est envoyée à crop.health, qui renvoie une liste
de maladies/ravageurs possibles avec leur probabilité. On normalise la réponse
pour notre interface : nom, certitude (%), et — si disponibles — symptômes,
cause et traitement.

La clé API reste côté serveur (jamais exposée au navigateur).
Doc : https://crop.kindwise.com/docs
"""
import base64
import requests

from app.core.config import settings

# Point d'entrée de l'API d'identification crop.health
API_URL = "https://crop.kindwise.com/api/v1/identification"


class CropHealthError(Exception):
    """Erreur lors de l'appel à l'API crop.health."""
    pass


def identifier_maladie(image_bytes: bytes, langue: str = "fr") -> dict:
    """
    Envoie une image à crop.health et renvoie un diagnostic normalisé.

    Renvoie un dict :
      {
        "disponible": True/False,
        "maladies": [
            {"nom": str, "certitude": int (0-100),
             "symptomes": str|None, "cause": str|None, "traitement": str|None}
        ]
      }
    """
    cle = settings.CROP_HEALTH_API_KEY
    if not cle:
        raise CropHealthError("Clé API crop.health absente (CROP_HEALTH_API_KEY).")

    # L'image est transmise en base64 dans le corps JSON.
    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    payload = {
        "images": [image_b64],
    }
    # details et language doivent passer en parametres d'URL (exigence Kindwise)
    params = {
        "details": "common_names,description,treatment",
        "language": langue,
    }
    headers = {
        "Content-Type": "application/json",
        "Api-Key": cle,            # authentification Kindwise
    }

    try:
        r = requests.post(API_URL, params=params, json=payload, headers=headers, timeout=30)
    except requests.RequestException as e:
        raise CropHealthError(f"Connexion à crop.health impossible : {e}")

    if r.status_code in (401, 403):
        raise CropHealthError("Clé API crop.health invalide ou non autorisée.")
    if r.status_code == 429:
        raise CropHealthError("Quota crop.health dépassé (crédits épuisés).")
    if r.status_code >= 400:
        raise CropHealthError(f"crop.health a renvoyé une erreur {r.status_code}.")

    data = r.json()
    return _normaliser(data)


def _normaliser(data: dict) -> dict:
    """
    Transforme la réponse brute de crop.health en format simple pour l'interface.
    La structure Kindwise place les suggestions dans
    result -> disease -> suggestions (liste triée par probabilité).
    """
    maladies = []
    try:
        suggestions = (
            data.get("result", {})
                .get("disease", {})
                .get("suggestions", [])
        )
    except AttributeError:
        suggestions = []

    for s in suggestions[:3]:   # on garde les 3 plus probables
        details = s.get("details", {}) or {}
        # description et traitement peuvent être des chaînes ou des structures
        symptomes = None
        traitement = None
        desc = details.get("description")
        if isinstance(desc, dict):
            symptomes = desc.get("value")
        elif isinstance(desc, str):
            symptomes = desc
        trait = details.get("treatment")
        if isinstance(trait, dict):
            # treatment peut contenir biological / chemical / prevention
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
