#!/usr/bin/env python3
"""
Comprehensive Flippable Analysis
===============================

This script provides a complete analysis of flippable races combining:
- Narrow margin analysis
- DVA scenario testing
- Strategic precinct targeting
- Resource allocation recommendations

Usage:
    python3 comprehensive_flippable_analysis.py [--output-dir results] [--dva-levels 1.0,1.5,2.0,2.5]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import json

class ComprehensiveFlippableAnalysis:
    """Complete flippable race analysis and strategic planning."""
    
    def __init__(self, output_dir="flippable_analysis_results"):
        """Initialize with database connection and output directory."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def get_all_competitive_races(self, max_margin=10.0, min_votes=25):
        """Get all competitive races for comprehensive analysis."""
        query = '''
        WITH race_totals AS (
            SELECT 
                county, precinct, contest_name, election_date,
                SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
                SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes,
                SUM(CASE WHEN choice_party NOT IN ('DEM', 'REP') THEN total_votes ELSE 0 END) as other_votes,
                SUM(total_votes) as total_votes
            FROM candidate_vote_results 
            WHERE choice_party IN ('DEM', 'REP')
            GROUP BY county, precinct, contest_name, election_date
            HAVING SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) > 0 
               AND SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) > 0
        ),
        margins AS (
            SELECT *,
                CASE 
                    WHEN dem_votes > rep_votes THEN 'DEM'
                    WHEN rep_votes > dem_votes THEN 'REP'
                    ELSE 'TIE'
                END as winner,
                ABS(dem_votes - rep_votes) as vote_diff,
                ROUND((ABS(dem_votes - rep_votes) * 100.0 / total_votes), 2) as margin_pct,
                ROUND(((dem_votes - rep_votes) * 100.0 / total_votes), 2) as dem_margin_pct,
                ROUND(((ABS(dem_votes - rep_votes) + 1) * 100.0 / (total_votes + 2)), 2) as dva_pct_needed
            FROM race_totals
        )
        SELECT *
        FROM margins 
        WHERE margin_pct BETWEEN 0.01 AND :max_margin
          AND total_votes >= :min_votes
        ORDER BY margin_pct ASC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'max_margin': max_margin,
                'min_votes': min_votes
            })
            
            races = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'rep_votes', 'other_votes', 'total_votes', 
                'winner', 'vote_diff', 'margin_pct', 'dem_margin_pct', 'dva_pct_needed'
            ])
            
            # Convert to numeric
            numeric_cols = ['dem_votes', 'rep_votes', 'other_votes', 'total_votes', 
                          'vote_diff', 'margin_pct', 'dem_margin_pct', 'dva_pct_needed']
            for col in numeric_cols:
                races[col] = pd.to_numeric(races[col], errors='coerce')
        
        return races
    
    def analyze_strategic_tiers(self, races):
        """Categorize races into strategic tiers."""
        if len(races) == 0:
            return pd.DataFrame()
        
        # Focus on Republican-won races (Democratic targets)
        rep_targets = races[races['winner'] == 'REP'].copy()
        dem_defensive = races[races['winner'] == 'DEM'].copy()
        
        # Create strategic tiers for Republican targets
        def assign_tier(row):
            margin = row['margin_pct']
            votes = row['total_votes']
            
            if margin <= 0.5:
                return "Tier 1: Immediate (≤0.5%)"
            elif margin <= 1.0:
                return "Tier 2: High Priority (0.5-1.0%)"
            elif margin <= 2.0:
                return "Tier 3: Medium Priority (1.0-2.0%)"
            elif margin <= 5.0:
                return "Tier 4: Opportunity (2.0-5.0%)"
            else:
                return "Tier 5: Long-term (5.0%+)"
        
        if len(rep_targets) > 0:
            rep_targets['strategic_tier'] = rep_targets.apply(assign_tier, axis=1)
            rep_targets['priority_score'] = (1 / (rep_targets['margin_pct'] + 0.1)) * (rep_targets['total_votes'] / 1000)
        
        if len(dem_defensive) > 0:
            dem_defensive['strategic_tier'] = dem_defensive.apply(assign_tier, axis=1)
            dem_defensive['priority_score'] = (1 / (dem_defensive['margin_pct'] + 0.1)) * (dem_defensive['total_votes'] / 1000)
        
        return rep_targets, dem_defensive
    
    def test_multiple_dva_scenarios(self, rep_targets, dva_levels):
        """Test multiple DVA scenarios and track results."""
        dva_results = {}
        
        for dva_pct in dva_levels:
            print(f"🧪 Testing {dva_pct}% DVA scenario...")
            
            simulation = rep_targets.copy()
            simulation['dva_votes_added'] = (simulation['total_votes'] * dva_pct / 100).round().astype(int)
            simulation['new_dem_votes'] = simulation['dem_votes'] + simulation['dva_votes_added']
            simulation['new_total_votes'] = simulation['total_votes'] + simulation['dva_votes_added']
            simulation['new_vote_diff'] = simulation['rep_votes'] - simulation['new_dem_votes']
            simulation['flipped'] = simulation['new_vote_diff'] < 0
            
            flipped_count = simulation['flipped'].sum()
            total_dva_votes = simulation['dva_votes_added'].sum()
            
            dva_results[dva_pct] = {
                'flipped_races': flipped_count,
                'total_dva_votes': total_dva_votes,
                'efficiency_ratio': flipped_count / (total_dva_votes / 1000) if total_dva_votes > 0 else 0,
                'flipped_races_list': simulation[simulation['flipped']].copy()
            }
            
            print(f"   Races flipped: {flipped_count}")
            print(f"   DVA votes needed: {total_dva_votes:,}")
            
        return dva_results
    
    def find_high_impact_precincts(self, rep_targets, top_n=15):
        """Find precincts with highest impact potential."""
        if len(rep_targets) == 0:
            return pd.DataFrame()
        
        # Group by precinct and calculate impact metrics
        precinct_analysis = rep_targets.groupby(['county', 'precinct']).agg({
            'contest_name': 'count',
            'vote_diff': 'sum',
            'total_votes': 'sum',
            'dva_pct_needed': 'mean',
            'margin_pct': 'mean',
            'priority_score': 'sum'
        }).round(2)
        
        precinct_analysis.columns = [
            'flippable_races', 'total_vote_gap', 'total_votes', 
            'avg_dva_needed', 'avg_margin', 'impact_score'
        ]
        
        # Calculate efficiency metrics
        precinct_analysis['votes_per_race'] = precinct_analysis['total_votes'] / precinct_analysis['flippable_races']
        precinct_analysis['gap_per_race'] = precinct_analysis['total_vote_gap'] / precinct_analysis['flippable_races']
        
        # Sort by impact score
        high_impact = precinct_analysis.sort_values('impact_score', ascending=False).head(top_n)
        
        return high_impact
    
    def generate_resource_recommendations(self, dva_results, high_impact_precincts, rep_targets):
        """Generate strategic resource allocation recommendations."""
        recommendations = {
            'executive_summary': {
                'total_republican_targets': len(rep_targets),
                'high_impact_precincts': len(high_impact_precincts),
                'dva_scenarios_tested': len(dva_results)
            },
            'dva_efficiency': {},
            'top_precincts': {},
            'strategic_recommendations': []
        }
        
        # DVA efficiency analysis
        for dva_pct, results in dva_results.items():
            recommendations['dva_efficiency'][f'{dva_pct}%'] = {
                'races_flipped': int(results['flipped_races']),
                'votes_needed': int(results['total_dva_votes']),
                'efficiency_ratio': round(results['efficiency_ratio'], 2)
            }
        
        # Top precincts
        for (county, precinct), stats in high_impact_precincts.head(10).iterrows():
            key = f"{county} Precinct {precinct}"
            recommendations['top_precincts'][key] = {
                'flippable_races': int(stats['flippable_races']),
                'avg_dva_needed': float(stats['avg_dva_needed']),
                'impact_score': float(stats['impact_score']),
                'total_vote_gap': int(stats['total_vote_gap'])
            }
        
        # Strategic recommendations
        recommendations['strategic_recommendations'] = [
            {
                'priority': 'Immediate',
                'action': 'Focus on Tier 1 races (≤0.5% margin)',
                'races_count': len(rep_targets[rep_targets['margin_pct'] <= 0.5]),
                'estimated_dva_needed': '0.5-1.0%'
            },
            {
                'priority': 'High',
                'action': 'Target top 5 impact precincts',
                'precincts': list(high_impact_precincts.head(5).index),
                'estimated_dva_needed': f"{high_impact_precincts.head(5)['avg_dva_needed'].mean():.1f}%"
            },
            {
                'priority': 'Medium',
                'action': 'Expand to Tier 2-3 races with 1.5-2.0% DVA',
                'races_count': len(rep_targets[(rep_targets['margin_pct'] > 0.5) & (rep_targets['margin_pct'] <= 2.0)]),
                'estimated_dva_needed': '1.5-2.0%'
            }
        ]
        
        return recommendations
    
    def export_comprehensive_analysis(self, races, rep_targets, dem_defensive, dva_results, high_impact_precincts, recommendations):
        """Export all analysis results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export main datasets
        races.to_csv(f"{self.output_dir}/all_competitive_races_{timestamp}.csv", index=False)
        rep_targets.to_csv(f"{self.output_dir}/republican_targets_{timestamp}.csv", index=False)
        dem_defensive.to_csv(f"{self.output_dir}/democratic_defensive_{timestamp}.csv", index=False)
        high_impact_precincts.to_csv(f"{self.output_dir}/high_impact_precincts_{timestamp}.csv")
        
        # Export DVA scenario results
        for dva_pct, results in dva_results.items():
            filename = f"{self.output_dir}/dva_{dva_pct}pct_flipped_{timestamp}.csv"
            results['flipped_races_list'].to_csv(filename, index=False)
        
        # Export recommendations as JSON
        with open(f"{self.output_dir}/strategic_recommendations_{timestamp}.json", 'w') as f:
            json.dump(recommendations, f, indent=2, default=str)
        
        print(f"📄 Analysis exported to {self.output_dir}/")
        return timestamp
    
    def generate_summary_report(self, races, rep_targets, dem_defensive, dva_results, high_impact_precincts, recommendations):
        """Generate comprehensive summary report."""
        print(f"\n📊 COMPREHENSIVE FLIPPABLE ANALYSIS REPORT")
        print("=" * 70)
        
        # Overall statistics
        print(f"COMPETITIVE RACE OVERVIEW:")
        print(f"  Total competitive races (≤10% margin): {len(races)}")
        print(f"  Republican-held targets: {len(rep_targets)} ({len(rep_targets)/len(races)*100:.1f}%)")
        print(f"  Democratic defensive priorities: {len(dem_defensive)} ({len(dem_defensive)/len(races)*100:.1f}%)")
        print()
        
        # Tier analysis
        if len(rep_targets) > 0:
            tier_counts = rep_targets['strategic_tier'].value_counts().sort_index()
            print(f"REPUBLICAN TARGET TIERS:")
            for tier, count in tier_counts.items():
                print(f"  {tier}: {count} races")
            print()
        
        # DVA scenario results
        print(f"DVA SCENARIO EFFICIENCY:")
        for dva_pct in sorted(dva_results.keys()):
            results = dva_results[dva_pct]
            print(f"  {dva_pct}% DVA: {results['flipped_races']} races flipped with {results['total_dva_votes']:,} votes")
            print(f"             Efficiency: {results['efficiency_ratio']:.2f} races per 1,000 votes")
        print()
        
        # High impact precincts
        print(f"TOP HIGH-IMPACT PRECINCTS:")
        for (county, precinct), stats in high_impact_precincts.head(8).iterrows():
            print(f"  {county} Precinct {precinct}: {stats['flippable_races']} races, {stats['avg_dva_needed']:.1f}% avg DVA needed")
        print()
        
        # Key recommendations
        print(f"STRATEGIC RECOMMENDATIONS:")
        for rec in recommendations['strategic_recommendations']:
            print(f"  {rec['priority']} Priority: {rec['action']}")
            if 'races_count' in rec:
                print(f"    Target races: {rec['races_count']}")
            if 'estimated_dva_needed' in rec:
                print(f"    DVA needed: {rec['estimated_dva_needed']}")
            print()

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Comprehensive flippable race analysis')
    parser.add_argument('--max-margin', type=float, default=10.0,
                       help='Maximum margin percentage to consider (default: 10.0)')
    parser.add_argument('--min-votes', type=int, default=25,
                       help='Minimum total votes in race (default: 25)')
    parser.add_argument('--dva-levels', type=str, default="1.0,1.5,2.0,2.5",
                       help='Comma-separated DVA levels to test (default: 1.0,1.5,2.0,2.5)')
    parser.add_argument('--output-dir', type=str, default="flippable_analysis_results",
                       help='Output directory for results (default: flippable_analysis_results)')
    parser.add_argument('--top-precincts', type=int, default=15,
                       help='Number of top precincts to analyze (default: 15)')
    
    args = parser.parse_args()
    
    print("🎯 COMPREHENSIVE FLIPPABLE ANALYSIS")
    print("=" * 50)
    print("Complete strategic analysis of flippable races and targeting opportunities")
    print()
    
    # Parse DVA levels
    dva_levels = [float(x.strip()) for x in args.dva_levels.split(',')]
    
    # Initialize analyzer
    analyzer = ComprehensiveFlippableAnalysis(args.output_dir)
    
    # Step 1: Get all competitive races
    print(f"🔍 Step 1: Gathering competitive races...")
    races = analyzer.get_all_competitive_races(args.max_margin, args.min_votes)
    
    if len(races) == 0:
        print("No competitive races found with current criteria.")
        return
    
    print(f"Found {len(races)} competitive races")
    
    # Step 2: Strategic tier analysis
    print(f"🎯 Step 2: Analyzing strategic tiers...")
    rep_targets, dem_defensive = analyzer.analyze_strategic_tiers(races)
    
    if len(rep_targets) == 0:
        print("No Republican targets found.")
        return
    
    print(f"Identified {len(rep_targets)} Republican targets and {len(dem_defensive)} Democratic defensive priorities")
    
    # Step 3: DVA scenario testing
    print(f"🧪 Step 3: Testing DVA scenarios...")
    dva_results = analyzer.test_multiple_dva_scenarios(rep_targets, dva_levels)
    
    # Step 4: High-impact precinct analysis
    print(f"📍 Step 4: Finding high-impact precincts...")
    high_impact_precincts = analyzer.find_high_impact_precincts(rep_targets, args.top_precincts)
    
    # Step 5: Generate recommendations
    print(f"💡 Step 5: Generating strategic recommendations...")
    recommendations = analyzer.generate_resource_recommendations(dva_results, high_impact_precincts, rep_targets)
    
    # Step 6: Export analysis
    print(f"💾 Step 6: Exporting comprehensive analysis...")
    timestamp = analyzer.export_comprehensive_analysis(
        races, rep_targets, dem_defensive, dva_results, high_impact_precincts, recommendations
    )
    
    # Step 7: Generate summary report
    analyzer.generate_summary_report(
        races, rep_targets, dem_defensive, dva_results, high_impact_precincts, recommendations
    )
    
    print(f"\n✅ Comprehensive analysis complete!")
    print(f"   Results exported to: {args.output_dir}/")
    print(f"   Analysis timestamp: {timestamp}")

if __name__ == "__main__":
    main()