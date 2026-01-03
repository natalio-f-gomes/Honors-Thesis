#!/usr/bin/env python3
"""
Main test runner for all Lambda function tests.
Imports and runs all test suites from separate test files.
"""

import unittest
import sys
from unittest.mock import MagicMock

# Mock AWS services before importing test modules
sys.modules['boto3'] = MagicMock()
sys.modules['PyPDF2'] = MagicMock()
sys.modules['anthropic'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Import all test modules
from test_utils import (
    TestDecimalConversion,
    TestCORSResponse,
    TestS3PathParsing,
    TestJSONParsing
)
from test_validation import (
    TestEmailValidation,
    TestRatingValidation,
    TestMessageLengthValidation,
    TestRequiredFieldsValidation,
    TestJobSearchParametersValidation
)
from test_resume_management import (
    TestResumeNumbering,
    TestResumeIDGeneration,
    TestResumeDataFormatting
)
from test_event_handling import (
    TestOptionsRequestHandling,
    TestEventDataExtraction
)
from test_ai_integration import (
    TestPromptCreation,
    TestJobSearchQuery
)
from test_messaging import (
    TestSNSMessageFormatting,
    TestFeedbackFormatting
)
from test_error_handling import TestErrorHandling


def create_test_suite():
    """Create a test suite containing all test cases"""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add all test classes
    test_classes = [
        # Utils tests
        TestDecimalConversion,
        TestCORSResponse,
        TestS3PathParsing,
        TestJSONParsing,
        
        # Validation tests
        TestEmailValidation,
        TestRatingValidation,
        TestMessageLengthValidation,
        TestRequiredFieldsValidation,
        TestJobSearchParametersValidation,
        
        # Resume management tests
        TestResumeNumbering,
        TestResumeIDGeneration,
        TestResumeDataFormatting,
        
        # Event handling tests
        TestOptionsRequestHandling,
        TestEventDataExtraction,
        
        # AI integration tests
        TestPromptCreation,
        TestJobSearchQuery,
        
        # Messaging tests
        TestSNSMessageFormatting,
        TestFeedbackFormatting,
        
        # Error handling tests
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_tests():
    """Run all tests with detailed output"""
    print("=" * 80)
    print("RUNNING UNIT TESTS FOR LAMBDA FUNCTIONS")
    print("=" * 80)
    print()
    
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
