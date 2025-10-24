#!/usr/bin/env python3
"""
A/B Test Results Tracker
========================

Track and analyze results from A/B message tests.

Usage:
    python ab_results_tracker.py fundraising_ab_test.json --add-result A sent 150
    python ab_results_tracker.py fundraising_ab_test.json --add-result A opened 45
    python ab_results_tracker.py fundraising_ab_test.json --analyze
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any
import math

class ABResultsTracker:
    """Track and analyze A/B test results."""
    
    def __init__(self, test_file: str):
        self.test_file = test_file
        self.load_test_data()
    
    def load_test_data(self):
        """Load test data from JSON file."""
        try:
            with open(self.test_file, 'r') as f:
                self.test_data = json.load(f)
            
            # Initialize results tracking if not exists
            if 'results' not in self.test_data:
                self.test_data['results'] = {}
                for variant in self.test_data['variants']:
                    self.test_data['results'][variant['variant_id']] = {
                        'sent': 0,
                        'opened': 0,
                        'clicked': 0,
                        'responded': 0,
                        'converted': 0,
                        'last_updated': None
                    }
                self.save_test_data()
        except FileNotFoundError:
            print(f"Error: Test file {self.test_file} not found!")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.test_file}!")
            sys.exit(1)
    
    def save_test_data(self):
        """Save test data back to JSON file."""
        with open(self.test_file, 'w') as f:
            json.dump(self.test_data, f, indent=2)
    
    def add_result(self, variant_id: str, metric: str, value: int):
        """Add a result for a specific variant and metric."""
        if variant_id not in self.test_data['results']:
            print(f"Error: Variant {variant_id} not found!")
            return False
        
        valid_metrics = ['sent', 'opened', 'clicked', 'responded', 'converted']
        if metric not in valid_metrics:
            print(f"Error: Metric must be one of: {', '.join(valid_metrics)}")
            return False
        
        self.test_data['results'][variant_id][metric] = value
        self.test_data['results'][variant_id]['last_updated'] = datetime.now().isoformat()
        
        self.save_test_data()
        print(f"✅ Added {metric}={value} for variant {variant_id}")
        return True
    
    def calculate_rates(self, results: Dict) -> Dict:
        """Calculate percentage rates from raw numbers."""
        sent = results.get('sent', 0)
        opened = results.get('opened', 0)
        clicked = results.get('clicked', 0)
        responded = results.get('responded', 0)
        converted = results.get('converted', 0)
        
        return {
            'open_rate': (opened / sent * 100) if sent > 0 else 0,
            'click_rate': (clicked / sent * 100) if sent > 0 else 0,
            'response_rate': (responded / sent * 100) if sent > 0 else 0,
            'conversion_rate': (converted / sent * 100) if sent > 0 else 0,
            'ctr': (clicked / opened * 100) if opened > 0 else 0  # Click-through rate
        }
    
    def statistical_significance(self, variant_a: Dict, variant_b: Dict, metric: str = 'conversion_rate') -> Dict:
        """Calculate statistical significance between two variants."""
        # Get raw numbers
        sent_a = variant_a.get('sent', 0)
        sent_b = variant_b.get('sent', 0)
        
        if metric == 'conversion_rate':
            success_a = variant_a.get('converted', 0)
            success_b = variant_b.get('converted', 0)
        elif metric == 'click_rate':
            success_a = variant_a.get('clicked', 0)
            success_b = variant_b.get('clicked', 0)
        elif metric == 'open_rate':
            success_a = variant_a.get('opened', 0)
            success_b = variant_b.get('opened', 0)
        else:
            return {"error": f"Metric {metric} not supported for significance testing"}
        
        if sent_a == 0 or sent_b == 0:
            return {"error": "Need positive sample sizes for both variants"}
        
        # Calculate rates
        rate_a = success_a / sent_a
        rate_b = success_b / sent_b
        
        # Pooled rate
        pooled_rate = (success_a + success_b) / (sent_a + sent_b)
        
        # Standard error
        se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/sent_a + 1/sent_b))
        
        if se == 0:
            return {"error": "Cannot calculate significance (zero standard error)"}
        
        # Z-score
        z_score = (rate_a - rate_b) / se
        
        # Two-tailed p-value approximation
        p_value = 2 * (1 - abs(z_score) / math.sqrt(2 * math.pi) * math.exp(-z_score**2 / 2))
        
        # Effect size (difference in rates)
        effect_size = abs(rate_a - rate_b)
        
        # Determine winner
        winner = "A" if rate_a > rate_b else "B"
        
        return {
            "rate_a": rate_a * 100,
            "rate_b": rate_b * 100,
            "effect_size": effect_size * 100,
            "z_score": z_score,
            "p_value": p_value,
            "significant": p_value < 0.05,
            "winner": winner,
            "confidence": (1 - p_value) * 100
        }
    
    def analyze_results(self):
        """Analyze current test results."""
        print("=" * 80)
        print(f"A/B TEST ANALYSIS: {self.test_data['test_metadata']['subject']}")
        print(f"Test ID: {self.test_data['test_metadata']['test_id']}")
        print("=" * 80)
        
        # Show individual variant performance
        print("\n📊 VARIANT PERFORMANCE")
        print("-" * 60)
        
        variant_data = {}
        for variant in self.test_data['variants']:
            variant_id = variant['variant_id']
            results = self.test_data['results'][variant_id]
            rates = self.calculate_rates(results)
            
            variant_data[variant_id] = {**results, **rates}
            
            print(f"\nVariant {variant_id} ({variant['variant_name']}):")
            print(f"  Config: {variant['config']}")
            print(f"  Sent: {results['sent']}")
            print(f"  Opened: {results['opened']} ({rates['open_rate']:.1f}%)")
            print(f"  Clicked: {results['clicked']} ({rates['click_rate']:.1f}%)")
            print(f"  Responded: {results['responded']} ({rates['response_rate']:.1f}%)")
            print(f"  Converted: {results['converted']} ({rates['conversion_rate']:.1f}%)")
            if results['opened'] > 0:
                print(f"  CTR: {rates['ctr']:.1f}%")
        
        # Statistical significance analysis
        variant_ids = list(variant_data.keys())
        if len(variant_ids) >= 2:
            print(f"\n🔬 STATISTICAL ANALYSIS")
            print("-" * 60)
            
            # Compare all pairs
            for i in range(len(variant_ids)):
                for j in range(i + 1, len(variant_ids)):
                    variant_a_id = variant_ids[i]
                    variant_b_id = variant_ids[j]
                    
                    for metric in ['conversion_rate', 'click_rate', 'open_rate']:
                        if (variant_data[variant_a_id]['sent'] > 0 and 
                            variant_data[variant_b_id]['sent'] > 0):
                            
                            sig_test = self.statistical_significance(
                                self.test_data['results'][variant_a_id],
                                self.test_data['results'][variant_b_id],
                                metric
                            )
                            
                            if 'error' not in sig_test:
                                print(f"\n{variant_a_id} vs {variant_b_id} ({metric}):")
                                print(f"  {variant_a_id}: {sig_test['rate_a']:.1f}%")
                                print(f"  {variant_b_id}: {sig_test['rate_b']:.1f}%")
                                print(f"  Effect size: {sig_test['effect_size']:.1f}%")
                                print(f"  P-value: {sig_test['p_value']:.4f}")
                                print(f"  Significant: {'✅ YES' if sig_test['significant'] else '❌ NO'}")
                                if sig_test['significant']:
                                    print(f"  Winner: Variant {sig_test['winner']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 60)
        
        # Find best performing variant by conversion rate
        best_variant = max(variant_data.keys(), 
                          key=lambda x: variant_data[x]['conversion_rate'])
        
        print(f"Best performing variant: {best_variant}")
        print(f"Conversion rate: {variant_data[best_variant]['conversion_rate']:.1f}%")
        
        # Sample size recommendations
        min_sample = 100
        for variant_id, data in variant_data.items():
            if data['sent'] < min_sample:
                needed = min_sample - data['sent']
                print(f"⚠️  Variant {variant_id} needs {needed} more samples for reliable results")
    
    def export_summary(self, filename: str = None):
        """Export analysis summary to file."""
        if filename is None:
            test_id = self.test_data['test_metadata']['test_id']
            filename = f"ab_analysis_{test_id}.txt"
        
        # Capture analysis output
        # This would require redirecting stdout, simplified for now
        print(f"\n✅ Analysis can be exported to {filename}")
        print("   (Feature available in full implementation)")

def main():
    """Main CLI function for results tracking."""
    
    parser = argparse.ArgumentParser(
        description="Track and analyze A/B test results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s test.json --add-result A sent 150
    %(prog)s test.json --add-result A opened 45 --add-result A clicked 12
    %(prog)s test.json --analyze
    %(prog)s test.json --analyze --export summary.txt
        """
    )
    
    parser.add_argument("test_file", help="A/B test JSON file")
    parser.add_argument("--add-result", nargs=3, action="append",
                       metavar=("VARIANT", "METRIC", "VALUE"),
                       help="Add result: variant_id metric value")
    parser.add_argument("--analyze", action="store_true",
                       help="Analyze current results")
    parser.add_argument("--export", help="Export analysis to file")
    
    args = parser.parse_args()
    
    # Create tracker instance
    tracker = ABResultsTracker(args.test_file)
    
    # Add results if specified
    if args.add_result:
        for variant_id, metric, value in args.add_result:
            try:
                tracker.add_result(variant_id, metric, int(value))
            except ValueError:
                print(f"Error: Value must be a number, got '{value}'")
                sys.exit(1)
    
    # Analyze results if requested
    if args.analyze:
        tracker.analyze_results()
    
    # Export if requested
    if args.export:
        tracker.export_summary(args.export)

if __name__ == "__main__":
    main()