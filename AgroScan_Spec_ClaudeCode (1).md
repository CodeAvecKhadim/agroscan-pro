# AgroScan Pro — Spécification de construction (pour Claude Code)

> **À lire en entier avant de coder.** Ce document décrit QUOI construire et DANS QUEL ORDRE.
> Tu (Claude Code) écris tout le code toi-même, en lisant le projet réel.

---

## 0. Comment utiliser ce document

1. **Commence par explorer le projet** (`/opt/agroscan`) et **crée/mets à jour `CLAUDE.md`** à la racine, résumant l'architecture réelle (chemins, service, base de données, routes, tables, état actuel).
2. **Exécute UNE phase à la fois**, dans l'ordre (Phase 0 → 7).
3. **À la fin de chaque phase** :
   - redémarre le service **seulement si** un fichier `.py` a changé (`systemctl restart agroscan`) ; les fichiers `app/static/*.html` sont pris en compte au simple rechargement de la page,
   - teste,
   - `git add -A && git commit -m "Phase X : ..."`,
   - **puis demande validation à l'utilisateur AVANT de passer à la phase suivante.**
4. **Réponds toujours en français**, en étapes simples. L'utilisateur est débutant côté technique.

---

## 1. Contexte technique (infra réelle)

- **Code** : `/opt/agroscan` — venv : `/opt/agroscan/.venv`
- **Service** : `agroscan.service` (systemd, `User=agroscan`, `EnvironmentFile=/opt/agroscan/.env`, lance `gunicorn app.main:app`, écoute `127.0.0.1:8000`). Redémarrage : `systemctl restart agroscan`.
- **Base de données** : PostgreSQL, URL `postgresql+psycopg://agroscan:...@localhost:5432/agroscan`.
  Accès psql : `PGURL=$(.venv/bin/python -c "from app.core.config import settings; print(str(settings.DATABASE_URL).replace('+psycopg',''))")` puis `psql "$PGURL"`.
- **Coeur** : `app/core/database.py` (`get_db`, `Base`, `engine`, `SessionLocal`) · `app/core/deps.py` (`current_user` → User, OAuth2, `tokenUrl=/api/auth/login`).
- **Routeurs** : `app/routers/*.py`, enregistrés dans `app/main.py` via `app.include_router(...)`.
- **Front** : HTML statiques dans `app/static/`. Routes existantes : `/`, `/carte`, `/saisie`, `/oad`, `/scan`, `/resultat`, `/cultures`, `/vitrine`, `/tarifs`, `/calendrier`.
- **Auth front** : JWT stocké dans `localStorage['agro_token']` ; le header `Authorization: Bearer <token>` est ajouté aux appels API. Login/inscription sur la page d'accueil.
- **Dépôt** : `github.com/CodeAvecKhadim/agroscan-pro`.

### Tables existantes
`users`, `organizations`, `farms`, `subscriptions`, `payments`, `usage_counters`, `analyses`, système de crédits (`services`, `wallets`, `credit_ledger`, `credit_purchases`, `service_requests`), et **`parcelles`** :
`id, user_id (→users.id), nom, culture, superficie_ha, superficie_m2, centre_lat, centre_lng, contour (JSONB), precision_m, methode, created_at`.

### Fonctionnalités déjà en place
- **Carte / parcelles** (`/carte`) : dessin du contour (tour à pied GPS + pointage), calcul de superficie, enregistrement, **Mes parcelles** (liste + suppression), rapport imprimable, géocodage auto (région/département/commune/altitude).
- **API parcelles** : `/api/parcelles` `POST` (création, **limite gratuite `FREE_PARCEL_LIMIT = 2`** dans `parcelles.py`), `GET` (liste), `GET /{id}`, `DELETE /{id}`. Toutes protégées + vérif de propriété.
- **MVP** : analyse de sol (capteur 8 mesures), diagnostic maladie (**Kindwise**), météo temps réel, calendrier cultural.

---

## 2. Principe de conception (NON NÉGOCIABLE — VALABLE POUR TOUTE LA PLATEFORME ET TOUS LES UTILISATEURS)

**Le principe de simplicité s'applique à TOUS les utilisateurs et à TOUS les écrans** : producteur, conseiller, admin, ainsi que le site public, la connexion, les tarifs, etc. **Aucune page** de la plateforme ne doit être compliquée, encombrée ou pleine de jargon. Partout, la même exigence : **simple, clair, efficace, cohérent** — comme la carte.

**Une seule règle de design, appliquée partout** : réutiliser le langage de `/carte` —
gros boutons pleine largeur, panneaux en bas d'écran (bottom sheet) quand c'est pertinent, police 17–18 px, repères couleur + emoji, contenu centré (max-width ~560 px), français simple, **un minimum d'étapes**, fonctionne sur téléphone Android bas de gamme.
👉 Factoriser ces styles dans **une feuille commune `app/static/css/agroscan.css`** réutilisée par TOUS les écrans (et non seulement le producteur).

**Cacher la complexité — protection spécifique au producteur :**
Le **producteur ne voit JAMAIS** : NDVI, NDRE, SAVI, indices satellites, analyses SIG, bases de données, scores bruts.
Il voit **uniquement des phrases simples** :
- « Votre champ va bien. »
- « Risque de stress hydrique. »
- « Une fertilisation est recommandée. »
- « Une maladie est suspectée, envoyez une photo. »
- « Une anomalie a été détectée sur la parcelle Nord. »

Le **conseiller** a accès aux données techniques (NDVI, sol, historique…), mais **présentées clairement et simplement** — jamais un mur de chiffres brut. La simplicité d'usage vaut aussi pour lui.

**3 rôles :**
- **producteur** : 4 boutons. Réponses simples, photos, messages vocaux. Zéro jargon.
- **conseiller** : tableau de bord web complet (données techniques présentées clairement) + validation humaine.
- **admin** : accès total.

**Moteur AgroScan (côté serveur)** : fait tout le travail technique et **auto-remplit** région / département / commune / parcelle / culture / stade / calendrier cultural / indicateurs satellite. Une **couche de traduction** convertit chaque résultat technique (valeur NDVI, probabilité de maladie, etc.) en **une phrase simple** pour le producteur.

> ⚠️ **Vérité technique à respecter** : une **photo de téléphone** permet le **diagnostic maladie + état visuel**, mais **PAS** le NDVI. Le **NDVI / stress hydrique vient du satellite (Sentinel-2)** appliqué au **contour de la parcelle**. Ne jamais prétendre calculer un NDVI depuis une photo.

---

## 3. Modèle de données à ajouter (migrations PostgreSQL)

Ajoute via `ALTER`/`CREATE TABLE IF NOT EXISTS`, sans casser l'existant. Toujours `user_id` + vérif de propriété.

1. **`users.role`** : `ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'producteur';`
   (valeurs : `producteur`, `conseiller`, `admin`). Optionnel : `gie TEXT`, `conseiller_id INTEGER` (le conseiller qui suit ce producteur).
2. **`parcelles`** : ajouter `stade_culture TEXT`, `date_semis DATE`, `variete TEXT`.
3. **`activites`** (nouvelle) : `id, parcelle_id (→parcelles), user_id, type TEXT, date_prevue DATE, date_realisee DATE NULL, statut TEXT ('prevu'|'realise'|'en_retard'), note TEXT, created_at`.
4. **`observations`** (nouvelle) : `id, parcelle_id, user_id, type TEXT ('photo'|'audio'|'video'), chemin TEXT, diagnostic JSONB (résultat Kindwise/IA), etat_simple TEXT (la phrase montrée au producteur), anomalie BOOL DEFAULT false, validation_conseiller TEXT NULL, created_at`.
5. **`analyses_satellite`** (nouvelle) : `id, parcelle_id, date DATE, ndvi_moyen NUMERIC, ndre NUMERIC NULL, zones JSONB NULL, message_simple TEXT, source TEXT DEFAULT 'sentinel-2', created_at`. (Le producteur ne voit que `message_simple`.)
6. **`exploitation`** (nouvelle, Phase 5) : par parcelle ou par user : `surface_cultivee, production_estimee, couts, revenus` (saisie simple au départ).

---

## 4. Phases

### Phase 0 — Rôles + écran d'accueil producteur *(le socle)*
- **Données** : `users.role` (cf. §3.1).
- **Backend** : à la connexion, exposer le rôle ; helper de dépendance `require_role(...)` pour protéger les routes conseiller/admin.
- **Routage** : après login, rediriger selon le rôle → producteur vers `/app`, conseiller vers `/conseiller`, admin vers l'admin existant.
- **UI producteur** `/app` : page d'accueil avec **exactement 4 gros boutons** (style `/carte`) :
  🌾 **Mes parcelles** · 📋 **Mes activités** · 📸 **Envoyer une photo** · 📊 **Mon exploitation**.
- **Fin** : un compte `producteur` voit les 4 boutons ; un `conseiller` est redirigé vers son dashboard. Créer la feuille commune `agroscan.css`.

### Phase 1 — Mes parcelles enrichies
- **Données** : `parcelles.stade_culture`, `date_semis`, `variete` (§3.2).
- **UI producteur** : chaque parcelle s'affiche comme :
  `Parcelle A · Maïs · 2,5 ha · Floraison`. Réutilise/branche la liste « Mes parcelles » déjà construite sur `/carte`.
- **Moteur** : si `date_semis` + `culture` connus, **dériver le stade** automatiquement depuis le calendrier cultural (sinon, champ manuel simple).
- **Fin** : le stade s'affiche, en français, sans jargon.

### Phase 2 — Mes activités
- **Données** : table `activites` (§3.3).
- **Moteur** : à partir du **calendrier cultural** + culture + `date_semis`, **générer automatiquement** les activités (semis, désherbage, fertilisation, traitement, irrigation, récolte) avec `date_prevue`. Recalculer `statut` (`en_retard` si `date_prevue < aujourd'hui` et non réalisée).
- **UI producteur** `/app/activites` : liste simple — ✅ réalisé · 🟡 prévu (dans X jours) · 🔴 en retard. Bouton « Marquer réalisé » + possibilité d'envoyer une photo après l'intervention.
- **Fin** : un producteur voit ses activités à venir/réalisées par parcelle, en une page.

### Phase 3 — Envoyer une photo → diagnostic
- **Données** : table `observations` (§3.4) + stockage des fichiers (dossier `app/static/uploads/` ou équivalent, chemins en base).
- **UI producteur** `/app/photo` : un écran ultra-simple → prendre/charger une **photo** (plus tard audio/vidéo), associer à une parcelle, envoyer.
- **Moteur** : envoyer la photo à **Kindwise** (déjà intégré) → stocker le diagnostic brut dans `diagnostic`, calculer `anomalie` + `etat_simple` (phrase). Le producteur ne reçoit que : **« État : Bon »** ou **« Une anomalie a été détectée — un conseiller va vérifier. »**
- **Conseiller** : voit la photo, le diagnostic brut, et peut **valider/corriger** (`validation_conseiller`).
- **Fin** : photo → diagnostic stocké → message simple au producteur → visible côté conseiller.

### Phase 4 — Satellite caché (NDVI) *(gros morceau "précision")*
- **Pré-requis** : compte **Copernicus / Sentinel Hub** gratuit (clé dans `.env`).
- **Moteur** : pour une parcelle (via son **contour**), récupérer Sentinel-2, calculer **NDVI moyen** (+ optionnel NDRE, carte de zones), stocker dans `analyses_satellite`. Gérer : nuages (image inutilisable), absence de végétation.
- **Couche de traduction** → `message_simple` : ex. NDVI élevé/stable → « Votre champ va bien. » ; baisse de NDVI → « Une baisse de vigueur est détectée. » ; signe de sécheresse → « Risque de stress hydrique. »
- **UI producteur** : **aucun chiffre** — juste la phrase + couleur (vert/orange/rouge).
- **Conseiller** : NDVI/NDRE, historique, carte de zones.
- **Fin** : analyse satellite déclenchable sur une parcelle ; producteur ne voit que la phrase.

### Phase 5 — Mon exploitation
- **Données** : table `exploitation` (§3.6).
- **UI producteur** `/app/exploitation` : **surface cultivée**, **production estimée**, **coûts engagés**, **revenus** — chiffres simples, gros, peu nombreux. Saisie manuelle simple au départ ; estimation auto plus tard.
- **Fin** : un écran récap clair par exploitation.

### Phase 6 — Dashboard Conseiller
- **UI conseiller** `/conseiller` (protégé par rôle) : liste des producteurs/parcelles suivis ; pour chaque parcelle, vue détaillée :
  - **Parcelle** : GPS, commune, département, GIE, culture, stade.
  - **Sol** : pH, matière organique, salinité (depuis les analyses sol).
  - **Satellite** : NDVI, NDRE, historique.
  - **Activités** : réalisées / en retard.
  - **Photos** : avant / après.
  - **Maladies** : diagnostic IA + validation humaine.
- **Fin** : un conseiller a une vue technique complète + peut valider les diagnostics.

---

## 5. Règles transverses (toujours)

- **Sécurité** : toutes les routes API protégées ; vérification de propriété (`user_id`) sur chaque accès parcelle/activité/observation. Les routes conseiller/admin protégées par rôle.
- **Simplicité partout** : tous les écrans, tous les rôles, suivent le style de `/carte` (gros boutons, français simple, peu d'étapes). Producteur = en plus, **aucune** donnée technique exposée.
- **Style** : une seule feuille `app/static/css/agroscan.css` réutilisée sur **TOUTE** la plateforme.
- **Git** : un commit par phase.
- **Tests** : après chaque phase, vérifier dans le navigateur sur `https://agroscanpro.com`.

## 6. ⚠️ Sécurité avant mise en production (paiement)
Avant d'activer le paiement, **régénérer** : la clé **Kindwise**, le **SECRET_KEY**, le **mot de passe de la base**, et le **PAYMENT_WEBHOOK_SECRET** (puis mettre à jour `.env` + redémarrer). Ne pas committer `.env`.

---

## 7. Ordre recommandé
**0 → 1 → 2 → 3 → 6 (version minimale) → 4 → 5.**
(Le dashboard conseiller minimal en avance permet de visualiser les données dès la Phase 3.)
