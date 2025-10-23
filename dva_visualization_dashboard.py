#!/usr/bin/env python3
"""
DVA Visualization Dashboard
===========================

Creates comprehensive visualizations for flippable race analysis with:
- DVA percentage needed calculations
- Strategic tier classifications
- Interactive charts showing flippable, competitive, and stretch targets
- Resource allocation recommendations

Usage:
    python3 dva_visualization_dashboard.py [--max-margin 10.0] [--min-votes 25]
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
from precinct_utils import normalize_precinct_id, normalize_precinct_join

class DVAVisualizationDashboard:
    """Creates comprehensive DVA analysis visualizations."""
    
    def __init__(self):
        """Initialize with database connection."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
        
        # Strategic tier definitions
        self.tiers = {
            'highly_flippable': {'dva_max': 25, 'color': '#00ff00', 'label': 'Highly Flippable (≤25% DVA)'},
            'flippable': {'dva_max': 50, 'color': '#ffff00', 'label': 'Flippable (25-50% DVA)'},
            'competitive': {'dva_max': 75, 'color': '#ffa500', 'label': 'Competitive (50-75% DVA)'},
            'stretch': {'dva_max': 100, 'color': '#ff4500', 'label': 'Stretch Target (75-100% DVA)'},
            'difficult': {'dva_max': float('inf'), 'color': '#ff0000', 'label': 'Difficult (>100% DVA)'}
        }
    
    def get_flippable_races_with_dva(self, max_margin=10.0, min_votes=25):
        """Get all competitive races with DVA calculations."""
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
        margins AS (
            SELECT 
                rt.*,
                gt.gov_dem_votes,
                CASE 
                    WHEN rt.dem_votes > rt.rep_votes THEN 'DEM'
                    WHEN rt.rep_votes > rt.dem_votes THEN 'REP'
                    ELSE 'TIE'
                END as winner,
                ABS(rt.dem_votes - rt.rep_votes) as vote_diff,
                ROUND((ABS(rt.dem_votes - rt.rep_votes) * 100.0 / rt.total_votes), 2) as margin_pct,
                ROUND(((rt.dem_votes - rt.rep_votes) * 100.0 / rt.total_votes), 2) as dem_margin_pct,
                -- DVA calculation: votes needed to win divided by available absentee Dems
                CASE 
                    WHEN gt.gov_dem_votes IS NULL OR gt.gov_dem_votes <= rt.dem_votes THEN 999.9
                    ELSE ROUND(((rt.rep_votes + 1 - rt.dem_votes) * 100.0 / (gt.gov_dem_votes - rt.dem_votes)), 1)
                END as dva_pct_needed,
                COALESCE(gt.gov_dem_votes - rt.dem_votes, 0) as dem_absenteeism
            FROM race_totals rt
            LEFT JOIN governor_turnout gt ON rt.county = gt.county 
                                          AND rt.precinct = gt.precinct 
                                          AND rt.election_date = gt.election_date
        )
        SELECT *
        FROM margins 
        WHERE margin_pct BETWEEN 0.01 AND :max_margin
          AND total_votes >= :min_votes
          AND winner = 'REP'  -- Focus on Republican wins we could flip
        ORDER BY dva_pct_needed ASC, margin_pct ASC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'max_margin': max_margin,
                'min_votes': min_votes
            })
            
            races = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'rep_votes', 'total_votes', 'gov_dem_votes',
                'winner', 'vote_diff', 'margin_pct', 'dem_margin_pct',
                'dva_pct_needed', 'dem_absenteeism'
            ])
            
            # Convert to numeric
            numeric_cols = ['dem_votes', 'rep_votes', 'total_votes', 'gov_dem_votes',
                          'vote_diff', 'margin_pct', 'dem_margin_pct', 'dva_pct_needed', 'dem_absenteeism']
            for col in numeric_cols:
                races[col] = pd.to_numeric(races[col], errors='coerce')
        
        return races
    
    def classify_strategic_tiers(self, races):
        """Add strategic tier classifications to races."""
        def get_tier(dva_pct):
            if dva_pct <= 25:
                return 'highly_flippable'
            elif dva_pct <= 50:
                return 'flippable'
            elif dva_pct <= 75:
                return 'competitive'
            elif dva_pct <= 100:
                return 'stretch'
            else:
                return 'difficult'
        
        races['strategic_tier'] = races['dva_pct_needed'].apply(get_tier)
        races['tier_color'] = races['strategic_tier'].map(lambda x: self.tiers[x]['color'])
        races['tier_label'] = races['strategic_tier'].map(lambda x: self.tiers[x]['label'])
        
        return races
    
    def create_dva_scatter_plot(self, races):
        """Create scatter plot of DVA needed vs margin percentage."""
        fig = go.Figure()
        
        # Add traces for each tier
        for tier_name, tier_config in self.tiers.items():
            tier_races = races[races['strategic_tier'] == tier_name]
            if len(tier_races) > 0:
                fig.add_trace(go.Scatter(
                    x=tier_races['margin_pct'],
                    y=tier_races['dva_pct_needed'],
                    mode='markers',
                    marker=dict(
                        color=tier_config['color'],
                        size=8,
                        line=dict(width=1, color='black')
                    ),
                    name=tier_config['label'],
                    text=[
                        f"{row['county']} P{row['precinct']}<br>"
                        f"{row['contest_name'][:30]}...<br>"
                        f"Margin: {row['margin_pct']:.1f}%<br>"
                        f"DVA Needed: {row['dva_pct_needed']:.1f}%<br>"
                        f"Vote Gap: {row['vote_diff']} votes<br>"
                        f"Dem Absenteeism: {row['dem_absenteeism']}"
                        for _, row in tier_races.iterrows()
                    ],
                    hovertemplate='%{text}<extra></extra>'
                ))
        
        # Add strategic zone lines
        fig.add_hline(y=25, line_dash="dash", line_color="green", 
                     annotation_text="Highly Flippable Threshold")
        fig.add_hline(y=50, line_dash="dash", line_color="gold", 
                     annotation_text="Flippable Threshold")
        fig.add_hline(y=75, line_dash="dash", line_color="orange", 
                     annotation_text="Competitive Threshold")
        fig.add_hline(y=100, line_dash="dash", line_color="red", 
                     annotation_text="Stretch Target Threshold")
        
        fig.update_layout(
            title='DVA Strategic Analysis: Flippable Republican-Won Races',
            xaxis_title='Republican Margin (%)',
            yaxis_title='DVA Percentage Needed to Flip',
            height=600,
            width=1000,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig
    
    def create_tier_summary_chart(self, races):
        """Create summary chart of races by strategic tier."""
        tier_summary = races.groupby('strategic_tier').agg({
            'contest_name': 'count',
            'vote_diff': 'sum',
            'dem_absenteeism': 'sum',
            'dva_pct_needed': 'mean'
        }).round(1)
        
        tier_summary.columns = ['race_count', 'total_vote_gap', 'total_absenteeism', 'avg_dva_needed']
        tier_summary = tier_summary.reset_index()
        
        # Order by strategic priority
        tier_order = ['highly_flippable', 'flippable', 'competitive', 'stretch', 'difficult']
        tier_summary['tier_order'] = tier_summary['strategic_tier'].map(
            {tier: i for i, tier in enumerate(tier_order)}
        )
        tier_summary = tier_summary.sort_values('tier_order')
        
        # Create subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Race Count by Tier', 'Total Vote Gap', 
                          'Available Absenteeism', 'Average DVA Needed'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        colors = [self.tiers[tier]['color'] for tier in tier_summary['strategic_tier']]
        labels = [self.tiers[tier]['label'] for tier in tier_summary['strategic_tier']]
        
        # Race count
        fig.add_trace(go.Bar(
            x=labels, y=tier_summary['race_count'],
            marker_color=colors, name='Race Count'
        ), row=1, col=1)
        
        # Total vote gap
        fig.add_trace(go.Bar(
            x=labels, y=tier_summary['total_vote_gap'],
            marker_color=colors, name='Vote Gap'
        ), row=1, col=2)
        
        # Available absenteeism
        fig.add_trace(go.Bar(
            x=labels, y=tier_summary['total_absenteeism'],
            marker_color=colors, name='Absenteeism'
        ), row=2, col=1)
        
        # Average DVA needed
        fig.add_trace(go.Bar(
            x=labels, y=tier_summary['avg_dva_needed'],
            marker_color=colors, name='Avg DVA'
        ), row=2, col=2)
        
        fig.update_layout(
            title='Strategic Tier Analysis Summary',
            height=800,
            showlegend=False,
            template='plotly_white'
        )
        
        # Rotate x-axis labels
        fig.update_xaxes(tickangle=45)
        
        return fig, tier_summary
    
    def create_county_analysis(self, races):
        """Create county-level analysis visualization."""
        county_summary = races.groupby('county').agg({
            'contest_name': 'count',
            'vote_diff': 'sum',
            'dem_absenteeism': 'sum',
            'dva_pct_needed': 'mean'
        }).round(1)
        
        county_summary.columns = ['race_count', 'total_vote_gap', 'total_absenteeism', 'avg_dva_needed']
        county_summary = county_summary.reset_index()
        county_summary = county_summary.sort_values('race_count', ascending=False)
        
        # Get top 15 counties
        top_counties = county_summary.head(15)
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Flippable Races by County', 'DVA Efficiency by County'),
            specs=[[{"type": "bar"}], [{"type": "scatter"}]]
        )
        
        # Race count by county
        fig.add_trace(go.Bar(
            x=top_counties['county'],
            y=top_counties['race_count'],
            marker_color='lightblue',
            name='Race Count'
        ), row=1, col=1)
        
        # DVA efficiency (lower is better)
        fig.add_trace(go.Scatter(
            x=top_counties['county'],
            y=top_counties['avg_dva_needed'],
            mode='markers+lines',
            marker=dict(size=top_counties['race_count']*2, color='red'),
            name='Avg DVA Needed (%)'
        ), row=2, col=1)
        
        fig.update_layout(
            title='County-Level Strategic Analysis',
            height=800,
            template='plotly_white'
        )
        
        fig.update_xaxes(tickangle=45)
        
        return fig, county_summary
    
    def print_strategic_recommendations(self, races, tier_summary):
        """Print strategic recommendations based on analysis."""
        total_races = len(races)
        
        print("\n🎯 STRATEGIC RECOMMENDATIONS")
        print("=" * 60)
        print(f"Total flippable Republican-won races analyzed: {total_races}")
        print()
        
        for _, tier in tier_summary.iterrows():
            tier_name = tier['strategic_tier']
            config = self.tiers[tier_name]
            
            print(f"📊 {config['label']}")
            print(f"   Races: {int(tier['race_count'])} ({tier['race_count']/total_races*100:.1f}%)")
            print(f"   Total vote gap: {int(tier['total_vote_gap']):,} votes")
            print(f"   Available absenteeism: {int(tier['total_absenteeism']):,} voters")
            print(f"   Average DVA needed: {tier['avg_dva_needed']:.1f}%")
            
            if tier_name == 'highly_flippable':
                print("   🎯 PRIORITY TARGET: Focus heavy resources here")
            elif tier_name == 'flippable':
                print("   💪 STRONG OPPORTUNITY: Allocate significant resources")
            elif tier_name == 'competitive':
                print("   ⚡ MODERATE OPPORTUNITY: Secondary priority")
            elif tier_name == 'stretch':
                print("   🎲 STRETCH GOAL: Resource-permitting targets")
            else:
                print("   ❌ LOW PRIORITY: Focus elsewhere unless unique opportunities")
            print()
        
        # Resource allocation recommendations
        highly_flippable = tier_summary[tier_summary['strategic_tier'] == 'highly_flippable']
        flippable = tier_summary[tier_summary['strategic_tier'] == 'flippable']
        
        if len(highly_flippable) > 0:
            hf_races = int(highly_flippable.iloc[0]['race_count'])
            hf_gap = int(highly_flippable.iloc[0]['total_vote_gap'])
            print(f"🎯 IMMEDIATE ACTION PLAN:")
            print(f"   • Focus on {hf_races} highly flippable races")
            print(f"   • Total vote gap to close: {hf_gap:,} votes")
            print(f"   • Requires ≤25% DVA activation")
            print()
        
        if len(flippable) > 0:
            f_races = int(flippable.iloc[0]['race_count'])
            f_gap = int(flippable.iloc[0]['total_vote_gap'])
            print(f"💪 SECONDARY TARGETS:")
            print(f"   • {f_races} flippable races with 25-50% DVA needs")
            print(f"   • Additional vote gap: {f_gap:,} votes")
            print()
    
    def generate_race_details_report(self, races, top_n=20):
        """Generate detailed report of top races."""
        print(f"\n📋 TOP {top_n} STRATEGIC TARGETS")
        print("=" * 80)
        
        # Sort by strategic priority then DVA needed
        priority_order = {'highly_flippable': 1, 'flippable': 2, 'competitive': 3, 'stretch': 4, 'difficult': 5}
        races['priority'] = races['strategic_tier'].map(priority_order)
        top_races = races.sort_values(['priority', 'dva_pct_needed']).head(top_n)
        
        for i, (_, race) in enumerate(top_races.iterrows(), 1):
            print(f"{i:2d}. 🎯 {race['county']} County, Precinct {race['precinct']}")
            print(f"     Race: {race['contest_name']}")
            print(f"     Election: {race['election_date']}")
            print(f"     Results: DEM {int(race['dem_votes']):,} vs REP {int(race['rep_votes']):,}")
            print(f"     Margin: {race['margin_pct']:.1f}% ({int(race['vote_diff'])} votes)")
            print(f"     DVA Needed: {race['dva_pct_needed']:.1f}% of {int(race['dem_absenteeism'])} absent Dems")
            print(f"     Tier: {race['tier_label']}")
            print()
    
    def run_analysis(self, max_margin=10.0, min_votes=25, save_html=True):
        """Run complete DVA visualization analysis."""
        print("🔍 LOADING FLIPPABLE RACES DATA...")
        races = self.get_flippable_races_with_dva(max_margin, min_votes)
        
        if len(races) == 0:
            print("❌ No flippable races found with current criteria.")
            return
        
        print(f"✅ Found {len(races)} flippable races")
        
        # Classify tiers
        races = self.classify_strategic_tiers(races)
        
        # Create visualizations
        print("📊 CREATING VISUALIZATIONS...")
        
        # 1. Main scatter plot
        scatter_fig = self.create_dva_scatter_plot(races)
        if save_html:
            scatter_fig.write_html("dva_strategic_scatter.html")
            print("💾 Saved: dva_strategic_scatter.html")
        
        # 2. Tier summary
        tier_fig, tier_summary = self.create_tier_summary_chart(races)
        if save_html:
            tier_fig.write_html("dva_tier_summary.html")
            print("💾 Saved: dva_tier_summary.html")
        
        # 3. County analysis
        county_fig, county_summary = self.create_county_analysis(races)
        if save_html:
            county_fig.write_html("dva_county_analysis.html")
            print("💾 Saved: dva_county_analysis.html")
        
        # Print analysis
        self.print_strategic_recommendations(races, tier_summary)
        self.generate_race_details_report(races)
        
        # Show plots
        scatter_fig.show()
        tier_fig.show()
        county_fig.show()
        
        return races, tier_summary, county_summary

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='DVA Visualization Dashboard')
    parser.add_argument('--max-margin', type=float, default=10.0,
                      help='Maximum margin percentage for competitive races (default: 10.0)')
    parser.add_argument('--min-votes', type=int, default=25,
                      help='Minimum total votes for race inclusion (default: 25)')
    parser.add_argument('--no-html', action='store_true',
                      help='Skip saving HTML files')
    
    args = parser.parse_args()
    
    print("🎯 DVA VISUALIZATION DASHBOARD")
    print("=" * 50)
    print(f"Max margin: {args.max_margin}%")
    print(f"Min votes: {args.min_votes}")
    print()
    
    dashboard = DVAVisualizationDashboard()
    results = dashboard.run_analysis(
        max_margin=args.max_margin,
        min_votes=args.min_votes,
        save_html=not args.no_html
    )
    
    if results:
        races, tier_summary, county_summary = results
        print(f"\n✅ Analysis complete! Found {len(races)} flippable races.")
        print("📊 Interactive visualizations have been generated.")

if __name__ == "__main__":
    main()