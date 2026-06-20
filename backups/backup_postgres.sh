#!/usr/bin/env bash
# Sauvegarde quotidienne PostgreSQL — AgroScan Pro
# Usage: ./backup_postgres.sh [--test]
set -euo pipefail

DB_NAME="agroscan"
BACKUP_DIR="/opt/agroscan/backups/postgres"
LOG_FILE="/opt/agroscan/backups/logs/backup_postgres.log"
STATUS_FILE="/opt/agroscan/backups/last_backup_status.json"
RETENTION_DAYS=14
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/agroscan_${DATE}.sql.gz"
ALERT_EMAIL="thiamkhadim304@gmail.com"

log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
alert() {
    local subject="$1" body="$2"
    log "ALERTE: $subject"
    # Email si msmtp configuré
    if [ -f /etc/msmtprc ] && grep -q "^account default" /etc/msmtprc 2>/dev/null; then
        echo "$body" | mail -s "[AgroScan] $subject" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    # Toujours écrire dans le fichier de statut (lu par /api/health/backup)
    cat > "$STATUS_FILE" <<JSON
{"status":"error","message":"$subject","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","backup_file":null}
JSON
}

# Trap toute sortie en erreur
trap 'alert "Backup échoué — vérifier $LOG_FILE" "Le backup PostgreSQL du $(date) a échoué. Serveur: agroscanpro.com. Log: $LOG_FILE"' ERR

log "=== Démarrage sauvegarde PostgreSQL ==="
mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

# ── Vérification espace disque (min 500 MB) ──────────────────────────────────
AVAIL_MB=$(df -m "$BACKUP_DIR" | awk 'NR==2{print $4}')
if [ "$AVAIL_MB" -lt 500 ]; then
    alert "Espace disque insuffisant" "Seulement ${AVAIL_MB}MB disponibles sur $BACKUP_DIR (500MB requis)."
    exit 1
fi

# ── Sauvegarde PostgreSQL ─────────────────────────────────────────────────────
log "Dump de la base '$DB_NAME' → $BACKUP_FILE"
if sudo -u postgres pg_dump "$DB_NAME" --no-owner --no-acl | gzip > "$BACKUP_FILE"; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Dump OK: $BACKUP_FILE ($SIZE)"
else
    rm -f "$BACKUP_FILE"
    alert "pg_dump échoué" "Erreur lors du dump PostgreSQL de la base $DB_NAME."
    exit 1
fi

# ── Vérification intégrité ────────────────────────────────────────────────────
if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    rm -f "$BACKUP_FILE"
    alert "Backup corrompu" "Le fichier $BACKUP_FILE ne passe pas la vérification gzip."
    exit 1
fi
log "Intégrité gzip: OK"

# ── Rotation ──────────────────────────────────────────────────────────────────
DELETED=$(find "$BACKUP_DIR" -name "agroscan_*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
[ "$DELETED" -gt 0 ] && log "Rotation: $DELETED anciens backups supprimés (>${RETENTION_DAYS}j)"

# ── Sync Backblaze B2 ─────────────────────────────────────────────────────────
# Pré-requis: rclone configuré avec profil "b2agroscan" (voir /etc/rclone_agroscan.conf)
# Pour activer: décommenter les lignes ci-dessous après avoir fourni les credentials B2.
# if command -v rclone &>/dev/null && [ -f /etc/rclone_agroscan.conf ]; then
#     log "Sync B2 → rclone copy en cours..."
#     if rclone copy "$BACKUP_FILE" b2agroscan:agroscan-backups-prod/postgres/ \
#          --config /etc/rclone_agroscan.conf --quiet 2>>"$LOG_FILE"; then
#         log "Sync B2: OK ($(basename "$BACKUP_FILE") uploadé)"
#     else
#         log "AVERTISSEMENT: Sync B2 échoué — backup local conservé"
#     fi
# else
#     log "INFO: Sync B2 désactivé (rclone ou config manquante)"
# fi

# ── Résumé + statut ───────────────────────────────────────────────────────────
NB_BACKUPS=$(find "$BACKUP_DIR" -name "agroscan_*.sql.gz" | wc -l)
LAST_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Total backups conservés: $NB_BACKUPS | Taille: $LAST_SIZE | Espace dispo: $(df -h "$BACKUP_DIR" | awk 'NR==2{print $4}')"
log "=== Sauvegarde terminée avec succès ==="

# Fichier de statut (lu par /api/health/backup)
cat > "$STATUS_FILE" <<JSON
{"status":"ok","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","backup_file":"$(basename "$BACKUP_FILE")","size_bytes":$(stat -c%s "$BACKUP_FILE"),"total_backups":$NB_BACKUPS}
JSON
