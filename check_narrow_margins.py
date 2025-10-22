#!/usr/bin/env python3
"""
Narrow Margins Analysis
======================

This script analyzes races with very narrow margins to identify the most competitive
contests and potential flipping opportunities. It focuses on races where small vote
shifts could change outcomes.

Criteria for narrow margin analysis:
- Races decided by 5% or less
- Minimum 25 total votes (to ensure statistical relevance)
- Both Democratic and Republican candidates present
- Analysis of DVA (Dem Vote Added) percentages needed

Usage:
    python3 check_narrow_margins.py [--max-margin 5.0] [--min-votes 25] [--export-csv]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class NarrowMarginsAnalyzer:
    """Analyzes races with very narrow margins for strategic targeting."""
    
    def __init__(self, max_margin=5.0, min_votes=25):
        """Initialize with database connection and criteria."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
        self.max_margin = max_margin
        self.min_votes = min_votes
        
    def find_narrow_margin_races(self):
        """Find all races with narrow margins."""
        print(f"🔍 Analyzing narrow margin races...")
        print(f"   - Maximum margin: {self.max_margin}%")
        print(f"   - Minimum total votes: {self.min_votes}")
        
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
                ROUND(((ABS(dem_votes - rep_votes) + 1) * 100.0 / (total_votes + 2)), 2) as dva_pct_needed
            FROM race_totals
        ),
        narrow_races AS (
            SELECT *
            FROM margins 
            WHERE margin_pct BETWEEN 0.01 AND :max_margin  -- Very narrow races
              AND total_votes >= :min_votes  -- Minimum vote threshold
        )
        SELECT 
            county, precinct, contest_name, election_date,
            dem_votes, rep_votes, other_votes, total_votes, 
            winner, vote_diff, margin_pct, dva_pct_needed
        FROM narrow_races 
        ORDER BY margin_pct ASC, total_votes DESC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'max_margin': self.max_margin,
                'min_votes': self.min_votes
            })
            
            narrow_races = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'rep_votes', 'other_votes', 'total_votes', 
                'winner', 'vote_diff', 'margin_pct', 'dva_pct_needed'
            ])
            
            # Convert numeric columns to proper types
            numeric_cols = ['dem_votes', 'rep_votes', 'other_votes', 'total_votes', 
                          'vote_diff', 'margin_pct', 'dva_pct_needed']
            for col in numeric_cols:
                narrow_races[col] = pd.to_numeric(narrow_races[col], errors='coerce')
        
        print(f"✅ Found {len(narrow_races)} narrow margin races")
        return narrow_races
    
    def analyze_flippable_opportunities(self, narrow_races):
        """Analyze which narrow races represent the best flipping opportunities."""
        if len(narrow_races) == 0:
            return pd.DataFrame()
            
        print(f"\n🎯 Analyzing flippable opportunities...")
        
        # Focus on Republican-won races (potential Democratic targets)
        rep_wins = narrow_races[narrow_races['winner'] == 'REP'].copy()
        dem_wins = narrow_races[narrow_races['winner'] == 'DEM'].copy()
        
        print(f"   - Republican-won narrow races: {len(rep_wins)} (potential Democratic targets)")
        print(f"   - Democratic-won narrow races: {len(dem_wins)} (defensive priorities)")
        
        # Calculate strategic priority scores
        for df, party in [(rep_wins, 'REP'), (dem_wins, 'DEM')]:
            if len(df) > 0:
                # Priority score: inverse of margin × vote volume weight
                df['volume_weight'] = (df['total_votes'] / df['total_votes'].max())
                df['priority_score'] = (1 / (df['margin_pct'] + 0.1)) * df['volume_weight']
                
                # Create dynamic bins based on max_margin
                if self.max_margin <= 2.0:
                    bins = [0, 0.5, 1.0, self.max_margin]
                    labels = ['Ultra-Competitive', 'Highly Competitive', 'Competitive']
                else:
                    bins = [0, 0.5, 1.0, 2.0, self.max_margin]
                    labels = ['Ultra-Competitive', 'Highly Competitive', 'Competitive', 'Narrow']
                
                # Remove duplicate bin edges
                unique_bins = []
                for i, b in enumerate(bins):
                    if i == 0 or b != bins[i-1]:
                        unique_bins.append(b)
                
                if len(unique_bins) > 1:
                    df['strategic_category'] = pd.cut(
                        df['margin_pct'], 
                        bins=unique_bins, 
                        labels=labels[:len(unique_bins)-1]
                    )
                else:
                    df['strategic_category'] = 'Competitive'
        
        return rep_wins, dem_wins
    
    def generate_geographical_analysis(self, narrow_races):
        """Analyze narrow races by geographical distribution."""
        if len(narrow_races) == 0:
            return
            
        print(f"\n🗺️  GEOGRAPHICAL ANALYSIS")
        print("=" * 50)
        
        # County-level analysis
        county_stats = narrow_races.groupby('county').agg({
            'contest_name': 'count',
            'margin_pct': ['mean', 'min'],
            'total_votes': 'sum',
            'dva_pct_needed': 'mean'
        }).round(2)
        
        county_stats.columns = ['total_races', 'avg_margin', 'tightest_margin', 'total_votes', 'avg_dva_needed']
        county_stats = county_stats.sort_values('total_races', ascending=False)
        
        print(f"Counties with most narrow races:")
        for county, stats in county_stats.head(10).iterrows():
            print(f"  {county}: {stats['total_races']} races (avg: {stats['avg_margin']}%, tightest: {stats['tightest_margin']}%)")
        
        # Precinct concentration analysis
        print(f"\nPrecincts with multiple narrow races:")
        precinct_counts = narrow_races.groupby(['county', 'precinct']).size().sort_values(ascending=False)
        for (county, precinct), count in precinct_counts.head(10).items():
            if count > 1:
                print(f"  {county} Precinct {precinct}: {count} narrow races")
    
    def generate_temporal_analysis(self, narrow_races):
        """Analyze narrow races by election timing."""
        if len(narrow_races) == 0:
            return
            
        print(f"\n📅 TEMPORAL ANALYSIS")
        print("=" * 50)
        
        # Convert election_date to datetime and extract year
        narrow_races['year'] = pd.to_datetime(narrow_races['election_date']).dt.year
        narrow_races['month'] = pd.to_datetime(narrow_races['election_date']).dt.month
        
        # Year analysis
        year_stats = narrow_races.groupby('year').agg({
            'contest_name': 'count',
            'margin_pct': 'mean',
            'total_votes': 'sum'
        }).round(2)
        year_stats.columns = ['races', 'avg_margin', 'total_votes']
        
        print(f"Narrow races by election year:")
        for year, stats in year_stats.iterrows():
            print(f"  {year}: {stats['races']} races (avg margin: {stats['avg_margin']}%)")
        
        # Election type analysis (inferred from month)
        narrow_races['election_type'] = narrow_races['month'].map({
            11: 'General', 5: 'Primary', 3: 'Municipal/Special'
        }).fillna('Other')
        
        type_stats = narrow_races.groupby('election_type').size()
        print(f"\nNarrow races by election type:")
        for election_type, count in type_stats.items():
            print(f"  {election_type}: {count} races")
    
    def identify_super_close_races(self, narrow_races, ultra_threshold=0.5):
        """Identify extremely close races requiring minimal vote shifts."""
        if len(narrow_races) == 0:
            return pd.DataFrame()
            
        print(f"\n🔥 ULTRA-COMPETITIVE RACES (≤{ultra_threshold}% margin)")
        print("=" * 60)
        
        ultra_close = narrow_races[narrow_races['margin_pct'] <= ultra_threshold].copy()
        
        if len(ultra_close) == 0:
            print(f"No races found with margin ≤{ultra_threshold}%")
            return ultra_close
        
        print(f"Found {len(ultra_close)} ultra-competitive races:")
        print()
        
        for idx, race in ultra_close.iterrows():
            print(f"📍 {race['county']} Precinct {race['precinct']}")
            print(f"   Contest: {race['contest_name']}")
            print(f"   Election: {race['election_date']}")
            print(f"   Votes: DEM {race['dem_votes']} vs {race['winner']} {race['rep_votes']}")
            print(f"   Margin: {race['margin_pct']}% ({race['vote_diff']} votes)")
            print(f"   Winner: {race['winner']}")
            if race['winner'] == 'REP':
                print(f"   🎯 DVA needed: {race['dva_pct_needed']}%")
            else:
                print(f"   🛡️  Defensive priority for Democrats")
            print()
        
        return ultra_close
    
    def export_analysis_to_csv(self, narrow_races, filename=None):
        """Export narrow margin analysis to CSV."""
        if len(narrow_races) == 0:
            print("No data to export.")
            return
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"narrow_margins_analysis_{timestamp}.csv"
        
        # Add analysis columns
        export_data = narrow_races.copy()
        export_data['flippable_target'] = export_data['winner'] == 'REP'
        export_data['defensive_priority'] = export_data['winner'] == 'DEM'
        export_data['votes_needed_to_flip'] = export_data['vote_diff'] + 1
        
        export_data.to_csv(filename, index=False)
        print(f"💾 Exported analysis to: {filename}")
        return filename
    
    def generate_summary_report(self, narrow_races, rep_wins=None, dem_wins=None):
        """Generate comprehensive summary report."""
        print(f"\n📊 NARROW MARGINS SUMMARY REPORT")
        print("=" * 60)
        
        if len(narrow_races) == 0:
            print("No narrow margin races found with current criteria.")
            return
        
        # Overall statistics
        print(f"Total narrow margin races: {len(narrow_races)}")
        print(f"Average margin: {narrow_races['margin_pct'].mean():.2f}%")
        print(f"Tightest margin: {narrow_races['margin_pct'].min():.2f}%")
        print(f"Average DVA % needed: {narrow_races['dva_pct_needed'].mean():.2f}%")
        print(f"Total votes in narrow races: {narrow_races['total_votes'].sum():,}")
        print()
        
        # Winner breakdown
        winner_counts = narrow_races['winner'].value_counts()
        print(f"Results breakdown:")
        for winner, count in winner_counts.items():
            pct = (count / len(narrow_races)) * 100
            print(f"  {winner} wins: {count} ({pct:.1f}%)")
        print()
        
        # Strategic analysis
        if rep_wins is not None and len(rep_wins) > 0:
            print(f"🎯 REPUBLICAN-WON TARGETS ({len(rep_wins)} races):")
            print(f"   Average margin: {rep_wins['margin_pct'].mean():.2f}%")
            print(f"   Easiest target: {rep_wins['margin_pct'].min():.2f}% margin")
            print(f"   Average DVA needed: {rep_wins['dva_pct_needed'].mean():.2f}%")
        
        if dem_wins is not None and len(dem_wins) > 0:
            print(f"🛡️  DEMOCRATIC DEFENSIVE PRIORITIES ({len(dem_wins)} races):")
            print(f"   Average margin: {dem_wins['margin_pct'].mean():.2f}%")
            print(f"   Most vulnerable: {dem_wins['margin_pct'].min():.2f}% margin")
        
        # Contest type analysis
        print(f"\nMost competitive contest types:")
        contest_stats = narrow_races.groupby('contest_name').size().sort_values(ascending=False)
        for contest, count in contest_stats.head(10).items():
            print(f"  {contest}: {count} narrow races")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Analyze races with very narrow margins')
    parser.add_argument('--max-margin', type=float, default=5.0,
                       help='Maximum margin percentage (default: 5.0)')
    parser.add_argument('--min-votes', type=int, default=25,
                       help='Minimum total votes in race (default: 25)')
    parser.add_argument('--ultra-threshold', type=float, default=0.5,
                       help='Threshold for ultra-competitive races (default: 0.5)')
    parser.add_argument('--export-csv', action='store_true',
                       help='Export results to CSV file')
    parser.add_argument('--filename', type=str,
                       help='Custom filename for CSV export')
    
    args = parser.parse_args()
    
    print("🔍 NARROW MARGINS ANALYZER")
    print("=" * 40)
    print("Analyzing the most competitive races for strategic targeting")
    print()
    
    # Initialize analyzer
    analyzer = NarrowMarginsAnalyzer(max_margin=args.max_margin, min_votes=args.min_votes)
    
    # Find narrow margin races
    narrow_races = analyzer.find_narrow_margin_races()
    
    if len(narrow_races) == 0:
        print("No narrow margin races found with current criteria.")
        print(f"Consider adjusting --max-margin (currently {args.max_margin}%) or --min-votes (currently {args.min_votes})")
        return
    
    # Analyze flippable opportunities
    rep_wins, dem_wins = analyzer.analyze_flippable_opportunities(narrow_races)
    
    # Identify ultra-competitive races
    ultra_close = analyzer.identify_super_close_races(narrow_races, args.ultra_threshold)
    
    # Geographical and temporal analysis
    analyzer.generate_geographical_analysis(narrow_races)
    analyzer.generate_temporal_analysis(narrow_races)
    
    # Generate summary report
    analyzer.generate_summary_report(narrow_races, rep_wins, dem_wins)
    
    # Export to CSV if requested
    if args.export_csv:
        analyzer.export_analysis_to_csv(narrow_races, args.filename)
    
    print(f"\n✅ Analysis complete!")
    print(f"   Narrow races analyzed: {len(narrow_races)}")
    print(f"   Republican targets: {len(rep_wins) if rep_wins is not None else 0}")
    print(f"   Democratic defensive: {len(dem_wins) if dem_wins is not None else 0}")
    print(f"   Ultra-competitive: {len(ultra_close)}")

if __name__ == "__main__":
    main()
