#!/usr/bin/env python3
"""
Campaign Message Workflow
==========================

Complete workflow for campaign message generation, A/B testing, and analysis.

Usage:
    python campaign_workflow.py create --subject "Volunteer Drive" --variants 3
    python campaign_workflow.py deploy volunteer_drive_ab_test.json
    python campaign_workflow.py track volunteer_drive_ab_test.json --sent A 200 B 200 C 200
    python campaign_workflow.py analyze volunteer_drive_ab_test.json
"""

import argparse
import json
import sys
import subprocess
from datetime import datetime
from typing import List, Dict, Any

class CampaignWorkflow:
    """Manage complete campaign message workflow."""
    
    def __init__(self):
        self.message_generator = "message_generator_cli.py"
        self.ab_tester = "ab_message_tester.py"
        self.results_tracker = "ab_results_tracker.py"
    
    def create_campaign(self, subject: str, variants: int = 3, 
                       test_factors: List[str] = None, **kwargs):
        """Create a new A/B test campaign."""
        print(f"🚀 Creating campaign: {subject}")
        print(f"   Variants: {variants}")
        
        # Default test factors
        if test_factors is None:
            test_factors = ["tone", "format"]
        
        # Build command for A/B tester
        cmd = [
            "python", self.ab_tester,
            subject,
            "--variants", str(variants),
            "--test-factors", ",".join(test_factors)
        ]
        
        # Add optional parameters
        if kwargs.get("length"):
            cmd.extend(["--length", kwargs["length"]])
        if kwargs.get("audience"):
            cmd.extend(["--audience", kwargs["audience"]])
        
        # Auto-generate export filename if not provided
        export_file = kwargs.get("export")
        if not export_file:
            # Create safe filename from subject
            safe_subject = subject.lower().replace(" ", "_").replace("-", "_")
            export_file = f"{safe_subject}_ab_test.json"
        
        cmd.extend(["--export", export_file])
        
        # Run A/B test creation
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Campaign created successfully!")
            print(result.stdout)
        else:
            print("❌ Error creating campaign:")
            print(result.stderr)
            return False
        
        return True
    
    def deploy_campaign(self, test_file: str):
        """Generate deployment code for campaign."""
        print(f"📦 Generating deployment code for {test_file}")
        
        cmd = ["python", self.ab_tester, "--load", test_file, "--deployment-code"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Deployment code generated!")
            print(result.stdout)
        else:
            print("❌ Error generating deployment code:")
            print(result.stderr)
            return False
        
        return True
    
    def track_results(self, test_file: str, results: Dict[str, Dict[str, int]]):
        """Add tracking results to campaign."""
        print(f"📊 Adding results to {test_file}")
        
        cmd_base = ["python", self.results_tracker, test_file]
        
        for variant_id, metrics in results.items():
            for metric, value in metrics.items():
                cmd = cmd_base + ["--add-result", variant_id, metric, str(value)]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ Error adding {metric} for variant {variant_id}:")
                    print(result.stderr)
                    return False
        
        print("✅ Results added successfully!")
        return True
    
    def analyze_campaign(self, test_file: str, export: str = None):
        """Analyze campaign results."""
        print(f"🔬 Analyzing campaign: {test_file}")
        
        cmd = ["python", self.results_tracker, test_file, "--analyze"]
        
        if export:
            cmd.extend(["--export", export])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            if export:
                print(f"✅ Analysis exported to {export}")
        else:
            print("❌ Error analyzing campaign:")
            print(result.stderr)
            return False
        
        return True
    
    def campaign_status(self, test_file: str):
        """Show campaign status and next steps."""
        try:
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            print(f"📋 CAMPAIGN STATUS: {data['test_metadata']['subject']}")
            print(f"   Test ID: {data['test_metadata']['test_id']}")
            created_field = data['test_metadata'].get('created_date') or data['test_metadata'].get('created_at')
            print(f"   Created: {created_field}")
            print(f"   Variants: {len(data['variants'])}")
            
            # Check if results exist
            if 'results' in data:
                total_sent = sum(variant_results.get('sent', 0) 
                               for variant_results in data['results'].values())
                if total_sent > 0:
                    print(f"   Status: 📊 Results tracking active ({total_sent} total sent)")
                    print("   Next steps: Add more results or analyze")
                else:
                    print("   Status: 🚀 Ready for deployment")
                    print("   Next steps: Deploy and start tracking results")
            else:
                print("   Status: 📝 Test created, needs deployment")
                print("   Next steps: Generate deployment code")
            
            return True
        except FileNotFoundError:
            print(f"❌ Campaign file {test_file} not found!")
            return False
        except json.JSONDecodeError:
            print(f"❌ Invalid campaign file: {test_file}")
            return False
    
    def list_campaigns(self):
        """List all available campaign files."""
        import glob
        
        json_files = glob.glob("*_ab_test.json")
        
        if not json_files:
            print("📁 No campaign files found")
            print("   Create a new campaign with: python campaign_workflow.py create")
            return
        
        print("📁 AVAILABLE CAMPAIGNS")
        print("-" * 50)
        
        for file in sorted(json_files):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                subject = data['test_metadata']['subject']
                test_id = data['test_metadata']['test_id']
                created_field = data['test_metadata'].get('created_date') or data['test_metadata'].get('created_at')
                variants = len(data['variants'])
                
                # Check status
                if 'results' in data:
                    total_sent = sum(variant_results.get('sent', 0) 
                                   for variant_results in data['results'].values())
                    status = f"📊 Active ({total_sent} sent)" if total_sent > 0 else "🚀 Ready"
                else:
                    status = "📝 Created"
                
                print(f"{file}")
                print(f"  Subject: {subject}")
                print(f"  ID: {test_id}")
                print(f"  Variants: {variants}")
                print(f"  Status: {status}")
                print(f"  Created: {created_field}")
                print()
                
            except (json.JSONDecodeError, KeyError):
                print(f"{file} (invalid)")

def main():
    """Main CLI function for campaign workflow."""
    
    parser = argparse.ArgumentParser(
        description="Complete campaign message workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
    create      Create new A/B test campaign
    deploy      Generate deployment code
    track       Add tracking results
    analyze     Analyze campaign results
    status      Show campaign status
    list        List all campaigns

Examples:
    %(prog)s create --subject "Volunteer Drive" --variants 3
    %(prog)s deploy volunteer_drive_ab_test.json
    %(prog)s track test.json --sent A 200 B 200 --opened A 85 B 92
    %(prog)s analyze test.json
    %(prog)s status test.json
    %(prog)s list
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new campaign")
    create_parser.add_argument("--subject", required=True, help="Campaign subject")
    create_parser.add_argument("--variants", type=int, default=3, help="Number of variants")
    create_parser.add_argument("--test-factors", nargs="+", 
                             choices=["tone", "length", "format", "audience"],
                             default=["tone", "format"], help="Factors to test")
    create_parser.add_argument("--length", choices=["short", "medium", "long"],
                             help="Message length")
    create_parser.add_argument("--audience", help="Target audience")
    create_parser.add_argument("--export", help="Export filename")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Generate deployment code")
    deploy_parser.add_argument("test_file", help="A/B test JSON file")
    
    # Track command
    track_parser = subparsers.add_parser("track", help="Add tracking results")
    track_parser.add_argument("test_file", help="A/B test JSON file")
    track_parser.add_argument("--sent", nargs="+", help="Sent counts: variant count ...")
    track_parser.add_argument("--opened", nargs="+", help="Opened counts: variant count ...")
    track_parser.add_argument("--clicked", nargs="+", help="Clicked counts: variant count ...")
    track_parser.add_argument("--responded", nargs="+", help="Response counts: variant count ...")
    track_parser.add_argument("--converted", nargs="+", help="Conversion counts: variant count ...")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze campaign results")
    analyze_parser.add_argument("test_file", help="A/B test JSON file")
    analyze_parser.add_argument("--export", help="Export analysis to file")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show campaign status")
    status_parser.add_argument("test_file", help="A/B test JSON file")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all campaigns")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    workflow = CampaignWorkflow()
    
    if args.command == "create":
        success = workflow.create_campaign(
            subject=args.subject,
            variants=args.variants,
            test_factors=args.test_factors,
            length=args.length,
            audience=args.audience,
            export=args.export
        )
        sys.exit(0 if success else 1)
    
    elif args.command == "deploy":
        success = workflow.deploy_campaign(args.test_file)
        sys.exit(0 if success else 1)
    
    elif args.command == "track":
        # Parse tracking data
        results = {}
        
        for metric in ["sent", "opened", "clicked", "responded", "converted"]:
            metric_data = getattr(args, metric)
            if metric_data and len(metric_data) % 2 == 0:
                for i in range(0, len(metric_data), 2):
                    variant = metric_data[i]
                    count = int(metric_data[i + 1])
                    
                    if variant not in results:
                        results[variant] = {}
                    results[variant][metric] = count
        
        if results:
            success = workflow.track_results(args.test_file, results)
            sys.exit(0 if success else 1)
        else:
            print("❌ No valid tracking data provided")
            sys.exit(1)
    
    elif args.command == "analyze":
        success = workflow.analyze_campaign(args.test_file, args.export)
        sys.exit(0 if success else 1)
    
    elif args.command == "status":
        success = workflow.campaign_status(args.test_file)
        sys.exit(0 if success else 1)
    
    elif args.command == "list":
        workflow.list_campaigns()

if __name__ == "__main__":
    main()