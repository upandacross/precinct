# Database Migration Guide

## Migration Required for Recent Model Changes

### Summary of Changes
Recent fixes to the Precinct application test suite revealed that the database schema needs to be updated to match the current model definitions.

### Schema Changes Required

#### Maps Table
- **Add Column**: `updated_at` (DATETIME)
- **Purpose**: Track when map records are last modified
- **Default Value**: Set to `created_at` value for existing records
- **Behavior**: Automatically updated when record is modified

### Migration Options

#### Option 1: Automated Migration Script (Recommended)
```bash
# Run the provided migration script
python migrate_database.py
```

#### Option 2: Manual SQL Migration
For direct database access:

**PostgreSQL:**
```sql
-- Add updated_at column
ALTER TABLE maps 
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Set initial values for existing records
UPDATE maps 
SET updated_at = created_at 
WHERE updated_at IS NULL;
```

**SQLite (for testing):**
```sql
-- Add updated_at column  
ALTER TABLE maps 
ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Set initial values for existing records
UPDATE maps 
SET updated_at = created_at 
WHERE updated_at IS NULL;
```

#### Option 3: Flask-Migrate (If using Alembic)
If your application uses Flask-Migrate:

```bash
# Generate migration
flask db migrate -m "Add updated_at column to maps table"

# Review the generated migration file
# Edit if necessary

# Apply migration
flask db upgrade
```

### Pre-Migration Checklist

- [ ] **Backup Database**: Create full backup of production database
- [ ] **Test Migration**: Run migration on development/staging environment first
- [ ] **Verify Schema**: Confirm current database structure
- [ ] **Check Dependencies**: Ensure no other applications depend on current schema
- [ ] **Plan Downtime**: Schedule maintenance window if needed

### Post-Migration Verification

1. **Verify Column Addition**:
   ```sql
   -- PostgreSQL
   SELECT column_name, data_type, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'maps' AND column_name = 'updated_at';
   
   -- SQLite
   PRAGMA table_info(maps);
   ```

2. **Test Application**:
   - Restart the application
   - Create a new map record
   - Update an existing map record
   - Verify timestamps are working correctly

3. **Run Tests**:
   ```bash
   # Run database tests to verify schema changes
   pytest test/test_database.py -v
   
   # Run all tests to ensure no regressions
   pytest test/ --tb=short
   ```

### Rollback Plan

If migration causes issues:

1. **Stop Application**
2. **Restore Database Backup**
3. **Restart with Previous Code Version**

### Alternative: Fresh Database Setup

For development environments, you might prefer to:

1. **Drop existing database**
2. **Recreate with new schema**:
   ```python
   from main import create_app
   from models import db
   
   app = create_app()
   with app.app_context():
       db.drop_all()
       db.create_all()
   ```
3. **Re-import any required data**

### Why This Migration is Needed

The test suite fixes revealed that:

1. **Map Model Evolution**: Tests expected `updated_at` functionality
2. **Timestamp Tracking**: Application needs to track map modifications
3. **Test Coverage**: Database tests now verify complete model behavior
4. **Data Integrity**: Proper timestamping improves audit capabilities

### Impact Assessment

- **Breaking Changes**: None (additive only)
- **Performance Impact**: Minimal (single column addition)
- **Application Downtime**: Brief (seconds for column addition)
- **Data Loss Risk**: None (no data removed)

### Support

If you encounter issues during migration:

1. Check the migration logs for specific error messages
2. Verify database permissions and connectivity
3. Ensure the database supports ALTER TABLE operations
4. Contact system administrator if using managed database service

---

**Note**: This migration is required for the application to function correctly with the recent test suite improvements and model enhancements.