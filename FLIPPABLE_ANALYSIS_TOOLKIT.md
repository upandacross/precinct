# Flippable Race Analysis Toolkit
## Comprehensive Strategic Analysis System

This toolkit provides a complete suite of analysis tools for identifying and strategically targeting flippable races. The system has been enhanced with 212 newly discovered close races and provides multi-layered analysis for democratic campaign targeting.

## 🎯 Core Analysis Tools

### 1. `check_narrow_margins.py` - Narrow Margin Analysis
**Purpose**: Identifies the most competitive races with very tight margins
- **Focus**: Races decided by ≤5% (configurable)
- **Key Features**:
  - Ultra-competitive race identification (≤0.5% margins)
  - Geographic and temporal analysis
  - Republican targets vs Democratic defensive priorities
  - CSV export for strategic planning

**Usage Examples**:
```bash
# Find races with ≤3% margins, ultra-competitive at ≤0.25%
python3 check_narrow_margins.py --max-margin 3.0 --ultra-threshold 0.25

# Export priority targets with ≤2% margins
python3 check_narrow_margins.py --max-margin 2.0 --export-csv --filename "priority_targets.csv"
```

### 2. `test_dva_scenarios.py` - DVA Scenario Testing
**Purpose**: Models the impact of specific Democratic Vote Added (DVA) percentages
- **Focus**: Testing realistic voter turnout increase scenarios
- **Key Features**:
  - Multiple DVA percentage testing (1.0%, 1.5%, 2.0%, etc.)
  - Precinct-specific targeting options
  - Optimal precinct identification
  - Efficiency ratio calculations (races flipped per 1,000 votes)

**Usage Examples**:
```bash
# Test 1.5% DVA increase on races with ≤5% Republican margin
python3 test_dva_scenarios.py --dva-increase 1.5 --max-margin 5.0 --find-optimal

# Target specific precincts with 2% DVA
python3 test_dva_scenarios.py --dva-increase 2.0 --target-precincts "132,131,43"
```

### 3. `comprehensive_flippable_analysis.py` - Complete Strategic Analysis
**Purpose**: Provides comprehensive analysis combining all methodologies
- **Focus**: Complete strategic overview with resource allocation recommendations
- **Key Features**:
  - Strategic tier classification (Tier 1-5 priorities)
  - Multiple DVA scenario testing
  - High-impact precinct identification
  - Resource allocation recommendations
  - Complete export package (CSV + JSON)

**Usage Examples**:
```bash
# Full analysis with 8% max margin, testing 4 DVA scenarios
python3 comprehensive_flippable_analysis.py --max-margin 8.0 --dva-levels "1.0,1.5,2.0,3.0"

# Custom output directory and precinct count
python3 comprehensive_flippable_analysis.py --output-dir "strategic_analysis" --top-precincts 20
```

### 4. `test_expanded_criteria.py` - Enhanced Targeting Analysis
**Purpose**: Analyzes flippable opportunities using expanded strategic criteria
- **Focus**: Beyond narrow margins - strategic opportunity identification
- **Key Features**:
  - Target category classification (Ultra/High/Medium/Opportunity/Long-term)
  - Feasibility tier analysis (Immediate/Short/Medium/Long-term)
  - Cluster targeting opportunities (multiple races per precinct)
  - Scaled DVA impact testing

**Usage Examples**:
```bash
# Expanded criteria with 12% max margin, 4% DVA feasibility cap
python3 test_expanded_criteria.py --max-margin 12.0 --dva-cap 4.0 --export-csv

# Conservative analysis with tighter constraints
python3 test_expanded_criteria.py --max-margin 8.0 --dva-cap 3.0 --min-votes 75
```

### 5. `update_flippable_races.py` - Database Enhancement
**Purpose**: Discovers and adds new close races to the flippable database
- **Focus**: Automated discovery of previously unidentified competitive races
- **Key Features**:
  - Automated race discovery (≤15% Republican margin)
  - Quality assurance (excludes existing races)
  - Database integration
  - Impact reporting

**Usage Examples**:
```bash
# Dry run to preview new races
python3 update_flippable_races.py --dry-run --max-margin 12.0

# Add new races to database
python3 update_flippable_races.py --max-margin 15.0 --min-votes 50
```

## 📊 Analysis Results Summary

### Current Database Status
- **Total Flippable Races**: 6,745 (enhanced from 6,533)
- **New Races Added**: 212 close races discovered
- **Precinct Coverage**: 152 precincts with flippable data
- **Average New Race Margin**: 7.95% (highly competitive)

### Key Findings from Recent Analysis

#### Narrow Margins Analysis (≤3% margin)
- **Total Narrow Races**: 228 races
- **Republican Targets**: 117 races (51.3%)
- **Democratic Defensive**: 111 races (48.7%)
- **Ultra-Competitive**: 16 races (≤0.25% margin)
- **Tightest Race**: 0.03% margin (1 vote difference)

#### DVA Scenario Results (1.5% increase)
- **Races Flipped**: 59 races (29.6% of narrow targets)
- **Total DVA Votes Needed**: 7,102 votes
- **Efficiency**: 4.73 races per 1,000 votes
- **Top Target**: FORSYTH Precinct 132 (23 flippable races)

#### Comprehensive Analysis (≤8% margin)
- **Total Competitive Races**: 691 races
- **Republican Targets**: 373 races (54.0%)
- **Strategic Tiers**:
  - Tier 1 (≤0.5%): 20 races - Immediate priority
  - Tier 2 (0.5-1.0%): 19 races - High priority
  - Tier 3 (1.0-2.0%): 41 races - Medium priority
  - Tier 4 (2.0-5.0%): 122 races - Opportunity
  - Tier 5 (5.0%+): 171 races - Long-term

#### Expanded Criteria Analysis (≤12% margin, ≤4% DVA)
- **Strategic Targets**: 153 races
- **Ultra-Target**: 17 races (≤0.5% margin)
- **High-Target**: 60 races (0.5-2.0% margin)
- **Cluster Opportunities**: 22 precincts with 3+ races
- **4% DVA Impact**: All 153 races flippable

## 🎯 Strategic Recommendations

### Phase 1: Immediate Targets (Priority 1)
**Focus**: Ultra-competitive races (≤0.5% margin)
- **Target Count**: 20 races
- **DVA Required**: 0.5-1.0%
- **Timeline**: Immediate deployment
- **Expected Success Rate**: 90%+

### Phase 2: High-Impact Clusters (Priority 2)
**Focus**: Top 5 precincts with multiple races
- **Target Precincts**: 132, 131, 71, 809, 43
- **Race Count**: 54 races across 5 precincts
- **DVA Required**: 2.2% average
- **Timeline**: 2-4 weeks
- **Resource Efficiency**: 10.8 races per precinct

### Phase 3: Strategic Expansion (Priority 3)
**Focus**: Medium-term opportunities (1.0-2.0% margin)
- **Target Count**: 60-80 races
- **DVA Required**: 1.5-2.0%
- **Timeline**: 1-3 months
- **Resource Requirements**: Moderate

## 📈 Efficiency Metrics

### DVA Efficiency by Scenario
| DVA Increase | Races Flipped | Votes Needed | Efficiency (per 1K votes) |
|--------------|---------------|--------------|---------------------------|
| 1.0%         | 37 races      | 8,725        | 4.24                     |
| 1.5%         | 62 races      | 13,108       | 4.73                     |
| 2.0%         | 79 races      | 17,472       | 4.52                     |
| 3.0%         | 117 races     | 26,190       | 4.47                     |

**Optimal DVA Level**: 1.5% provides best efficiency ratio

### Top Strategic Precincts
| Precinct | Races | Avg DVA | Impact Score | Total Gap |
|----------|-------|---------|--------------|-----------|
| FORSYTH 132 | 39 | 4.2% | 83.89 | 5,685 votes |
| FORSYTH 131 | 35 | 4.2% | 39.56 | 4,187 votes |
| FORSYTH 71  | 7  | 4.1% | 22.28 | 878 votes   |
| FORSYTH 809 | 6  | 2.1% | 21.84 | 503 votes   |
| FORSYTH 43  | 36 | 4.9% | 25.87 | 3,719 votes |

## 🔄 Integration with Clustering Analysis

### Enhanced Clustering Results
- **Flippability Clustering**: 355 precincts (enhanced from 349)
- **Silhouette Score**: 0.448 (best separation)
- **Coverage Improvement**: 152 precincts with flippable data (+2)
- **Strategic Focus**: Cluster 3 with 12 precincts enhanced

### Automated Updates
- **Discovery System**: `update_flippable_races.py` for ongoing enhancement
- **Integration**: Seamless connection to clustering analysis
- **Maintenance**: Regular updates to capture evolving competitive landscape

## 💾 Output Files and Exports

### Standard Exports
1. **CSV Files**: Detailed race data with strategic classifications
2. **JSON Reports**: Strategic recommendations and metrics
3. **Analysis Summaries**: Executive-level overviews

### File Naming Convention
- `narrow_margins_analysis_YYYYMMDD_HHMMSS.csv`
- `priority_flippable_targets.csv`
- `strategic_recommendations_YYYYMMDD_HHMMSS.json`
- `expanded_criteria_targets_YYYYMMDD_HHMMSS.csv`

## 🚀 Next Steps

1. **Deploy Phase 1 Targeting**: Focus immediate resources on 20 ultra-competitive races
2. **Cluster Precinct Strategy**: Implement multi-race targeting in top 5 precincts
3. **Regular Analysis Updates**: Run monthly updates to capture new competitive races
4. **Resource Allocation**: Use efficiency metrics to optimize campaign spending
5. **Performance Tracking**: Monitor actual results against DVA predictions

## 📞 Usage Support

Each tool includes built-in help:
```bash
python3 [tool_name].py --help
```

For detailed analysis of specific scenarios, tools can be chained together:
1. Use `update_flippable_races.py` to enhance database
2. Run `comprehensive_flippable_analysis.py` for strategic overview
3. Use `test_dva_scenarios.py` for specific targeting tests
4. Apply `check_narrow_margins.py` for immediate opportunities

The toolkit provides a complete strategic framework for democratic campaign targeting with data-driven precision and measurable efficiency metrics.