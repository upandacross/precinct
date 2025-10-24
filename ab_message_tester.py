#!/usr/bin/env python3
"""
A/B Message Testing System
==========================

Generate and test multiple message variants for A/B testing campaigns.

Usage:
    python ab_message_tester.py "voter outreach" --variants 3 --test-factors tone,length
    python ab_message_tester.py "fundraising event" --variants 2 --test-factors tone --baseline persuasive
    python ab_message_tester.py "meeting reminder" --variants 4 --test-factors tone,format --export results.json
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
import uuid
from message_generator_cli import generate_message_content

class ABMessageTester:
    """A/B testing system for message generation and tracking."""
    
    def __init__(self):
        self.test_results = []
        self.test_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now().isoformat()
        
    def generate_variants(self, subject: str, num_variants: int, test_factors: List[str], baseline: Dict[str, str] = None) -> List[Dict]:
        """
        Generate multiple message variants for A/B testing.
        
        Args:
            subject: Message subject/topic
            num_variants: Number of variants to generate
            test_factors: Factors to vary (tone, length, format, audience)
            baseline: Base configuration for comparison
            
        Returns:
            List of variant dictionaries with messages and metadata
        """
        if baseline is None:
            baseline = {
                "length": "medium",
                "tone": "informative", 
                "format": "general",
                "audience": "general"
            }
            
        # Define possible values for each factor
        factor_options = {
            "tone": ["formal", "casual", "persuasive", "informative", "urgent", "buttigieg", "obama"],
            "length": ["short", "medium", "long"],
            "format": ["email", "sms", "social_media", "letter", "general"],
            "audience": ["general", "technical", "executive", "youth", "seniors"]
        }
        
        variants = []
        
        # Generate baseline variant (A)
        baseline_config = baseline.copy()
        baseline_message = generate_message_content(subject, **baseline_config)
        
        variants.append({
            "variant_id": "A",
            "variant_name": "Baseline",
            "config": baseline_config,
            "message": baseline_message,
            "word_count": len(baseline_message.split()),
            "char_count": len(baseline_message),
            "is_baseline": True,
            "test_factors": []
        })
        
        # Generate test variants (B, C, D, etc.)
        variant_letters = "BCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        for i in range(num_variants - 1):  # -1 because we already have baseline
            variant_config = baseline.copy()
            varied_factors = []
            
            # Vary one or more factors
            for factor in test_factors:
                if factor in factor_options:
                    # Choose a different option than baseline
                    available_options = [opt for opt in factor_options[factor] 
                                       if opt != baseline.get(factor)]
                    if available_options:
                        # Cycle through options for different variants
                        variant_config[factor] = available_options[i % len(available_options)]
                        varied_factors.append(factor)
            
            # Generate message for this variant
            variant_message = generate_message_content(subject, **variant_config)
            
            variants.append({
                "variant_id": variant_letters[i],
                "variant_name": f"Test Variant {variant_letters[i]}",
                "config": variant_config,
                "message": variant_message,
                "word_count": len(variant_message.split()),
                "char_count": len(variant_message),
                "is_baseline": False,
                "test_factors": varied_factors
            })
            
        return variants
    
    def display_variants(self, variants: List[Dict], subject: str):
        """Display all variants in a formatted way."""
        print("=" * 80)
        print(f"A/B TEST: {subject}")
        print(f"Test ID: {self.test_id}")
        print(f"Generated: {self.created_at}")
        print(f"Variants: {len(variants)}")
        print("=" * 80)
        
        for variant in variants:
            print(f"\n{'='*20} VARIANT {variant['variant_id']} {'='*20}")
            print(f"Name: {variant['variant_name']}")
            print(f"Config: {variant['config']}")
            if variant['test_factors']:
                print(f"Testing: {', '.join(variant['test_factors'])}")
            print(f"Stats: {variant['word_count']} words, {variant['char_count']} chars")
            print("-" * 60)
            print(variant['message'])
            print("-" * 60)
    
    def create_test_framework(self, variants: List[Dict], subject: str) -> Dict:
        """Create a complete A/B test framework with tracking structure."""
        
        test_framework = {
            "test_metadata": {
                "test_id": self.test_id,
                "subject": subject,
                "created_at": self.created_at,
                "status": "ready",
                "total_variants": len(variants)
            },
            "variants": variants,
            "tracking_template": {
                "metrics": {
                    "impressions": 0,
                    "clicks": 0,
                    "responses": 0,
                    "conversions": 0,
                    "click_through_rate": 0.0,
                    "response_rate": 0.0,
                    "conversion_rate": 0.0
                },
                "audience_segments": {
                    "total_sent": 0,
                    "demographics": {},
                    "engagement_by_time": {}
                },
                "feedback": {
                    "sentiment_scores": [],
                    "user_comments": [],
                    "quality_ratings": []
                }
            },
            "test_plan": {
                "distribution": "equal",  # equal, weighted, sequential
                "sample_size_per_variant": 100,
                "duration_days": 7,
                "success_metrics": ["click_through_rate", "response_rate"],
                "significance_threshold": 0.05
            },
            "analysis_framework": {
                "statistical_tests": ["chi_square", "t_test"],
                "confidence_level": 0.95,
                "minimum_effect_size": 0.02,
                "power": 0.8
            }
        }
        
        return test_framework
    
    def generate_deployment_code(self, variants: List[Dict], subject: str) -> str:
        """Generate sample code for deploying the A/B test."""
        
        code = f'''
# A/B Test Deployment Code
# Test ID: {self.test_id}
# Subject: {subject}

import random
from datetime import datetime

class ABTestDeployment:
    def __init__(self):
        self.test_id = "{self.test_id}"
        self.variants = {json.dumps([v["variant_id"] for v in variants])}
        self.messages = {{
{chr(10).join([f'            "{v["variant_id"]}": """{v["message"]}""",' for v in variants])}
        }}
        self.tracking = {{variant: {{"sent": 0, "opened": 0, "clicked": 0}} for variant in self.variants}}
    
    def get_variant_for_user(self, user_id: str) -> str:
        """Assign user to variant (deterministic based on user_id)."""
        random.seed(hash(user_id))
        return random.choice(self.variants)
    
    def send_message(self, user_id: str, delivery_method: str = "email"):
        """Send appropriate variant to user."""
        variant = self.get_variant_for_user(user_id)
        message = self.messages[variant]
        
        # Track sending
        self.tracking[variant]["sent"] += 1
        
        # Your delivery logic here
        print(f"Sending variant {{variant}} to {{user_id}} via {{delivery_method}}")
        print(f"Message: {{message[:100]}}...")
        
        return variant
    
    def track_engagement(self, user_id: str, action: str):
        """Track user engagement (open, click, etc.)."""
        variant = self.get_variant_for_user(user_id)
        if action in self.tracking[variant]:
            self.tracking[variant][action] += 1
        
        # Log to analytics system
        print(f"User {{user_id}} (variant {{variant}}) performed: {{action}}")
    
    def get_results(self):
        """Get current test results."""
        results = {{}}
        for variant in self.variants:
            stats = self.tracking[variant]
            sent = stats.get("sent", 0)
            opened = stats.get("opened", 0)
            clicked = stats.get("clicked", 0)
            
            results[variant] = {{
                "sent": sent,
                "opened": opened,
                "clicked": clicked,
                "open_rate": opened / sent if sent > 0 else 0,
                "click_rate": clicked / sent if sent > 0 else 0,
                "ctr": clicked / opened if opened > 0 else 0
            }}
        
        return results

# Usage example:
# test = ABTestDeployment()
# test.send_message("user123", "email")
# test.track_engagement("user123", "opened")
# test.track_engagement("user123", "clicked")
# print(test.get_results())
'''
        return code
    
    def export_test(self, variants: List[Dict], subject: str, filename: str = None):
        """Export complete A/B test data to JSON file."""
        
        if filename is None:
            filename = f"ab_test_{self.test_id}_{subject.replace(' ', '_')}.json"
        
        test_data = self.create_test_framework(variants, subject)
        
        # Add deployment code as string
        test_data["deployment_code"] = self.generate_deployment_code(variants, subject)
        
        with open(filename, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        print(f"\n✅ A/B test exported to: {filename}")
        print(f"   Test ID: {self.test_id}")
        print(f"   Variants: {len(variants)}")
        print(f"   Ready for deployment!")
        
        return filename

def main():
    """Main CLI function for A/B testing."""
    
    parser = argparse.ArgumentParser(
        description="Generate A/B test variants for message testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "voter outreach" --variants 3 --test-factors tone,length
    %(prog)s "fundraising event" --variants 2 --test-factors tone --baseline-tone persuasive
    %(prog)s "meeting reminder" --variants 4 --test-factors tone,format --export results.json
    %(prog)s "policy update" --variants 3 --test-factors tone --show-deployment --show-stats
        """
    )
    
    parser.add_argument("subject", help="Subject/topic for the message")
    parser.add_argument("--variants", type=int, default=2, 
                       help="Number of variants to generate (including baseline)")
    parser.add_argument("--test-factors", default="tone",
                       help="Comma-separated factors to test (tone,length,format,audience)")
    
    # Baseline configuration
    parser.add_argument("--baseline-tone", default="informative",
                       choices=["formal", "casual", "persuasive", "informative", "urgent", "buttigieg", "obama"])
    parser.add_argument("--baseline-length", default="medium", 
                       choices=["short", "medium", "long"])
    parser.add_argument("--baseline-format", default="general",
                       choices=["email", "sms", "social_media", "letter", "general"])
    parser.add_argument("--baseline-audience", default="general",
                       choices=["general", "technical", "executive", "youth", "seniors"])
    
    # Output options
    parser.add_argument("--export", help="Export test to JSON file")
    parser.add_argument("--show-deployment", action="store_true",
                       help="Show deployment code example")
    parser.add_argument("--show-stats", action="store_true",
                       help="Show detailed statistics for each variant")
    parser.add_argument("--quiet", action="store_true",
                       help="Minimal output (useful for scripting)")
    
    args = parser.parse_args()
    
    # Parse test factors
    test_factors = [factor.strip() for factor in args.test_factors.split(",")]
    
    # Build baseline configuration
    baseline = {
        "tone": args.baseline_tone,
        "length": args.baseline_length,
        "format": args.baseline_format,
        "audience": args.baseline_audience
    }
    
    # Create tester instance
    tester = ABMessageTester()
    
    try:
        # Generate variants
        variants = tester.generate_variants(
            subject=args.subject,
            num_variants=args.variants,
            test_factors=test_factors,
            baseline=baseline
        )
        
        if not args.quiet:
            # Display variants
            tester.display_variants(variants, args.subject)
            
            if args.show_stats:
                print(f"\n📊 VARIANT STATISTICS")
                print("-" * 40)
                for variant in variants:
                    print(f"Variant {variant['variant_id']}: {variant['word_count']} words, {variant['char_count']} chars")
                    print(f"  Config: {variant['config']}")
                    if variant['test_factors']:
                        print(f"  Testing: {', '.join(variant['test_factors'])}")
                    print()
        
        # Show deployment code if requested
        if args.show_deployment:
            print("\n" + "="*60)
            print("DEPLOYMENT CODE")
            print("="*60)
            print(tester.generate_deployment_code(variants, args.subject))
        
        # Export if requested
        if args.export:
            tester.export_test(variants, args.subject, args.export)
        
        print(f"\n✅ Generated {len(variants)} variants for A/B testing!")
        
    except Exception as e:
        print(f"Error generating A/B test: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()