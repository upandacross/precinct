#!/usr/bin/env python3
"""
Fix Precinct Zero Padding Issues
================================

This script fixes the zero-padding inconsistency in the clustering analysis
that causes precincts to show zeros for political metrics.

The issue: Precincts table uses "074" but voting tables use "74"
The fix: Normalize precinct numbers during data loading and joining

Usage:
    cd app_administration
    python fix_clustering_zero_padding.py

Note: Script automatically changes to parent directory to access main files.
"""

import os
import shutil
from datetime import datetime

def create_backup():
    """Create a backup of the original clustering analysis file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"clustering_analysis_backup_{timestamp}.py"
    shutil.copy("clustering_analysis.py", backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def fix_clustering_analysis():
    """Fix the clustering analysis script to handle zero padding."""
    
    print("🔧 FIXING CLUSTERING ANALYSIS ZERO PADDING")
    print("=" * 50)
    
    # Change to parent directory where the main scripts are located
    original_dir = os.getcwd()
    parent_dir = os.path.dirname(original_dir)
    os.chdir(parent_dir)
    print(f"📁 Changed directory to: {parent_dir}")
    
    # Create backup
    backup_path = create_backup()
    
    # Read the original file
    with open("clustering_analysis.py", "r") as f:
        content = f.read()
    
    # Define the fixes needed
    fixes = [
        {
            "description": "Add precinct normalization function",
            "search": "class PrecinctClusteringAnalysis:",
            "replace": """def normalize_precinct_id(precinct_str):
    \"\"\"Normalize precinct ID to handle zero-padding inconsistencies.
    
    Args:
        precinct_str: Precinct ID as string (e.g., '074', '74', '4')
        
    Returns:
        Tuple of (padded, unpadded) versions for flexible matching
    \"\"\"
    if pd.isna(precinct_str):
        return None, None
    
    # Convert to string and strip whitespace
    precinct = str(precinct_str).strip()
    
    # Handle empty strings
    if not precinct:
        return None, None
    
    # Get unpadded version (remove leading zeros)
    unpadded = precinct.lstrip('0') or '0'  # Keep at least one zero if all zeros
    
    # Get padded version (ensure 3 digits)
    padded = unpadded.zfill(3)
    
    return padded, unpadded

class PrecinctClusteringAnalysis:"""
        },
        {
            "description": "Import pandas at top for the normalize function",
            "search": "import warnings\nwarnings.filterwarnings('ignore')",
            "replace": "import warnings\nwarnings.filterwarnings('ignore')\n\n# Import pandas for normalize function\nimport pandas as pd"
        },
        {
            "description": "Fix flippable data loading with precinct normalization",
            "search": """        # 3. Flippability data
        self.flippable_data = pd.read_sql(text(\"\"\"
            SELECT 
                county,
                precinct,
                contest_name,
                dem_votes,
                oppo_votes,
                dem_margin,
                dva_pct_needed
            FROM flippable
            WHERE dem_votes IS NOT NULL 
                AND oppo_votes IS NOT NULL
            ORDER BY county, precinct
        \"\"\"), db.session.connection())""",
            "replace": """        # 3. Flippability data with precinct normalization
        flippable_raw = pd.read_sql(text(\"\"\"
            SELECT 
                county,
                precinct,
                contest_name,
                dem_votes,
                oppo_votes,
                dem_margin,
                dva_pct_needed
            FROM flippable
            WHERE dem_votes IS NOT NULL 
                AND oppo_votes IS NOT NULL
            ORDER BY county, precinct
        \"\"\"), db.session.connection())
        
        # Normalize precinct IDs to handle zero-padding
        flippable_raw[['precinct_padded', 'precinct_unpadded']] = pd.DataFrame(
            flippable_raw['precinct'].apply(lambda x: normalize_precinct_id(x)).tolist()
        )
        self.flippable_data = flippable_raw"""
        },
        {
            "description": "Fix spatial data loading with precinct normalization", 
            "search": """        # 1. Spatial data from precincts table
        self.spatial_data = pd.read_sql(text(\"\"\"
            SELECT 
                precinct,
                county,
                precinct_name,
                ST_Area(ST_Transform(geom, 3857)) / 1000000 as area_km2,
                ST_Perimeter(ST_Transform(geom, 3857)) / 1000 as perimeter_km,
                ST_Area(ST_Transform(geom, 3857)) / (ST_Perimeter(ST_Transform(geom, 3857)) * ST_Perimeter(ST_Transform(geom, 3857))) as shape_complexity,
                ST_X(ST_Centroid(geom)) as longitude,
                ST_Y(ST_Centroid(geom)) as latitude
            FROM precincts
            WHERE geom IS NOT NULL
            ORDER BY county, precinct
        \"\"\"), db.session.connection())""",
            "replace": """        # 1. Spatial data from precincts table with precinct normalization
        spatial_raw = pd.read_sql(text(\"\"\"
            SELECT 
                precinct,
                county,
                precinct_name,
                ST_Area(ST_Transform(geom, 3857)) / 1000000 as area_km2,
                ST_Perimeter(ST_Transform(geom, 3857)) / 1000 as perimeter_km,
                ST_Area(ST_Transform(geom, 3857)) / (ST_Perimeter(ST_Transform(geom, 3857)) * ST_Perimeter(ST_Transform(geom, 3857))) as shape_complexity,
                ST_X(ST_Centroid(geom)) as longitude,
                ST_Y(ST_Centroid(geom)) as latitude
            FROM precincts
            WHERE geom IS NOT NULL
            ORDER BY county, precinct
        \"\"\"), db.session.connection())
        
        # Normalize precinct IDs to handle zero-padding
        spatial_raw[['precinct_padded', 'precinct_unpadded']] = pd.DataFrame(
            spatial_raw['precinct'].apply(lambda x: normalize_precinct_id(x)).tolist()
        )
        self.spatial_data = spatial_raw"""
        },
        {
            "description": "Fix flippable data aggregation to use flexible precinct matching",
            "search": """        # Aggregate flippability data by precinct
        flippable_agg = self.flippable_data.groupby(['county', 'precinct']).agg({
            'dem_votes': 'sum',
            'oppo_votes': 'sum', 
            'dem_margin': 'mean',
            'dva_pct_needed': 'mean'
        }).reset_index()""",
            "replace": """        # Aggregate flippability data by normalized precinct
        # Use unpadded precinct for consistent grouping
        flippable_for_agg = self.flippable_data.copy()
        flippable_for_agg['precinct_key'] = flippable_for_agg['precinct_unpadded']
        
        flippable_agg = flippable_for_agg.groupby(['county', 'precinct_key']).agg({
            'dem_votes': 'sum',
            'oppo_votes': 'sum', 
            'dem_margin': 'mean',
            'dva_pct_needed': 'mean'
        }).reset_index()
        
        # Rename back to precinct for consistency
        flippable_agg = flippable_agg.rename(columns={'precinct_key': 'precinct'})"""
        },
        {
            "description": "Fix comprehensive data merge to handle precinct padding",
            "search": """        # Merge all datasets
        comprehensive = spatial_data.merge(
            voting_summary, on=['county', 'precinct'], how='left'
        ).merge(
            flippable_data, on=['county', 'precinct'], how='left'  
        )""",
            "replace": """        # Prepare spatial data for merging with normalized precinct
        spatial_for_merge = spatial_data.copy()
        spatial_for_merge['precinct_key'] = spatial_for_merge['precinct_unpadded']
        
        # Prepare flippable data for merging
        flippable_for_merge = flippable_data.copy() 
        flippable_for_merge['precinct_key'] = flippable_for_merge['precinct']
        
        # Merge all datasets using normalized precinct keys
        comprehensive = spatial_for_merge.merge(
            voting_summary, left_on=['county', 'precinct_key'], right_on=['county', 'precinct'], how='left'
        ).merge(
            flippable_for_merge, on=['county', 'precinct_key'], how='left', suffixes=('', '_flippable')
        )
        
        # Clean up duplicate columns and keep original precinct naming
        comprehensive = comprehensive.drop(columns=[col for col in comprehensive.columns if col.endswith('_flippable') and col != 'precinct_flippable'])
        if 'precinct_flippable' in comprehensive.columns:
            comprehensive = comprehensive.drop(columns=['precinct_flippable'])"""
        }
    ]
    
    # Apply each fix
    modified_content = content
    for i, fix in enumerate(fixes, 1):
        print(f"🔧 Applying fix {i}/{len(fixes)}: {fix['description']}")
        
        if fix["search"] in modified_content:
            modified_content = modified_content.replace(fix["search"], fix["replace"])
            print(f"   ✅ Applied successfully")
        else:
            print(f"   ⚠️  Search pattern not found - may need manual review")
    
    # Write the fixed file
    with open("clustering_analysis.py", "w") as f:
        f.write(modified_content)
    
    print(f"\n✅ FIXES APPLIED")
    print(f"   - Original backed up to: {backup_path}")
    print(f"   - Fixed clustering_analysis.py")
    print(f"   - Added precinct ID normalization function")
    print(f"   - Updated data loading to handle zero-padding")
    print(f"   - Modified merging logic for flexible precinct matching")
    
    # Restore original directory
    os.chdir(original_dir)
    print(f"📁 Restored directory to: {original_dir}")
    
    return True

def main():
    """Main execution function.""" 
    # Check if clustering_analysis.py exists in parent directory
    parent_dir = os.path.dirname(os.getcwd())
    clustering_file = os.path.join(parent_dir, "clustering_analysis.py")
    
    if not os.path.exists(clustering_file):
        print("❌ clustering_analysis.py not found in parent directory")
        print(f"   Looking for: {clustering_file}")
        return False
    
    try:
        success = fix_clustering_analysis()
        if success:
            print(f"\n🎯 NEXT STEPS:")
            print(f"   1. Test the fixed clustering analysis: cd .. && python clustering_analysis.py")
            print(f"   2. Check if precinct 074 now shows proper political metrics")
            print(f"   3. Regenerate clustering results CSV if needed")
        return success
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False

if __name__ == "__main__":
    main()