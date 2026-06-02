#!/usr/bin/env bash
# =============================================================================
#  AgroScan Pro — Script d'installation sur VPS OVH (Ubuntu 24.04)
#  Social Technologie · +221 78 491 90 11
# -----------------------------------------------------------------------------
#  À LANCER UNE SEULE FOIS, connecté en root sur le serveur :
#     bash install_ovh.sh
#  Le script s'arrête à la moindre erreur (set -e) pour ne rien casser.
# =============================================================================
set -e

# ---- Paramètres à adapter (ou laisser par défaut) ---------------------------
APP_USER="agroscan"                       # utilisateur Linux dédié à l'app
APP_DIR="/opt/agroscan"                   # dossier de l'application
DB_NAME="agroscan"
DB_USER="agroscan"
DB_PASS="$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-20)"   # mot de passe DB aléatoire
PY=python3

echo "=================================================="
echo " Installation AgroScan Pro sur OVH"
echo "=================================================="

# ---- 1. Mises à jour + paquets système --------------------------------------
echo "[1/7] Mise à jour du système et installation des paquets..."
apt update && apt upgrade -y
apt install -y python3-venv python3-pip nginx postgresql git curl ufw

# ---- 2. Pare-feu (on n'ouvre que SSH + web) ---------------------------------
echo "[2/7] Configuration du pare-feu..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ---- 3. Utilisateur dédié (sécurité : l'app ne tourne pas en root) ----------
echo "[3/7] Création de l'utilisateur applicatif..."
if ! id "$APP_USER" &>/dev/null; then
  adduser --system --group --home "$APP_DIR" "$APP_USER"
fi
mkdir -p "$APP_DIR"

# ---- 4. Base de données PostgreSQL ------------------------------------------
echo "[4/7] Configuration de PostgreSQL..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# ---- 5. Code de l'application -----------------------------------------------
echo "[5/7] Mise en place du code..."
# Le code doit déjà être présent dans $APP_DIR (via git clone ou scp).
# Si le dossier app/ n'est pas là, on prévient et on s'arrête.
if [ ! -d "$APP_DIR/app" ]; then
  echo "  ⚠️  Le code n'est pas dans $APP_DIR."
  echo "     Envoyez d'abord votre projet, par exemple :"
  echo "       git clone VOTRE_DEPOT $APP_DIR"
  echo "     ou depuis votre PC :  scp -r agroscan-saas/* root@IP:$APP_DIR/"
  echo "     Puis relancez ce script."
  exit 1
fi

cd "$APP_DIR"
$PY -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install gunicorn psycopg[binary]   # serveur de prod + driver PostgreSQL

# ---- 6. Fichier .env de production ------------------------------------------
echo "[6/7] Génération du fichier .env de production..."
SECRET=$(openssl rand -base64 48 | tr -d '\n')
if [ ! -f "$APP_DIR/.env" ]; then
cat > "$APP_DIR/.env" <<EOF
ENV=production
DATABASE_URL=postgresql+psycopg://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
SECRET_KEY=$SECRET
PRICE_PREMIUM_HT=5000
PRICE_COOP_HT=25000
PAYMENT_PROVIDER=manuel
PAYMENT_API_KEY=
PAYMENT_WEBHOOK_SECRET=$(openssl rand -hex 16)
ANTHROPIC_API_KEY=
EOF
  echo "  → .env créé (mot de passe DB et clés générés automatiquement)."
else
  echo "  → .env déjà présent, conservé tel quel."
fi

chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# ---- 7. Service systemd + Nginx ---------------------------------------------
echo "[7/7] Installation du service et de Nginx..."
cp "$APP_DIR/deploy/agroscan.service" /etc/systemd/system/agroscan.service
systemctl daemon-reload
systemctl enable agroscan
systemctl restart agroscan

cp "$APP_DIR/deploy/nginx_agroscan.conf" /etc/nginx/sites-available/agroscan
ln -sf /etc/nginx/sites-available/agroscan /etc/nginx/sites-enabled/agroscan
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ""
echo "=================================================="
echo " ✅ Installation terminée !"
echo "=================================================="
echo " • Application : http://$(curl -s ifconfig.me)/"
echo " • Identifiants DB enregistrés dans : $APP_DIR/.env"
echo ""
echo " ÉTAPES SUIVANTES :"
echo "  1. Pointez votre domaine vers cette IP : $(curl -s ifconfig.me)"
echo "  2. Activez le HTTPS :   bash $APP_DIR/deploy/setup_https.sh VOTRE_DOMAINE"
echo "  3. Vérifiez l'état :    systemctl status agroscan"
echo "=================================================="
