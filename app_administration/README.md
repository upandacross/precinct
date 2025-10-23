# App Administration Tools

This directory contains administrative scripts and utilities for managing the precinct analysis application.

## Data Management

### Database Operations

- `backup_users.py` - Backup and restore user data
- `cleanup_test_users.py` - Remove test users from the database
- `create_test_users.py` - Generate test users for development
- `migrate_database.py` - Handle database schema migrations

### Data Import/Export

- `load_maps.sql` - Load precinct map data into the database
- Various SQL files for database schema management

## Data Quality & Fixes

### Precinct Data Normalization

- `fix_clustering_quick.py` - Quick fix for precinct zero-padding issues in clustering analysis
- `fix_clustering_zero_padding.py` - Comprehensive fix for precinct format inconsistencies

**Usage:**

```bash
cd app_administration
python fix_clustering_quick.py          # Apply quick zero-padding fix
python fix_clustering_zero_padding.py   # Apply comprehensive fixes
```

**What these scripts fix:**

- Resolves data join failures between precincts table ('074') and voting tables ('74')
- Ensures clustering analysis shows proper political metrics for all precincts
- Handles zero-padding inconsistencies across different data sources

**Note:** These scripts automatically change to the parent directory to access main application files.

## Backup and Restore

### Database Backups

- `dump_nc_database.sh` - Create complete database dumps
- `nc_dump_*.sql` - Historical database backup files
- `maps_backup_*.json` - Precinct map data backups

### Recovery Procedures

See `BACKUP_RESTORE_GUIDE.md` for detailed backup and restore procedures.

## Usage Guidelines

1. **Always backup before running fixes:** Administrative scripts can modify application files
2. **Run from app_administration directory:** Scripts are designed to work from this location
3. **Check parent directory:** Most scripts operate on files in the parent directory
4. **Test in development first:** Validate changes before applying to production

## Directory Structure

```text
app_administration/
├── README.md                           # This file
├── backup_users.py                     # User data backup/restore
├── cleanup_test_users.py               # Test user cleanup
├── create_test_users.py                # Test user generation
├── fix_clustering_quick.py             # Quick precinct format fix
├── fix_clustering_zero_padding.py      # Comprehensive precinct fix
├── migrate_database.py                 # Database migrations
├── *.sql                               # Database schema files
└── *.json                              # Data backup files
```

## Recent Additions (October 2024)

### Precinct Format Fixes

Added comprehensive solution for precinct zero-padding inconsistencies:

- Created centralized precinct normalization utilities in parent directory
- Fixed clustering analysis to handle both '074' and '74' precinct formats
- Verified precinct 074 now shows proper political metrics (48.6% Dem Vote vs 0.0%)
- Enhanced database join success rate to 100% (was failing before)

### Integration Status

- ✅ Flask application integration complete
- ✅ Database models enhanced with precinct utilities  
- ✅ Clustering analysis fixed and tested
- ✅ DVA analysis scripts updated
- ✅ Administrative tools moved and configured
