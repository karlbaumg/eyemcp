import pytest
from unittest.mock import patch, MagicMock
import json
from vision import (
    describe_screen_interactions,
    find_element_coordinates_by_description,
    run_prompt_against_screen,
)


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


@pytest.fixture
def mock_openai_text_client():
    """Create a mock OpenAI client that returns text responses with coordinates."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Set up the mock response structure with text content containing coordinates
    mock_message.content = """
    I found the element you described. It appears to be a button in the middle of the screen.
    The coordinates are x: 150 and y: 250. My confidence level is 0.85 that this is the correct element.
    """
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


def test_find_element_coordinates_from_text(mock_openai_text_client):
    """Test that find_element_coordinates_by_description can extract coordinates from text responses."""
    with (
        patch("vision.OpenAI", return_value=mock_openai_text_client),
        patch("vision.PROVIDER", "openrouter"),
        patch("vision.OPENROUTER_API_KEY", "test_key"),
    ):

        # Call the function with a mock screenshot and description
        result = find_element_coordinates_by_description(
            "mock_screenshot_base64", "button"
        )

        # Check that the client was called with the correct parameters
        mock_openai_text_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_openai_text_client.chat.completions.create.call_args

        # Check that the model is set correctly
        assert kwargs["model"] is not None

        # Check that the messages contain the screenshot and description
        messages = kwargs["messages"]
        user_message = [m for m in messages if m["role"] == "user"][0]
        assert "button" in user_message["content"][0]["text"]
        assert "image_url" in user_message["content"][1]

        # Check that the result contains the expected fields extracted from text
        assert result["x"] == 150
        assert result["y"] == 250
        assert result["confidence"] == 0.85
        assert result["element_description"] == "button"


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


def test_find_element_coordinates_text_error_response():
    """Test that find_element_coordinates_by_description handles text error responses correctly."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Set up the mock response structure with a text error
    mock_message.content = "I'm sorry, but I couldn't find any element matching that description. Element not found."
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


def test_find_element_coordinates_missing_coordinates():
    """Test that find_element_coordinates_by_description handles responses with missing coordinates."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Set up the mock response structure with missing coordinates
    mock_message.content = "I found the button you're looking for. It's a blue button in the center of the screen."
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    with (
        patch("vision.OpenAI", return_value=mock_client),
        patch("vision.PROVIDER", "openrouter"),
        patch("vision.OPENROUTER_API_KEY", "test_key"),
    ):

        # Call the function and check that it raises the expected error
        with pytest.raises(ValueError, match="Could not find x coordinate in response"):
            find_element_coordinates_by_description("mock_screenshot_base64", "button")


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


def test_analyze_screen_detail(mock_openai_client):
    """Test that analyze_screen_detail calls the OpenAI API correctly and returns the response."""
    with (
        patch("vision.OpenAI", return_value=mock_openai_client),
        patch("vision.PROVIDER", "openrouter"),
        patch("vision.OPENROUTER_API_KEY", "test_key"),
    ):

        # Call the function with a mock screenshot and prompt
        result = run_prompt_against_screen(
            "mock_screenshot_base64", "What color is the login button?"
        )

        # Check that the client was called with the correct parameters
        mock_openai_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_openai_client.chat.completions.create.call_args

        # Check that the model is set correctly
        assert kwargs["model"] is not None

        # Check that the messages contain the screenshot and prompt
        messages = kwargs["messages"]
        user_message = [m for m in messages if m["role"] == "user"][0]
        assert "What color is the login button?" in user_message["content"][0]["text"]
        assert "image_url" in user_message["content"][1]

        # Check that the result is the mock response
        assert result == "Mock response content"


def test_analyze_screen_detail_error_handling():
    """Test that analyze_screen_detail handles errors correctly."""
    with (
        patch("vision.OpenAI", side_effect=Exception("API Error")),
        patch("vision.logger.error") as mock_logger,
    ):

        # Call the function with a mock screenshot and prompt
        result = run_prompt_against_screen(
            "mock_screenshot_base64", "What color is the login button?"
        )

        # Check that the error was logged
        mock_logger.assert_called_once()

        # Check that an error message is returned
        assert "Error analyzing screen detail" in result


def test_find_element_coordinates_api_error():
    """Test that find_element_coordinates_by_description handles API errors correctly."""
    with patch("vision.OpenAI", side_effect=Exception("API Error")):

        # Call the function and check that it raises the expected error
        with pytest.raises(ValueError, match="Failed to find element"):
            find_element_coordinates_by_description("mock_screenshot_base64", "button")
