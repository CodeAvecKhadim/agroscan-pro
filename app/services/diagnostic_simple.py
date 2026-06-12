"""
Traduction diagnostic Kindwise → phrase simple pour le producteur.
Le producteur ne voit jamais les noms de maladies ou les probabilités.
"""


def phrase_etat(diagnostic: dict) -> tuple[str, bool]:
    """Retourne (etat_simple, anomalie).

    Rules:
    - Pas de résultat → phrase neutre, pas d'anomalie
    - Top maladie ≥ 70% → anomalie confirmée
    - Top maladie 40-69% → signe inhabituel, anomalie signalée
    - < 40% → tout va bien
    """
    if not diagnostic or not diagnostic.get("disponible"):
        return "Impossible d'analyser la photo. Vérifiez la qualité de l'image.", False

    maladies = diagnostic.get("maladies", [])
    if not maladies:
        return "Votre culture semble en bonne santé.", False

    top = maladies[0]
    certitude = top.get("certitude", 0)

    if certitude >= 70:
        return "Une anomalie a été détectée sur votre culture. Un conseiller va vérifier.", True
    if certitude >= 40:
        return "Un signe inhabituel a été repéré. Surveillez et envoyez une autre photo si ça empire.", True
    return "Votre culture semble en bonne santé.", False
