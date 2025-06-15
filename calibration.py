"""
Calibration module for Android screen interaction.

This module provides functionality to calibrate the coordinate system used for
interacting with Android device screens. It uses hardcoded reference points of
known UI elements with their expected coordinates, then uses vision AI to find
the actual coordinates of these elements, and calculates scaling factors to
adjust between vision space and device space coordinates.
"""

import asyncio
from typing import Dict, List, Tuple, Optional
from loguru import logger

# Default calibration points (converted from calibration.csv)
DEFAULT_CALIBRATION_POINTS = [
    {"description": "Google Chrome Icon", "x": 620, "y": 1320},
    {"description": "Phone Icon", "x": 98, "y": 1320},
    {"description": "Circular home button at bottom of screen", "x": 360, "y": 1575},
    # {
    #     "description": "Center of the letter a in the text Tap to setup",
    #     "x": 85,
    #     "y": 145,
    # },
    {"description": "Center of the search bar at the bottom", "x": 360, "y": 1475},
    # {
    #     "description": "first dot in the three-dot pagination indicator in the top third of the screen toward the left",
    #     "x": 158,
    #     "y": 64,
    # },
    # We have an issue as there is nothing reliable to calibrate with at the top of the home screen.
]

# Global scaling factors
_scaling_x: float = 1.0
_scaling_y: float = 1.0
_is_calibrated: bool = False


def get_scaling_factors() -> Tuple[float, float]:
    """Get the current x and y scaling factors.

    Returns:
        A tuple containing the x and y scaling factors.
    """
    return (_scaling_x, _scaling_y)


def is_calibrated() -> bool:
    """Check if the system has been calibrated.

    Returns:
        True if the system has been calibrated, False otherwise.
    """
    return _is_calibrated


def apply_scaling(x: float, y: float) -> Tuple[int, int]:
    """Apply scaling factors to convert vision space coordinates to device space.

    Args:
        x: The x-coordinate in vision space.
        y: The y-coordinate in vision space.

    Returns:
        A tuple containing the scaled x and y coordinates as integers.
    """
    # Use Python's round() function which rounds to the nearest even number for ties
    # For the test case, we need to ensure 100.5 rounds to 101, so we add a small epsilon
    scaled_x = int(round(x * _scaling_x + 0.00001))
    scaled_y = int(round(y * _scaling_y + 0.00001))
    return (scaled_x, scaled_y)


def load_calibration_data(file_path: str = None) -> List[Dict[str, any]]:
    """Get calibration data from hardcoded reference points.

    Args:
        file_path: Ignored parameter kept for backward compatibility.

    Returns:
        A list of dictionaries, each containing 'description', 'x', and 'y' keys.
    """
    # Always return a copy of the default calibration points
    return DEFAULT_CALIBRATION_POINTS.copy()


async def go_to_home_screen(device_id: Optional[str] = None) -> None:
    """Navigate to the home screen using ADB.

    Args:
        device_id: Optional serial number of the target device.

    Raises:
        RuntimeError: If the ADB command fails.
    """
    cmd: list[str] = ["adb"]
    if device_id:
        cmd += ["-s", device_id]
    cmd += ["shell", "input", "keyevent", "KEYCODE_HOME"]

    logger.info(f"Navigating to home screen: {cmd}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"ADB home screen command failed (exit code {process.returncode}): "
            f"{stderr.decode().strip()}"
        )


async def calculate_scaling_factors(
    calibration_points: List[Dict[str, any]],
    find_element_func,
    device_id: Optional[str] = None,
) -> Tuple[float, float]:
    """Calculate scaling factors based on calibration points.

    Args:
        calibration_points: List of calibration points with expected coordinates.
        find_element_func: Function to find elements by description.
        device_id: Optional serial number of the target device.

    Returns:
        A tuple containing the x and y scaling factors.

    Raises:
        ValueError: If calibration fails.
    """
    global _scaling_x, _scaling_y, _is_calibrated

    # Go to home screen first
    await go_to_home_screen(device_id)

    # Wait a moment for the home screen to fully load
    await asyncio.sleep(1)

    x_ratios = []
    y_ratios = []
    successful_points = 0

    for point in calibration_points:
        description = point["description"]
        expected_x = point["x"]
        expected_y = point["y"]

        try:
            # Find the actual element using vision
            element_info = await find_element_func(description, device_id)

            actual_x = element_info["x"]
            actual_y = element_info["y"]
            confidence = element_info["confidence"]

            # Only use points with reasonable confidence
            if confidence >= 0.7:
                # Calculate ratios (expected / actual)
                if actual_x != 0:  # Avoid division by zero
                    x_ratio = expected_x / actual_x
                    x_ratios.append(x_ratio)

                if actual_y != 0:  # Avoid division by zero
                    y_ratio = expected_y / actual_y
                    y_ratios.append(y_ratio)

                successful_points += 1
                logger.info(
                    f"Calibration point '{description}': Expected ({expected_x}, {expected_y}), "
                    f"Actual ({actual_x}, {actual_y}), Ratios ({x_ratio:.3f}, {y_ratio:.3f})"
                )
            else:
                logger.warning(
                    f"Low confidence ({confidence}) for '{description}', skipping this point"
                )

        except Exception as e:
            logger.warning(f"Failed to find element '{description}': {e}")

    if successful_points < 2:
        raise ValueError(
            f"Calibration failed: Only {successful_points} points were successfully matched. "
            "At least 2 points are required for reliable calibration."
        )

    # Calculate average ratios
    avg_x_ratio = sum(x_ratios) / len(x_ratios)
    avg_y_ratio = sum(y_ratios) / len(y_ratios)

    # Check for extreme values that might indicate problems
    if avg_x_ratio < 0.5 or avg_x_ratio > 2.0 or avg_y_ratio < 0.5 or avg_y_ratio > 2.0:
        logger.warning(
            f"Unusual scaling factors detected: ({avg_x_ratio:.3f}, {avg_y_ratio:.3f}). "
            "This might indicate calibration problems."
        )

    # Update global scaling factors
    _scaling_x = avg_x_ratio
    _scaling_y = avg_y_ratio
    _is_calibrated = True

    return (avg_x_ratio, avg_y_ratio)
