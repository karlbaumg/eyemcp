"""
Evaluation script for vision calibration accuracy.

This script evaluates the accuracy of the vision system by:
1. Loading calibration data from calibration.csv
2. Using the actual screenshot (ss.png) to find elements
3. For each entry, calculating:
   - Pre-calibration absolute error (in pixels)
   - Pre-calibration relative error (as percentage)
   - Post-calibration absolute error (in pixels)
   - Post-calibration relative error (as percentage)
4. Outputting summary statistics for all points
"""

import base64
import csv
import json
import math
import statistics
from typing import Dict, List, Any
import asyncio

from dotenv import load_dotenv
import calibration
from vision import find_element_coordinates_by_description

# Ensure environment variables are loaded
load_dotenv()


def load_calibration_data(file_path: str) -> List[Dict[str, Any]]:
    """Load calibration data from a CSV file.

    Args:
        file_path: Path to the CSV file containing calibration data.

    Returns:
        A list of dictionaries, each containing 'description', 'x', and 'y' keys.
    """
    calibration_points = []

    with open(file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            point = {
                "description": row["description"],
                "x": int(row["x"]),
                "y": int(row["y"]),
            }
            calibration_points.append(point)

    return calibration_points


def load_screenshot_base64(file_path: str) -> str:
    """Load a screenshot file and convert it to base64.

    Args:
        file_path: Path to the screenshot file.

    Returns:
        Base64-encoded string of the screenshot.
    """
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def calculate_error_metrics(
    expected_x: int, expected_y: int, actual_x: int, actual_y: int
) -> Dict[str, float]:
    """Calculate error metrics between expected and actual coordinates.

    Args:
        expected_x: Expected x-coordinate.
        expected_y: Expected y-coordinate.
        actual_x: Actual x-coordinate.
        actual_y: Actual y-coordinate.

    Returns:
        Dictionary containing error metrics:
        - abs_error_x: Absolute error in x-coordinate (pixels)
        - abs_error_y: Absolute error in y-coordinate (pixels)
        - abs_error_total: Euclidean distance between points (pixels)
        - rel_error_x: Relative error in x-coordinate (percentage)
        - rel_error_y: Relative error in y-coordinate (percentage)
        - rel_error_total: Relative Euclidean error (percentage)
    """
    # Calculate absolute errors
    abs_error_x = abs(expected_x - actual_x)
    abs_error_y = abs(expected_y - actual_y)
    abs_error_total = math.sqrt(abs_error_x**2 + abs_error_y**2)

    # Calculate relative errors (as percentages)
    # Avoid division by zero
    rel_error_x = (abs_error_x / expected_x * 100) if expected_x != 0 else float("inf")
    rel_error_y = (abs_error_y / expected_y * 100) if expected_y != 0 else float("inf")

    # For total relative error, use the distance from origin
    expected_distance = math.sqrt(expected_x**2 + expected_y**2)
    rel_error_total = (
        (abs_error_total / expected_distance * 100)
        if expected_distance != 0
        else float("inf")
    )

    return {
        "abs_error_x": abs_error_x,
        "abs_error_y": abs_error_y,
        "abs_error_total": abs_error_total,
        "rel_error_x": rel_error_x,
        "rel_error_y": rel_error_y,
        "rel_error_total": rel_error_total,
    }


def calculate_statistics(
    metrics_list: List[Dict[str, float]],
) -> Dict[str, Dict[str, float]]:
    """Calculate statistics for a list of error metrics.

    Args:
        metrics_list: List of error metric dictionaries.

    Returns:
        Dictionary containing statistics for each error metric:
        - min: Minimum value
        - max: Maximum value
        - mean: Mean value
        - median: Median value
        - stdev: Standard deviation
    """
    stats = {}

    # Get all metric keys from the first entry
    if not metrics_list:
        return stats

    metric_keys = metrics_list[0].keys()

    for key in metric_keys:
        values = [m[key] for m in metrics_list if not math.isinf(m[key])]

        if not values:
            stats[key] = {
                "min": float("nan"),
                "max": float("nan"),
                "mean": float("nan"),
                "median": float("nan"),
                "stdev": float("nan"),
            }
            continue

        stats[key] = {
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
        }

    return stats


async def evaluate_calibration(calibration_file: str, screenshot_file: str) -> None:
    """Evaluate calibration accuracy using the provided screenshot.

    Args:
        calibration_file: Path to the calibration CSV file.
        screenshot_file: Path to the screenshot file.
    """
    # Load calibration data
    calibration_points = load_calibration_data(calibration_file)

    # Load screenshot
    screenshot_base64 = load_screenshot_base64(screenshot_file)

    # Store results for each point
    results = []
    errors = []

    # Save original calibration state
    original_is_calibrated = calibration.is_calibrated()
    original_scaling_x, original_scaling_y = calibration.get_scaling_factors()

    # Temporarily disable calibration to get pre-calibration coordinates
    import importlib

    importlib.reload(calibration)

    print(f"\nEvaluating {len(calibration_points)} calibration points...")
    print("-" * 80)
    print(
        f"{'Description':<40} | {'Expected (x,y)':<15} | {'Actual (x,y)':<15} | {'Abs Error (x,y)':<15} | {'Rel Error %':<10}"
    )
    print("-" * 80)

    # First pass: Get all valid points and their pre-calibration coordinates
    valid_points = []
    for point in calibration_points:
        description = point["description"]
        expected_x = point["x"]
        expected_y = point["y"]

        try:
            # Get pre-calibration coordinates
            result = find_element_coordinates_by_description(
                screenshot_base64, description
            )
            pre_cal_x = result["x"]
            pre_cal_y = result["y"]
            confidence = result["confidence"]

            # Calculate pre-calibration errors
            pre_cal_errors = calculate_error_metrics(
                expected_x, expected_y, pre_cal_x, pre_cal_y
            )

            valid_points.append(
                {
                    "description": description,
                    "expected_x": expected_x,
                    "expected_y": expected_y,
                    "pre_cal_x": pre_cal_x,
                    "pre_cal_y": pre_cal_y,
                    "confidence": confidence,
                    "pre_cal_errors": pre_cal_errors,
                }
            )
        except json.JSONDecodeError as e:
            errors.append(f"JSON parsing error for '{description}': {e}")
            print(f"Error: JSON parsing error for '{description}': {e}")
        except KeyError as e:
            errors.append(f"Missing field '{e}' in response for '{description}'")
            print(f"Error: Missing field '{e}' in response for '{description}'")
        except Exception as e:
            errors.append(f"Error processing '{description}': {e}")
            print(f"Error: Failed to process '{description}': {e}")

    # Calculate scaling factors using all valid points
    x_ratios = []
    y_ratios = []

    for point in valid_points:
        if point["pre_cal_x"] != 0:
            x_ratio = point["expected_x"] / point["pre_cal_x"]
            x_ratios.append(x_ratio)

        if point["pre_cal_y"] != 0:
            y_ratio = point["expected_y"] / point["pre_cal_y"]
            y_ratios.append(y_ratio)

    if not x_ratios or not y_ratios:
        print("Error: Could not calculate scaling factors (insufficient valid points)")
        return

    # Calculate average scaling factors
    avg_x_ratio = sum(x_ratios) / len(x_ratios)
    avg_y_ratio = sum(y_ratios) / len(y_ratios)

    print(f"\nCalculated scaling factors: x={avg_x_ratio:.4f}, y={avg_y_ratio:.4f}")
    print("-" * 80)

    # Second pass: Calculate post-calibration coordinates and errors for each valid point
    for point in valid_points:
        description = point["description"]
        expected_x = point["expected_x"]
        expected_y = point["expected_y"]
        pre_cal_x = point["pre_cal_x"]
        pre_cal_y = point["pre_cal_y"]
        confidence = point["confidence"]
        pre_cal_errors = point["pre_cal_errors"]

        # Apply scaling to get post-calibration coordinates
        post_cal_x = int(round(pre_cal_x * avg_x_ratio + 0.00001))
        post_cal_y = int(round(pre_cal_y * avg_y_ratio + 0.00001))

        # Calculate post-calibration errors
        post_cal_errors = calculate_error_metrics(
            expected_x, expected_y, post_cal_x, post_cal_y
        )

        # Store results
        result_entry = {
            "description": description,
            "expected_x": expected_x,
            "expected_y": expected_y,
            "pre_cal_x": pre_cal_x,
            "pre_cal_y": pre_cal_y,
            "post_cal_x": post_cal_x,
            "post_cal_y": post_cal_y,
            "confidence": confidence,
            "pre_cal_errors": pre_cal_errors,
            "post_cal_errors": post_cal_errors,
        }
        results.append(result_entry)

        # Print results for this point
        print(
            f"{description[:38]:<40} | ({expected_x:4d},{expected_y:4d}) | "
            f"({pre_cal_x:4d},{pre_cal_y:4d}) | "
            f"({pre_cal_errors['abs_error_x']:4.1f},{pre_cal_errors['abs_error_y']:4.1f}) | "
            f"{pre_cal_errors['rel_error_total']:8.2f}%"
        )

    # Calculate statistics
    if results:
        pre_cal_metrics = [r["pre_cal_errors"] for r in results]
        post_cal_metrics = [r["post_cal_errors"] for r in results]

        pre_cal_stats = calculate_statistics(pre_cal_metrics)
        post_cal_stats = calculate_statistics(post_cal_metrics)

        # Print summary statistics
        print("\nSummary:")
        print(f"- Total calibration points: {len(calibration_points)}")
        print(f"- Successfully processed points: {len(results)}")
        print(f"- Failed points: {len(errors)}")

        print("\nPre-Calibration Error Statistics:")
        print("-" * 80)
        print(
            f"{'Metric':<15} | {'Min':>8} | {'Max':>8} | {'Mean':>8} | {'Median':>8} | {'StdDev':>8}"
        )
        print("-" * 80)

        for metric, stats in pre_cal_stats.items():
            print(
                f"{metric:<15} | {stats['min']:8.2f} | {stats['max']:8.2f} | "
                f"{stats['mean']:8.2f} | {stats['median']:8.2f} | {stats['stdev']:8.2f}"
            )

        print("\nPost-Calibration Error Statistics:")
        print("-" * 80)
        print(
            f"{'Metric':<15} | {'Min':>8} | {'Max':>8} | {'Mean':>8} | {'Median':>8} | {'StdDev':>8}"
        )
        print("-" * 80)

        for metric, stats in post_cal_stats.items():
            print(
                f"{metric:<15} | {stats['min']:8.2f} | {stats['max']:8.2f} | "
                f"{stats['mean']:8.2f} | {stats['median']:8.2f} | {stats['stdev']:8.2f}"
            )

        # Calculate improvement percentages
        print("\nImprovement with Calibration:")
        print("-" * 80)
        print(f"{'Metric':<15} | {'Absolute':>8} | {'Percentage':>8}")
        print("-" * 80)

        for metric in pre_cal_stats.keys():
            pre_mean = pre_cal_stats[metric]["mean"]
            post_mean = post_cal_stats[metric]["mean"]
            abs_improvement = pre_mean - post_mean
            pct_improvement = (
                (abs_improvement / pre_mean * 100) if pre_mean != 0 else float("inf")
            )

            print(f"{metric:<15} | {abs_improvement:8.2f} | {pct_improvement:7.2f}%")

        if errors:
            print("\nErrors encountered:")
            print("-" * 80)
            for i, error in enumerate(errors, 1):
                print(f"{i}. {error}")

    # Restore original calibration state
    # This would require modifying global variables in the calibration module
    # which is not ideal, but we'll do it for the sake of this evaluation


if __name__ == "__main__":
    asyncio.run(evaluate_calibration("calibration.csv", "ss.png"))
