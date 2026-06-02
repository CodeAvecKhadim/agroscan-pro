# AgroScan Pro — Plateforme SaaS d'analyse de sol

Backend **FastAPI + SQLAlchemy** et interface web pour la plateforme agronomique
**AgroScan Pro**, éditée par **Social Technologie** (Sénégal · 📞 +221 78 491 90 11).

Système **Freemium / Premium / Coopérative** complet : authentification, abonnements,
quotas, contrôle d'accès, multi-tenant, tableau de bord coopérative.

---

## 🏗️ Architecture

```
agroscan-saas/
├── app/
│   ├── main.py                 # Point d'entrée FastAPI (assemble tout)
│   ├── core/
│   │   ├── config.py           # Configuration via .env (jamais de clé en dur)
│   │   ├── database.py         # Connexion SQLite/PostgreSQL
│   │   ├── security.py         # Hachage bcrypt + jetons JWT
│   │   └── deps.py             # CONTRÔLE D'ACCÈS : auth, quotas, rôles, features
│   ├── models/__init__.py      # TABLES SQL (org, users, subscriptions, farms, …)
│   ├── schemas/__init__.py     # Validation Pydantic (contrat d'API)
│   ├── routers/
│   │   ├── auth.py             # Inscription / connexion
│   │   ├── analyses.py         # Diagnostics (quota gratuit appliqué ici)
│   │   ├── billing.py          # Plans, paiement, webhook
│   │   └── coop.py             # Multi-utilisateurs / multi-exploitations / dashboard
│   ├── services/
│   │   ├── plans.py            # MATRICE DES PLANS (source unique de vérité)
│   │   ├── subscription.py     # Logique d'abonnement + TVA 18 %
│   │   ├── diagnostic.py       # Diagnostic capteur (mesures vs seuils par culture)
│   │   ├── fertilite.py        # MOTEUR DE FERTILITÉ (interprète une analyse de labo)
│   │   └── rapport_pdf.py      # GÉNÉRATEUR DE RAPPORT PDF (4 pages, QR, signature)
│   └── static/index.html       # Interface web (consomme l'API)
├── requirements.txt
├── .env.example
└── run.sh
```

### Multi-tenant par Organisation
L'abonnement est porté par l'**organisation** (le client facturable), pas par
l'utilisateur. Un compte individuel = une organisation à 1 membre ; une coopérative =
une organisation à plusieurs membres et exploitations. C'est la bonne pratique SaaS qui
permet de partager quotas et facturation au sein d'une équipe.

---

## 📋 Les trois plans

| Fonctionnalité            | Gratuit       | Premium      | Coopérative    |
|---------------------------|---------------|--------------|----------------|
| Analyses / mois           | 3             | illimité     | illimité       |
| Historique                | 30 jours      | complet      | complet        |
| Diagnostic                | simplifié     | avancé       | avancé         |
| Rapports PDF              | ✕             | ✓            | ✓              |
| Support WhatsApp          | ✕             | ✓            | ✓              |
| Multi-utilisateurs        | ✕             | ✕            | ✓ (jusqu'à 50) |
| Multi-exploitations       | ✕             | ✓            | ✓              |
| Tableau de bord collab.   | ✕             | ✕            | ✓              |
| Prix HT (FCFA/mois)       | 0             | 5 000        | 25 000 / siège |

Les prix et limites se modifient dans `app/services/plans.py` et `.env`. TVA 18 %
appliquée automatiquement.

---

## 📄 Générateur de rapport PDF

`app/services/rapport_pdf.py` produit un rapport d'analyse **professionnel de 4 pages**
(charte verte & bleue) à partir d'un diagnostic de fertilité :

1. **Couverture** — logo, titre, badge de fertilité, n° unique, date, QR code.
2. **Producteur & GPS + Résultats + Graphiques** — tableau des 7 paramètres, jauge de
   fertilité demi-circulaire, barres par paramètre.
3. **Diagnostic** (français simple + technique) et **constats** (carences, excès,
   contraintes, risques).
4. **Plan de fertilisation** chiffré, **cultures recommandées**, **signature numérique**
   (empreinte SHA-256) et QR code de vérification.

Chaque rapport porte un **numéro unique** (`AGS-{org}-{horodatage}`), une **date de
génération** et une **signature SHA-256** scellant son contenu.

Endpoint : `POST /api/fertilite/rapport-pdf` — réservé aux plans **Premium / Coopérative**
(fonctionnalité `pdf_reports`). Renvoie le PDF en téléchargement.

Démo hors serveur :
```bash
python -c "from app.services.fertilite import *; from app.services.rapport_pdf import RapportPDF; \
d=MoteurFertilite().diagnostiquer(AnalyseSol(ph=5.2,ce=0.3,azote=0.04,phosphore=9,potassium=55,matiere_organique=0.4,texture=Texture.SABLEUX)).to_dict(); \
RapportPDF().generer(d,{'nom':'Modou Diop','region':'Fatick','culture':'Mil','latitude':14.16,'longitude':-16.41,'superficie':1.5},'rapport.pdf'); print('rapport.pdf généré')"
```

---

## 🧪 Moteur d'interprétation de la fertilité

`app/services/fertilite.py` est le **cerveau agronomique** : il interprète une analyse
de sol de laboratoire (pH, CE, N, P, K, matière organique, texture) et produit un
diagnostic complet — distinct du diagnostic « capteur » (mesures vs seuils par culture).

Endpoint : `POST /api/fertilite/interpreter`

Il applique deux principes d'expert :
- **Seuils modulés par la texture** — un même taux de K se juge différemment en sol
  sableux (*dior*) et argileux (*deck*), car la capacité de rétention diffère.
- **Loi du minimum (Liebig)** — une contrainte sévère (pH < 4.5, salinité > 2.5 dS/m)
  plafonne le niveau de fertilité, quels que soient les autres paramètres : un sol
  toxique reste « Faible » même s'il est riche en NPK.

Retour : niveau de fertilité (Très faible → Excellent), score /100, diagnostic en
français simple ET technique, carences, excès, contraintes, risques, cultures
recommandées et actions correctives chiffrées. Version allégée en plan gratuit,
complète en Premium/Coopérative.

---

## 🚀 Démarrage rapide

```bash
# 1. Environnement + dépendances
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env
# éditez .env : générez une SECRET_KEY ( python -c "import secrets;print(secrets.token_urlsafe(48))" )

# 3. Lancement
uvicorn app.main:app --reload
```

- Interface : <http://localhost:8000>
- Documentation API interactive (Swagger) : <http://localhost:8000/docs>

SQLite est utilisé par défaut (aucune installation). Pour la production, renseignez
`DATABASE_URL` vers PostgreSQL dans `.env`.

---

## 🔐 Contrôle d'accès (sécurité SaaS)

Tout est appliqué **côté serveur** dans `app/core/deps.py` — impossible à contourner
depuis le navigateur :

- `current_user` — exige un jeton JWT valide.
- `enforce_analysis_quota` — bloque la 4ᵉ analyse du mois sur le plan gratuit (HTTP 402).
- `require_feature("pdf_reports")` — refuse une fonctionnalité hors plan (HTTP 403).
- `require_role(OWNER, ADMIN)` — réserve les actions sensibles (HTTP 403).

---

## 💳 Paiement (Sénégal)

La logique d'abonnement est complète ; le connecteur de paiement est modulaire.
Configurez `PAYMENT_PROVIDER` dans `.env` (`wave`, `orange_money`, `paydunya`) et
implémentez l'appel au PSP dans `app/services/subscription.py`. Le fournisseur confirme
le paiement via le webhook `POST /api/billing/webhook`, qui active l'abonnement et
prolonge la période de 30 jours.

---

## 🧭 Évolutivité

- **Migrations** : passez à Alembic dès la production (au lieu de `create_all`).
- **Cache / files** : ajoutez Redis pour les compteurs de quota à grande échelle.
- **Stateless** : l'API ne garde pas d'état en mémoire → scalable horizontalement
  derrière un load-balancer.
- **Séparation** : `services/` isole la logique métier des routes → tests faciles.

---

*AgroScan Pro — Social Technologie · Caméras de surveillance & équipements agricoles · +221 78 491 90 11*
