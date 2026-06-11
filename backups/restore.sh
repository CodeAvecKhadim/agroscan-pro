#!/usr/bin/env bash
# Script de restauration complète — AgroScan Pro
# Usage:
#   ./restore.sh --list                          Liste les backups disponibles
#   ./restore.sh --db FICHIER.sql.gz             Restaure la base de données
#   ./restore.sh --uploads FICHIER.tar.gz        Restaure les uploads
#   ./restore.sh --full DB.sql.gz UPLOADS.tar.gz Restauration complète
set -euo pipefail

BACKUP_DIR="/opt/agroscan/backups"
DB_NAME="agroscan"
UPLOADS_DIR="/opt/agroscan/uploads"
APP_DIR="/opt/agroscan"
LOG_FILE="$BACKUP_DIR/logs/restore.log"

log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
error() { log "ERREUR: $*"; exit 1; }
confirm() {
    read -r -p "$1 [oui/NON] " ans
    [[ "$ans" == "oui" ]] || { echo "Annulé."; exit 0; }
}

list_backups() {
    echo ""
    echo "=== BACKUPS POSTGRESQL ==="
    ls -lht "$BACKUP_DIR/postgres"/agroscan_*.sql.gz 2>/dev/null | head -10 || echo "  Aucun backup"
    echo ""
    echo "=== BACKUPS UPLOADS ==="
    ls -lht "$BACKUP_DIR/uploads"/uploads_*.tar.gz 2>/dev/null | head -10 || echo "  Aucun backup"
    echo ""
    echo "Dernier backup DB:      $(ls -t $BACKUP_DIR/postgres/agroscan_*.sql.gz 2>/dev/null | head -1 || echo 'aucun')"
    echo "Dernier backup uploads: $(ls -t $BACKUP_DIR/uploads/uploads_*.tar.gz 2>/dev/null | head -1 || echo 'aucun')"
}

restore_db() {
    local backup_file="$1"
    [[ -f "$backup_file" ]] || error "Fichier introuvable: $backup_file"
    gzip -t "$backup_file" 2>/dev/null || error "Archive corrompue: $backup_file"

    log "=== Restauration base de données ==="
    log "Source: $backup_file ($(du -h "$backup_file" | cut -f1))"

    confirm "ATTENTION: Ceci va ÉCRASER la base '$DB_NAME'. Continuer ?"

    # Stop gunicorn pour éviter écritures concurrentes
    log "Arrêt de l'application..."
    systemctl stop agroscan 2>/dev/null || true

    # Drop et recréer la base
    log "Recréation de la base..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME}_restore_tmp;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME}_restore_tmp OWNER agroscan;"

    # Restauration dans base temporaire d'abord
    log "Import en cours..."
    if gunzip -c "$backup_file" | sudo -u postgres psql -d "${DB_NAME}_restore_tmp" --quiet; then
        log "Import dans base temp OK — bascule vers base principale..."
        sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB_NAME' AND pid <> pg_backend_pid();"
        sudo -u postgres psql -c "DROP DATABASE $DB_NAME;"
        sudo -u postgres psql -c "ALTER DATABASE ${DB_NAME}_restore_tmp RENAME TO $DB_NAME;"
        log "Restauration DB réussie"
    else
        sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME}_restore_tmp;" 2>/dev/null || true
        error "Import échoué — base originale préservée"
    fi

    # Redémarrage
    log "Redémarrage de l'application..."
    systemctl start agroscan
    sleep 3
    systemctl is-active agroscan && log "Application redémarrée" || log "ATTENTION: Application non démarrée — vérifier manuellement"
}

restore_uploads() {
    local backup_file="$1"
    [[ -f "$backup_file" ]] || error "Fichier introuvable: $backup_file"
    gzip -t "$backup_file" 2>/dev/null || error "Archive corrompue: $backup_file"

    log "=== Restauration uploads ==="
    log "Source: $backup_file ($(du -h "$backup_file" | cut -f1))"

    confirm "ATTENTION: Ceci va ÉCRASER le dossier uploads. Continuer ?"

    # Sauvegarde du dossier courant
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    if [ -d "$UPLOADS_DIR" ]; then
        mv "$UPLOADS_DIR" "${UPLOADS_DIR}.pre-restore-${TIMESTAMP}"
        log "Ancien uploads sauvegardé → ${UPLOADS_DIR}.pre-restore-${TIMESTAMP}"
    fi

    mkdir -p "$UPLOADS_DIR"
    tar -xzf "$backup_file" -C "$(dirname "$UPLOADS_DIR")"
    chown -R agroscan:agroscan "$UPLOADS_DIR"
    log "Uploads restaurés: $(find "$UPLOADS_DIR" -type f | wc -l) fichiers"
}

# Dispatch
case "${1:-}" in
    --list)    list_backups ;;
    --db)      [[ -n "${2:-}" ]] || error "Usage: $0 --db FICHIER.sql.gz"; restore_db "$2" ;;
    --uploads) [[ -n "${2:-}" ]] || error "Usage: $0 --uploads FICHIER.tar.gz"; restore_uploads "$2" ;;
    --full)
        [[ -n "${2:-}" && -n "${3:-}" ]] || error "Usage: $0 --full DB.sql.gz UPLOADS.tar.gz"
        restore_db "$2"
        restore_uploads "$3"
        ;;
    *)
        echo "Usage:"
        echo "  $0 --list"
        echo "  $0 --db     /opt/agroscan/backups/postgres/agroscan_YYYYMMDD_HHMMSS.sql.gz"
        echo "  $0 --uploads /opt/agroscan/backups/uploads/uploads_YYYYMMDD_HHMMSS.tar.gz"
        echo "  $0 --full   DB.sql.gz UPLOADS.tar.gz"
        exit 1
        ;;
esac
