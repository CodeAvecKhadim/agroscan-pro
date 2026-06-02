"""
Démo autonome du moteur de fertilité — à lancer sans serveur :
    python demo_fertilite.py

Illustre l'interprétation sur des profils de sols sénégalais types.
"""
from app.services.fertilite import MoteurFertilite, AnalyseSol, Texture

moteur = MoteurFertilite()

CAS = {
    "Sol dior dégradé — Diourbel": AnalyseSol(
        ph=5.2, ce=0.3, azote=0.04, phosphore=9, potassium=55,
        matiere_organique=0.4, texture=Texture.SABLEUX),
    "Tanne salée — Fatick": AnalyseSol(
        ph=7.8, ce=3.2, azote=0.08, phosphore=20, potassium=180,
        matiere_organique=1.2, texture=Texture.ARGILEUX),
    "Terre maraîchère — Niayes": AnalyseSol(
        ph=6.5, ce=0.5, azote=0.18, phosphore=45, potassium=220,
        matiere_organique=2.4, texture=Texture.LIMONEUX),
    "Sol ferrallitique — Casamance": AnalyseSol(
        ph=4.3, ce=0.2, azote=0.10, phosphore=12, potassium=90,
        matiere_organique=1.8, texture=Texture.LIMONO_ARGILEUX),
}


def afficher(titre, analyse):
    d = moteur.diagnostiquer(analyse)
    print("=" * 74)
    print(f"  {titre}")
    print("=" * 74)
    print(f"  NIVEAU DE FERTILITÉ : {d.niveau_fertilite.value}  (score {d.score_sur_100}/100)\n")
    print("  ▸ Diagnostic général :")
    print(f"    {d.diagnostic_general}\n")
    if d.carences:
        print("  ▸ Carences :", ", ".join(c.split(' :')[0] for c in d.carences))
    if d.exces:
        print("  ▸ Excès :", ", ".join(e.split(' :')[0] for e in d.exces))
    if d.contraintes:
        print("  ▸ Contraintes :")
        for c in d.contraintes:
            print(f"      - {c}")
    if d.risques:
        print("  ▸ Risques :")
        for r in d.risques:
            print(f"      - {r}")
    print("  ▸ Cultures recommandées :", ", ".join(d.cultures_recommandees))
    if d.actions_correctives:
        print("  ▸ Actions correctives :")
        for a in d.actions_correctives:
            print(f"      • {a}")
    print()


if __name__ == "__main__":
    for titre, analyse in CAS.items():
        afficher(titre, analyse)
    print("⚖️  Outil d'orientation (~70 %). Confirmer par ISRA / ANCAR pour toute décision importante.")
