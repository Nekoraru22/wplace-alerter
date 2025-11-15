#!/bin/bash

# Backup script for wplace-alerter data folder
# This script creates a compressed tar archive of the data folder with timestamp

# Configuration
BACKUP_DIR="backups"
DATA_DIR="data"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tgz"
LATEST_LINK="$BACKUP_DIR/backup.tgz"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create backups directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Creating backup directory: $BACKUP_DIR${NC}"
    mkdir -p "$BACKUP_DIR"
fi

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}Error: Data directory '$DATA_DIR' not found!${NC}"
    exit 1
fi

# Create the backup
echo -e "${YELLOW}Creating backup of $DATA_DIR...${NC}"
if tar -czf "$BACKUP_FILE" "$DATA_DIR"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)${NC}"

    # Update the latest backup symlink
    rm -f "$LATEST_LINK"
    ln -s "$(basename "$BACKUP_FILE")" "$LATEST_LINK"
    echo -e "${GREEN}Latest backup link updated: $LATEST_LINK${NC}"

    # Keep only the last N backups (uncomment to enable)
    # KEEP_BACKUPS=5
    # echo -e "${YELLOW}Cleaning up old backups (keeping last $KEEP_BACKUPS)...${NC}"
    # cd "$BACKUP_DIR" && ls -t backup_*.tgz | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -f

    echo -e "${GREEN}Backup completed successfully!${NC}"
else
    echo -e "${RED}Error: Backup failed!${NC}"
    exit 1
fi
