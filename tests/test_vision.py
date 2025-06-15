import pytest
from unittest.mock import patch, MagicMock
import json
from vision import describe_screen_interactions, find_element_coordinates_by_description


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Set up the mock response structure
    mock_message.content = "Mock response content"
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    return mock_client


@pytest.fixture
def mock_openai_json_client():
    """Create a mock OpenAI client that returns JSON responses."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Set up the mock response structure with JSON content
    mock_message.content = json.dumps(
        {"x": 100, "y": 200, "confidence": 0.9, "element_description": "Mock element"}
    )
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    return mock_client


def test_describe_screen_interactions(mock_openai_client):
    """Test that describe_screen_interactions calls the OpenAI API correctly and returns the response."""
    with (
        patch("vision.OpenAI", return_value=mock_openai_client),
        patch("vision.PROVIDER", "openrouter"),
        patch("vision.OPENROUTER_API_KEY", "test_key"),
    ):

        # Call the function with a mock screenshot
        result = describe_screen_interactions("mock_screenshot_base64")

        # Check that the client was called with the correct parameters
        mock_openai_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_openai_client.chat.completions.create.call_args

        # Check that the model is set correctly
        assert kwargs["model"] is not None

        # Check that the messages contain the screenshot
        messages = kwargs["messages"]
        assert any(
            "image_url" in content.get("content", [{}])[1]
            for content in messages
            if isinstance(content.get("content", []), list)
        )

        # Check that the result is the mock response
        assert result == "Mock response content"


def test_describe_screen_interactions_error_handling():
    """Test that describe_screen_interactions handles errors correctly."""
    with (
        patch("vision.OpenAI", side_effect=Exception("API Error")),
        patch("vision.logger.error") as mock_logger,
    ):

        # Call the function with a mock screenshot
        result = describe_screen_interactions("mock_screenshot_base64")

        # Check that the error was logged
        mock_logger.assert_called_once()

        # Check that an empty string is returned on error
        assert result == ""


def test_find_element_coordinates_by_description(mock_openai_json_client):
    """Test that find_element_coordinates_by_description calls the OpenAI API correctly and returns the parsed response."""
    with (
        patch("vision.OpenAI", return_value=mock_openai_json_client),
        patch("vision.PROVIDER", "openrouter"),
        patch("vision.OPENROUTER_API_KEY", "test_key"),
        patch("vision.calibration.is_calibrated", return_value=False),
    ):

        # Call the function with a mock screenshot and description
        result = find_element_coordinates_by_description(
            "mock_screenshot_base64", "button"
        )

        # Check that the client was called with the correct parameters
        mock_openai_json_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_openai_json_client.chat.completions.create.call_args

        # Check that the model is set correctly
        assert kwargs["model"] is not None

        # Check that response_format is set to json_object
        assert kwargs["response_format"] == {"type": "json_object"}

        # Check that the messages contain the screenshot and description
        messages = kwargs["messages"]
        user_message = [m for m in messages if m["role"] == "user"][0]
        assert "button" in user_message["content"][0]["text"]
        assert "image_url" in user_message["content"][1]

        # Check that the result contains the expected fields
        assert result["x"] == 100
        assert result["y"] == 200
        assert result["confidence"] == 0.9
        assert result["element_description"] == "Mock element"


def test_find_element_coordinates_with_calibration(mock_openai_json_client):
    """Test that find_element_coordinates_by_description applies calibration scaling when calibrated."""
    with (
        patch("vision.OpenAI", return_value=mock_openai_json_client),
        patch("vision.PROVIDER", "openrouter"),
        patch("vision.OPENROUTER_API_KEY", "test_key"),
        patch("vision.calibration.is_calibrated", return_value=True),
        patch("vision.calibration.apply_scaling", return_value=(150, 300)),
    ):

        # Call the function with a mock screenshot and description
        result = find_element_coordinates_by_description(
            "mock_screenshot_base64", "button"
        )

        # Check that calibration scaling was applied
        assert result["x"] == 150
        assert result["y"] == 300


def test_find_element_coordinates_error_response():
    """Test that find_element_coordinates_by_description handles error responses correctly."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Set up the mock response structure with an error
    mock_message.content = json.dumps({"error": "Element not found"})
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    with (
        patch("vision.OpenAI", return_value=mock_client),
        patch("vision.PROVIDER", "openrouter"),
        patch("vision.OPENROUTER_API_KEY", "test_key"),
    ):

        # Call the function and check that it raises the expected error
        with pytest.raises(ValueError, match="Element not found"):
            find_element_coordinates_by_description(
                "mock_screenshot_base64", "nonexistent button"
            )


def test_find_element_coordinates_invalid_response():
    """Test that find_element_coordinates_by_description handles invalid responses correctly."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Set up the mock response structure with an invalid response (missing required fields)
    mock_message.content = json.dumps(
        {"x": 100, "y": 200}
    )  # Missing confidence and element_description
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    with (
        patch("vision.OpenAI", return_value=mock_client),
        patch("vision.PROVIDER", "openrouter"),
        patch("vision.OPENROUTER_API_KEY", "test_key"),
    ):

        # Call the function and check that it raises the expected error
        with pytest.raises(ValueError, match="Invalid response format"):
            find_element_coordinates_by_description("mock_screenshot_base64", "button")


def test_find_element_coordinates_api_error():
    """Test that find_element_coordinates_by_description handles API errors correctly."""
    with patch("vision.OpenAI", side_effect=Exception("API Error")):

        # Call the function and check that it raises the expected error
        with pytest.raises(ValueError, match="Failed to find element"):
            find_element_coordinates_by_description("mock_screenshot_base64", "button")
