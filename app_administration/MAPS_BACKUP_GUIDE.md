# Maps Table Backup and Restore System

This directory contains scripts for backing up and restoring the maps table from the NC database.

## Scripts Overview

### `backup_maps.py`
Creates timestamped backup files of all maps in the database.

**Features:**
- Backs up all map data including HTML content
- Creates timestamped JSON files
- Shows detailed statistics (file size, content size, location breakdown)
- Includes backup verification
- Interactive menu interface

**Usage:**
```bash
cd app_administration
python backup_maps.py
```

**Menu Options:**
1. Create new backup
2. List existing backups
3. Verify backup integrity
4. Exit

### `restore_maps.py`
Restores maps from backup files with multiple modes.

**Features:**
- Two restore modes: Replace (clear existing) or Merge (add/update)
- Interactive backup selection
- Validates backup file integrity
- Shows detailed progress and statistics
- Command line or interactive interface

**Usage:**

Interactive mode:
```bash
cd app_administration
python restore_maps.py
```

Command line mode:
```bash
cd app_administration
python restore_maps.py <backup_filename> [mode]

# Examples:
python restore_maps.py maps_backup_20251013_203843.json replace
python restore_maps.py maps_backup_20251013_203843.json merge
```

**Restore Modes:**
- `replace` (default): Deletes all existing maps and restores from backup
- `merge`: Adds new maps and updates existing ones, preserves other maps

### `load_maps.py`
Loads HTML map files from the file system into the database.

**Features:**
- Scans `static_html/` directory for HTML files
- Extracts precinct numbers from filenames (first 3 characters)
- Sets all maps to state='NC', county='FORSYTH'
- Handles both new loads and updates
- Shows verification listing of loaded maps

**Usage:**
```bash
cd app_administration
python load_maps.py
```

## Backup File Format

Backup files are JSON format with the following structure:

```json
{
  "backup_timestamp": "20251013_203843",
  "backup_datetime": "2025-10-13T20:38:43.190002",
  "total_maps": 112,
  "total_content_size_bytes": 13271040,
  "maps": [
    {
      "id": 1,
      "state": "NC",
      "county": "FORSYTH",
      "precinct": "012",
      "map": "<!DOCTYPE html>...",
      "created_at": "2025-10-14T00:34:12.345678",
      "content_size": 106496
    }
  ]
}
```

## Workflow Examples

### Regular Backup
```bash
# Create a backup
cd app_administration
python backup_maps.py
# Choose option 1 to create new backup
```

### Disaster Recovery
```bash
# Restore from backup (replace all maps)
cd app_administration
python restore_maps.py maps_backup_20251013_203843.json replace
```

### Adding New Maps
```bash
# 1. Add HTML files to static_html/ directory
# 2. Load them into database
python load_maps.py

# 3. Create backup with new maps
python backup_maps.py
```

### Merging Backups
```bash
# Restore additional maps without losing existing ones
python restore_maps.py maps_backup_20251013_203843.json merge
```

## File Locations

- **Backup files**: Saved in `app_administration/` directory
- **HTML source files**: `static_html/` directory (temporary)
- **Database**: NC PostgreSQL database, `maps` table

## Security Notes

- Backup files contain full HTML content (can be large)
- Backup files are not encrypted
- Store backup files securely
- Verify backup integrity regularly
- Test restore procedures periodically

## Error Handling

All scripts include comprehensive error handling:
- File validation before processing
- Database transaction rollbacks on errors
- Detailed error messages and logging
- Graceful handling of missing files or data

## Database Schema

The maps table has the following structure:
```sql
CREATE TABLE maps (
    id SERIAL PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    county VARCHAR(100) NOT NULL,
    precinct VARCHAR(100) NOT NULL,
    map TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Troubleshooting

### "No backup files found"
- Check you're in the `app_administration/` directory
- Look for files matching `maps_backup_*.json`

### "Database connection error"
- Verify NC database configuration in `config.py`
- Ensure database server is running
- Check network connectivity

### "Invalid backup file"
- Run backup verification: option 3 in `backup_maps.py`
- Check file is not corrupted or truncated
- Ensure file is valid JSON format

### "Permission denied"
- Check file permissions on backup directory
- Ensure write access to create backup files
- Verify database user has appropriate permissions