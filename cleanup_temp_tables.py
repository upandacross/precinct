#!/usr/bin/env python3
"""
Temporary Table Cleanup Script
=============================

This script cleans up any temporary tables left behind by flippable race
analysis scripts. Run this if temp tables accumulate or cause issues.

Usage:
    python cleanup_temp_tables.py [--dry-run]
"""

import os
import argparse
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text

class TempTableCleaner:
    """Cleans up temporary tables from PostgreSQL database."""
    
    def __init__(self):
        """Initialize database connection."""
        load_dotenv()
        
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
    
    def find_temp_tables(self):
        """Find all temporary tables in the database."""
        print("🔍 Scanning for temporary tables...")
        
        with self.engine.connect() as conn:
            # Check for temp tables in all schemas
            result = conn.execute(text("""
                SELECT schemaname, tablename, tableowner
                FROM pg_tables 
                WHERE schemaname LIKE 'pg_temp_%' 
                   OR (schemaname = 'public' AND (
                       tablename ILIKE '%temp%' 
                       OR tablename ILIKE '%tmp%'
                       OR tablename ILIKE '%test%'
                       OR tablename ILIKE '%backup%'
                   ))
                ORDER BY schemaname, tablename
            """))
            
            temp_tables = result.fetchall()
            
            if temp_tables:
                print(f"Found {len(temp_tables)} temporary tables:")
                for schema, table, owner in temp_tables:
                    print(f"  📋 {schema}.{table} (owner: {owner})")
            else:
                print("✅ No temporary tables found")
            
            return temp_tables
    
    def cleanup_temp_tables(self, dry_run=False):
        """Clean up temporary tables."""
        temp_tables = self.find_temp_tables()
        
        if not temp_tables:
            return
        
        if dry_run:
            print(f"\n🧪 DRY RUN - Would drop {len(temp_tables)} tables:")
            for schema, table, owner in temp_tables:
                print(f"  Would drop: {schema}.{table}")
            return
        
        print(f"\n🧹 Cleaning up {len(temp_tables)} temporary tables...")
        
        with self.engine.connect() as conn:
            cleaned_count = 0
            failed_count = 0
            
            for schema, table, owner in temp_tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {schema}.{table} CASCADE"))
                    print(f"  ✅ Dropped {schema}.{table}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to drop {schema}.{table}: {e}")
                    failed_count += 1
            
            try:
                conn.commit()
                print(f"\n📊 Cleanup Summary:")
                print(f"  ✅ Successfully dropped: {cleaned_count} tables")
                if failed_count > 0:
                    print(f"  ❌ Failed to drop: {failed_count} tables")
                else:
                    print(f"  🎉 All temporary tables cleaned up successfully!")
                    
            except Exception as e:
                print(f"❌ Error committing cleanup: {e}")
                conn.rollback()
    
    def cleanup_specific_tables(self, table_names, dry_run=False):
        """Clean up specific temporary tables by name."""
        print(f"🎯 Targeting specific tables: {', '.join(table_names)}")
        
        with self.engine.connect() as conn:
            # Find these specific tables across all schemas
            placeholders = ','.join(['%s'] * len(table_names))
            result = conn.execute(text(f"""
                SELECT schemaname, tablename, tableowner
                FROM pg_tables 
                WHERE tablename IN ({placeholders})
                ORDER BY schemaname, tablename
            """), table_names)
            
            found_tables = result.fetchall()
            
            if not found_tables:
                print("✅ No matching temporary tables found")
                return
            
            print(f"Found {len(found_tables)} matching tables:")
            for schema, table, owner in found_tables:
                print(f"  📋 {schema}.{table} (owner: {owner})")
            
            if dry_run:
                print(f"\n🧪 DRY RUN - Would drop {len(found_tables)} tables")
                return
            
            print(f"\n🧹 Cleaning up {len(found_tables)} tables...")
            
            cleaned_count = 0
            failed_count = 0
            
            for schema, table, owner in found_tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {schema}.{table} CASCADE"))
                    print(f"  ✅ Dropped {schema}.{table}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to drop {schema}.{table}: {e}")
                    failed_count += 1
            
            try:
                conn.commit()
                print(f"\n📊 Cleanup Summary:")
                print(f"  ✅ Successfully dropped: {cleaned_count} tables")
                if failed_count > 0:
                    print(f"  ❌ Failed to drop: {failed_count} tables")
                else:
                    print(f"  🎉 All targeted tables cleaned up successfully!")
                    
            except Exception as e:
                print(f"❌ Error committing cleanup: {e}")
                conn.rollback()

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Clean up temporary database tables')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be cleaned up without actually doing it')
    parser.add_argument('--tables', nargs='+', 
                       help='Specific table names to clean up (e.g., temp_dem temp_oppo)')
    
    args = parser.parse_args()
    
    print("🧹 TEMPORARY TABLE CLEANUP SCRIPT")
    print("=" * 50)
    
    cleaner = TempTableCleaner()
    
    if args.tables:
        cleaner.cleanup_specific_tables(args.tables, dry_run=args.dry_run)
    else:
        cleaner.cleanup_temp_tables(dry_run=args.dry_run)
    
    print("\n✅ Cleanup script completed!")

if __name__ == "__main__":
    main()