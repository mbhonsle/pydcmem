#!/usr/bin/env python3
"""
Simple test runner script for pydcmem.
"""

import sys
import subprocess
import os


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"\n✅ {description} completed successfully")
        return True


def main():
    """Main test runner."""
    print("🧪 PyDCMem Test Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Error: pyproject.toml not found. Please run from project root.")
        sys.exit(1)
    
    # Install development dependencies if needed
    if "--install-dev" in sys.argv:
        if not run_command(["pip", "install", "-e", ".[dev]"], "Installing development dependencies"):
            sys.exit(1)
    
    # Run different test suites based on arguments
    test_type = "unit"
    if len(sys.argv) > 1:
        if "integration" in sys.argv:
            test_type = "integration"
        elif "all" in sys.argv:
            test_type = "all"
    
    success = True
    
    if test_type in ["unit", "all"]:
        success &= run_command(["pytest", "-m", "not integration", "-v"], "Unit Tests")
    
    if test_type in ["integration", "all"]:
        # Check for required environment variables
        required_env_vars = ["OPENAI_API_KEY", "MEMORY_DLO", "MEMORY_CONNECTOR"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"\n⚠️  Warning: Missing environment variables for integration tests: {missing_vars}")
            print("Integration tests will be skipped.")
        else:
            success &= run_command(["pytest", "-m", "integration", "-v"], "Integration Tests")
    
    if test_type == "all":
        success &= run_command(["pytest", "--cov=src/pydc_mem", "--cov-report=term-missing"], "Coverage Report")
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
