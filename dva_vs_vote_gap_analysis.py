#!/usr/bin/env python3
"""
DVA vs Vote Gap Metric Comparison Analysis
==========================================

This script compares DVA percentage needed vs raw vote gap as metrics for 
determining the most effective pathway to flip Republican-won races.

Key Question: Is DVA percentage or vote gap the better metric for prioritizing flippable races?

Usage:
    python3 dva_vs_vote_gap_analysis.py
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

class DVAVsVoteGapAnalysis:
    """Compare DVA vs vote gap metrics for flippable race assessment."""
    
    def __init__(self):
        """Initialize with database connection."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
    
    def get_flippable_races_with_both_metrics(self, max_margin=10.0, min_votes=25):
        """Get flippable races with both DVA and vote gap calculations."""
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
        governor_turnout AS (
            SELECT 
                county, precinct, election_date,
                SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as gov_dem_votes
            FROM candidate_vote_results 
            WHERE choice_party = 'DEM' 
              AND LOWER(contest_name) LIKE '%governor%'
            GROUP BY county, precinct, election_date
        ),
        comprehensive_metrics AS (
            SELECT 
                rt.*,
                gt.gov_dem_votes,
                ABS(rt.dem_votes - rt.rep_votes) as vote_diff,
                (rt.rep_votes + 1) - rt.dem_votes as vote_gap,
                ROUND((ABS(rt.dem_votes - rt.rep_votes) * 100.0 / rt.total_votes), 2) as margin_pct,
                COALESCE(gt.gov_dem_votes - rt.dem_votes, 0) as dem_absenteeism,
                CASE 
                    WHEN gt.gov_dem_votes IS NULL OR gt.gov_dem_votes <= rt.dem_votes THEN 999.9
                    ELSE ROUND(((rt.rep_votes + 1 - rt.dem_votes) * 100.0 / (gt.gov_dem_votes - rt.dem_votes)), 1)
                END as dva_pct_needed
            FROM race_totals rt
            LEFT JOIN governor_turnout gt ON rt.county = gt.county 
                                          AND rt.precinct = gt.precinct 
                                          AND rt.election_date = gt.election_date
            WHERE rt.rep_votes > rt.dem_votes  -- Republican wins only
        )
        SELECT *
        FROM comprehensive_metrics 
        WHERE margin_pct BETWEEN 0.01 AND :max_margin
          AND total_votes >= :min_votes
        ORDER BY vote_gap ASC, dva_pct_needed ASC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'max_margin': max_margin,
                'min_votes': min_votes
            })
            
            races = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'rep_votes', 'total_votes', 'gov_dem_votes',
                'vote_diff', 'vote_gap', 'margin_pct', 'dem_absenteeism', 'dva_pct_needed'
            ])
            
            # Convert to numeric
            numeric_cols = ['dem_votes', 'rep_votes', 'total_votes', 'gov_dem_votes',
                          'vote_diff', 'vote_gap', 'margin_pct', 'dem_absenteeism', 'dva_pct_needed']
            for col in numeric_cols:
                races[col] = pd.to_numeric(races[col], errors='coerce')
        
        return races
    
    def classify_by_both_metrics(self, races):
        """Classify races using both DVA and vote gap thresholds."""
        
        # Vote Gap Classifications
        def classify_vote_gap(gap):
            if gap <= 25:
                return 'slam_dunk'
            elif gap <= 100:
                return 'highly_flippable'
            elif gap <= 300:
                return 'competitive'
            else:
                return 'stretch'
        
        # DVA Classifications
        def classify_dva(dva_pct):
            if dva_pct <= 15:
                return 'slam_dunk'
            elif dva_pct <= 35:
                return 'highly_flippable'
            elif dva_pct <= 60:
                return 'competitive'
            else:
                return 'stretch'
        
        # Best Pathway Logic (from our previous analysis)
        def determine_best_pathway(row):
            vote_gap = row['vote_gap']
            dva_pct = row['dva_pct_needed']
            dem_abs = row['dem_absenteeism']
            
            if vote_gap <= 25 or dva_pct <= 15:
                return "traditional" if vote_gap <= 25 else "dva"
            elif vote_gap <= 100 or dva_pct <= 35:
                return "traditional" if vote_gap <= 100 else "dva"
            elif vote_gap <= 300 or dva_pct <= 60:
                return "traditional" if vote_gap <= 300 else "dva"
            else:
                return "traditional" if vote_gap < dva_pct else "dva"
        
        races['vote_gap_tier'] = races['vote_gap'].apply(classify_vote_gap)
        races['dva_tier'] = races['dva_pct_needed'].apply(classify_dva)
        races['best_pathway'] = races.apply(determine_best_pathway, axis=1)
        
        return races
    
    def create_metric_comparison_visualization(self, races):
        """Create comprehensive comparison visualization."""
        
        # Create subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('DVA vs Vote Gap Scatter', 'Pathway Distribution', 
                          'Metric Agreement Analysis', 'Efficiency Comparison'),
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 1. Scatter plot: DVA vs Vote Gap
        fig.add_trace(go.Scatter(
            x=races['vote_gap'],
            y=races['dva_pct_needed'],
            mode='markers',
            marker=dict(
                color=races['dva_pct_needed'],
                colorscale='RdYlGn_r',
                size=6,
                colorbar=dict(title="DVA %")
            ),
            text=[
                f"{row['county']} P{row['precinct']}<br>"
                f"Vote Gap: {row['vote_gap']} votes<br>"
                f"DVA Needed: {row['dva_pct_needed']:.1f}%<br>"
                f"Best Path: {row['best_pathway']}"
                for _, row in races.iterrows()
            ],
            hovertemplate='%{text}<extra></extra>',
            name='Races'
        ), row=1, col=1)
        
        # Add threshold lines
        fig.add_hline(y=15, line_dash="dash", line_color="green", row=1, col=1)
        fig.add_hline(y=35, line_dash="dash", line_color="orange", row=1, col=1)
        fig.add_vline(x=25, line_dash="dash", line_color="green", row=1, col=1)
        fig.add_vline(x=100, line_dash="dash", line_color="orange", row=1, col=1)
        
        # 2. Best pathway distribution
        pathway_counts = races['best_pathway'].value_counts()
        fig.add_trace(go.Bar(
            x=pathway_counts.index,
            y=pathway_counts.values,
            marker_color=['lightblue', 'lightcoral'],
            name='Pathway Count'
        ), row=1, col=2)
        
        # 3. Metric agreement analysis
        races['metrics_agree'] = races['vote_gap_tier'] == races['dva_tier']
        agreement_counts = races.groupby(['vote_gap_tier', 'dva_tier']).size().reset_index(name='count')
        
        # Create agreement matrix visualization
        tiers = ['slam_dunk', 'highly_flippable', 'competitive', 'stretch']
        agreement_matrix = []
        for vg_tier in tiers:
            row = []
            for dva_tier in tiers:
                count = agreement_counts[
                    (agreement_counts['vote_gap_tier'] == vg_tier) & 
                    (agreement_counts['dva_tier'] == dva_tier)
                ]['count'].sum()
                row.append(count)
            agreement_matrix.append(row)
        
        fig.add_trace(go.Heatmap(
            z=agreement_matrix,
            x=tiers,
            y=tiers,
            colorscale='Blues',
            name='Agreement Matrix'
        ), row=2, col=1)
        
        # 4. Efficiency comparison: Resources needed vs success probability
        efficiency_data = races.groupby('best_pathway').agg({
            'vote_gap': 'mean',
            'dva_pct_needed': 'mean',
            'dem_absenteeism': 'mean',
            'contest_name': 'count'
        }).reset_index()
        
        fig.add_trace(go.Scatter(
            x=efficiency_data['vote_gap'],
            y=efficiency_data['dva_pct_needed'],
            mode='markers+text',
            marker=dict(size=efficiency_data['contest_name']*2, color=['red', 'blue']),
            text=efficiency_data['best_pathway'],
            textposition="middle center",
            name='Pathway Efficiency'
        ), row=2, col=2)
        
        # Update layout
        fig.update_layout(
            title='DVA vs Vote Gap: Comprehensive Metric Comparison',
            height=800,
            showlegend=False
        )
        
        # Update axis labels
        fig.update_xaxes(title_text="Vote Gap", row=1, col=1)
        fig.update_yaxes(title_text="DVA % Needed", row=1, col=1)
        fig.update_xaxes(title_text="Best Pathway", row=1, col=2)
        fig.update_yaxes(title_text="Number of Races", row=1, col=2)
        fig.update_xaxes(title_text="DVA Tier", row=2, col=1)
        fig.update_yaxes(title_text="Vote Gap Tier", row=2, col=1)
        fig.update_xaxes(title_text="Avg Vote Gap", row=2, col=2)
        fig.update_yaxes(title_text="Avg DVA % Needed", row=2, col=2)
        
        return fig
    
    def analyze_metric_effectiveness(self, races):
        """Analyze which metric is more effective for identifying flippable races."""
        
        print("\n🔍 DVA vs VOTE GAP METRIC COMPARISON ANALYSIS")
        print("=" * 70)
        print(f"Total races analyzed: {len(races)}")
        print()
        
        # Agreement analysis
        races['metrics_agree'] = races['vote_gap_tier'] == races['dva_tier']
        agreement_rate = races['metrics_agree'].mean() * 100
        
        print(f"📊 METRIC AGREEMENT ANALYSIS:")
        print(f"   Metrics agree on classification: {agreement_rate:.1f}% of races")
        print(f"   Metrics disagree: {100-agreement_rate:.1f}% of races")
        print()
        
        # Pathway analysis
        pathway_dist = races['best_pathway'].value_counts()
        print(f"🎯 BEST PATHWAY DISTRIBUTION:")
        for pathway, count in pathway_dist.items():
            pct = (count / len(races)) * 100
            print(f"   {pathway.upper():12s}: {count:3d} races ({pct:4.1f}%)")
        print()
        
        # Tier comparison
        print(f"📈 TIER CLASSIFICATION COMPARISON:")
        tier_comparison = pd.crosstab(races['vote_gap_tier'], races['dva_tier'], 
                                    margins=True, margins_name="Total")
        print(tier_comparison)
        print()
        
        # Effectiveness analysis
        dva_races = races[races['best_pathway'] == 'dva']
        traditional_races = races[races['best_pathway'] == 'traditional']
        
        print(f"⚡ PATHWAY EFFECTIVENESS ANALYSIS:")
        print()
        print(f"DVA PATHWAY ({len(dva_races)} races):")
        if len(dva_races) > 0:
            print(f"   Average DVA needed: {dva_races['dva_pct_needed'].mean():.1f}%")
            print(f"   Average vote gap: {dva_races['vote_gap'].mean():.1f} votes")
            print(f"   Average absenteeism: {dva_races['dem_absenteeism'].mean():.0f} voters")
            print(f"   Resource efficiency: {(dva_races['vote_gap'].sum() / dva_races['dem_absenteeism'].sum() * 100):.1f}% activation needed")
        print()
        
        print(f"TRADITIONAL PATHWAY ({len(traditional_races)} races):")
        if len(traditional_races) > 0:
            print(f"   Average vote gap: {traditional_races['vote_gap'].mean():.1f} votes")
            print(f"   Average DVA needed: {traditional_races['dva_pct_needed'].mean():.1f}%")
            print(f"   Total new votes needed: {traditional_races['vote_gap'].sum():,}")
        print()
        
        # Recommendation
        print(f"💡 METRIC RECOMMENDATION:")
        
        # Calculate which metric identifies more "easy wins"
        dva_easy_wins = len(races[races['dva_pct_needed'] <= 25])
        gap_easy_wins = len(races[races['vote_gap'] <= 100])
        
        print(f"   DVA identifies {dva_easy_wins} races needing ≤25% activation")
        print(f"   Vote Gap identifies {gap_easy_wins} races needing ≤100 votes")
        print()
        
        if dva_easy_wins > gap_easy_wins:
            print("   🎯 RECOMMENDATION: DVA is superior metric")
            print("      - Identifies more achievable targets")
            print("      - Leverages existing Democratic voter pool")
            print("      - More resource-efficient approach")
        elif gap_easy_wins > dva_easy_wins:
            print("   🎯 RECOMMENDATION: Vote Gap is superior metric") 
            print("      - Identifies more concrete numerical targets")
            print("      - Easier to understand and campaign around")
            print("      - More traditional approach")
        else:
            print("   🎯 RECOMMENDATION: Use Combined Approach")
            print("      - Both metrics identify similar opportunities")
            print("      - Use best pathway logic for each race")
            print("      - Leverage strengths of both approaches")
        
        return races
    
    def generate_strategic_recommendations(self, races):
        """Generate strategic recommendations based on metric analysis."""
        
        print(f"\n🚀 STRATEGIC RECOMMENDATIONS")
        print("=" * 50)
        
        # Top targets by each metric
        top_dva = races.nsmallest(10, 'dva_pct_needed')
        top_gap = races.nsmallest(10, 'vote_gap')
        
        print(f"🏆 TOP 10 BY DVA METRIC:")
        for i, (_, race) in enumerate(top_dva.iterrows(), 1):
            print(f"   {i:2d}. {race['county']} P{race['precinct']} - "
                  f"{race['dva_pct_needed']:.1f}% DVA ({race['vote_gap']} vote gap)")
        print()
        
        print(f"🏆 TOP 10 BY VOTE GAP METRIC:")
        for i, (_, race) in enumerate(top_gap.iterrows(), 1):
            print(f"   {i:2d}. {race['county']} P{race['precinct']} - "
                  f"{race['vote_gap']} votes ({race['dva_pct_needed']:.1f}% DVA)")
        print()
        
        # Resource allocation recommendations
        dva_pathway_races = races[races['best_pathway'] == 'dva']
        trad_pathway_races = races[races['best_pathway'] == 'traditional']
        
        if len(dva_pathway_races) > 0:
            dva_total_activation = (dva_pathway_races['vote_gap'].sum() / 
                                  dva_pathway_races['dem_absenteeism'].sum() * 100)
            print(f"📊 DVA PATHWAY RESOURCE REQUIREMENTS:")
            print(f"   Races: {len(dva_pathway_races)}")
            print(f"   Total activation needed: {dva_total_activation:.1f}% of absent Dems")
            print(f"   Available voters: {dva_pathway_races['dem_absenteeism'].sum():,}")
            print()
        
        if len(trad_pathway_races) > 0:
            print(f"📊 TRADITIONAL PATHWAY RESOURCE REQUIREMENTS:")
            print(f"   Races: {len(trad_pathway_races)}")
            print(f"   Total new votes needed: {trad_pathway_races['vote_gap'].sum():,}")
            print(f"   Average per race: {trad_pathway_races['vote_gap'].mean():.1f} votes")
            print()
    
    def run_analysis(self, max_margin=10.0, min_votes=25, save_html=True):
        """Run complete DVA vs vote gap comparison analysis."""
        
        print("🔍 LOADING FLIPPABLE RACES DATA...")
        races = self.get_flippable_races_with_both_metrics(max_margin, min_votes)
        
        if len(races) == 0:
            print("❌ No flippable races found with current criteria.")
            return
        
        print(f"✅ Found {len(races)} flippable races")
        
        # Classify by both metrics
        races = self.classify_by_both_metrics(races)
        
        # Create visualization
        print("📊 CREATING COMPARISON VISUALIZATION...")
        comparison_fig = self.create_metric_comparison_visualization(races)
        
        if save_html:
            comparison_fig.write_html("dva_vs_vote_gap_comparison.html")
            print("💾 Saved: dva_vs_vote_gap_comparison.html")
        
        # Run analysis
        races = self.analyze_metric_effectiveness(races)
        self.generate_strategic_recommendations(races)
        
        # Show visualization
        comparison_fig.show()
        
        return races

def main():
    """Main execution function."""
    print("🔬 DVA vs VOTE GAP METRIC COMPARISON")
    print("=" * 50)
    print("Analyzing which metric is more effective for identifying flippable races")
    print()
    
    analyzer = DVAVsVoteGapAnalysis()
    results = analyzer.run_analysis()
    
    if results is not None:
        print(f"\n✅ Analysis complete! Analyzed {len(results)} races.")
        print("📊 Comprehensive metric comparison visualization generated.")

if __name__ == "__main__":
    main()