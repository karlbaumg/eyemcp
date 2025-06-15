# Testing Guide for EyeMCP

This document provides information about the test suite for the EyeMCP project, including how to run tests, what is being tested, and how to add new tests.

## Test Structure

The test suite is organized into three main files:

1. **test_main.py**: Tests for the MCP server tools and ADB interactions in `main.py`
2. **test_vision.py**: Tests for the vision AI functionality in `vision.py`
3. **test_calibration.py**: Tests for the coordinate calibration system in `calibration.py`

## Running Tests

To run the entire test suite:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_main.py
```

To run a specific test:

```bash
pytest tests/test_main.py::test_describe_screen
```

To run tests with verbose output:

```bash
pytest -v
```

## Test Coverage

### Main Module Tests (`test_main.py`)

- **take_android_screenshot**: Tests capturing screenshots from Android devices
- **describe_screen**: Tests the screen description functionality
- **tap_android_screen**: Tests tapping at specific coordinates
- **find_element_by_description**: Tests finding elements by description
- **tap_element_by_description**: Tests tapping elements by description
- **calibrate**: Tests the calibration process

### Vision Module Tests (`test_vision.py`)

- **describe_screen_interactions**: Tests analyzing screenshots and describing interactive elements
- **find_element_coordinates_by_description**: Tests finding element coordinates by description
- Error handling tests for both functions

### Calibration Module Tests (`test_calibration.py`)

- **get_scaling_factors**: Tests retrieving scaling factors
- **is_calibrated**: Tests checking calibration status
- **apply_scaling**: Tests applying scaling to coordinates
- **load_calibration_data**: Tests loading calibration data from CSV files
- **go_to_home_screen**: Tests navigating to the home screen
- **calculate_scaling_factors**: Tests calculating scaling factors

## Mocking Strategy

The tests use Python's `unittest.mock` library to mock external dependencies:

1. **ADB Commands**: All ADB interactions are mocked to avoid requiring a real Android device
2. **Vision AI API**: OpenAI API calls are mocked to avoid requiring API keys and network access
3. **File Operations**: File operations are mocked using `mock_open`

## Adding New Tests

When adding new tests, follow these guidelines:

1. **Test Naming**: Use descriptive names that clearly indicate what is being tested
2. **Test Organization**: Add tests to the appropriate file based on what module they test
3. **Mocking**: Mock all external dependencies to ensure tests can run in any environment
4. **Assertions**: Include clear assertions that verify the expected behavior
5. **Error Cases**: Test both success and error cases

### Example Test Structure

```python
@pytest.mark.asyncio  # For async functions
async def test_function_name():
    """Test description explaining what is being tested."""
    # Setup mocks
    with patch("module.dependency", mock_value):
        # Call the function being tested
        result = await function_being_tested()
        
        # Assert expected behavior
        assert result == expected_value
```

## Test Configuration

The test configuration is defined in `conftest.py` and `pyproject.toml`:

- **conftest.py**: Provides fixtures for the test suite, including the event loop for asyncio tests
- **pyproject.toml**: Configures pytest options, including test paths and asyncio mode

## Continuous Integration

When setting up CI for this project, ensure that:

1. All dependencies are installed
2. The test environment has Python 3.12 or higher
3. No actual Android device or API keys are required to run tests

## Troubleshooting Tests

If tests are failing, check:

1. **Mock Configuration**: Ensure mocks are correctly set up
2. **Async Tests**: Make sure async tests are properly decorated with `@pytest.mark.asyncio`
3. **Dependencies**: Verify all test dependencies are installed
