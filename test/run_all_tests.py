#!/usr/bin/env python3
"""
Comprehensive test runner for the Precinct application.

This script runs all tests with proper configuration and reporting.
It provides options for running specific test categories and generating
coverage reports.
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(command)}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(command, check=True, capture_output=False)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ {description} completed successfully in {duration:.2f} seconds")
        return True
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"❌ {description} failed after {duration:.2f} seconds")
        print(f"Exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        print("Please ensure pytest is installed: pip install pytest")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-flask',
        'pytest-cov',
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def run_test_category(category, args):
    """Run a specific category of tests."""
    test_files = {
        'auth': 'test_auth.py',
        'security': 'test_security.py',
        'database': 'test_database.py',
        'maps': 'test_maps.py',
        'api': 'test_api.py',
        'admin': 'test_admin.py',
        'integration': 'test_integration.py',
        'performance': 'test_performance.py',
        'clustering': 'test_clustering_integration.py'
    }
    
    if category not in test_files:
        print(f"❌ Unknown test category: {category}")
        print(f"Available categories: {', '.join(test_files.keys())}")
        return False
    
    test_file = test_files[category]
    
    # Special handling for clustering integration test (standalone script)
    if category == 'clustering':
        command = ['python', f'test/{test_file}']
        return run_command(command, f"Running {category.upper()} tests")
    
    # Standard pytest command for other tests
    command = ['python', '-m', 'pytest', f'test/{test_file}', '-v']
    
    if args.coverage:
        command.extend(['--cov=.', '--cov-report=term-missing'])
    
    if args.markers:
        command.extend(['-m', args.markers])
    
    if args.verbose:
        command.append('-vv')
    
    return run_command(command, f"Running {category.upper()} tests")

def run_all_tests(args):
    """Run all test categories."""
    print("🚀 Starting comprehensive test suite...")
    
    test_categories = [
        ('auth', 'Authentication Tests'),
        ('security', 'Security Tests'),
        ('database', 'Database Tests'),
        ('maps', 'Map Functionality Tests'),
        ('api', 'API Tests'),
        ('admin', 'Admin Interface Tests'),
        ('integration', 'Integration Tests'),
        ('clustering', 'Clustering Integration Tests'),
    ]
    
    if args.include_performance:
        test_categories.append(('performance', 'Performance Tests'))
    
    results = {}
    total_start_time = time.time()
    
    for category, description in test_categories:
        print(f"\n📋 Starting {description}...")
        success = run_test_category(category, args)
        results[category] = success
        
        if not success and args.stop_on_failure:
            print(f"🛑 Stopping due to failure in {category} tests")
            break
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for category, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{category.upper():15} {status}")
    
    print(f"\nOverall: {passed_count}/{total_count} test categories passed")
    print(f"Total execution time: {total_duration:.2f} seconds")
    
    if passed_count == total_count:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

def run_coverage_report(args):
    """Generate comprehensive coverage report."""
    print("📈 Generating coverage report...")
    
    # Run tests with coverage
    command = [
        'python', '-m', 'pytest', 'test/', 
        '--cov=.', 
        '--cov-report=html',
        '--cov-report=term',
        '--cov-report=xml'
    ]
    
    if args.markers:
        command.extend(['-m', args.markers])
    
    success = run_command(command, "Generating coverage report")
    
    if success:
        print("\n📄 Coverage reports generated:")
        print("  - HTML: htmlcov/index.html")
        print("  - XML: coverage.xml")
        print("  - Terminal output above")
    
    return success

def run_quick_tests(args):
    """Run a quick subset of tests for development."""
    print("⚡ Running quick test suite (excluding slow tests)...")
    
    command = [
        'python', '-m', 'pytest', 'test/',
        '-v',
        '-m', 'not slow and not performance'
    ]
    
    if args.coverage:
        command.extend(['--cov=.', '--cov-report=term'])
    
    return run_command(command, "Running quick tests")

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for Precinct application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                          # Run all tests except performance
  python run_all_tests.py --include-performance   # Run all tests including performance
  python run_all_tests.py --category auth         # Run only authentication tests
  python run_all_tests.py --quick                 # Run quick tests (no slow/performance)
  python run_all_tests.py --coverage              # Run with coverage report
  python run_all_tests.py --markers security      # Run only security-marked tests
        """
    )
    
    parser.add_argument(
        '--category', 
        choices=['auth', 'security', 'database', 'maps', 'api', 'admin', 'integration', 'performance', 'clustering'],
        help='Run specific test category'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '--include-performance',
        action='store_true',
        help='Include performance tests (slow)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (exclude slow and performance tests)'
    )
    
    parser.add_argument(
        '--markers',
        help='Run tests with specific pytest markers (e.g., "security", "slow")'
    )
    
    parser.add_argument(
        '--stop-on-failure',
        action='store_true',
        help='Stop running tests after first category failure'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Extra verbose output'
    )
    
    parser.add_argument(
        '--coverage-only',
        action='store_true',
        help='Only generate coverage report without running individual categories'
    )
    
    args = parser.parse_args()
    
    print("🧪 Precinct Application Test Suite")
    print(f"Working directory: {os.getcwd()}")
    
    # Check dependencies (skip for clustering-only runs)
    if args.category != 'clustering' and not check_dependencies():
        print("❌ Missing required dependencies. Please install them first.")
        return 1
    
    # Handle different run modes
    success = True
    
    if args.coverage_only:
        success = run_coverage_report(args)
    elif args.quick:
        success = run_quick_tests(args)
    elif args.category:
        success = run_test_category(args.category, args)
    else:
        success = run_all_tests(args)
        
        # Generate coverage report if requested
        if args.coverage and success:
            print("\n" + "="*60)
            success = run_coverage_report(args)
    
    # Exit with appropriate code
    if success:
        print("\n🎯 Test execution completed successfully!")
        return 0
    else:
        print("\n💥 Test execution completed with failures!")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)