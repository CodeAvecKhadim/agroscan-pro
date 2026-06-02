#!/usr/bin/env bash
# =============================================================================
#  AgroScan Pro — Activation du HTTPS gratuit (Let's Encrypt / certbot)
# -----------------------------------------------------------------------------
#  À lancer APRÈS avoir pointé votre domaine vers l'IP du serveur OVH.
#  Usage :   bash setup_https.sh agroscan.sn
#            bash setup_https.sh agroscan.sn www.agroscan.sn
# =============================================================================
set -e

if [ -z "$1" ]; then
  echo "Usage : bash setup_https.sh VOTRE_DOMAINE [autre_domaine]"
  echo "Exemple : bash setup_https.sh agroscan.sn www.agroscan.sn"
  exit 1
fi

DOMAINE="$1"

echo "[1/3] Mise à jour de la configuration Nginx avec le domaine $DOMAINE..."
# Remplace le "server_name _;" par le vrai domaine.
DOMAINS_LINE="$*"
sed -i "s/server_name .*/server_name $DOMAINS_LINE;/" /etc/nginx/sites-available/agroscan
nginx -t && systemctl reload nginx

echo "[2/3] Installation de certbot..."
apt install -y certbot python3-certbot-nginx

echo "[3/3] Obtention du certificat HTTPS..."
# Construit les arguments -d pour chaque domaine fourni.
ARGS=""
for d in "$@"; do ARGS="$ARGS -d $d"; done
certbot --nginx $ARGS --non-interactive --agree-tos --redirect \
        --register-unsafely-without-email || \
certbot --nginx $ARGS

echo ""
echo "✅ HTTPS activé. Votre site est accessible en https://$DOMAINE"
echo "   Le certificat se renouvelle automatiquement (certbot.timer)."
