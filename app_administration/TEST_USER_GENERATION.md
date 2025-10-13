# Test User Generation System

## Overview

This directory contains scripts to generate, manage, and clean up test users for the Precinct Member's Application. The test users are designed to populate every precinct in FORSYTH county with realistic data for testing analytics and user management features.

## Scripts

### 1. `create_test_users.py` - Main Generation Script

**Purpose**: Creates test users for every precinct in FORSYTH county

**Usage**:
```bash
python3 create_test_users.py
```

**Features**:
- Automatically discovers all precincts in FORSYTH county from the maps table
- Creates 10-25 active users per precinct (random distribution)
- Creates 3-5 inactive users per precinct (random distribution)
- Generates sequential usernames: `test001`, `test002`, `test003`, etc.
- Creates matching passwords: `test001!123`, `test002!123`, etc.
- Assigns realistic metadata (phone numbers, roles, notes)
- All users are regular users (no admin or county privileges)
- Sets all users to NC state, FORSYTH county, with appropriate precinct

### 2. `check_test_users.py` - Statistics Script

**Purpose**: Displays statistics about existing test users

**Usage**:
```bash
python3 check_test_users.py
```

**Output**:
- Total test users count
- Breakdown by precinct (active/inactive counts)
- Overall summary statistics (all regular users)
- Precinct coverage report

### 3. `cleanup_test_users.py` - Cleanup Script

**Purpose**: Safely removes all test users from the database

**Usage**:
```bash
python3 cleanup_test_users.py
```

**Safety Features**:
- Requires explicit "yes" confirmation
- Only removes users with usernames starting with "test"
- Provides count before deletion
- Handles database rollback on errors

## Generated User Structure

### Username/Password Pattern
```
Username: test001, test002, test003, ...
Password: test001!123, test002!123, test003!123, ...
Email:    test001@example.com, test002@example.com, ...
```

### User Distribution Per Precinct
- **Active Users**: 10-25 (randomly determined)
- **Inactive Users**: 3-5 (randomly determined)
- **User Type**: All users are regular users (no admin or county privileges)

### Geographic Assignment
- **State**: NC
- **County**: FORSYTH
- **Precinct**: Automatically assigned based on existing precincts in maps table

### Additional User Data
- **Phone**: Random format 336-555-XXXX
- **Role**: "Volunteer [precinct number]"
- **Notes**: "Test user for precinct [precinct number]"
- **Last Login**: Random date within last 30 days (active users only)
- **Created At**: Script execution time

## Testing Analytics Features

The generated test users enable comprehensive testing of:

### User Permission Levels
- **Regular Users**: All test users are regular users who see only their specific precinct data
- **Testing Focus**: Ideal for testing precinct-level analytics and data filtering

### Analytics Data Filtering
- **Precinct-Level Analytics**: All test users see only their specific precinct data
- **User Statistics**: Real data for pie charts and statistics cards within precinct scope
- **Geographic Scope**: Proper filtering by state, county, and precinct
- **Data Isolation**: Each test user sees only data relevant to their assigned precinct

### Dashboard Features
- **Quick Actions**: Standard user dashboard with precinct-specific options
- **Navigation Menu**: Analytics menu available for precinct-level data
- **User Profile**: Each test user can manage their own profile settings
- **Precinct Focus**: All features scoped to the user's assigned precinct

## Database Integration

### User Table Fields Populated
```sql
username        VARCHAR(80)     -- test001, test002, etc.
email           VARCHAR(120)    -- test001@example.com, etc.
password        VARCHAR(255)    -- Original password (test001!123)
password_hash   VARCHAR(255)    -- Hashed version for security
is_admin        BOOLEAN         -- Always false (regular users only)
is_county       BOOLEAN         -- Always false (regular users only)
is_active       BOOLEAN         -- Majority true (10-25 per precinct)
created_at      DATETIME        -- Script execution time
last_login      DATETIME        -- Random within 30 days (active only)
phone           VARCHAR(20)     -- 336-555-XXXX format
role            VARCHAR(100)    -- "Volunteer [precinct]"
precinct        VARCHAR(100)    -- Actual precinct from maps table
state           VARCHAR(50)     -- "NC"
county          VARCHAR(100)    -- "FORSYTH"
notes           TEXT            -- "Test user for precinct X"
```

### Maps Table Integration
The script reads from the `maps` table to discover all available precincts:
```sql
SELECT DISTINCT precinct 
FROM maps 
WHERE state = 'NC' AND county = 'FORSYTH';
```

## Expected Results

After running `create_test_users.py`, you should have:

### User Distribution
- **Total Users**: Varies based on number of precincts (typically 500-1000+ users)
- **Active Users**: ~75-85% of total users
- **Inactive Users**: ~15-25% of total users  
- **User Type**: 100% regular users (no admin or county privileges)

### Precinct Coverage
- Every precinct in FORSYTH county will have 13-30 total users
- Each precinct guaranteed to have both active and inactive users
- Geographic distribution matches actual precinct boundaries

### Analytics Testing
- **Precinct Analytics**: All test users will see data for their specific precinct only
- **User Activity Charts**: Will show realistic login and activity patterns within precinct scope
- **Data Filtering**: Perfect for testing precinct-level data isolation and security
- **Permission Testing**: Validates that regular users can only access their assigned precinct data

## Security Considerations

### Test User Identification
- All test users have usernames starting with "test" for easy identification
- Test users are clearly marked in the `notes` field
- Cleanup script only affects users with "test" prefix

### Password Security
- Passwords follow a predictable but secure pattern
- All passwords are properly hashed using Werkzeug security
- Test passwords are clearly identifiable and separate from real user passwords

### Data Isolation
- Test users respect the same geographic and permission boundaries as real users
- All test users are regular users with standard precinct-level access only
- Test data doesn't interfere with production user data and maintains proper scope isolation

## Troubleshooting

### Common Issues

**Script fails to find precincts**:
- Ensure the `maps` table is populated with FORSYTH county data
- Check that precincts have state='NC' and county='FORSYTH'

**Database connection errors**:
- Ensure PostgreSQL NC database is running
- Verify database connection settings in `config.py`
- Check that Flask app context is properly initialized

**User creation conflicts**:
- Run cleanup script first if usernames conflict
- Check for existing test users with `check_test_users.py`
- Verify email uniqueness constraints

### Verification Steps

1. **Check precinct discovery**:
   ```python
   python3 -c "
   from models import db, Map
   from main import create_app
   app = create_app()
   with app.app_context():
       precincts = db.session.query(Map.precinct).filter_by(state='NC', county='FORSYTH').distinct().all()
       print([p[0] for p in precincts])
   "
   ```

2. **Verify user creation**:
   ```bash
   python3 check_test_users.py
   ```

3. **Test login capability**:
   - Use any generated username/password combination
   - Example: username `test001`, password `test001!123`

## Maintenance

### Regular Cleanup
- Run cleanup script before regenerating test data
- Monitor database size impact of test users
- Remove test users before production deployment

### Updating Test Data
- Modify user count ranges in `create_test_users_for_precinct()` function
- Adjust admin/county probability percentages
- Customize user metadata generation as needed

### Adding New Precincts
- Test users automatically include any new precincts added to maps table
- Re-run generation script after adding new precincts
- No code changes needed for new geographic areas

## File Locations

```
precinct/
├── create_test_users.py      # Main generation script
├── check_test_users.py       # Statistics and verification
├── cleanup_test_users.py     # Safe cleanup utility
└── test/
    └── README.md            # This documentation
```

## Support

For issues or questions about the test user system:
1. Check this documentation for common solutions
2. Verify database connectivity and table structure
3. Review script output for specific error messages
4. Test with small precinct subsets for debugging