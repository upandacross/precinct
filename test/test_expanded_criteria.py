#!/usr/bin/env python3
"""
Expanded Criteria Flippable Analysis
===================================

This script analyzes flippable races using expanded criteria based on the
enhanced targeting approach from the clustering analysis. It looks for races
that could be competitive with strategic intervention beyond just narrow margins.

Usage:
    python3 test_expanded_criteria.py [--max-margin 15.0] [--min-turnout 0.6] [--dva-cap 5.0]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

class ExpandedCriteriaAnalyzer:
    """Analyzes flippable races using expanded strategic criteria."""
    
    def __init__(self):
        """Initialize with database connection."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
    
    def find_expanded_targets(self, max_margin=15.0, min_votes=50, dva_cap=5.0):
        """Find Republican-won races using expanded criteria."""
        print(f"🎯 Finding races with expanded targeting criteria...")
        print(f"   - Maximum Republican margin: {max_margin}%")
        print(f"   - Minimum total votes: {min_votes}")
        print(f"   - DVA cap for feasibility: {dva_cap}%")
        
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
                (rep_votes - dem_votes) as vote_diff,
                ROUND(((rep_votes - dem_votes) * 100.0 / total_votes), 2) as rep_margin_pct,
                ROUND(((rep_votes - dem_votes + 1) * 100.0 / (total_votes + 2)), 2) as dva_pct_needed,
                ROUND((dem_votes * 100.0 / total_votes), 2) as dem_base_pct
            FROM race_totals
            WHERE rep_votes > dem_votes  -- Republicans currently winning
        ),
        expanded_targets AS (
            SELECT *,
                CASE 
                    WHEN rep_margin_pct <= 0.5 THEN 'Ultra-Target'
                    WHEN rep_margin_pct <= 2.0 THEN 'High-Target'
                    WHEN rep_margin_pct <= 5.0 THEN 'Medium-Target'
                    WHEN rep_margin_pct <= 10.0 THEN 'Opportunity'
                    ELSE 'Long-term'
                END as target_category,
                CASE 
                    WHEN dva_pct_needed <= 1.0 THEN 'Immediate'
                    WHEN dva_pct_needed <= 2.0 THEN 'Short-term'
                    WHEN dva_pct_needed <= 3.0 THEN 'Medium-term'
                    WHEN dva_pct_needed <= 5.0 THEN 'Longer-term'
                    ELSE 'Aspirational'
                END as feasibility_tier,
                -- Strategic scoring
                (1.0 / (rep_margin_pct + 0.1)) * (total_votes / 1000.0) as opportunity_score
            FROM margins 
            WHERE rep_margin_pct BETWEEN 0.1 AND :max_margin
              AND total_votes >= :min_votes
              AND dva_pct_needed <= :dva_cap  -- Feasible DVA requirement
        )
        SELECT *
        FROM expanded_targets 
        ORDER BY opportunity_score DESC, rep_margin_pct ASC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'max_margin': max_margin,
                'min_votes': min_votes,
                'dva_cap': dva_cap
            })
            
            targets = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'rep_votes', 'other_votes', 'total_votes', 
                'vote_diff', 'rep_margin_pct', 'dva_pct_needed', 'dem_base_pct',
                'target_category', 'feasibility_tier', 'opportunity_score'
            ])
            
            # Convert to numeric
            numeric_cols = ['dem_votes', 'rep_votes', 'other_votes', 'total_votes', 
                          'vote_diff', 'rep_margin_pct', 'dva_pct_needed', 'dem_base_pct', 'opportunity_score']
            for col in numeric_cols:
                targets[col] = pd.to_numeric(targets[col], errors='coerce')
        
        print(f"✅ Found {len(targets)} races meeting expanded criteria")
        return targets
    
    def analyze_by_criteria_categories(self, targets):
        """Analyze targets by category and feasibility."""
        if len(targets) == 0:
            return
        
        print(f"\n📊 EXPANDED CRITERIA ANALYSIS")
        print("=" * 60)
        
        # Target category breakdown
        category_stats = targets.groupby('target_category').agg({
            'contest_name': 'count',
            'rep_margin_pct': 'mean',
            'dva_pct_needed': 'mean',
            'opportunity_score': 'sum',
            'total_votes': 'sum'
        }).round(2)
        
        category_stats.columns = ['races', 'avg_margin', 'avg_dva_needed', 'total_opportunity', 'total_votes']
        
        print(f"TARGET CATEGORIES:")
        for category, stats in category_stats.iterrows():
            print(f"  {category}: {stats['races']} races")
            print(f"    Avg margin: {stats['avg_margin']}%")
            print(f"    Avg DVA needed: {stats['avg_dva_needed']}%")
            print(f"    Opportunity score: {stats['total_opportunity']:.1f}")
            print(f"    Total votes: {stats['total_votes']:,}")
            print()
        
        # Feasibility tier breakdown
        feasibility_stats = targets.groupby('feasibility_tier').agg({
            'contest_name': 'count',
            'dva_pct_needed': 'mean',
            'rep_margin_pct': 'mean'
        }).round(2)
        
        feasibility_stats.columns = ['races', 'avg_dva_needed', 'avg_margin']
        
        print(f"FEASIBILITY TIERS:")
        for tier, stats in feasibility_stats.iterrows():
            print(f"  {tier}: {stats['races']} races (avg DVA: {stats['avg_dva_needed']}%)")
    
    def find_cluster_opportunities(self, targets):
        """Find precincts with multiple opportunities for cluster targeting."""
        if len(targets) == 0:
            return pd.DataFrame()
        
        # Group by precinct to find cluster opportunities
        precinct_clusters = targets.groupby(['county', 'precinct']).agg({
            'contest_name': 'count',
            'dva_pct_needed': 'mean',
            'rep_margin_pct': 'mean',
            'opportunity_score': 'sum',
            'total_votes': 'sum',
            'vote_diff': 'sum'
        }).round(2)
        
        precinct_clusters.columns = [
            'target_races', 'avg_dva_needed', 'avg_margin', 
            'cluster_opportunity', 'total_votes', 'total_gap'
        ]
        
        # Calculate cluster efficiency
        precinct_clusters['efficiency_ratio'] = (
            precinct_clusters['target_races'] / precinct_clusters['avg_dva_needed']
        ).round(2)
        
        # Focus on precincts with multiple races (cluster targeting)
        multi_race_clusters = precinct_clusters[precinct_clusters['target_races'] >= 3].copy()
        multi_race_clusters = multi_race_clusters.sort_values('cluster_opportunity', ascending=False)
        
        print(f"\n🎯 CLUSTER TARGETING OPPORTUNITIES")
        print("=" * 60)
        print(f"Precincts with 3+ flippable races (cluster targeting potential):")
        print()
        
        for (county, precinct), stats in multi_race_clusters.head(10).iterrows():
            print(f"📍 {county} Precinct {precinct}:")
            print(f"   Target races: {stats['target_races']}")
            print(f"   Avg DVA needed: {stats['avg_dva_needed']}%")
            print(f"   Total vote gap: {stats['total_gap']} votes")
            print(f"   Cluster efficiency: {stats['efficiency_ratio']:.2f}")
            print(f"   Opportunity score: {stats['cluster_opportunity']:.1f}")
            print()
        
        return multi_race_clusters
    
    def test_scaled_dva_impact(self, targets, dva_scenarios=[1.0, 2.0, 3.0, 4.0]):
        """Test impact of scaled DVA increases on expanded targets."""
        print(f"\n🧪 SCALED DVA IMPACT ANALYSIS")
        print("=" * 60)
        
        impact_summary = {}
        
        for dva_pct in dva_scenarios:
            # Simulate DVA impact
            simulation = targets.copy()
            simulation['dva_votes_added'] = (simulation['total_votes'] * dva_pct / 100).round().astype(int)
            simulation['new_dem_votes'] = simulation['dem_votes'] + simulation['dva_votes_added']
            simulation['new_vote_diff'] = simulation['rep_votes'] - simulation['new_dem_votes']
            simulation['flipped'] = simulation['new_vote_diff'] < 0
            
            # Calculate improvements for non-flipped races
            simulation['margin_improvement'] = (
                simulation['rep_margin_pct'] - 
                ((simulation['new_vote_diff'] / (simulation['total_votes'] + simulation['dva_votes_added'])) * 100)
            ).round(2)
            
            flipped_count = simulation['flipped'].sum()
            total_dva_votes = simulation['dva_votes_added'].sum()
            improved_count = (simulation['margin_improvement'] > 0.5).sum()
            
            impact_summary[dva_pct] = {
                'flipped': flipped_count,
                'improved_significantly': improved_count,
                'total_dva_votes': total_dva_votes,
                'efficiency': flipped_count / (total_dva_votes / 1000) if total_dva_votes > 0 else 0
            }
            
            print(f"{dva_pct}% DVA Scenario:")
            print(f"  Races flipped: {flipped_count}")
            print(f"  Races improved >0.5%: {improved_count}")
            print(f"  Total DVA votes: {total_dva_votes:,}")
            print(f"  Efficiency: {impact_summary[dva_pct]['efficiency']:.2f} flips per 1K votes")
            print()
        
        return impact_summary
    
    def generate_strategic_targeting_plan(self, targets, multi_race_clusters):
        """Generate a strategic targeting plan based on expanded criteria."""
        print(f"\n📋 STRATEGIC TARGETING PLAN")
        print("=" * 60)
        
        # Phase 1: Immediate opportunities
        immediate = targets[
            (targets['target_category'] == 'Ultra-Target') | 
            (targets['feasibility_tier'] == 'Immediate')
        ]
        
        # Phase 2: High-value cluster targets
        cluster_precincts = set(multi_race_clusters.head(5).index)
        cluster_targets = targets[
            targets.set_index(['county', 'precinct']).index.isin(cluster_precincts)
        ]
        
        # Phase 3: Medium-term opportunities
        medium_term = targets[
            (targets['target_category'].isin(['High-Target', 'Medium-Target'])) &
            (targets['feasibility_tier'].isin(['Short-term', 'Medium-term']))
        ]
        
        print(f"PHASE 1 - IMMEDIATE TARGETS ({len(immediate)} races):")
        print(f"  Criteria: Ultra-narrow margins OR immediate feasibility")
        print(f"  Avg DVA needed: {immediate['dva_pct_needed'].mean():.2f}%")
        print(f"  Avg margin: {immediate['rep_margin_pct'].mean():.2f}%")
        print()
        
        print(f"PHASE 2 - CLUSTER TARGETING ({len(cluster_targets)} races in top 5 precincts):")
        print(f"  Criteria: Multiple races in high-opportunity precincts")
        print(f"  Avg DVA needed: {cluster_targets['dva_pct_needed'].mean():.2f}%")
        print(f"  Total races per precinct: {len(cluster_targets) / min(5, len(multi_race_clusters)):.1f}")
        print()
        
        print(f"PHASE 3 - MEDIUM-TERM EXPANSION ({len(medium_term)} races):")
        print(f"  Criteria: High/Medium targets with feasible DVA requirements")
        print(f"  Avg DVA needed: {medium_term['dva_pct_needed'].mean():.2f}%")
        print(f"  Avg margin: {medium_term['rep_margin_pct'].mean():.2f}%")
        print()
        
        total_strategic = len(immediate) + len(cluster_targets) + len(medium_term)
        print(f"TOTAL STRATEGIC TARGETS: {total_strategic} races")
        print(f"Percentage of all targets: {(total_strategic / len(targets)) * 100:.1f}%")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Analyze flippable races with expanded criteria')
    parser.add_argument('--max-margin', type=float, default=15.0,
                       help='Maximum Republican margin percentage (default: 15.0)')
    parser.add_argument('--min-votes', type=int, default=50,
                       help='Minimum total votes in race (default: 50)')
    parser.add_argument('--dva-cap', type=float, default=5.0,
                       help='Maximum DVA percentage for feasibility (default: 5.0)')
    parser.add_argument('--export-csv', action='store_true',
                       help='Export results to CSV file')
    
    args = parser.parse_args()
    
    print("🎯 EXPANDED CRITERIA FLIPPABLE ANALYSIS")
    print("=" * 50)
    print("Strategic analysis using enhanced targeting criteria")
    print()
    
    # Initialize analyzer
    analyzer = ExpandedCriteriaAnalyzer()
    
    # Find expanded targets
    targets = analyzer.find_expanded_targets(args.max_margin, args.min_votes, args.dva_cap)
    
    if len(targets) == 0:
        print("No targets found with current expanded criteria.")
        return
    
    # Analyze by categories
    analyzer.analyze_by_criteria_categories(targets)
    
    # Find cluster opportunities
    multi_race_clusters = analyzer.find_cluster_opportunities(targets)
    
    # Test scaled DVA impact
    impact_summary = analyzer.test_scaled_dva_impact(targets)
    
    # Generate strategic plan
    analyzer.generate_strategic_targeting_plan(targets, multi_race_clusters)
    
    # Export if requested
    if args.export_csv:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"expanded_criteria_targets_{timestamp}.csv"
        targets.to_csv(filename, index=False)
        print(f"\n💾 Exported {len(targets)} targets to: {filename}")
    
    print(f"\n✅ Expanded criteria analysis complete!")
    print(f"   Total targets found: {len(targets)}")
    print(f"   Cluster opportunities: {len(multi_race_clusters)}")
    print(f"   DVA scenarios tested: {len(impact_summary)}")

if __name__ == "__main__":
    main()