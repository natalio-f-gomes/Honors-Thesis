# Lambda Function Test Suite

This test suite is organized into multiple files based on functionality for better maintainability and organization.

## Test Files

### 1. `test_utils.py`
Utility function tests including:
- **TestDecimalConversion**: Converting Decimal objects to int/float
- **TestCORSResponse**: CORS response structure and headers
- **TestS3PathParsing**: Parsing S3 bucket paths
- **TestJSONParsing**: Parsing Claude AI JSON responses (with/without markdown)

### 2. `test_validation.py`
Input validation tests including:
- **TestEmailValidation**: Email format validation
- **TestRatingValidation**: Rating (1-5) validation
- **TestMessageLengthValidation**: Message length constraints
- **TestRequiredFieldsValidation**: Required field presence checks
- **TestJobSearchParametersValidation**: Job search parameter validation

### 3. `test_resume_management.py`
Resume-related functionality tests including:
- **TestResumeNumbering**: Resume numbering logic and limit enforcement
- **TestResumeIDGeneration**: Resume ID format generation
- **TestResumeDataFormatting**: Resume metadata formatting and sorting

### 4. `test_event_handling.py`
Lambda event handling tests including:
- **TestOptionsRequestHandling**: CORS preflight (OPTIONS) requests
- **TestEventDataExtraction**: Extracting user info and query parameters from events

### 5. `test_ai_integration.py`
Claude AI and prompt-related tests including:
- **TestPromptCreation**: Creating prompts with resume and job data
- **TestJobSearchQuery**: Building job search queries

### 6. `test_messaging.py`
SNS and notification tests including:
- **TestSNSMessageFormatting**: Contact form message formatting
- **TestFeedbackFormatting**: Star rating display

### 7. `test_error_handling.py`
Error handling pattern tests including:
- **TestErrorHandling**: Item not found, empty list searches, successful retrieval

## Running Tests

### Run All Tests
```bash
python run_all_tests.py
```

### Run Individual Test Files
```bash
python -m unittest test_utils
python -m unittest test_validation
python -m unittest test_resume_management
python -m unittest test_event_handling
python -m unittest test_ai_integration
python -m unittest test_messaging
python -m unittest test_error_handling
```

### Run Specific Test Class
```bash
python -m unittest test_utils.TestDecimalConversion
python -m unittest test_validation.TestEmailValidation
```

### Run Specific Test Method
```bash
python -m unittest test_utils.TestDecimalConversion.test_decimal_to_int
```

## Test Structure

Each test file follows this structure:
- Import necessary modules
- Define test classes (one per logical component)
- Each test class contains multiple test methods
- Test methods include inline function definitions being tested
- Clear, descriptive test names and docstrings

## Dependencies

The test suite mocks the following external dependencies:
- `boto3` (AWS SDK)
- `PyPDF2` (PDF processing)
- `anthropic` (Claude AI SDK)
- `requests` (HTTP library)

These are mocked in `run_all_tests.py` to allow tests to run without AWS credentials or external service access.

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Clarity**: Test names clearly describe what is being tested
3. **Coverage**: Tests cover both success and failure cases
4. **Documentation**: Each test class and method includes docstrings
5. **Organization**: Related tests are grouped into logical files

## Adding New Tests

When adding new tests:
1. Determine which category the test belongs to
2. Add the test to the appropriate file
3. If creating a new category, create a new test file
4. Update `run_all_tests.py` to import and include the new tests
5. Update this README with the new test information
