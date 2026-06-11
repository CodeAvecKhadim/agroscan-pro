#!/usr/bin/env bash
# Sauvegarde quotidienne PostgreSQL — AgroScan Pro
# Usage: ./backup_postgres.sh [--test]
set -euo pipefail

DB_NAME="agroscan"
BACKUP_DIR="/opt/agroscan/backups/postgres"
LOG_FILE="/opt/agroscan/backups/logs/backup_postgres.log"
RETENTION_DAYS=14
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/agroscan_${DATE}.sql.gz"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "=== Démarrage sauvegarde PostgreSQL ==="

# Vérification espace disque (min 500 MB)
AVAIL_MB=$(df -m "$BACKUP_DIR" | awk 'NR==2{print $4}')
if [ "$AVAIL_MB" -lt 500 ]; then
    log "ERREUR: Espace disque insuffisant (${AVAIL_MB}MB disponibles, 500MB requis)"
    exit 1
fi

# Sauvegarde
log "Dump de la base '$DB_NAME' → $BACKUP_FILE"
if sudo -u postgres pg_dump "$DB_NAME" --no-owner --no-acl | gzip > "$BACKUP_FILE"; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Succès: $BACKUP_FILE ($SIZE)"
else
    log "ERREUR: pg_dump a échoué"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Vérification intégrité (teste que le gzip est lisible)
if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    log "ERREUR: Fichier backup corrompu"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Rotation — suppression des fichiers > RETENTION_DAYS jours
DELETED=$(find "$BACKUP_DIR" -name "agroscan_*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
[ "$DELETED" -gt 0 ] && log "Rotation: $DELETED anciens backups supprimés (>${RETENTION_DAYS}j)"

# Résumé
NB_BACKUPS=$(find "$BACKUP_DIR" -name "agroscan_*.sql.gz" | wc -l)
log "Total backups conservés: $NB_BACKUPS | Espace dispo: $(df -h "$BACKUP_DIR" | awk 'NR==2{print $4}')"
log "=== Sauvegarde terminée ==="
