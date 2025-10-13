# NC Database Users Backup & Restore

## Overview

These scripts provide backup and restore functionality specifically for the `users` table in the NC database. They are designed to work alongside the test user generation scripts, allowing you to preserve real user data before testing and restore it afterwards.

## Scripts

### `backup_users.py` - Backup Script

**Purpose**: Creates a timestamped JSON backup of all users in the database

**Usage**:
```bash
python3 backup_users.py
```

**Features**:
- Interactive menu with options to create backup or list existing backups
- Creates timestamped backup files: `users_backup_YYYYMMDD_HHMMSS.json`
- Backs up all user data including passwords, permissions, and metadata
- Shows detailed statistics about backed up users
- Provides restore command suggestion

**Backup File Format**:
- JSON format with metadata and user array
- Includes backup timestamp and total user count
- Preserves all user fields including encrypted passwords
- Human-readable format for manual inspection

### `restore_users.py` - Restore Script

**Purpose**: Restores users from a backup file, replacing current users

**Usage**:
```bash
# Interactive mode - choose from available backups
python3 restore_users.py

# Direct mode - specify backup file
python3 restore_users.py users_backup_20251013_143022.json
```

**Features**:
- Interactive backup selection or command-line specification
- Shows backup details before restoration
- Requires explicit confirmation before proceeding
- Replaces ALL existing users with backup data
- Preserves all user attributes and timestamps
- Shows detailed restoration statistics

**Safety Features**:
- Confirmation prompt before destructive operations
- Transaction rollback on errors
- Detailed progress reporting
- Validation of backup file format

## Typical Workflow

### 1. Before Testing
```bash
# Create backup of current users
python3 backup_users.py

# Generate test users
python3 create_test_users.py
```

### 2. After Testing
```bash
# Clean up test users (optional)
python3 cleanup_test_users.py

# Restore original users
python3 restore_users.py users_backup_20251013_143022.json
```

## Backup File Structure

```json
{
  "backup_timestamp": "20251013_143022",
  "backup_datetime": "2025-10-13T14:30:22.123456",
  "total_users": 25,
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "password": "original_password",
      "password_hash": "hashed_version",
      "is_admin": true,
      "is_county": false,
      "is_active": true,
      "created_at": "2025-10-01T10:00:00.000000",
      "last_login": "2025-10-13T09:15:30.000000",
      "state": "NC",
      "county": "FORSYTH",
      "precinct": "001",
      "phone": "336-555-0123",
      "role": "System Administrator",
      "notes": "Primary admin user"
    }
  ]
}
```

## Important Notes

### Data Safety
- **Always backup before testing**: Create a backup before generating test users
- **Restore completely replaces**: The restore process replaces ALL users in the database
- **Test carefully**: Verify backup files before depending on them for important data

### File Management
- Backup files are stored in the same directory as the scripts
- Files are named with timestamps for easy identification
- Old backup files are not automatically deleted - manage them manually

### Database Integrity
- Both scripts use proper database transactions
- Errors trigger rollback to maintain database consistency
- All user relationships and constraints are preserved

## Troubleshooting

### Common Issues

**"No backup files found"**:
- Run `backup_users.py` first to create a backup
- Check that you're in the correct directory

**"Invalid backup file format"**:
- Ensure the backup file wasn't corrupted or manually edited
- Try creating a new backup

**Database connection errors**:
- Ensure the NC database is running
- Verify database connection settings in `config.py`
- Check Flask app context initialization

### Verification
```bash
# Check current user count before backup
python3 check_test_users.py

# Create backup
python3 backup_users.py

# Verify backup was created
ls -la users_backup_*.json

# After restore, verify user count matches
python3 check_test_users.py
```

## Security Considerations

- Backup files contain plaintext passwords and hashed passwords
- Store backup files securely and limit access
- Consider encrypting backup files for sensitive environments
- Regular cleanup of old backup files is recommended

## Integration with Test Scripts

These backup/restore scripts work seamlessly with the test user generation system:

1. **Before testing**: Backup real users
2. **During testing**: Generate test users, run tests
3. **After testing**: Clean up test users, restore real users

This workflow ensures that testing doesn't interfere with production user data while allowing comprehensive testing scenarios.