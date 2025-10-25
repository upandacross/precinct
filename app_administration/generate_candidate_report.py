#!/usr/bin/env python3
"""
Generate Candidate Recruitment Report

Creates a personalized markdown report for a specific candidate showing:
- Historical flippability data for their target race
- DVA needed and voter activation targets
- Past performance (if they've run before)
- Recruitment talking points and strategy
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import Config
    DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI
except ImportError:
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("Error: Cannot import config.py and DATABASE_URL environment variable not set")
        sys.exit(1)


class CandidateReportGenerator:
    """Generates personalized candidate recruitment reports."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.engine = create_engine(DATABASE_URL)
    
    def get_candidate_history(self, candidate_name, county=None):
        """
        Get historical performance for a candidate.
        
        Returns:
            list: Past races this candidate has run in
        """
        with self.engine.connect() as conn:
            where_clause = "AND county = :county" if county else ""
            params = {'candidate_name': f"%{candidate_name}%"}
            if county:
                params['county'] = county
            
            result = conn.execute(text(f"""
                SELECT DISTINCT
                    county, election_date, contest_name,
                    dem_candidate, dem_votes, oppo_votes, dem_margin,
                    dva_pct_needed, race_type
                FROM flippable
                WHERE (dem_candidate ILIKE :candidate_name)
                {where_clause}
                ORDER BY election_date DESC
            """), params)
            
            return [dict(zip(result.keys(), row)) for row in result]
    
    def get_race_history(self, contest_name, county, precinct=None):
        """
        Get historical flippability data for a specific race/contest type.
        
        Returns:
            list: Historical instances of this race being flippable
        """
        with self.engine.connect() as conn:
            precinct_clause = "AND precinct = :precinct" if precinct else ""
            params = {
                'contest_name': f"%{contest_name}%",
                'county': county
            }
            if precinct:
                params['precinct'] = precinct
            
            result = conn.execute(text(f"""
                SELECT 
                    county, precinct, election_date, contest_name,
                    dem_votes, oppo_votes, dem_margin, dva_pct_needed,
                    dem_candidate, rep_candidate, race_type
                FROM flippable
                WHERE contest_name ILIKE :contest_name
                AND county = :county
                AND dva_pct_needed > 0
                {precinct_clause}
                ORDER BY election_date DESC, dva_pct_needed ASC
                LIMIT 20
            """), params)
            
            return [dict(zip(result.keys(), row)) for row in result]
    
    def get_dva_voters(self, county, precinct):
        """
        Estimate DVA voter pool for a precinct.
        
        Returns:
            dict: Statistics about potential DVA voters
        """
        with self.engine.connect() as conn:
            # Get average gov_votes and total votes from partisan races
            result = conn.execute(text("""
                SELECT 
                    AVG(gov_votes) as avg_gov_votes,
                    AVG(dem_votes + oppo_votes) as avg_downballot_votes,
                    COUNT(*) as race_count
                FROM flippable
                WHERE county = :county
                AND precinct = :precinct
                AND race_type = 'partisan'
                AND gov_votes IS NOT NULL
            """), {'county': county, 'precinct': precinct})
            
            row = result.fetchone()
            if row and row[0]:
                avg_gov = int(row[0])
                avg_downballot = int(row[1])
                dva_pool = avg_gov - avg_downballot
                dva_pct = (dva_pool / avg_gov * 100) if avg_gov > 0 else 0
                
                return {
                    'avg_gov_votes': avg_gov,
                    'avg_downballot_votes': avg_downballot,
                    'dva_pool_size': dva_pool,
                    'dva_pool_pct': dva_pct,
                    'sample_size': int(row[2])
                }
            
            return None
    
    def generate_report(self, candidate_last_name, contest_name, county, 
                       candidate_first_name=None, precinct=None, output_dir="candidate_reports"):
        """
        Generate a complete candidate recruitment report.
        
        Args:
            candidate_last_name: Candidate's last name
            contest_name: Contest/race they're considering
            county: County name
            candidate_first_name: Optional first name
            precinct: Optional specific precinct
            output_dir: Directory to save report
        """
        # Get data
        full_name = f"{candidate_first_name} {candidate_last_name}" if candidate_first_name else candidate_last_name
        candidate_history = self.get_candidate_history(candidate_last_name, county)
        race_history = self.get_race_history(contest_name, county, precinct)
        
        # Build report
        timestamp = datetime.now()
        filename = f"{candidate_last_name}_{contest_name.replace(' ', '_')}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = Path(output_dir) / filename
        
        # Ensure directory exists
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate markdown
        report = self._build_markdown_report(
            full_name, candidate_last_name, contest_name, county, precinct,
            candidate_history, race_history, timestamp
        )
        
        # Save file
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Report generated: {filepath}")
        print(f"   Candidate: {full_name}")
        print(f"   Contest: {contest_name}")
        print(f"   County: {county}")
        if precinct:
            print(f"   Precinct: {precinct}")
        
        return filepath
    
    def _build_markdown_report(self, full_name, last_name, contest_name, county, precinct,
                               candidate_history, race_history, timestamp):
        """Build the markdown content for the report."""
        
        # Header
        md = f"""# Candidate Recruitment Report: {full_name}

**Contest:** {contest_name}  
**County:** {county}  
{f'**Precinct:** {precinct}  ' if precinct else ''}
**Report Generated:** {timestamp.strftime('%B %d, %Y at %I:%M %p')}

---

## Executive Summary

"""
        
        # Candidate history section
        if candidate_history:
            md += f"""### {full_name}'s Track Record

**Previous Races:**

"""
            for race in candidate_history:
                margin_desc = "WON" if race['dem_margin'] > 0 else "LOST"
                margin_votes = abs(race['dem_margin'])
                margin_pct = abs(race['dem_margin'] / (race['dem_votes'] + race['oppo_votes']) * 100) if (race['dem_votes'] + race['oppo_votes']) > 0 else 0
                
                md += f"""- **{race['election_date'].strftime('%Y')} - {race['contest_name']}**
  - Result: {margin_desc} by {margin_votes} votes ({margin_pct:.1f}%)
  - Vote count: {race['dem_votes']:,} (D) vs {race['oppo_votes']:,} (R)
  - DVA needed: {race['dva_pct_needed']:.1f}% if applicable
  - Race type: {race['race_type'].title()}

"""
            
            # Calculate trajectory
            if len(candidate_history) > 1:
                latest = candidate_history[0]
                previous = candidate_history[-1]
                latest_margin_pct = latest['dem_margin'] / (latest['dem_votes'] + latest['oppo_votes']) * 100
                prev_margin_pct = previous['dem_margin'] / (previous['dem_votes'] + previous['oppo_votes']) * 100
                improvement = latest_margin_pct - prev_margin_pct
                
                md += f"""**Performance Trajectory:**  
{full_name}'s margin {'improved' if improvement > 0 else 'declined'} by {abs(improvement):.1f} percentage points from {previous['election_date'].year} to {latest['election_date'].year}. """
                
                if improvement > 0:
                    md += f"This upward trend shows growing voter support and name recognition.\n\n"
                else:
                    md += f"This suggests the need for a refreshed strategy or different race selection.\n\n"
        else:
            md += f"""### {full_name}'s Track Record

**No Previous Races Found**

This appears to be {full_name}'s first run for office (or name not yet in our database). First-time candidates can be highly effective, especially in races with strong DVA potential.

"""
        
        # Race history section
        md += f"""---

## Historical Flippability: {contest_name}

"""
        
        if race_history:
            # Calculate statistics
            avg_dva = sum(r['dva_pct_needed'] for r in race_history) / len(race_history)
            avg_margin = sum(abs(r['dem_margin']) for r in race_history) / len(race_history)
            total_votes_avg = sum((r['dem_votes'] + r['oppo_votes']) for r in race_history) / len(race_history)
            avg_gap_pct = (avg_margin / total_votes_avg * 100) if total_votes_avg > 0 else 0
            
            # Determine flippability rating
            if avg_dva < 15:
                rating = "🎯 HIGHLY FLIPPABLE"
                rating_desc = "This race type has consistently shown strong flippability with moderate DVA activation."
            elif avg_dva < 25:
                rating = "✅ COMPETITIVE"
                rating_desc = "This race is winnable with a strong field operation and candidate quality."
            else:
                rating = "🔵 CHALLENGING"
                rating_desc = "This race requires significant DVA activation but has shown flippable patterns."
            
            md += f"""**Rating:** {rating}

**Historical Performance ({len(race_history)} instances):**
- Average DVA needed: **{avg_dva:.1f}%**
- Average vote gap: **{avg_margin:.0f} votes** ({avg_gap_pct:.1f}%)
- Average total votes: **{total_votes_avg:.0f}**

{rating_desc}

### Recent Races:

"""
            for race in race_history[:5]:  # Show top 5
                dva_rating = "🎯" if race['dva_pct_needed'] < 15 else "✅" if race['dva_pct_needed'] < 25 else "🔵"
                dem_name = race['dem_candidate'][:30] if race['dem_candidate'] else "Unnamed Democrat"
                rep_name = race['rep_candidate'][:30] if race['rep_candidate'] else "Unnamed Republican"
                
                md += f"""**{race['election_date'].strftime('%Y')} - Precinct {race['precinct']}** {dva_rating}
- Democratic: {dem_name} - {race['dem_votes']:,} votes
- Republican: {rep_name} - {race['oppo_votes']:,} votes
- Margin: {race['dem_margin']:+,} votes
- **DVA needed: {race['dva_pct_needed']:.1f}%**

"""
        else:
            md += f"""**No Historical Data Found**

We don't have flippable race data for "{contest_name}" in {county} County yet. This could mean:
- This is a new race type not yet in our database
- The contest name might be slightly different
- This race hasn't been competitive in recent cycles

Consider looking at similar race types or expanding the search criteria.

"""
        
        # DVA Analysis section
        if race_history:
            # Get precinct data if available
            sample_race = race_history[0]
            dva_data = self.get_dva_voters(county, sample_race['precinct'])
            
            md += f"""---

## Voter Activation Strategy

"""
            if dva_data:
                md += f"""### DVA Voter Pool (Precinct {sample_race['precinct']} Analysis)

- **Average Governor votes:** {dva_data['avg_gov_votes']:,}
- **Average downballot votes:** {dva_data['avg_downballot_votes']:,}
- **DVA voter pool:** ~{dva_data['dva_pool_size']:,} voters ({dva_data['dva_pool_pct']:.1f}%)

**What This Means:**

In a typical election, about **{dva_data['dva_pool_size']:,} voters** in this precinct vote for Democratic governor but skip downballot races. These are your **prime target voters**.

To activate {avg_dva:.0f}% DVA ({int(dva_data['avg_gov_votes'] * avg_dva / 100):,} voters), you need:
"""
                activation_needed = int(dva_data['avg_gov_votes'] * avg_dva / 100)
                
                md += f"""
1. **Targeted Voter Contact**
   - Mail pieces: {activation_needed} households
   - Canvassing: {int(activation_needed * 0.6)} doors (assuming 60% contact rate goal)
   - Phone banking: {int(activation_needed * 1.2)} calls (assuming multiple attempts)

2. **Messaging Focus**
   - These voters already support Democrats at the top of the ticket
   - They need to know THIS race matters too
   - Local impact messaging works best

3. **Field Operation Scale**
   - Estimated volunteer hours needed: {int(activation_needed * 0.15)} hours
   - Canvassers needed (4-hour shifts): {int(activation_needed * 0.15 / 4)} volunteers
   - Weeks of operation: 6-8 weeks before election

"""
            else:
                md += """**DVA data not available for this precinct.** Historical DVA calculations suggest moderate to high activation is needed based on contest type.

"""
        
        # Recruitment talking points
        md += f"""---

## Recruitment Strategy & Talking Points

### Why {full_name} Should Run

"""
        if candidate_history:
            if candidate_history[0]['dem_margin'] < 0:  # Lost last race
                lost_by = abs(candidate_history[0]['dem_margin'])
                md += f"""**"You Were So Close"**

In your last race, you lost by just {lost_by:,} votes. Our data shows this race is consistently competitive, and you already have:
- Name recognition in the district
- Campaign experience and lessons learned
- A proven base of support

With our DVA targeting and field operation, those {lost_by:,} votes are absolutely reachable.

"""
            else:  # Won last race
                md += f"""**"Build On Your Success"**

You've proven you can win. Our data shows you can win again with the right strategy and voter activation plan.

"""
        else:
            md += f"""**"This Race Is Winnable - Here's the Data"**

You may be a first-time candidate, but our historical analysis shows this race has clear flippable patterns. We have the data, the strategy, and the support system to help you win.

"""
        
        if race_history and avg_dva < 20:
            md += f"""**"The Numbers Are On Your Side"**

- Historical DVA needed: {avg_dva:.0f}% - This is **very achievable**
- Average vote gap: {avg_margin:.0f} votes - Winnable margin
- We have the exact voter list of DVA targets
- Our field operation has the proven playbook

"""
        
        md += f"""### What We Offer

1. **Data-Driven Targeting**
   - Precise DVA voter lists
   - Historical performance analysis
   - Opposition research

2. **Field Operation Support**
   - Volunteer recruitment and training
   - Canvassing schedules and routes
   - Phone banking infrastructure

3. **Strategic Guidance**
   - Message development based on data
   - Resource allocation advice
   - Multi-cycle campaign planning

### The Ask

{f"**Would you consider running for {contest_name} in {timestamp.year + 1}?**" if timestamp.month < 6 else f"**Would you consider running for {contest_name}?**"}

We can schedule a follow-up meeting to:
- Review detailed voter targeting lists
- Discuss campaign timeline and resource needs
- Answer any questions about the race

**Next Steps:**
1. Review this data analysis
2. Schedule 1-on-1 meeting with campaign leadership
3. Tour the district/precinct
4. Make decision within [TIMELINE]

---

## Appendix: Data Sources

- **Flippable Race Database:** Historical election results with DVA calculations
- **Partisan Baseline:** Governor race performance in target precincts
- **Municipal Races:** Proxy DVA using partisan baseline from same precinct
- **Candidate History:** Public election results database

**Report Version:** 1.0  
**Generated By:** Precinct Campaign Platform - Candidate Recruitment Module

---

*This report is confidential and intended for campaign strategy purposes only.*
"""
        
        return md


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Generate personalized candidate recruitment report'
    )
    parser.add_argument(
        'last_name',
        help='Candidate last name'
    )
    parser.add_argument(
        'contest',
        help='Contest name (e.g., "City Council", "County Commissioner")'
    )
    parser.add_argument(
        'county',
        help='County name (e.g., FORSYTH)'
    )
    parser.add_argument(
        '--first-name',
        help='Candidate first name (optional)',
        default=None
    )
    parser.add_argument(
        '--precinct',
        help='Specific precinct (optional)',
        default=None
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for report',
        default='candidate_reports'
    )
    
    args = parser.parse_args()
    
    generator = CandidateReportGenerator()
    generator.generate_report(
        candidate_last_name=args.last_name,
        contest_name=args.contest,
        county=args.county,
        candidate_first_name=args.first_name,
        precinct=args.precinct,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
