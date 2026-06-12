"""
Traduction NDVI/NDWI → message simple pour le producteur.
Le producteur ne voit JAMAIS de chiffre — uniquement une phrase + couleur.
"""
from typing import Optional


def ndvi_to_message(
    ndvi: Optional[float],
    ndwi: Optional[float] = None,
    source: str = "sentinel-2",
    lang: str = "fr",
) -> tuple[str, str]:
    """Retourne (message_simple, couleur) où couleur ∈ {vert, orange, rouge}.

    NDVI élevé = bonne végétation.
    NDWI négatif = stress hydrique potentiel.
    """
    if ndvi is None:
        return "Données satellite non disponibles pour cette parcelle.", "orange"

    stress_eau = ndwi is not None and ndwi < -0.15

    if ndvi >= 0.6:
        msg = "Votre champ va très bien. La végétation est vigoureuse."
        couleur = "vert"
    elif ndvi >= 0.4:
        if stress_eau:
            msg = "Votre culture est en bon état, mais un risque de stress hydrique est détecté. Pensez à l'irrigation."
            couleur = "orange"
        else:
            msg = "Votre champ est en bon état général."
            couleur = "vert"
    elif ndvi >= 0.2:
        if stress_eau:
            msg = "Risque de stress hydrique détecté. Un arrosage est recommandé."
            couleur = "orange"
        else:
            msg = "Une baisse de vigueur est détectée sur votre culture. Surveillez l'évolution."
            couleur = "orange"
    else:
        msg = "Une anomalie a été détectée sur la parcelle. Un conseiller peut vérifier."
        couleur = "rouge"

    if source in ("simule", "simule_fallback"):
        msg += " (estimation saisonnière — pas d'image satellite récente)"

    return msg, couleur
