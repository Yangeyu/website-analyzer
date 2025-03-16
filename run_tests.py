#!/usr/bin/env python3
"""
Test runner for website-analyzer.
This script runs all tests using pytest and generates a test report.
"""
import os
import sys
import json
import datetime
import subprocess
from pathlib import Path

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Test directory
TEST_DIR = Path(__file__).parent / "tests"
OUTPUT_DIR = Path(__file__).parent / "test_reports"


def run_tests():
    """Run all tests with pytest and generate a report."""
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Create timestamp for report
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define report files
    json_report = str(OUTPUT_DIR / f"pytest_report_{timestamp}.json")
    html_report = str(OUTPUT_DIR / f"pytest_report_{timestamp}.html")
    coverage_dir = str(OUTPUT_DIR / f"coverage_{timestamp}")
    
    # Run pytest with coverage and generate reports
    cmd = [
        "python", "-m", "pytest",
        "-v",
        "--cov=src",
        "--cov-report=term",
        f"--cov-report=html:{coverage_dir}",
        f"--json={json_report}",
        f"--html={html_report}",
        str(TEST_DIR)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Generate a summary report
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "exit_code": result.returncode,
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "report_files": {
                "json": json_report,
                "html": html_report,
                "coverage": coverage_dir
            }
        }
        
        # Save summary to file
        summary_file = OUTPUT_DIR / f"test_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(report, f, indent=2)
        
        # Print report summary
        print("\n" + "=" * 80)
        print(f"TEST REPORT: {timestamp}")
        print("=" * 80)
        print(f"Exit code: {result.returncode}")
        print(f"HTML report: {html_report}")
        print(f"JSON report: {json_report}")
        print(f"Coverage report: {coverage_dir}")
        print(f"Summary: {summary_file}")
        print("=" * 80)
        
        # Print short stdout summary
        print("\nTest Output Summary:")
        print("-" * 40)
        
        # Show last few lines of output if available
        output_lines = result.stdout.strip().split("\n")
        for line in output_lines[-10:]:
            print(line)
            
        print("=" * 80)
        
    except Exception as e:
        print(f"Error running tests: {e}")


if __name__ == "__main__":
    sys.exit(run_tests()) 