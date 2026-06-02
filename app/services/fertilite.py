"""
================================================================================
 MOTEUR D'INTERPRÉTATION DE LA FERTILITÉ DES SOLS — AgroScan Pro / Social Technologie
================================================================================
Conçu selon l'approche agronomique ISRA / CDH pour les sols d'Afrique de l'Ouest.

ENTRÉE : une analyse de sol (laboratoire ou kit terrain) avec :
    pH (eau), CE (conductivité électrique, dS/m ou µS/cm), N total (%),
    P assimilable (ppm/mg/kg), K échangeable (ppm/mg/kg ou meq/100g),
    matière organique (%), texture (sableux / limoneux / argileux / …).

SORTIE : un diagnostic structuré (voir la dataclass DiagnosticSol) avec :
    - niveau de fertilité (Très faible → Excellent)
    - carences et excès détectés
    - contraintes agronomiques (acidité, salinité, sodicité…)
    - diagnostic en français simple ET diagnostic technique
    - cultures recommandées et actions correctives chiffrées

PRINCIPE CLÉ : les seuils sont MODULÉS PAR LA TEXTURE. Un sol sableux (faible
capacité d'échange) tolère moins et retient moins que l'argile : un même chiffre
ne se juge pas de la même façon. C'est le cœur de l'expertise encodée ici.

⚠️ Outil d'orientation (~70 %). Ne remplace pas l'analyse certifiée d'un laboratoire
   (ISRA Hann / LNRPV) ni l'avis d'un technicien ANCAR.
================================================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# ----------------------------------------------------------------------------
#  ÉNUMÉRATIONS
# ----------------------------------------------------------------------------
class NiveauFertilite(str, Enum):
    TRES_FAIBLE = "Très faible"
    FAIBLE = "Faible"
    MOYEN = "Moyen"
    BON = "Bon"
    EXCELLENT = "Excellent"


class Texture(str, Enum):
    SABLEUX = "sableux"        # sols "dior" — Diourbel, Louga, Kaffrine
    SABLO_LIMONEUX = "sablo-limoneux"
    LIMONEUX = "limoneux"
    LIMONO_ARGILEUX = "limono-argileux"
    ARGILEUX = "argileux"      # sols "deck" / vertisols — bas-fonds, vallée


class Statut(str, Enum):
    CARENCE_SEVERE = "carence sévère"
    CARENCE = "carence"
    OPTIMAL = "optimal"
    EXCES = "excès"
    EXCES_SEVERE = "excès sévère"


# ----------------------------------------------------------------------------
#  STRUCTURES DE DONNÉES
# ----------------------------------------------------------------------------
@dataclass
class AnalyseSol:
    """Les variables d'entrée d'une analyse de sol."""
    ph: Optional[float] = None              # pH eau
    ce: Optional[float] = None              # conductivité électrique
    ce_unite: str = "dS/m"                  # "dS/m" ou "µS/cm" (converti en interne)
    azote: Optional[float] = None           # N total, en %
    phosphore: Optional[float] = None       # P assimilable, en mg/kg (ppm)
    potassium: Optional[float] = None       # K échangeable, en mg/kg (ppm)
    matiere_organique: Optional[float] = None   # MO, en %
    texture: Optional[Texture] = None

    def ce_ds_m(self) -> Optional[float]:
        """Normalise la CE en dS/m (1 dS/m = 1000 µS/cm)."""
        if self.ce is None:
            return None
        return self.ce / 1000.0 if self.ce_unite == "µS/cm" else self.ce


@dataclass
class EvaluationParametre:
    """Évaluation d'un paramètre : sa valeur, son statut, sa plage de référence."""
    parametre: str
    valeur: Optional[float]
    unite: str
    statut: Statut
    plage_ref: str
    commentaire: str = ""


@dataclass
class DiagnosticSol:
    """Le diagnostic complet renvoyé par le moteur."""
    niveau_fertilite: NiveauFertilite
    score_sur_100: int
    diagnostic_general: str                 # français simple
    diagnostic_technique: str               # vocabulaire agronomique
    evaluations: list = field(default_factory=list)      # EvaluationParametre[]
    carences: list = field(default_factory=list)         # str[]
    exces: list = field(default_factory=list)            # str[]
    contraintes: list = field(default_factory=list)      # str[]
    risques: list = field(default_factory=list)          # str[]
    cultures_recommandees: list = field(default_factory=list)  # str[]
    actions_correctives: list = field(default_factory=list)    # str[]
    avertissement: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["niveau_fertilite"] = self.niveau_fertilite.value
        d["evaluations"] = [
            {**asdict(e), "statut": e.statut.value} for e in self.evaluations
        ]
        return d


# ----------------------------------------------------------------------------
#  RÉFÉRENTIELS AGRONOMIQUES (modulés par la texture)
# ----------------------------------------------------------------------------
# Coefficient d'ajustement des seuils nutritifs selon la texture.
# Un sol sableux a une faible CEC : on relève les seuils de "suffisance" car les
# nutriments y sont moins retenus et plus vite lessivés.
COEF_TEXTURE = {
    Texture.SABLEUX:         1.00,   # référence basse (faible rétention)
    Texture.SABLO_LIMONEUX:  1.10,
    Texture.LIMONEUX:        1.20,
    Texture.LIMONO_ARGILEUX: 1.30,
    Texture.ARGILEUX:        1.40,   # forte rétention : seuils de suffisance plus hauts
}

# Seuils de BASE (référence sol sableux). [carence_severe<, carence<, exces>, exces_severe>]
# P et K en mg/kg ; N et MO en %.
SEUILS_BASE = {
    "azote":     {"car_sev": 0.03, "car": 0.06, "exc": 0.30, "exc_sev": 0.50, "unite": "%"},
    "phosphore": {"car_sev": 8,    "car": 15,   "exc": 80,   "exc_sev": 150,  "unite": "mg/kg"},
    "potassium": {"car_sev": 40,   "car": 80,   "exc": 300,  "exc_sev": 500,  "unite": "mg/kg"},
}

# La matière organique a ses propres classes (clé de la fertilité au Sénégal).
SEUILS_MO = {"tres_faible": 0.5, "faible": 1.0, "moyen": 2.0, "bon": 3.0, "unite": "%"}


# ----------------------------------------------------------------------------
#  MOTEUR
# ----------------------------------------------------------------------------
class MoteurFertilite:
    """Interprète une analyse de sol et produit un diagnostic agronomique complet."""

    def diagnostiquer(self, a: AnalyseSol) -> DiagnosticSol:
        evals: list[EvaluationParametre] = []
        carences, exces, contraintes, risques, actions = [], [], [], [], []

        coef = COEF_TEXTURE.get(a.texture, 1.15)  # défaut ~ sablo-limoneux

        # --- 1) pH ---
        if a.ph is not None:
            evals.append(self._eval_ph(a.ph, contraintes, risques, actions))

        # --- 2) Salinité (CE) ---
        ce = a.ce_ds_m()
        if ce is not None:
            evals.append(self._eval_ce(ce, contraintes, risques, actions))

        # --- 3) Matière organique (pivot) ---
        if a.matiere_organique is not None:
            evals.append(self._eval_mo(a.matiere_organique, carences, contraintes, actions))

        # --- 4) Azote ---
        if a.azote is not None:
            evals.append(self._eval_nutriment("azote", "Azote (N)", a.azote, coef,
                                              carences, exces, risques, actions))
        # --- 5) Phosphore ---
        if a.phosphore is not None:
            evals.append(self._eval_nutriment("phosphore", "Phosphore (P)", a.phosphore, coef,
                                              carences, exces, risques, actions))
        # --- 6) Potassium ---
        if a.potassium is not None:
            evals.append(self._eval_nutriment("potassium", "Potassium (K)", a.potassium, coef,
                                              carences, exces, risques, actions))

        # --- 7) Texture : contrainte structurelle ---
        if a.texture:
            self._eval_texture(a.texture, contraintes, risques, actions)

        # --- Score & niveau de fertilité ---
        score = self._score(a, evals)
        niveau = self._niveau(score)
        niveau = self._plafonner(niveau, a, evals)   # loi du minimum (Liebig)

        # --- Cultures recommandées ---
        cultures = self._cultures(a, niveau)

        # --- Rédaction des deux diagnostics ---
        diag_simple = self._redaction_simple(niveau, carences, exces, contraintes)
        diag_tech = self._redaction_technique(a, evals, niveau, score)

        return DiagnosticSol(
            niveau_fertilite=niveau,
            score_sur_100=score,
            diagnostic_general=diag_simple,
            diagnostic_technique=diag_tech,
            evaluations=evals,
            carences=carences,
            exces=exces,
            contraintes=contraintes,
            risques=risques,
            cultures_recommandees=cultures,
            actions_correctives=self._dedupe(actions),
            avertissement=("Diagnostic d'orientation (~70 %). Pour une décision importante, "
                           "confirmez par une analyse de laboratoire (ISRA Hann +221 33 832 84 26 / "
                           "LNRPV) ou un technicien ANCAR (+221 33 869 73 00)."),
        )

    # ---------------- Évaluations unitaires ----------------
    def _eval_ph(self, ph, contraintes, risques, actions) -> EvaluationParametre:
        if ph < 4.5:
            st, com = Statut.CARENCE_SEVERE, "Sol très acide : toxicité aluminique probable."
            contraintes.append("Acidité très forte (pH < 4.5) — toxicité aluminique et manganique.")
            risques.append("Blocage du phosphore et de molybdène ; racines brûlées par l'aluminium.")
            actions.append("Chaulage prioritaire : 2 à 4 t/ha de chaux agricole (CaCO₃), "
                           "4 à 6 semaines AVANT le semis. Re-tester ensuite.")
        elif ph < 5.5:
            st, com = Statut.CARENCE, "Sol acide : courant en Casamance, Kolda, Kédougou."
            contraintes.append("Acidité (pH 4.5–5.5) — disponibilité réduite de P, Ca, Mg.")
            actions.append("Chaulage léger : 1 à 2 t/ha de chaux agricole avant le semis.")
        elif ph <= 7.2:
            st, com = Statut.OPTIMAL, "pH favorable à la plupart des cultures."
        elif ph <= 8.5:
            st, com = Statut.EXCES, "Sol basique : risque de carences en fer, zinc, manganèse."
            contraintes.append("Alcalinité (pH 7.2–8.5) — blocage des oligo-éléments (Fe, Zn, Mn).")
            actions.append("Apporter du soufre agricole (300–600 kg/ha) et de la matière "
                           "organique pour abaisser progressivement le pH.")
        else:
            st, com = Statut.EXCES_SEVERE, "Sol très basique : suspicion de sodicité."
            contraintes.append("pH > 8.5 — suspicion de sol sodique (Na échangeable élevé).")
            risques.append("Structure dégradée, infiltration nulle. Analyser le sodium (ESP/SAR).")
            actions.append("Apport de gypse (CaSO₄) + lessivage contrôlé ; faire analyser le sodium.")
        return EvaluationParametre("pH", ph, "—", st, "5.5 – 7.2 (optimal)", com)

    def _eval_ce(self, ce, contraintes, risques, actions) -> EvaluationParametre:
        # CE en dS/m sur extrait — seuils FAO de salinité.
        if ce < 0.6:
            st, com = Statut.OPTIMAL, "Pas de problème de salinité."
        elif ce < 1.2:
            st, com = Statut.EXCES, "Légèrement salé : sensible pour cultures délicates."
            contraintes.append("Salinité légère (CE 0.6–1.2 dS/m).")
            risques.append("Cultures sensibles (oignon, carotte, laitue, haricot) pénalisées.")
        elif ce < 2.5:
            st, com = Statut.EXCES, "Salinité modérée : rendements réduits."
            contraintes.append("Salinité modérée (CE 1.2–2.5 dS/m) — fréquente à Fatick, Kaolack, delta.")
            risques.append("Baisse de rendement de 10–25 % sur cultures moyennement tolérantes.")
            actions.append("Améliorer le drainage et lessiver à l'eau douce ; apport de gypse "
                           "si sol salé-sodique. Privilégier des variétés tolérantes (riz Sahel).")
        else:
            st, com = Statut.EXCES_SEVERE, "Sol salé : la plupart des cultures souffrent."
            contraintes.append("Salinité forte (CE > 2.5 dS/m) — tannes salées du Sine-Saloum.")
            risques.append("Stress hydrique physiologique : la plante ne peut plus absorber l'eau.")
            actions.append("Drainage + lessivage intensifs, gypse, et cultures très tolérantes "
                           "uniquement. Envisager des aménagements anti-sel.")
        return EvaluationParametre("Conductivité (CE)", round(ce, 2), "dS/m", st,
                                   "< 0.6 dS/m (non salé)", com)

    def _eval_mo(self, mo, carences, contraintes, actions) -> EvaluationParametre:
        s = SEUILS_MO
        if mo < s["tres_faible"]:
            st = Statut.CARENCE_SEVERE
            com = "Sol très pauvre en humus — cas fréquent des sols dior dégradés."
            carences.append("Matière organique très faible (< 0.5 %).")
            contraintes.append("Sol biologiquement pauvre : faible rétention d'eau et de nutriments.")
            actions.append("Apport organique massif : fumier bien décomposé 5–10 t/ha ou compost, "
                           "+ enfouissement des résidus. C'est la PRIORITÉ n°1.")
        elif mo < s["faible"]:
            st = Statut.CARENCE
            com = "Teneur en humus faible."
            carences.append("Matière organique faible (0.5–1 %).")
            actions.append("Apport de fumier/compost 3–5 t/ha et restitution des résidus de culture.")
        elif mo < s["moyen"]:
            st = Statut.OPTIMAL
            com = "Teneur correcte pour les sols tropicaux."
        elif mo < s["bon"]:
            st = Statut.OPTIMAL
            com = "Bonne teneur en matière organique."
        else:
            st = Statut.EXCES
            com = "Teneur élevée — entretenir sans surcharge."
        return EvaluationParametre("Matière organique", mo, "%", st,
                                   "1.5 – 3 % (favorable)", com)

    def _eval_nutriment(self, key, label, val, coef, carences, exces, risques, actions) -> EvaluationParametre:
        s = SEUILS_BASE[key]
        # Modulation des seuils par la texture (sauf l'azote, exprimé en % MO-dépendant).
        if key == "azote":
            car_sev, car, exc, exc_sev = s["car_sev"], s["car"], s["exc"], s["exc_sev"]
        else:
            car_sev = s["car_sev"] * coef
            car = s["car"] * coef
            exc = s["exc"] * coef
            exc_sev = s["exc_sev"] * coef

        if val < car_sev:
            st = Statut.CARENCE_SEVERE
            carences.append(f"{label} : carence sévère.")
            actions.append(self._action_carence(key, severe=True))
        elif val < car:
            st = Statut.CARENCE
            carences.append(f"{label} : carence.")
            actions.append(self._action_carence(key, severe=False))
        elif val <= exc:
            st = Statut.OPTIMAL
        elif val <= exc_sev:
            st = Statut.EXCES
            exces.append(f"{label} : excès.")
            actions.append(self._action_exces(key))
        else:
            st = Statut.EXCES_SEVERE
            exces.append(f"{label} : excès marqué.")
            risques.append(f"Excès de {label.lower()} : déséquilibre et risque environnemental.")
            actions.append(self._action_exces(key))

        plage = (f"{car:.2f}–{exc:.2f} {s['unite']}" if key == "azote"
                 else f"{car:.0f}–{exc:.0f} {s['unite']}")
        return EvaluationParametre(label, val, s["unite"], st, plage,
                                   "Seuil ajusté à la texture du sol.")

    def _eval_texture(self, texture, contraintes, risques, actions):
        if texture in (Texture.SABLEUX, Texture.SABLO_LIMONEUX):
            contraintes.append("Texture sableuse : faible capacité de rétention d'eau et de nutriments.")
            risques.append("Lessivage rapide de l'azote et du potassium après les pluies.")
            actions.append("Fractionner les engrais (surtout azote) en 2–3 apports et augmenter "
                           "la matière organique pour améliorer la rétention.")
        elif texture in (Texture.LIMONO_ARGILEUX, Texture.ARGILEUX):
            contraintes.append("Texture argileuse : bonne rétention mais risque d'engorgement et de compaction.")
            risques.append("Mauvais drainage possible : asphyxie racinaire en saison des pluies.")
            actions.append("Assurer le drainage (billons, planches surélevées) et éviter le travail "
                           "du sol quand il est trop humide.")

    # ---------------- Actions correctives chiffrées ----------------
    def _action_carence(self, key, severe: bool) -> str:
        if key == "azote":
            dose = "150–200 kg/ha d'urée 46 %" if severe else "100 kg/ha d'urée 46 %"
            return f"Corriger l'azote : {dose}, fractionné en 2–3 apports. Combiner avec la MO."
        if key == "phosphore":
            dose = "150–200 kg/ha de DAP (18-46-0) ou TSP" if severe else "100 kg/ha de DAP"
            return f"Corriger le phosphore : {dose} au semis. Le phosphate de Thiès est une option locale."
        if key == "potassium":
            dose = "150–200 kg/ha de KCl (0-0-60)" if severe else "100 kg/ha de KCl"
            return f"Corriger le potassium : {dose}, surtout pour fruits, tubercules et arachide."
        return ""

    def _action_exces(self, key) -> str:
        return {
            "azote": "Réduire/suspendre l'azote : risque de verse, de maladies et de pollution des nappes.",
            "phosphore": "Suspendre les apports de phosphore ; surveiller le blocage du zinc et du fer.",
            "potassium": "Réduire le potassium ; un excès de K bloque l'absorption du magnésium (apporter MgSO₄ si besoin).",
        }.get(key, "")

    # ---------------- Score & niveau ----------------
    def _score(self, a: AnalyseSol, evals) -> int:
        """
        Score pondéré /100. La matière organique et le pH pèsent le plus (facteurs
        limitants majeurs au Sénégal). Chaque paramètre donne 0 à 1 ; on pondère.
        """
        poids = {"pH": 0.20, "Conductivité (CE)": 0.15, "Matière organique": 0.25,
                 "Azote (N)": 0.13, "Phosphore (P)": 0.13, "Potassium (K)": 0.14}
        note = {Statut.OPTIMAL: 1.0, Statut.CARENCE: 0.5, Statut.EXCES: 0.5,
                Statut.CARENCE_SEVERE: 0.15, Statut.EXCES_SEVERE: 0.15}
        total_poids, acc = 0.0, 0.0
        for e in evals:
            p = poids.get(e.parametre, 0.10)
            acc += note.get(e.statut, 0.5) * p
            total_poids += p
        if total_poids == 0:
            return 0
        return round(acc / total_poids * 100)

    def _niveau(self, score: int) -> NiveauFertilite:
        if score >= 85:
            return NiveauFertilite.EXCELLENT
        if score >= 68:
            return NiveauFertilite.BON
        if score >= 50:
            return NiveauFertilite.MOYEN
        if score >= 32:
            return NiveauFertilite.FAIBLE
        return NiveauFertilite.TRES_FAIBLE

    def _plafonner(self, niveau: NiveauFertilite, a: AnalyseSol, evals) -> NiveauFertilite:
        """
        Loi du minimum (Liebig) : un facteur fortement bloquant détermine le résultat,
        quels que soient les autres paramètres. On plafonne donc le niveau de fertilité.
        Exemples : pH < 4.5 (toxicité Al) ou salinité forte rendent un sol inexploitable
        pour la plupart des cultures, même s'il est riche en NPK.
        """
        ordre = [NiveauFertilite.TRES_FAIBLE, NiveauFertilite.FAIBLE, NiveauFertilite.MOYEN,
                 NiveauFertilite.BON, NiveauFertilite.EXCELLENT]
        plafond = NiveauFertilite.EXCELLENT

        ce = a.ce_ds_m()
        # Contraintes sévères -> plafond "Faible"
        if (a.ph is not None and a.ph < 4.5) or (ce is not None and ce >= 2.5):
            plafond = NiveauFertilite.FAIBLE
        # Contraintes modérées -> plafond "Moyen"
        elif (a.ph is not None and (a.ph < 5.0 or a.ph > 8.5)) or (ce is not None and 1.2 <= ce < 2.5):
            plafond = NiveauFertilite.MOYEN
        # MO très faible seule -> plafond "Moyen" (sol biologiquement épuisé)
        if a.matiere_organique is not None and a.matiere_organique < 0.5:
            if ordre.index(plafond) > ordre.index(NiveauFertilite.MOYEN):
                plafond = NiveauFertilite.MOYEN

        # On renvoie le plus bas des deux (niveau calculé vs plafond imposé).
        return niveau if ordre.index(niveau) <= ordre.index(plafond) else plafond

    # ---------------- Recommandation de cultures ----------------
    def _cultures(self, a: AnalyseSol, niveau: NiveauFertilite) -> list:
        """Propose des cultures adaptées au profil (pH, salinité, texture, fertilité)."""
        recs = []
        ph = a.ph
        ce = a.ce_ds_m()
        salin = ce is not None and ce >= 1.2
        acide = ph is not None and ph < 5.5
        basique = ph is not None and ph > 7.5
        sableux = a.texture in (Texture.SABLEUX, Texture.SABLO_LIMONEUX)
        argileux = a.texture in (Texture.LIMONO_ARGILEUX, Texture.ARGILEUX)

        if salin:
            recs += ["Riz tolérant au sel (variétés Sahel)", "Sorgho", "Mil", "Gombo"]
        elif acide:
            recs += ["Manioc", "Patate douce", "Mil", "Sorgho", "Riz pluvial (après chaulage)"]
        elif basique:
            recs += ["Sorgho", "Mil", "Coton", "Tournesol"]
        else:
            # sol équilibré : on oriente selon la fertilité et la texture
            if niveau in (NiveauFertilite.BON, NiveauFertilite.EXCELLENT):
                recs += ["Tomate", "Oignon", "Maïs", "Piment", "Chou"]
            elif niveau == NiveauFertilite.MOYEN:
                recs += ["Arachide", "Niébé", "Mil", "Gombo", "Pastèque"]
            else:
                recs += ["Mil", "Sorgho", "Niébé", "Arachide"]  # cultures rustiques

        if sableux and not salin:
            recs += ["Arachide", "Pastèque", "Manioc"]   # apprécient les sols légers
        if argileux and not salin:
            recs += ["Riz", "Canne à sucre"]             # tolèrent l'humidité

        # dédoublonnage en gardant l'ordre
        return list(dict.fromkeys(recs))[:6]

    # ---------------- Rédaction ----------------
    def _redaction_simple(self, niveau, carences, exces, contraintes) -> str:
        """Diagnostic en français simple, destiné directement à l'agriculteur."""
        intro = {
            NiveauFertilite.EXCELLENT: "Votre sol est très fertile. Il est prêt à bien produire.",
            NiveauFertilite.BON: "Votre sol est bon. Quelques ajustements le rendront encore meilleur.",
            NiveauFertilite.MOYEN: "Votre sol est moyen. Il faut corriger plusieurs points avant de semer.",
            NiveauFertilite.FAIBLE: "Votre sol est pauvre. Des corrections importantes sont nécessaires.",
            NiveauFertilite.TRES_FAIBLE: "Votre sol est très pauvre. Il faut le restaurer avant toute culture exigeante.",
        }[niveau]
        parts = [intro]
        if carences:
            parts.append("Ce qui manque : " + "; ".join(c.split(" :")[0] for c in carences) + ".")
        if exces:
            parts.append("Ce qu'il y a en trop : " + "; ".join(e.split(" :")[0] for e in exces) + ".")
        if contraintes:
            parts.append("Attention : " + contraintes[0])
        parts.append("Le plus important : nourrir le sol avec de la matière organique (fumier, compost) "
                     "et corriger le pH en premier si nécessaire.")
        return " ".join(parts)

    def _redaction_technique(self, a, evals, niveau, score) -> str:
        """Diagnostic en langage agronomique, pour technicien/conseiller."""
        lignes = [f"Niveau de fertilité : {niveau.value} (indice {score}/100)."]
        for e in evals:
            v = "n.d." if e.valeur is None else f"{e.valeur} {e.unite}".strip()
            lignes.append(f"• {e.parametre} = {v} → {e.statut.value} (réf. {e.plage_ref}). {e.commentaire}".strip())
        if a.texture:
            lignes.append(f"• Texture : {a.texture.value} → seuils nutritifs ajustés "
                          f"(coef. {COEF_TEXTURE.get(a.texture, 1.15):.2f}).")
        return "\n".join(lignes)

    @staticmethod
    def _dedupe(items: list) -> list:
        return list(dict.fromkeys([i for i in items if i]))
