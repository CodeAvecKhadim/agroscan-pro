#!/usr/bin/env bash
# Sauvegarde quotidienne du dossier uploads — AgroScan Pro
set -euo pipefail

UPLOADS_DIR="/opt/agroscan/uploads"
BACKUP_DIR="/opt/agroscan/backups/uploads"
LOG_FILE="/opt/agroscan/backups/logs/backup_uploads.log"
RETENTION_DAYS=14
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/uploads_${DATE}.tar.gz"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "=== Démarrage sauvegarde uploads ==="

if [ ! -d "$UPLOADS_DIR" ]; then
    log "ERREUR: Dossier uploads introuvable: $UPLOADS_DIR"
    exit 1
fi

# Compte et taille des fichiers
NB_FILES=$(find "$UPLOADS_DIR" -type f | wc -l)
SIZE_BEFORE=$(du -sh "$UPLOADS_DIR" | cut -f1)
log "Source: $NB_FILES fichiers, $SIZE_BEFORE"

# Archive
if tar -czf "$BACKUP_FILE" -C "$(dirname "$UPLOADS_DIR")" "$(basename "$UPLOADS_DIR")"; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Succès: $BACKUP_FILE ($SIZE)"
else
    log "ERREUR: tar a échoué"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Vérification intégrité
if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    log "ERREUR: Archive corrompue"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Rotation
DELETED=$(find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
[ "$DELETED" -gt 0 ] && log "Rotation: $DELETED anciens backups supprimés"

log "=== Sauvegarde uploads terminée ==="
