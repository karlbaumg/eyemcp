from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import asyncio
import base64
import os
import openai
from loguru import logger

# Configure logging: remove the default stderr sink and log exclusively to file.
logger.remove()
logger.add("mcp.log",encoding="utf-8", enqueue=True)

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
async def describe_screen(device_id: str | None = None) -> str:
    """Describe the screen of a connected Android device together with the pixel coordinates of the elements
    that can be tapped on via adb. The dimensions of the screen is 720x1616.

    Returns:
        A natural-language description of what is visible on the screen along with the coordinates of the elements.
    """

    screenshot_b64: str = await take_android_screenshot(device_id)
    data_url = f"data:image/png;base64,{screenshot_b64}"

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "List every clickable element on the screen with a description and the coordinate of its center to tap on it using adb. The dimensions of the screen is 720 wide x1616 high. Top left is the origin. coordinates are in pixels, x then y",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
            ],
        }
    ]
    try:
        from openai import AsyncOpenAI
        logger.info("Using OpenAI API")

        client = AsyncOpenAI(base_url="http://127.0.0.1:1234/v1", api_key="abcd")
        logger.info("Client created")
        response = await client.chat.completions.create(
            model="se-gui-7b",
            messages=messages,
        )
        logger.info(response)
        description = response.choices[0].message.content
    except Exception as e:  
        logger.error(f"Error: {e}")

    return description.strip()

@mcp.tool()
async def tap_android_screen(x: int, y: int, device_id: str | None = None) -> str:
    """Tap the screen of a connected Android device at the given coordinates.

    Args:
        x: Horizontal pixel coordinate.
        y: Vertical pixel coordinate.
        device_id: Optional device serial (from ``adb devices``) if multiple
            devices are connected.

    Returns:
        A short confirmation message when the tap succeeds.
    """

    if x < 0 or y < 0:
        raise ValueError("Coordinates must be non-negative integers.")

    cmd: list[str] = ["adb"]
    if device_id:
        cmd += ["-s", device_id]
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
    return f"Tapped at ({x}, {y}) on device {device_id or '<default>'}."

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')