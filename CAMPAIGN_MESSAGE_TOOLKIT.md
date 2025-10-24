# Campaign Message Testing Toolkit

A comprehensive suite of tools for generating, testing, and analyzing campaign messages with A/B testing capabilities.

## Tools Overview

### 1. Message Generator CLI (`message_generator_cli.py`)
**Purpose**: Generate individual campaign messages with specific parameters.

**Key Features**:
- 5 tone options: formal, casual, persuasive, informative, urgent
- 5 formats: email, SMS, social media, letter, general
- 3 length options: short, medium, long
- 5 audience targets: general, technical, executive, youth, seniors
- Word count and character statistics
- Comprehensive help system

**Usage Examples**:
```bash
python message_generator_cli.py "Town Hall Meeting" --tone persuasive --length short --format email
python message_generator_cli.py "Volunteer Drive" --tone casual --format sms --audience youth
```

### 2. A/B Message Tester (`ab_message_tester.py`)
**Purpose**: Create comprehensive A/B tests with multiple message variants.

**Key Features**:
- Generate 2-26 variants automatically
- Test multiple factors: tone, length, format, audience
- JSON export for external systems
- Deployment code generation
- Baseline configuration with systematic variations
- Statistical framework preparation

**Usage Examples**:
```bash
python ab_message_tester.py "Fundraising Event" --variants 4 --test-factors tone,format
python ab_message_tester.py "GOTV Drive" --variants 3 --export gotv_test.json
python ab_message_tester.py "Town Hall" --show-deployment --show-stats
```

### 3. A/B Results Tracker (`ab_results_tracker.py`)
**Purpose**: Track and analyze A/B test performance with statistical analysis.

**Key Features**:
- Track metrics: sent, opened, clicked, responded, converted
- Calculate conversion rates and click-through rates
- Statistical significance testing (z-scores, p-values)
- Effect size calculations
- Winner determination with confidence levels
- Sample size recommendations

**Usage Examples**:
```bash
python ab_results_tracker.py test.json --add-result A sent 500 --add-result A opened 235
python ab_results_tracker.py test.json --analyze
python ab_results_tracker.py test.json --analyze --export analysis_report.txt
```

### 4. Campaign Workflow Manager (`campaign_workflow.py`)
**Purpose**: Unified interface for complete campaign lifecycle management.

**Key Features**:
- Create campaigns with auto-generated filenames
- Deploy campaigns with generated deployment code
- Track results across multiple variants
- Analyze campaigns with statistical insights
- Campaign status monitoring
- List all active campaigns

**Usage Examples**:
```bash
python campaign_workflow.py create --subject "Volunteer Drive" --variants 3
python campaign_workflow.py track test.json --sent A 200 B 200 --opened A 85 B 92
python campaign_workflow.py analyze test.json
python campaign_workflow.py list
python campaign_workflow.py status test.json
```

## Workflow Examples

### Creating a Complete Campaign

1. **Create the campaign**:
```bash
python campaign_workflow.py create --subject "Summer Fundraiser" --variants 4 --test-factors tone format
```

2. **Generate deployment code**:
```bash
python campaign_workflow.py deploy summer_fundraiser_ab_test.json
```

3. **Track results as they come in**:
```bash
python campaign_workflow.py track summer_fundraiser_ab_test.json --sent A 500 B 500 C 500 D 500
python campaign_workflow.py track summer_fundraiser_ab_test.json --opened A 235 B 198 C 267 D 312
python campaign_workflow.py track summer_fundraiser_ab_test.json --clicked A 45 B 52 C 63 D 89
```

4. **Analyze results**:
```bash
python campaign_workflow.py analyze summer_fundraiser_ab_test.json
```

### Advanced Testing Scenarios

**Multi-factor testing**:
```bash
python ab_message_tester.py "Policy Update" --variants 8 --test-factors tone,length,audience
```

**Quick message generation**:
```bash
python message_generator_cli.py "Emergency Alert" --tone urgent --length short --format sms
```

**Detailed statistical analysis**:
```bash
python ab_results_tracker.py complex_test.json --analyze --export detailed_analysis.txt
```

## Output Formats

### JSON Export Structure
```json
{
  "test_metadata": {
    "test_id": "unique_id",
    "subject": "Campaign Subject",
    "created_at": "timestamp",
    "total_variants": 4
  },
  "variants": [
    {
      "variant_id": "A",
      "variant_name": "Baseline",
      "config": {"tone": "informative", "length": "medium"},
      "message_content": "Generated message text..."
    }
  ],
  "results": {
    "A": {"sent": 500, "opened": 235, "clicked": 45, "converted": 23}
  }
}
```

### Statistical Analysis Output
```
📊 VARIANT PERFORMANCE
Variant A (Baseline): 4.6% conversion rate
Variant B (Test): 6.2% conversion rate

🔬 STATISTICAL ANALYSIS
A vs B (conversion_rate):
  Effect size: 1.6%
  P-value: 0.2341
  Significant: ❌ NO
  Winner: Variant B
```

## Integration Capabilities

### Deployment Code Generation
The system generates ready-to-use deployment code for:
- User assignment to test variants
- Message delivery tracking
- Engagement measurement
- Results collection

### External System Integration
- JSON export compatible with analytics platforms
- CSV export for spreadsheet analysis
- API-ready data structures
- Database schema suggestions

## Best Practices

### Sample Size Guidelines
- Minimum 100 sent per variant for reliable results
- 500+ for high-confidence statistical analysis
- Consider effect size when determining sample needs

### Test Design
- Test 1-2 factors at a time for clear insights
- Use baseline variants for comparison
- Run tests long enough for statistical significance

### Analysis Interpretation
- P-value < 0.05 indicates statistical significance
- Effect size shows practical significance
- Consider both statistical and practical importance

## Technical Requirements

**Dependencies**:
- Python 3.8+
- Standard library modules: argparse, json, datetime, math, uuid, textwrap
- No external dependencies required

**File Structure**:
```
campaign_tools/
├── message_generator_cli.py
├── ab_message_tester.py
├── ab_results_tracker.py
├── campaign_workflow.py
└── campaign_data/
    ├── test1_ab_test.json
    ├── test2_ab_test.json
    └── analysis_reports/
```

## Future Enhancements

### Planned Features
- Integration with email service APIs
- Real-time analytics dashboard
- Advanced statistical models
- Machine learning optimization
- Multi-channel campaign support

### API Integration Targets
- Mailchimp, SendGrid (email)
- Twilio (SMS)
- Facebook, Twitter (social media)
- Google Analytics (tracking)

This toolkit provides a complete solution for data-driven campaign message optimization, from initial generation through statistical analysis of results.