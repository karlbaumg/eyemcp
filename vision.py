from typing import Any, Dict
import os
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv
import calibration

# Load environment variables from .env file
load_dotenv()

# Configuration options
# Provider: 'local' or 'openrouter'
PROVIDER = "openrouter"

# Model configuration
# For local provider
LOCAL_BASE_URL = "http://127.0.0.1:1234/v1"
LOCAL_API_KEY = "abcd"
LOCAL_MODEL = "se-gui-7b"

# For OpenRouter provider
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Get API key from .env file (loaded into environment variables by dotenv)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Choose your model - examples: "anthropic/claude-3-opus", "openai/gpt-4-vision", etc.
OPENROUTER_MODEL = "qwen/qwen2.5-vl-72b-instruct:free"

# Use stderr for logging in MCP server
# No need to add a logger sink as the default stderr sink is already configured in main.py


def describe_screen_interactions(screenshot_b64: str) -> str:
    """Analyze a screenshot and describe all interactive elements on the screen.

    This function uses vision AI to identify all interactive elements on the screen
    and provides a detailed description of each element. Unlike previous versions,
    this function no longer returns coordinates as those should be obtained using
    the find_element_by_description function.

    Args:
        screenshot_b64: Base64-encoded screenshot image (PNG format).

    Returns:
        A string containing detailed descriptions of all interactive elements on the screen.
    """
    data_url = f"data:image/png;base64,{screenshot_b64}"

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "You are an expert at analyzing mobile app screens. Focus on providing clear, descriptive information about UI elements that would help identify them. Provide detailed descriptions that uniquely identify each element, including its appearance, position relative to other elements, and function.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "List all interactable elements on the screen. For each element, provide a clear and detailed description that would allow it to be uniquely identified. Do NOT include coordinates in your descriptions.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
            ],
        },
    ]
    description = ""
    try:
        logger.info(f"Using provider: {PROVIDER}")

        if PROVIDER == "local":
            # Use local provider
            logger.info(f"Connecting to local model: {LOCAL_MODEL}")
            client = OpenAI(base_url=LOCAL_BASE_URL, api_key=LOCAL_API_KEY)
            model = LOCAL_MODEL
        elif PROVIDER == "openrouter":
            # Use OpenRouter
            if not OPENROUTER_API_KEY:
                raise ValueError(
                    "OPENROUTER_API_KEY not found in .env file. Please create a .env file with your API key."
                )

            logger.info(f"Connecting to OpenRouter model: {OPENROUTER_MODEL}")
            client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
            model = OPENROUTER_MODEL
        else:
            raise ValueError(f"Unknown provider: {PROVIDER}")

        logger.info("Client created")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        logger.info("Response received")
        description = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error: {e}")

    return description.strip()


def find_element_coordinates_by_description(
    screenshot_b64: str, element_description: str
) -> Dict[str, Any]:
    """Find an element on the screen matching the provided description and return its coordinates.

    This function uses vision AI to analyze a screenshot and locate the element
    that best matches the textual description provided. The returned coordinates
    are automatically adjusted using the calibration scaling factors if calibration
    has been performed.

    Args:
        screenshot_b64: Base64-encoded screenshot image (PNG format).
        element_description: Textual description of the element to find (e.g., "login button",
                           "search icon in the top right", "profile picture").

    Returns:
        A dictionary containing the x and y coordinates of the center of the matching element,
        along with a confidence score and the element's description as recognized by the vision model.
        Format: {"x": int, "y": int, "confidence": float, "element_description": str}
        Note: The coordinates are adjusted using calibration scaling factors if available.

    Raises:
        ValueError: If no matching element is found or if the description is ambiguous.
    """
    data_url = f"data:image/png;base64,{screenshot_b64}"

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "You are an expert at analyzing mobile app screens. The dimensions of the screen are 720 pixels wide by 1616 pixels high. The origin (0,0) is at the top left corner. Coordinates are specified in pixels, with x-coordinate first, then y-coordinate. Your task is to find a specific UI element based on a textual description and provide its exact center coordinates.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f'Find the element on the screen that matches this description: \'{element_description}\'. Return ONLY a JSON object with the following format: {{"x": int, "y": int, "confidence": float, "element_description": "string"}}. The confidence should be between 0.0 and 1.0, where 1.0 means you\'re absolutely certain you\'ve found the correct element. If you cannot find a matching element, return {{"error": "Element not found"}}. If the description is ambiguous and matches multiple elements, return {{"error": "Ambiguous description"}}.',
                },
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
            ],
        },
    ]

    try:
        logger.info(f"Using provider: {PROVIDER}")

        if PROVIDER == "local":
            # Use local provider
            logger.info(f"Connecting to local model: {LOCAL_MODEL}")
            client = OpenAI(base_url=LOCAL_BASE_URL, api_key=LOCAL_API_KEY)
            model = LOCAL_MODEL
        elif PROVIDER == "openrouter":
            # Use OpenRouter
            if not OPENROUTER_API_KEY:
                raise ValueError(
                    "OPENROUTER_API_KEY not found in .env file. Please create a .env file with your API key."
                )

            logger.info(f"Connecting to OpenRouter model: {OPENROUTER_MODEL}")
            client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
            model = OPENROUTER_MODEL
        else:
            raise ValueError(f"Unknown provider: {PROVIDER}")

        logger.info("Client created")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        logger.info("Response received")

        # Parse the JSON response
        import json

        result = json.loads(response.choices[0].message.content)

        # Check for error conditions
        if "error" in result:
            raise ValueError(result["error"])

        # Validate the response format
        required_keys = ["x", "y", "confidence", "element_description"]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Invalid response format: missing '{key}' field")

        # Ensure coordinates are integers
        result["x"] = int(result["x"])
        result["y"] = int(result["y"])

        # Ensure confidence is a float between 0 and 1
        result["confidence"] = float(result["confidence"])
        if not 0 <= result["confidence"] <= 1:
            result["confidence"] = max(0, min(result["confidence"], 1))

        # Apply calibration scaling if calibrated
        if calibration.is_calibrated():
            original_x, original_y = result["x"], result["y"]
            scaled_x, scaled_y = calibration.apply_scaling(original_x, original_y)
            result["x"], result["y"] = scaled_x, scaled_y
            logger.info(
                f"Applied calibration scaling: ({original_x}, {original_y}) -> ({scaled_x}, {scaled_y})"
            )
        else:
            logger.info("No calibration applied (system not calibrated)")

        return result

    except Exception as e:
        logger.error(f"Error finding element: {e}")
        raise ValueError(f"Failed to find element: {str(e)}")
