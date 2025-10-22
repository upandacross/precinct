#!/usr/bin/env python3
"""
DVA Scenario Tester
==================

This script tests specific Democratic Vote Added (DVA) scenarios to model
what would happen if we could increase Democratic turnout in specific precincts
by precise percentages.

Usage:
    python3 test_dva_scenarios.py [--dva-increase 2.0] [--target-precincts P1,P2,P3]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

class DVAScenarioTester:
    """Tests specific DVA scenarios for flippable race analysis."""
    
    def __init__(self):
        """Initialize with database connection."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
    
    def get_narrow_republican_wins(self, max_margin=10.0, min_votes=25):
        """Get Republican-won races that could be flipped with DVA."""
        query = '''
        WITH race_totals AS (
            SELECT 
                county, precinct, contest_name, election_date,
                SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
                SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes,
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
                ROUND(((rep_votes - dem_votes + 1) * 100.0 / (total_votes + 2)), 2) as dva_pct_needed
            FROM race_totals
            WHERE rep_votes > dem_votes  -- Republicans currently winning
        )
        SELECT *
        FROM margins 
        WHERE rep_margin_pct BETWEEN 0.1 AND :max_margin
          AND total_votes >= :min_votes
        ORDER BY rep_margin_pct ASC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'max_margin': max_margin,
                'min_votes': min_votes
            })
            
            races = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'rep_votes', 'total_votes', 
                'vote_diff', 'rep_margin_pct', 'dva_pct_needed'
            ])
            
            # Convert to numeric
            numeric_cols = ['dem_votes', 'rep_votes', 'total_votes', 
                          'vote_diff', 'rep_margin_pct', 'dva_pct_needed']
            for col in numeric_cols:
                races[col] = pd.to_numeric(races[col], errors='coerce')
        
        return races
    
    def simulate_dva_increase(self, races, dva_increase_pct, target_precincts=None):
        """Simulate the effect of a DVA increase on flippable races."""
        if len(races) == 0:
            return pd.DataFrame()
        
        # Filter to target precincts if specified
        if target_precincts:
            target_list = [p.strip() for p in target_precincts.split(',')]
            races = races[races['precinct'].isin(target_list)]
            print(f"🎯 Focusing on {len(target_list)} target precincts: {', '.join(target_list)}")
        
        # Calculate what happens with DVA increase
        simulation = races.copy()
        simulation['original_dem_votes'] = simulation['dem_votes']
        simulation['dva_votes_added'] = (simulation['total_votes'] * dva_increase_pct / 100).round().astype(int)
        simulation['new_dem_votes'] = simulation['dem_votes'] + simulation['dva_votes_added']
        simulation['new_total_votes'] = simulation['total_votes'] + simulation['dva_votes_added']
        simulation['new_dem_pct'] = (simulation['new_dem_votes'] / simulation['new_total_votes']) * 100
        simulation['new_vote_diff'] = simulation['rep_votes'] - simulation['new_dem_votes']
        simulation['flipped'] = simulation['new_vote_diff'] < 0
        
        # Calculate new margins for races that don't flip
        not_flipped = simulation[~simulation['flipped']].copy()
        if len(not_flipped) > 0:
            not_flipped['new_rep_margin_pct'] = (not_flipped['new_vote_diff'] / not_flipped['new_total_votes']) * 100
            simulation.loc[~simulation['flipped'], 'new_rep_margin_pct'] = not_flipped['new_rep_margin_pct']
        
        simulation.loc[simulation['flipped'], 'new_rep_margin_pct'] = 0.0  # Flipped races
        
        return simulation
    
    def analyze_dva_results(self, simulation, dva_increase_pct):
        """Analyze the results of DVA simulation."""
        if len(simulation) == 0:
            print("No races to analyze.")
            return
        
        total_races = len(simulation)
        flipped_races = simulation['flipped'].sum()
        total_dva_votes = simulation['dva_votes_added'].sum()
        
        print(f"\n📊 DVA SIMULATION RESULTS ({dva_increase_pct}% increase)")
        print("=" * 60)
        print(f"Total races analyzed: {total_races}")
        print(f"Races flipped: {flipped_races} ({(flipped_races/total_races)*100:.1f}%)")
        print(f"Total DVA votes added: {total_dva_votes:,}")
        print(f"Average DVA votes per race: {total_dva_votes/total_races:.1f}")
        print()
        
        if flipped_races > 0:
            flipped = simulation[simulation['flipped']]
            print(f"🎉 FLIPPED RACES ({flipped_races}):")
            for idx, race in flipped.iterrows():
                print(f"  📍 {race['county']} Precinct {race['precinct']}")
                print(f"     {race['contest_name']} ({race['election_date']})")
                print(f"     Original: DEM {race['original_dem_votes']} vs REP {race['rep_votes']} (margin: {race['rep_margin_pct']}%)")
                print(f"     With DVA: DEM {race['new_dem_votes']} vs REP {race['rep_votes']} (+{race['dva_votes_added']} votes)")
                print(f"     Result: DEM WIN by {abs(race['new_vote_diff'])} votes")
                print()
        
        # Analyze races that got closer but didn't flip
        closer = simulation[(~simulation['flipped']) & (simulation['new_rep_margin_pct'] < simulation['rep_margin_pct'])]
        if len(closer) > 0:
            print(f"🔥 RACES MADE MORE COMPETITIVE ({len(closer)}):")
            closest = closer.nsmallest(5, 'new_rep_margin_pct')
            for idx, race in closest.iterrows():
                improvement = race['rep_margin_pct'] - race['new_rep_margin_pct']
                print(f"  📍 {race['county']} Precinct {race['precinct']}")
                print(f"     {race['contest_name']}")
                print(f"     Margin: {race['rep_margin_pct']}% → {race['new_rep_margin_pct']:.2f}% (-{improvement:.2f}%)")
                print(f"     Still need {race['new_vote_diff']} more votes to flip")
                print()
    
    def find_optimal_precincts(self, races, target_flips=5):
        """Find precincts where DVA would be most effective."""
        if len(races) == 0:
            return pd.DataFrame()
        
        print(f"\n🎯 OPTIMAL PRECINCT TARGETING")
        print("=" * 50)
        
        # Calculate efficiency: races that could flip with minimal DVA
        races_copy = races.copy()
        races_copy['flip_efficiency'] = races_copy['vote_diff'] / races_copy['total_votes']
        races_copy['dva_cost_benefit'] = 1 / (races_copy['dva_pct_needed'] + 0.1)
        
        # Group by precinct to find precincts with multiple flippable races
        precinct_stats = races_copy.groupby(['county', 'precinct']).agg({
            'contest_name': 'count',
            'dva_pct_needed': 'mean',
            'vote_diff': 'sum',
            'total_votes': 'sum',
            'dva_cost_benefit': 'sum'
        }).round(2)
        
        precinct_stats.columns = ['races_count', 'avg_dva_needed', 'total_vote_gap', 'total_votes', 'efficiency_score']
        precinct_stats = precinct_stats.sort_values('efficiency_score', ascending=False)
        
        print(f"Top precincts for targeted DVA efforts:")
        for (county, precinct), stats in precinct_stats.head(10).iterrows():
            print(f"  {county} Precinct {precinct}:")
            print(f"    Flippable races: {stats['races_count']}")
            print(f"    Avg DVA needed: {stats['avg_dva_needed']:.2f}%")
            print(f"    Total vote gap: {stats['total_vote_gap']} votes")
            print(f"    Efficiency score: {stats['efficiency_score']:.2f}")
            print()
        
        return precinct_stats

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Test DVA scenarios for flippable races')
    parser.add_argument('--dva-increase', type=float, default=2.0,
                       help='DVA percentage increase to test (default: 2.0)')
    parser.add_argument('--max-margin', type=float, default=10.0,
                       help='Maximum Republican margin to consider (default: 10.0)')
    parser.add_argument('--min-votes', type=int, default=25,
                       help='Minimum total votes in race (default: 25)')
    parser.add_argument('--target-precincts', type=str,
                       help='Comma-separated list of precincts to focus on (e.g., "132,43,806")')
    parser.add_argument('--find-optimal', action='store_true',
                       help='Find optimal precincts for targeting')
    
    args = parser.parse_args()
    
    print("🧪 DVA SCENARIO TESTER")
    print("=" * 40)
    print(f"Testing {args.dva_increase}% Democratic vote increase")
    print()
    
    # Initialize tester
    tester = DVAScenarioTester()
    
    # Get flippable races
    print(f"🔍 Finding Republican-won races...")
    races = tester.get_narrow_republican_wins(args.max_margin, args.min_votes)
    
    if len(races) == 0:
        print("No flippable Republican-won races found with current criteria.")
        return
    
    print(f"Found {len(races)} Republican-won races with ≤{args.max_margin}% margin")
    
    # Find optimal precincts if requested
    if args.find_optimal:
        tester.find_optimal_precincts(races)
    
    # Simulate DVA increase
    simulation = tester.simulate_dva_increase(races, args.dva_increase, args.target_precincts)
    
    if len(simulation) == 0:
        print("No races match the targeting criteria.")
        return
    
    # Analyze results
    tester.analyze_dva_results(simulation, args.dva_increase)
    
    print(f"\n💡 Try different scenarios:")
    print(f"   Higher DVA: --dva-increase {args.dva_increase + 1.0}")
    print(f"   Tighter targeting: --max-margin {args.max_margin / 2}")
    print(f"   Find optimal precincts: --find-optimal")

if __name__ == "__main__":
    main()