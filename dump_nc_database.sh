#!/bin/bash

# PostgreSQL Database Dump Script
# Dumps the 'nc' database into a zip file named nc_dump.zip

set -e  # Exit on any error

# Configuration
DB_NAME="nc"
DUMP_FILE="nc_dump_$(date +%Y%m%d_%H%M%S).sql"
ZIP_FILE="nc_dump.zip"
TEMP_DIR="temp_dump_$$"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting PostgreSQL database dump for '${DB_NAME}'...${NC}"

# Create temporary directory
mkdir -p "$TEMP_DIR"

# Function to cleanup on exit
cleanup() {
    echo -e "${YELLOW}Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Check if database exists
echo -e "${YELLOW}Checking if database '${DB_NAME}' exists...${NC}"
if ! psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${RED}Error: Database '${DB_NAME}' does not exist!${NC}"
    echo "Available databases:"
    psql -l
    exit 1
fi

# Dump the database
echo -e "${YELLOW}Creating database dump...${NC}"
if pg_dump "$DB_NAME" > "$TEMP_DIR/$DUMP_FILE"; then
    echo -e "${GREEN}Database dump created successfully: ${DUMP_FILE}${NC}"
else
    echo -e "${RED}Error: Failed to create database dump!${NC}"
    exit 1
fi

# Get dump file size
DUMP_SIZE=$(du -h "$TEMP_DIR/$DUMP_FILE" | cut -f1)
echo -e "${GREEN}Dump file size: ${DUMP_SIZE}${NC}"

# Create zip file
echo -e "${YELLOW}Creating zip archive...${NC}"
if cd "$TEMP_DIR" && zip -9 "../$ZIP_FILE" "$DUMP_FILE"; then
    cd ..
    echo -e "${GREEN}Zip archive created successfully: ${ZIP_FILE}${NC}"
else
    echo -e "${RED}Error: Failed to create zip archive!${NC}"
    exit 1
fi

# Get zip file size
ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo -e "${GREEN}Zip file size: ${ZIP_SIZE}${NC}"

# Show compression ratio
echo -e "${GREEN}Compression completed successfully!${NC}"
echo -e "${YELLOW}Files created:${NC}"
echo "  - Original dump: $DUMP_SIZE"
echo "  - Compressed zip: $ZIP_SIZE ($(ls -la "$ZIP_FILE" | awk '{print $5}') bytes)"

# Show final location
echo -e "${GREEN}Final zip file location: $(pwd)/${ZIP_FILE}${NC}"

echo -e "${GREEN}Database dump completed successfully!${NC}"