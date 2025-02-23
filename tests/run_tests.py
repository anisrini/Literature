import unittest
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import all tests
from tests.test_card import TestCard
from tests.test_player import TestPlayer
from tests.test_game_state import TestGameState
from tests.test_ui_components import TestUIComponents
from tests.test_game_integration import TestGameIntegration
from tests.test_visualization_integration import TestVisualizationIntegration

def create_test_suite():
    """Create and return the test suite"""
    suite = unittest.TestSuite()
    
    # Unit Tests
    unit_tests = [
        unittest.TestLoader().loadTestsFromTestCase(TestCard),
        unittest.TestLoader().loadTestsFromTestCase(TestPlayer),
        unittest.TestLoader().loadTestsFromTestCase(TestGameState),
        unittest.TestLoader().loadTestsFromTestCase(TestUIComponents),
    ]
    
    # Integration Tests
    integration_tests = [
        unittest.TestLoader().loadTestsFromTestCase(TestGameIntegration),
        unittest.TestLoader().loadTestsFromTestCase(TestVisualizationIntegration),
    ]
    
    # Add all tests to suite
    for test in unit_tests + integration_tests:
        suite.addTests(test)
    
    return suite

def run_tests():
    """Run all tests and return success status"""
    suite = create_test_suite()
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    print("\nRunning Tests...")
    print("================")
    print("\nUnit Tests:")
    print("-----------")
    result = runner.run(suite)
    
    # Print summary
    print("\nTest Summary:")
    print("=============")
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    # Print failures and errors in detail
    if result.failures or result.errors:
        print("\nDetailed Test Failures:")
        print("=======================")
        for failure in result.failures:
            print(f"\nTest: {failure[0]}")
            print(f"Error: {failure[1]}")
        
        print("\nDetailed Test Errors:")
        print("====================")
        for error in result.errors:
            print(f"\nTest: {error[0]}")
            print(f"Error: {error[1]}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\nError running tests: {str(e)}")
        sys.exit(3) 