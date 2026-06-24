"""
Kapruka Sales Agent - Test Runner

Runs all tests in the tests/ directory.
Usage:
    python run_tests.py
    python run_tests.py tests/test_helpers.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if len(sys.argv) > 1:
    test_file = sys.argv[1]
    print(f"Running: {test_file}")
    loader = unittest.TestLoader()
    suite = loader.discover(str(Path(test_file).parent), pattern=Path(test_file).name)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
else:
    print("Running all tests...")
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

sys.exit(0 if result.wasSuccessful() else 1)
