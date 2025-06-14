from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import asyncio
import base64
import os
import openai

api_key = ""

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
    """Capture a screenshot of the Android device and obtain a textual description from OpenAI.

    Args:
        device_id: Optional Android device serial (from ``adb devices``) if more
            than one device is connected.

    Returns:
        A natural-language description of what is visible on the screen.
    """

    screenshot_b64: str = await take_android_screenshot(device_id)
    data_url = f"data:image/png;base64,{screenshot_b64}"

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please describe everything you see on this Android screenshot.",
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

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        description = response.choices[0].message.content
    except ImportError:
        openai.api_key = api_key
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=messages,
        )
        description = response.choices[0].message.content

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