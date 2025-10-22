#!/usr/bin/env python3
"""
Test the corrected DVA formula
==============================

Validate the DVA (Democratic Voter Absenteeism) calculation:
dva_pct_needed = ((oppo_votes + 1) - dem_votes) / (gov_votes - dem_votes)
"""

def test_dva_formula():
    """Test DVA calculation with example scenarios."""
    
    print("🧮 TESTING CORRECTED DVA FORMULA")
    print("=" * 50)
    print("Formula: dva_pct_needed = ((oppo_votes + 1) - dem_votes) / (gov_votes - dem_votes)")
    print()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Close race, high absenteeism",
            "dem_votes": 1000,
            "oppo_votes": 1020,  # Republicans ahead by 20
            "gov_votes": 1200,   # 200 Dems voted governor but not down-ballot
        },
        {
            "name": "Very close race, moderate absenteeism", 
            "dem_votes": 1500,
            "oppo_votes": 1503,  # Republicans ahead by 3
            "gov_votes": 1550,   # 50 Dems voted governor but not down-ballot
        },
        {
            "name": "Wider gap, high absenteeism",
            "dem_votes": 800,
            "oppo_votes": 900,   # Republicans ahead by 100
            "gov_votes": 1100,   # 300 Dems voted governor but not down-ballot
        },
        {
            "name": "Impossible scenario (no absenteeism)",
            "dem_votes": 1000,
            "oppo_votes": 1050,  # Republicans ahead by 50
            "gov_votes": 1000,   # No Democratic absenteeism
        }
    ]
    
    for scenario in scenarios:
        print(f"📊 {scenario['name']}:")
        print(f"   Democratic votes: {scenario['dem_votes']}")
        print(f"   Opposition votes: {scenario['oppo_votes']}")
        print(f"   Governor votes: {scenario['gov_votes']}")
        
        # Calculate components
        vote_gap = (scenario['oppo_votes'] + 1) - scenario['dem_votes']
        dem_absenteeism = scenario['gov_votes'] - scenario['dem_votes']
        
        print(f"   Vote gap to win: {vote_gap}")
        print(f"   Democratic absenteeism: {dem_absenteeism}")
        
        if dem_absenteeism <= 0:
            dva_pct = 999.9
            print(f"   DVA needed: {dva_pct}% (IMPOSSIBLE - no absenteeism)")
        else:
            dva_pct = (vote_gap / dem_absenteeism) * 100
            print(f"   DVA needed: {dva_pct:.1f}%")
            
            if dva_pct <= 50:
                print(f"   Assessment: ✅ HIGHLY FLIPPABLE (need {dva_pct:.1f}% of absent Dems)")
            elif dva_pct <= 100:
                print(f"   Assessment: 🟡 FLIPPABLE (need {dva_pct:.1f}% of absent Dems)")
            else:
                print(f"   Assessment: ❌ DIFFICULT (need {dva_pct:.1f}% of absent Dems)")
        
        print()

if __name__ == "__main__":
    test_dva_formula()