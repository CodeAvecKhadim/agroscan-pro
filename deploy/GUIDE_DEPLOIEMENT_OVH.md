# 🚀 Mettre AgroScan Pro en ligne sur OVH — Guide pas à pas

> Guide complet pour déployer la plateforme **AgroScan Pro** sur un serveur **VPS OVH**.
> Suivez les étapes **dans l'ordre**. Chaque commande est à copier-coller telle quelle.
> Préparé pour **Social Technologie** · +221 78 491 90 11

---

## ⚠️ À lire avant de commencer

**Prenez un VPS, PAS un hébergement web mutualisé.** L'hébergement mutualisé OVH
(~3 €/mois) ne fait tourner que du PHP/WordPress — votre application Python n'y
fonctionnera pas. Il vous faut un **VPS** (serveur Linux complet).

**Ce qu'il vous faut :**
- Un **VPS OVH** « Value » (~6 €/mois, 2 vCœurs, 4 Go RAM) suffit pour démarrer.
- Système : **Ubuntu 24.04**.
- (Optionnel mais recommandé) un **nom de domaine** (ex. `agroscan.sn`).
- Votre projet AgroScan (le dossier `agroscan-saas`).

---

## Étape 1 — Commander le VPS

1. Allez sur **ovhcloud.com** → menu **Serveurs** → **VPS**.
2. Choisissez le modèle **VPS Value** (ou supérieur).
3. Système d'exploitation : **Ubuntu 24.04**.
4. Datacenter : **Gravelines** ou **Strasbourg** (France — latence correcte vers le Sénégal).
5. Validez la commande.

OVH vous envoie un email avec :
- l'**adresse IP** de votre serveur (ex. `51.83.12.34`),
- l'utilisateur **`root`** et un **mot de passe** (ou une clé SSH).

> 📌 Notez bien cette IP, vous en aurez besoin partout. On la note ici `IP_SERVEUR`.

---

## Étape 2 — Se connecter au serveur (SSH)

**Sur Windows :** installez **Termius** (gratuit) ou utilisez **PowerShell**.
**Sur Mac / Linux :** ouvrez le **Terminal**.

Tapez (en remplaçant par votre IP) :

```bash
ssh root@IP_SERVEUR
```

La première fois, tapez `yes`, puis entrez le mot de passe reçu par email.
Vous êtes maintenant **sur le serveur** (l'invite change, ex. `root@vps:~#`).

> 💡 Changez le mot de passe root dès la première connexion : tapez `passwd`.

---

## Étape 3 — Envoyer votre code sur le serveur

Vous avez **deux méthodes**. La plus simple est GitHub.

### Méthode A — via GitHub (recommandée)
1. Créez un dépôt **privé** sur github.com et poussez-y le dossier `agroscan-saas`.
2. Sur le serveur :
```bash
apt update && apt install -y git
git clone https://github.com/VOTRE_COMPTE/agroscan-saas.git /opt/agroscan
```

### Méthode B — transfert direct depuis votre PC
Depuis le terminal de **votre PC** (pas le serveur), dans le dossier qui contient
`agroscan-saas` :
```bash
ssh root@IP_SERVEUR "mkdir -p /opt/agroscan"
scp -r agroscan-saas/* root@IP_SERVEUR:/opt/agroscan/
```

> Après cette étape, le dossier `/opt/agroscan` du serveur doit contenir `app/`,
> `requirements.txt`, `deploy/`, etc.

---

## Étape 4 — Lancer l'installation automatique

De retour **sur le serveur**, lancez le script fourni. Il fait tout le travail :
paquets système, base PostgreSQL, pare-feu, environnement Python, service, Nginx.

```bash
cd /opt/agroscan
bash deploy/install_ovh.sh
```

Patientez quelques minutes. À la fin, le script affiche :
- l'adresse pour tester (`http://IP_SERVEUR/`),
- un rappel des étapes suivantes.

**Testez tout de suite** dans votre navigateur :
```
http://IP_SERVEUR/
```
La page de connexion AgroScan Pro doit apparaître. 🎉

> La documentation technique de l'API est sur `http://IP_SERVEUR/docs`.

---

## Étape 5 — (Recommandé) Brancher votre nom de domaine

1. Chez votre fournisseur de domaine (ou l'espace OVH « Domaines »), créez un
   enregistrement **A** :
   - **Nom** : `@` (et un autre pour `www`)
   - **Cible** : votre `IP_SERVEUR`
2. Attendez la propagation (de quelques minutes à 1 h).
3. Vérifiez : `http://VOTRE_DOMAINE/` doit afficher le site.

---

## Étape 6 — Activer le HTTPS (cadenas vert) — INDISPENSABLE

Sans HTTPS, le paiement mobile et WhatsApp refuseront de fonctionner, et les
navigateurs afficheront « non sécurisé ». C'est **gratuit** et automatique :

```bash
bash /opt/agroscan/deploy/setup_https.sh VOTRE_DOMAINE www.VOTRE_DOMAINE
```

À la fin, votre site est en `https://VOTRE_DOMAINE`. Le certificat se renouvelle seul.

---

## ✅ C'est en ligne ! Commandes utiles au quotidien

```bash
# Voir si l'application tourne
systemctl status agroscan

# Redémarrer l'application (après une modification)
systemctl restart agroscan

# Voir les journaux en direct (erreurs, requêtes)
journalctl -u agroscan -f

# Redémarrer le serveur web
systemctl restart nginx
```

### Mettre à jour le code plus tard
```bash
cd /opt/agroscan
git pull                              # si vous utilisez GitHub
./.venv/bin/pip install -r requirements.txt
systemctl restart agroscan
```

---

## 🔧 En cas de problème

| Symptôme | Vérification |
|---|---|
| La page ne s'affiche pas | `systemctl status agroscan` et `systemctl status nginx` |
| Erreur 502 Bad Gateway | L'app est arrêtée → `journalctl -u agroscan -f` pour voir l'erreur |
| Le domaine ne pointe pas | Attendez la propagation DNS ou vérifiez l'enregistrement A |
| HTTPS échoue | Le domaine doit déjà pointer vers l'IP **avant** de lancer certbot |

---

## 📌 Ce qu'il reste à configurer (côté métier, pas serveur)

Une fois en ligne, pour ouvrir aux vrais clients :

1. **Paiement** — éditez `/opt/agroscan/.env` : mettez `PAYMENT_PROVIDER=wave`
   (ou `orange_money`/`paydunya`) et votre `PAYMENT_API_KEY`, puis
   `systemctl restart agroscan`. Le connecteur reste à coder avec votre compte marchand.
2. **Sauvegardes** — planifiez une sauvegarde de la base :
   `pg_dump agroscan > sauvegarde.sql` (idéalement automatisée chaque nuit).
3. **Données** — chargez vos 29 cultures complètes dans le moteur.

---

*AgroScan Pro — Social Technologie · Caméras de surveillance & équipements agricoles · +221 78 491 90 11*
