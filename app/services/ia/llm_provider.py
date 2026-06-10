"""
Abstraction Claude API — via SDK anthropic.
Fallback rules engine si clé API absente.
"""
import logging
import os
import time
from typing import Optional

log = logging.getLogger(__name__)

_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _client():
    """Retourne le client Anthropic. Lève RuntimeError si clé absente."""
    if not _API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY non configurée")
    import anthropic
    return anthropic.Anthropic(api_key=_API_KEY)


def disponible() -> bool:
    return bool(_API_KEY and _API_KEY.strip())


def chat(
    messages: list[dict],
    system: str,
    modele: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1500,
    temperature: float = 0.3,
) -> dict:
    """
    Appel Claude API.
    messages : [{role: "user"|"assistant", content: str}, ...]
    Retourne : {contenu, tokens_in, tokens_out, modele, duree_ms}
    """
    if not disponible():
        raise RuntimeError("ANTHROPIC_API_KEY non configurée")

    client = _client()
    t0 = time.perf_counter()

    try:
        response = client.messages.create(
            model=modele,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            temperature=temperature,
        )
    except Exception as e:
        log.error("Claude API erreur: %s", e)
        raise RuntimeError(f"IA indisponible : {e}")

    duree_ms = int((time.perf_counter() - t0) * 1000)
    contenu = response.content[0].text if response.content else ""

    return {
        "contenu":    contenu,
        "tokens_in":  response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "modele":     response.model,
        "duree_ms":   duree_ms,
    }


def chat_extraction(texte: str, system: str) -> Optional[list]:
    """
    Appel Claude dédié à l'extraction de recommandations structurées.
    Retourne liste de dicts ou None si échec.
    """
    if not disponible():
        return None

    try:
        result = chat(
            messages=[{"role": "user", "content": f"Texte à analyser :\n{texte}"}],
            system=system,
            modele="claude-haiku-4-5-20251001",
            max_tokens=800,
            temperature=0.0,
        )
        import json
        contenu = result["contenu"].strip()
        # Claude peut entourer de ```json ... ```
        if contenu.startswith("```"):
            contenu = contenu.split("```")[1]
            if contenu.startswith("json"):
                contenu = contenu[4:]
        return json.loads(contenu)
    except Exception as e:
        log.warning("Extraction JSON échouée: %s", e)
        return None
