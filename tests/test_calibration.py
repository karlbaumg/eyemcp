import pytest
from unittest.mock import patch, MagicMock, mock_open
from calibration import (
    get_scaling_factors,
    is_calibrated,
    apply_scaling,
    load_calibration_data,
    go_to_home_screen,
    calculate_scaling_factors,
)


def test_get_scaling_factors():
    # Test the default scaling factors
    x, y = get_scaling_factors()
    assert x == 1.0
    assert y == 1.0


def test_is_calibrated():
    # Test the default calibration state
    assert is_calibrated() is False


def test_apply_scaling():
    # Test scaling with default factors (1.0, 1.0)
    x, y = apply_scaling(100.0, 200.0)
    assert x == 100
    assert y == 200

    # Test with non-integer values
    x, y = apply_scaling(100.5, 200.7)
    assert x == 101
    assert y == 201

    # Test with custom scaling factors
    with patch("calibration._scaling_x", 1.2), patch("calibration._scaling_y", 0.8):
        x, y = apply_scaling(100, 200)
        assert x == 120
        assert y == 160


def test_load_calibration_data_file_not_found():
    # Test with non-existent file
    with pytest.raises(FileNotFoundError):
        load_calibration_data("nonexistent_file.csv")


def test_load_calibration_data_invalid_format():
    # Test with invalid CSV format
    mock_csv_content = "invalid,header\n1,2,3"
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=mock_csv_content)),
    ):
        with pytest.raises(ValueError):
            load_calibration_data("test.csv")


def test_load_calibration_data_valid():
    # Test with valid CSV format
    mock_csv_content = "description,x,y\nTest Element,100,200\nAnother Element,300,400"
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=mock_csv_content)),
    ):
        data = load_calibration_data("test.csv")
        assert len(data) == 2
        assert data[0]["description"] == "Test Element"
        assert data[0]["x"] == 100
        assert data[0]["y"] == 200
        assert data[1]["description"] == "Another Element"
        assert data[1]["x"] == 300
        assert data[1]["y"] == 400


@pytest.mark.asyncio
async def test_go_to_home_screen():
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0

    # Use an async function instead of asyncio.coroutine
    async def mock_communicate():
        return (b"", b"")

    mock_process.communicate = mock_communicate

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        await go_to_home_screen()
        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "KEYCODE_HOME" in args


@pytest.mark.asyncio
async def test_go_to_home_screen_error():
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1

    # Use an async function instead of asyncio.coroutine
    async def mock_communicate():
        return (b"", b"Error")

    mock_process.communicate = mock_communicate

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        with pytest.raises(RuntimeError):
            await go_to_home_screen()


@pytest.mark.asyncio
async def test_calculate_scaling_factors():
    # Mock calibration points
    calibration_points = [
        {"description": "Element 1", "x": 100, "y": 200},
        {"description": "Element 2", "x": 300, "y": 400},
    ]

    # Mock find_element_func
    async def mock_find_element(description, device_id=None):
        if description == "Element 1":
            return {
                "x": 90,
                "y": 180,
                "confidence": 0.9,
                "element_description": "Element 1",
            }
        elif description == "Element 2":
            return {
                "x": 270,
                "y": 360,
                "confidence": 0.9,
                "element_description": "Element 2",
            }
        else:
            raise ValueError("Element not found")

    # Mock go_to_home_screen with an async function
    async def mock_go_to_home_screen(device_id=None):
        return None

    # Mock go_to_home_screen
    with (
        patch(
            "calibration.go_to_home_screen",
            new=mock_go_to_home_screen,
        ),
        patch("calibration._scaling_x", 1.0),
        patch("calibration._scaling_y", 1.0),
        patch("calibration._is_calibrated", False),
    ):

        # Calculate scaling factors
        x_scale, y_scale = await calculate_scaling_factors(
            calibration_points, mock_find_element
        )

        # Check results
        assert round(x_scale, 2) == 1.11  # 100/90 = 1.11
        assert round(y_scale, 2) == 1.11  # 200/180 = 1.11


@pytest.mark.asyncio
async def test_calculate_scaling_factors_low_confidence():
    # Mock calibration points
    calibration_points = [
        {"description": "Element 1", "x": 100, "y": 200},
        {"description": "Element 2", "x": 300, "y": 400},
        {"description": "Element 3", "x": 500, "y": 600},  # Added a third element
    ]

    # Mock find_element_func with low confidence for one element
    async def mock_find_element(description, device_id=None):
        if description == "Element 1":
            return {
                "x": 90,
                "y": 180,
                "confidence": 0.5,  # Low confidence, should be skipped
                "element_description": "Element 1",
            }
        elif description == "Element 2":
            return {
                "x": 270,
                "y": 360,
                "confidence": 0.9,
                "element_description": "Element 2",
            }
        elif description == "Element 3":
            return {
                "x": 450,
                "y": 540,
                "confidence": 0.8,
                "element_description": "Element 3",
            }
        else:
            raise ValueError("Element not found")

    # Mock go_to_home_screen with an async function
    async def mock_go_to_home_screen(device_id=None):
        return None

    # Mock go_to_home_screen
    with (
        patch(
            "calibration.go_to_home_screen",
            new=mock_go_to_home_screen,
        ),
        patch("calibration._scaling_x", 1.0),
        patch("calibration._scaling_y", 1.0),
        patch("calibration._is_calibrated", False),
    ):

        # Calculate scaling factors - should only use Element 2 and Element 3 due to low confidence in Element 1
        x_scale, y_scale = await calculate_scaling_factors(
            calibration_points, mock_find_element
        )

        # Check results - average of (300/270 = 1.11) and (500/450 = 1.11)
        assert round(x_scale, 2) == 1.11
        assert round(y_scale, 2) == 1.11
