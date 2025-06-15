from mcp.server.fastmcp import FastMCP, Image
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
mcp.description = """Android device control via ADB with intelligent screen interaction.

RECOMMENDED WORKFLOW:
1. PRIMARY: inspect_screen_structure → extract coordinates from bounds → tap_screen
2. FALLBACK: If step 1 fails, use describe_visible_elements → tap_element_fallback

The view hierarchy (inspect_screen_structure) is 10x faster and more reliable than vision-based tools.
Only use vision tools for custom-drawn elements, games, or when the view hierarchy lacks information.

Example coordinate extraction from view hierarchy:
- Look for 'bounds' attribute in XML: bounds="[0,0][720,1616]"
- First bracket [0,0] is top-left, second [720,1616] is bottom-right
- Calculate center: x = (0+720)/2, y = (0+1616)/2
"""


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
async def inspect_screen_structure() -> str:
    """Get the complete UI structure of the Android screen as a view hierarchy. This is the PREFERRED method for understanding screen content and finding elements to interact with. Returns XML data containing all UI elements with their properties, bounds, and text content. Use this FIRST before trying vision-based tools. Response time: ~200ms"""
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
async def tap_screen(x: int, y: int) -> str:
    """Tap at specific coordinates on the Android screen. Use coordinates obtained from inspect_screen_structure for reliable interaction. Screen dimensions: 720x1616 pixels, origin (0,0) at top-left. Response time: ~100ms"""

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
async def swipe_up() -> str:
    """Perform a standard swipe up gesture from (360,1000) to (360,500). This is useful for scrolling down content. The swipe occurs in 100ms. Response time: ~200ms"""

    cmd: list[str] = ["adb"]
    cmd += ["shell", "input", "swipe", "360", "1000", "360", "500", "100"]

    logger.info(f"Executing command: {cmd}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"ADB swipe up command failed (exit code {process.returncode}): "
            f"{stderr.decode().strip()}"
        )
    _ = stdout
    return "Performed swipe up from (360, 1000) to (360, 500) in 100ms."


@mcp.tool()
async def swipe_down() -> str:
    """Perform a standard swipe down gesture from (360,500) to (360,1000). This is useful for scrolling up content. The swipe occurs in 100ms. Response time: ~200ms"""

    cmd: list[str] = ["adb"]
    cmd += ["shell", "input", "swipe", "360", "500", "360", "1000", "100"]

    logger.info(f"Executing command: {cmd}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"ADB swipe down command failed (exit code {process.returncode}): "
            f"{stderr.decode().strip()}"
        )
    _ = stdout
    return "Performed swipe down from (360, 500) to (360, 1000) in 100ms."


@mcp.tool()
async def custom_swipe(x1: int, y1: int, x2: int, y2: int) -> str:
    """Perform a custom swipe gesture from coordinates (x1,y1) to (x2,y2). The swipe occurs in 100ms. Use coordinates obtained from inspect_screen_structure for reliable interaction. Screen dimensions: 720x1616 pixels, origin (0,0) at top-left. Response time: ~200ms"""

    if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
        raise ValueError("Coordinates must be non-negative integers.")

    cmd: list[str] = ["adb"]
    cmd += ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), "100"]

    logger.info(f"Executing command: {cmd}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"ADB custom swipe command failed (exit code {process.returncode}): "
            f"{stderr.decode().strip()}"
        )
    _ = stdout
    return f"Performed custom swipe from ({x1}, {y1}) to ({x2}, {y2}) in 100ms."


@mcp.tool()
async def input_text(text: str) -> str:
    """Type text into the currently focused input field. Ensure an input field is selected (via tap_screen) before using. Response time: ~200ms"""
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


@mcp.tool()
async def describe_visible_elements() -> str:
    """FALLBACK TOOL: Use vision AI to describe interactive elements when inspect_screen_structure doesn't provide enough information. This is SLOWER and LESS RELIABLE than inspect_screen_structure. Only use when the view hierarchy lacks necessary details (e.g., custom-drawn elements, images without proper labels). Response time: 2-3 seconds"""
    screenshot_b64: str = await take_android_screenshot()

    return describe_screen_interactions(screenshot_b64)


@mcp.tool()
async def query_visual_details(prompt: str) -> str:
    """FALLBACK TOOL: Ask specific questions about visual appearance when such details aren't available in the view hierarchy (e.g., colors, visual styles, image content). This is a FALLBACK tool - prefer inspect_screen_structure for structural information. Response time: 2-3 seconds"""
    screenshot_b64: str = await take_android_screenshot()

    return run_prompt_against_screen(screenshot_b64, prompt)


@mcp.tool()
async def tap_element_fallback(description: str) -> str:
    """LAST RESORT: Find and tap an element using vision AI when inspect_screen_structure cannot locate it. This is UNRELIABLE and SLOW. Always try inspect_screen_structure + tap_screen first. Common valid uses: tapping on canvas-drawn elements, game interfaces, or custom graphics. Response time: 3-4 seconds"""
    # First, find the element coordinates
    screenshot_b64: str = await take_android_screenshot()
    element_info = find_element_coordinates_by_description(screenshot_b64, description)

    # Then tap at those coordinates
    x, y = element_info["x"], element_info["y"]
    tap_result = await tap_screen(x, y)

    # Return a detailed confirmation message
    return f"Tapped element '{element_info['element_description']}' at coordinates ({x}, {y}) with confidence {element_info['confidence']:.2f}"


@mcp.tool()
async def capture_screenshot() -> Image:
    """Capture a raw screenshot image. ONLY use this if you have vision capabilities and need to see the actual visual representation. For understanding screen structure and interaction, use inspect_screen_structure instead. Response time: ~500ms"""
    # Build the adb command: `adb exec-out screencap -p`
    cmd: list[str] = ["adb", "exec-out", "screencap", "-p"]

    # Execute the command asynchronously and capture stdout
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

    # Return the raw PNG binary data wrapped in an Image object
    return Image(data=stdout, format="PNG")


@mcp.tool()
async def run_adb_command(command: str) -> str:
    """Execute an arbitrary ADB command and return its output.

    This tool allows running any ADB command directly. Use with caution and only for commands
    not covered by the specialized tools above. The command should NOT include the 'adb' prefix.

    Args:
        command: The ADB command to execute (without the 'adb' prefix).
                 Example: "shell pm list packages" or "devices"

    Returns:
        The command's stdout output as a string.

    Response time: varies based on command complexity
    """
    if not command or not command.strip():
        raise ValueError("Command cannot be empty.")

    # Build the full command with adb prefix
    cmd: list[str] = ["adb"]
    cmd.extend(command.split())

    logger.info(f"Executing arbitrary ADB command: {cmd}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise RuntimeError(
            f"ADB command failed (exit code {process.returncode}): {error_msg}"
        )

    return stdout.decode().strip()


@mcp.tool()
async def get_device_info() -> dict:
    """Get useful properties about the connected Android device.

    This tool queries the device for various system properties including screen
    dimensions, Android version, device model, and other hardware/software information.

    Returns:
        A dictionary containing device properties with the following keys:
        - screen_dimensions: dict with width and height in pixels
        - android_version: string with OS version
        - device_model: string with device model name
        - manufacturer: string with device manufacturer
        - build_id: string with build identifier
        - battery: dict with level and charging status
        - memory: dict with total and available RAM in MB

    Response time: ~300ms
    """
    properties = {}

    # Helper function to execute ADB commands and get output
    async def adb_get_prop(command):
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(f"Command failed: {command}")
            return ""
        return stdout.decode().strip()

    # Get screen dimensions
    dimensions_str = await adb_get_prop(["adb", "shell", "wm", "size"])
    if "size:" in dimensions_str:
        dimensions = dimensions_str.split("size:")[1].strip().split("x")
        if len(dimensions) == 2:
            properties["screen_dimensions"] = {
                "width": int(dimensions[0]),
                "height": int(dimensions[1]),
            }

    # Get Android version
    android_version = await adb_get_prop(
        ["adb", "shell", "getprop", "ro.build.version.release"]
    )
    sdk_version = await adb_get_prop(
        ["adb", "shell", "getprop", "ro.build.version.sdk"]
    )
    properties["android_version"] = {"release": android_version, "sdk": sdk_version}

    # Get device model and manufacturer
    properties["device_model"] = await adb_get_prop(
        ["adb", "shell", "getprop", "ro.product.model"]
    )
    properties["manufacturer"] = await adb_get_prop(
        ["adb", "shell", "getprop", "ro.product.manufacturer"]
    )
    properties["build_id"] = await adb_get_prop(
        ["adb", "shell", "getprop", "ro.build.id"]
    )

    # Get battery info
    battery_level = await adb_get_prop(
        ["adb", "shell", "dumpsys", "battery", "|", "grep", "level"]
    )
    battery_status = await adb_get_prop(
        ["adb", "shell", "dumpsys", "battery", "|", "grep", "status"]
    )

    properties["battery"] = {}
    if "level" in battery_level:
        try:
            properties["battery"]["level"] = int(
                battery_level.split("level:")[1].strip()
            )
        except (IndexError, ValueError):
            properties["battery"]["level"] = -1

    if "status" in battery_status:
        try:
            status_code = int(battery_status.split("status:")[1].strip())
            # Status codes: 1=unknown, 2=charging, 3=discharging, 4=not charging, 5=full
            status_map = {
                1: "unknown",
                2: "charging",
                3: "discharging",
                4: "not_charging",
                5: "full",
            }
            properties["battery"]["status"] = status_map.get(status_code, "unknown")
        except (IndexError, ValueError):
            properties["battery"]["status"] = "unknown"

    # Get memory information
    mem_info = await adb_get_prop(["adb", "shell", "cat", "/proc/meminfo"])
    properties["memory"] = {}

    if mem_info:
        lines = mem_info.splitlines()
        for line in lines:
            if "MemTotal" in line:
                try:
                    # Convert from kB to MB
                    total = int(line.split()[1]) // 1024
                    properties["memory"]["total_mb"] = total
                except (IndexError, ValueError):
                    pass
            elif "MemAvailable" in line:
                try:
                    # Convert from kB to MB
                    available = int(line.split()[1]) // 1024
                    properties["memory"]["available_mb"] = available
                except (IndexError, ValueError):
                    pass

    return properties


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
