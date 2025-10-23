#!/usr/bin/env python3
"""
Quick Fix: Clustering Analysis Zero Padding
===========================================

This script applies a minimal, surgical fix to the clustering analysis
to handle precinct zero-padding without massive data migration.

Usage:
    cd app_administration
    python fix_clustering_quick.py

Note: Script automatically changes to parent directory to access main files.
"""

import os
import shutil
from datetime import datetime

def create_quick_fix():
    """Apply a targeted fix to clustering_analysis.py for zero padding."""
    
    print("🔧 APPLYING QUICK FIX FOR PRECINCT ZERO PADDING")
    print("=" * 55)
    
    # Change to parent directory where the main scripts are located
    original_dir = os.getcwd()
    parent_dir = os.path.dirname(original_dir)
    os.chdir(parent_dir)
    print(f"📁 Changed directory to: {parent_dir}")
    
    # Backup original
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"clustering_analysis_backup_{timestamp}.py"
    shutil.copy("clustering_analysis.py", backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    # Read original file
    with open("clustering_analysis.py", "r") as f:
        content = f.read()
    
    # Add the precinct normalization function at the top
    precinct_norm_function = '''
def normalize_precinct_for_join(precinct_str):
    """Handle precinct zero-padding for joins."""
    if pd.isna(precinct_str):
        return None
    precinct = str(precinct_str).strip()
    if not precinct:
        return None
    # Remove leading zeros, but keep at least one digit
    return precinct.lstrip('0') or '0'

'''
    
    # Insert after the imports
    import_end = content.find('warnings.filterwarnings(\'ignore\')')
    if import_end != -1:
        insert_point = content.find('\n', import_end) + 1
        content = content[:insert_point] + precinct_norm_function + content[insert_point:]
    
    # Fix the flippable data aggregation
    old_agg = '''        # Aggregate flippability data by precinct
        flippable_agg = self.flippable_data.groupby(['county', 'precinct']).agg({
            'dem_votes': 'sum',
            'oppo_votes': 'sum', 
            'dem_margin': 'mean',
            'dva_pct_needed': 'mean'
        }).reset_index()'''
    
    new_agg = '''        # Aggregate flippability data by precinct (normalized for zero padding)
        self.flippable_data['precinct_norm'] = self.flippable_data['precinct'].apply(normalize_precinct_for_join)
        flippable_agg = self.flippable_data.groupby(['county', 'precinct_norm']).agg({
            'dem_votes': 'sum',
            'oppo_votes': 'sum', 
            'dem_margin': 'mean',
            'dva_pct_needed': 'mean'
        }).reset_index()
        # Rename back to precinct for consistency
        flippable_agg = flippable_agg.rename(columns={'precinct_norm': 'precinct'})'''
    
    content = content.replace(old_agg, new_agg)
    
    # Fix the comprehensive data merge
    old_merge = '''        # Merge all datasets
        comprehensive = spatial_data.merge(
            voting_summary, on=['county', 'precinct'], how='left'
        ).merge(
            flippable_data, on=['county', 'precinct'], how='left'  
        )'''
    
    new_merge = '''        # Normalize precinct IDs for consistent joining
        spatial_data['precinct_norm'] = spatial_data['precinct'].apply(normalize_precinct_for_join)
        flippable_data['precinct_norm'] = flippable_data['precinct'].apply(normalize_precinct_for_join)
        
        # Merge all datasets using normalized precinct IDs
        comprehensive = spatial_data.merge(
            voting_summary, left_on=['county', 'precinct_norm'], right_on=['county', 'precinct'], how='left'
        ).merge(
            flippable_data, on=['county', 'precinct_norm'], how='left', suffixes=('', '_flippable')
        )
        
        # Clean up duplicate columns
        if 'precinct_flippable' in comprehensive.columns:
            comprehensive = comprehensive.drop(columns=['precinct_flippable'])'''
    
    content = content.replace(old_merge, new_merge)
    
    # Write the fixed file
    with open("clustering_analysis.py", "w") as f:
        f.write(content)
    
    # Restore original directory
    os.chdir(original_dir)
    print(f"📁 Restored directory to: {original_dir}")
    
    print(f"✅ Quick fix applied successfully!")
    print(f"   - Added precinct normalization function")
    print(f"   - Fixed flippable data aggregation")  
    print(f"   - Fixed data merging for zero-padding compatibility")
    print(f"\n🧪 TEST THE FIX:")
    print(f"   cd .. && python clustering_analysis.py")
    print(f"\n📋 Then check precinct_clustering_results.csv for precinct 074")
    
    return True

if __name__ == "__main__":
    # Check if clustering_analysis.py exists in parent directory
    parent_dir = os.path.dirname(os.getcwd())
    clustering_file = os.path.join(parent_dir, "clustering_analysis.py")
    
    if not os.path.exists(clustering_file):
        print("❌ clustering_analysis.py not found in parent directory")
        print(f"   Looking for: {clustering_file}")
    else:
        create_quick_fix()