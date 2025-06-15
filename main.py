from mcp.server.fastmcp import FastMCP
import asyncio
import base64
import sys
from loguru import logger
from vision import (
    describe_screen_interactions,
    find_element_coordinates_by_description,
    run_prompt_against_screen,
)


# Configure logging to use stderr for MCP server compatibility
# The default stderr sink is already added by loguru
# We can add additional configuration if needed
logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

# Initialize FastMCP server
mcp = FastMCP("eyemcp")


async def take_android_screenshot(device_id: str | None = None) -> str:
    """Capture a screenshot from a connected Android device using ADB.

    Args:
        device_id: Optional serial number of the target device as returned by
            ``adb devices``. If omitted, the first connected device is used.

    Returns:
        The screenshot encoded as a base64 *string* (PNG format). The raw PNG
        bytes are also stored in the module-level variable ``_latest_screenshot``.
    """

    # Build the adb command: `adb [-s SERIAL] exec-out screencap -p`
    cmd: list[str] = ["adb"]
    if device_id:
        cmd += ["-s", device_id]
    cmd += ["exec-out", "screencap", "-p"]

    # Execute the command asynchronously and capture stdout/stderr.
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"ADB screenshot command failed (exit code {process.returncode}): "
            f"{stderr.decode().strip()}"
        )
    return base64.b64encode(stdout).decode()


@mcp.tool()
async def get_view_hierarchy() -> str:
    """Get the view hierarchy of the Android screen."""
    cmd: list[str] = ["adb"]
    cmd += ["exec-out", "uiautomator", "dump", "/dev/tty"]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"ADB uiautomator dump command failed (exit code {process.returncode}): "
            f"{stderr.decode().strip()}"
        )
    return stdout.decode().strip()


@mcp.tool()
async def describe_screen() -> str:
    """Describe all interactive elements on the Android screen.

    This tool captures a screenshot from a connected Android device and uses vision AI
    to identify all interactive elements on the screen. It provides a detailed description
    of each element that can be used with find_element_by_description or tap_element_by_description.

    Unlike previous versions, this tool no longer returns coordinates. To get coordinates
    or tap elements, use the find_element_by_description or tap_element_by_description tools.

    Returns:
        A natural-language description of what is visible on the screen, including
        detailed information about each interactive element that can be used to identify
        them with other tools.
    """
    screenshot_b64: str = await take_android_screenshot()

    return describe_screen_interactions(screenshot_b64)


@mcp.tool()
async def tap_android_screen(x: int, y: int) -> str:
    """Tap the screen of a connected Android device at the specified coordinates.

    This tool sends a tap event to the specified coordinates on the Android device's screen.
    The screen dimensions are 720x1616 pixels with the origin (0,0) at the top-left corner.
    Coordinates are specified as (x,y) pairs where x is the horizontal position and y is
    the vertical position.

    Args:
        x: Horizontal pixel coordinate (0-719).
        y: Vertical pixel coordinate (0-1615).

    Returns:
        A confirmation message with the coordinates that were tapped and the device ID.
    """

    if x < 0 or y < 0:
        raise ValueError("Coordinates must be non-negative integers.")

    cmd: list[str] = ["adb"]
    cmd += ["shell", "input", "tap", str(x), str(y)]

    logger.info(f"Executing command: {cmd}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"ADB tap command failed (exit code {process.returncode}): "
            f"{stderr.decode().strip()}"
        )
    _ = stdout
    return f"Tapped at ({x}, {y})."


@mcp.tool()
async def find_element_by_description(description: str) -> dict:
    """Find an element on the Android screen matching the provided description and return its coordinates.

    This tool captures a screenshot, analyzes it using vision AI, and locates the element
    that best matches the textual description. The screen dimensions are 720x1616 pixels
    with the origin (0,0) at the top-left corner.

    Args:
        description: Textual description of the element to find (e.g., "login button",
                    "search icon in the top right", "profile picture").

    Returns:
        A dictionary containing the x and y coordinates of the center of the matching element,
        along with a confidence score and the element's description as recognized by the vision model.
        Format: {"x": int, "y": int, "confidence": float, "element_description": str}

    Raises:
        ValueError: If no matching element is found or if the description is ambiguous.
    """
    screenshot_b64: str = await take_android_screenshot()

    return find_element_coordinates_by_description(screenshot_b64, description)


@mcp.tool()
async def tap_element_by_description(description: str) -> str:
    """Find and tap an element on the Android screen that matches the provided description.

    This tool first locates the element using vision AI based on the textual description,
    then taps at the center coordinates of the matching element. The screen dimensions are
    720x1616 pixels with the origin (0,0) at the top-left corner.

    Args:
        description: Textual description of the element to tap (e.g., "login button",
                    "search icon in the top right", "profile picture").

    Returns:
        A confirmation message with details about the tapped element, including its
        coordinates and the element's description as recognized by the vision model.

    Raises:
        ValueError: If no matching element is found or if the description is ambiguous.
    """
    # First, find the element coordinates
    element_info = await find_element_by_description(description)

    # Then tap at those coordinates
    x, y = element_info["x"], element_info["y"]
    tap_result = await tap_android_screen(x, y)

    # Return a detailed confirmation message
    return f"Tapped element '{element_info['element_description']}' at coordinates ({x}, {y}) with confidence {element_info['confidence']:.2f}"


@mcp.tool()
async def analyze_screen_detail(prompt: str) -> str:
    """Analyze specific visual details on the Android screen based on a prompt.

    This tool captures a screenshot and uses vision AI to analyze specific visual
    aspects of the screen as requested in the prompt. It's useful for getting detailed
    information about UI elements' appearance, such as colors, shapes, styles, etc.

    Args:
        prompt: Specific question or instruction about visual details to analyze.
            Examples: "What color is the login button?", "Are the corners of the dialog rounded?"

    Returns:
        A detailed analysis of the requested visual aspects.
    """
    screenshot_b64: str = await take_android_screenshot()

    return run_prompt_against_screen(screenshot_b64, prompt)


@mcp.tool()
async def send_keys(text: str) -> str:
    """Send a series of keystrokes to a connected Android device.

    This tool sends the specified text as keystrokes to the Android device,
    which is useful for entering URLs, search terms, or other text input.

    Args:
        text: The text to send as keystrokes.

    Returns:
        A confirmation message with the text that was sent and the device ID.

    Raises:
        ValueError: If the text is empty.
        RuntimeError: If the ADB command fails.
    """
    if not text:
        raise ValueError("Text cannot be empty.")

    cmd: list[str] = ["adb"]
    cmd += ["shell", "input", "text", text]

    logger.info(f"Executing command: {cmd}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"ADB input text command failed (exit code {process.returncode}): "
            f"{stderr.decode().strip()}"
        )
    _ = stdout
    return f"Sent keystrokes '{text}' to device."


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
