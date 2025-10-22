#!/usr/bin/env python3
"""
Dual-Pathway Flippable Analysis
==============================

Shows both traditional vote gap AND DVA efficiency, highlighting the better pathway
for each race to avoid discouraging high DVA percentages when vote gaps are small.
"""

def analyze_flipping_pathways():
    """Analyze races using both traditional and DVA approaches."""
    
    print("🎯 DUAL-PATHWAY FLIPPABLE ANALYSIS")
    print("=" * 50)
    print("Shows the MORE ACHIEVABLE pathway for each race")
    print()
    
    # Test scenarios with different characteristics
    scenarios = [
        {
            "name": "Low vote gap, high DVA",
            "dem_votes": 1000,
            "oppo_votes": 1020,  # Only 20 vote gap
            "gov_votes": 1200,   # High absenteeism → high DVA%
            "total_turnout": 2200
        },
        {
            "name": "Medium vote gap, low DVA", 
            "dem_votes": 1500,
            "oppo_votes": 1550,  # 50 vote gap
            "gov_votes": 1520,   # Low absenteeism → low DVA%
            "total_turnout": 3200
        },
        {
            "name": "High vote gap, medium DVA",
            "dem_votes": 800,
            "oppo_votes": 950,   # 150 vote gap
            "gov_votes": 1100,   # Medium absenteeism
            "total_turnout": 2100
        },
        {
            "name": "Extremely close race",
            "dem_votes": 2000,
            "oppo_votes": 2003,  # Only 3 vote gap!
            "gov_votes": 2050,   # Some absenteeism
            "total_turnout": 4200
        }
    ]
    
    for scenario in scenarios:
        print(f"📊 {scenario['name']}:")
        print(f"   Dem: {scenario['dem_votes']:,} | Opp: {scenario['oppo_votes']:,} | Gov: {scenario['gov_votes']:,}")
        
        # Traditional pathway: raw vote gap
        vote_gap = (scenario['oppo_votes'] + 1) - scenario['dem_votes']
        turnout_pct = (vote_gap / scenario['total_turnout']) * 100
        
        # DVA pathway: mobilize absent Dem voters
        dem_absenteeism = scenario['gov_votes'] - scenario['dem_votes']
        if dem_absenteeism > 0:
            dva_pct = (vote_gap / dem_absenteeism) * 100
        else:
            dva_pct = 999.9
        
        print(f"   📈 Traditional: Need {vote_gap} votes ({turnout_pct:.1f}% of total turnout)")
        print(f"   🏛️  DVA: Need {dva_pct:.1f}% of {dem_absenteeism} absent Dem voters")
        
        # Determine better pathway
        traditional_difficulty = "EASY" if vote_gap <= 50 else "MEDIUM" if vote_gap <= 150 else "HARD"
        dva_difficulty = "EASY" if dva_pct <= 25 else "MEDIUM" if dva_pct <= 50 else "HARD"
        
        if traditional_difficulty == "EASY" or dva_difficulty == "HARD":
            recommended = "TRADITIONAL"
            strategy = f"Target {vote_gap} new voters through door-to-door/phone banking"
        elif dva_difficulty == "EASY" or traditional_difficulty == "HARD":
            recommended = "DVA"
            strategy = f"Mobilize {dva_pct:.1f}% of Dems who voted governor but skipped down-ballot"
        else:
            # Both medium - pick the lower percentage
            if turnout_pct <= dva_pct:
                recommended = "TRADITIONAL"
                strategy = f"Target {vote_gap} new voters ({turnout_pct:.1f}% effort)"
            else:
                recommended = "DVA"
                strategy = f"Mobilize absent Dem voters ({dva_pct:.1f}% effort)"
        
        print(f"   ✅ RECOMMENDED: {recommended}")
        print(f"   📋 Strategy: {strategy}")
        print()

def create_user_friendly_assessment():
    """Create assessment categories that encourage rather than discourage."""
    
    print("🎨 USER-FRIENDLY ASSESSMENT CATEGORIES")
    print("=" * 50)
    
    categories = [
        ("🎯 SLAM DUNK", "≤ 25 votes OR ≤ 15% DVA", "Weekend volunteer effort"),
        ("✅ HIGHLY FLIPPABLE", "≤ 100 votes OR ≤ 35% DVA", "Month-long focused campaign"),
        ("🟡 COMPETITIVE", "≤ 300 votes OR ≤ 60% DVA", "Season-long strategic effort"),
        ("🔴 STRETCH GOAL", "> 300 votes AND > 60% DVA", "Multi-cycle investment")
    ]
    
    for emoji, criteria, effort in categories:
        print(f"{emoji:<20} {criteria:<25} → {effort}")
    
    print("\n💡 Always show the BETTER of the two pathways to maintain volunteer optimism!")

if __name__ == "__main__":
    analyze_flipping_pathways()
    print()
    create_user_friendly_assessment()