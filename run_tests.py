#!/usr/bin/env python3
"""
Test runner for AI BOM Optimizer

This script runs all unit tests and provides a summary of results.
"""

import unittest
import sys
import os

def main():
    """Run all tests and display results"""
    print("🧪 Running AI BOM Optimizer Tests")
    print("=" * 50)

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary")
    print("=" * 50)

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors

    print(f"Total tests run: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")

    if failures > 0:
        print("\n❌ Test Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if errors > 0:
        print("\n💥 Test Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    if failures == 0 and errors == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)