#!/usr/bin/env bash
# =============================================================================
#  AgroScan Pro — Mise à jour complète (5 modules OAD + design harmonisé)
#  Social Technologie · À lancer sur le serveur, en root.
# -----------------------------------------------------------------------------
#  Ce script :
#   1. Sauvegarde l'ancien code (sécurité)
#   2. Télécharge la dernière version depuis GitHub (ZIP)
#   3. Remplace le code de l'application
#   4. Réinstalle les dépendances si besoin
#   5. Redémarre l'application
# =============================================================================
set -e

APP=/opt/agroscan
ZIP_URL="https://github.com/CodeAvecKhadim/agroscan-pro/raw/main/AgroScan-Pro-SaaS-Backend.zip"

echo "=== 1/5 : Sauvegarde de l'ancienne version ==="
TS=$(date +%Y%m%d-%H%M%S)
if [ -d "$APP/app" ]; then
  cp -r "$APP/app" "$APP/app.backup-$TS"
  echo "  -> Sauvegarde : $APP/app.backup-$TS"
fi

echo "=== 2/5 : Téléchargement de la dernière version ==="
cd /tmp
rm -f maj.zip && rm -rf maj_extract
wget -q -O maj.zip "$ZIP_URL"
echo "  -> Téléchargé ($(wc -c < maj.zip) octets)"
mkdir -p maj_extract && unzip -oq maj.zip -d maj_extract

echo "=== 3/5 : Mise en place du nouveau code ==="
# Le ZIP contient un dossier agroscan-saas/ — on copie son contenu dans /opt/agroscan
SRC=/tmp/maj_extract/agroscan-saas
if [ ! -d "$SRC/app" ]; then echo "  ⚠️ Contenu inattendu dans le ZIP"; exit 1; fi
# On préserve le fichier .env (clés/DB) existant !
cp -r "$SRC/app" "$APP/"
cp -r "$SRC/deploy" "$APP/" 2>/dev/null || true
cp "$SRC/requirements.txt" "$APP/" 2>/dev/null || true
cp "$SRC/README.md" "$APP/" 2>/dev/null || true
echo "  -> Code mis à jour (le fichier .env a été conservé)."

echo "=== 4/5 : Dépendances ==="
cd "$APP"
./.venv/bin/pip install -q -r requirements.txt 2>/dev/null || true
echo "  -> Dépendances à jour."

echo "=== 5/5 : Redémarrage ==="
chown -R agroscan:agroscan "$APP" 2>/dev/null || true
systemctl restart agroscan
sleep 3
systemctl is-active agroscan && echo "  -> Application active."

echo ""
echo "============================================================"
echo " ✅ Mise à jour terminée !"
echo " Pages disponibles :"
echo "   https://agroscanpro.com/         (accueil / connexion)"
echo "   https://agroscanpro.com/carte    (cartographie parcelle)"
echo "   https://agroscanpro.com/saisie   (saisie des mesures)"
echo "   https://agroscanpro.com/oad      (analyse capteur 29 cultures)"
echo "   https://agroscanpro.com/scan     (maladie par photo)"
echo "   https://agroscanpro.com/resultat (rapport final)"
echo "============================================================"
echo ""
echo " 💡 En cas de souci, l'ancienne version est dans : $APP/app.backup-$TS"
