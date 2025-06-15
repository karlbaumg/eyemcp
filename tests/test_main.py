import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import base64
from main import (
    take_android_screenshot,
    describe_screen,
    tap_android_screen,
    find_element_by_description,
    tap_element_by_description,
    calibrate,
    send_keys,
)


@pytest.mark.asyncio
async def test_take_android_screenshot():
    """Test that take_android_screenshot calls the ADB command correctly and returns base64 encoded screenshot."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"mock_screenshot_data", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        result = await take_android_screenshot()

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "screencap" in args

        # Check that the result is base64 encoded
        expected_result = base64.b64encode(b"mock_screenshot_data").decode()
        assert result == expected_result


@pytest.mark.asyncio
async def test_take_android_screenshot_with_device_id():
    """Test that take_android_screenshot includes the device ID when provided."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"mock_screenshot_data", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function with a device ID
        await take_android_screenshot("test_device")

        # Check that the correct command was executed with the device ID
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert args[1] == "-s"
        assert args[2] == "test_device"


@pytest.mark.asyncio
async def test_take_android_screenshot_error():
    """Test that take_android_screenshot handles errors correctly."""
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"ADB error"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        # Call the function and check that it raises the expected error
        with pytest.raises(RuntimeError, match="ADB screenshot command failed"):
            await take_android_screenshot()


@pytest.mark.asyncio
async def test_describe_screen():
    """Test that describe_screen calls take_android_screenshot and describe_screen_interactions correctly."""
    with (
        patch(
            "main.take_android_screenshot",
            return_value=AsyncMock(return_value="mock_screenshot_base64"),
        ),
        patch(
            "main.describe_screen_interactions", return_value="Mock screen description"
        ),
    ):

        # Call the function
        result = await describe_screen()

        # Check that the result is the mock description
        assert result == "Mock screen description"


@pytest.mark.asyncio
async def test_tap_android_screen():
    """Test that tap_android_screen calls the ADB command correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        result = await tap_android_screen(100, 200)

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "input" in args
        assert "tap" in args
        assert "100" in args
        assert "200" in args

        # Check that the result is a confirmation message
        assert "Tapped at (100, 200)" in result


@pytest.mark.asyncio
async def test_tap_android_screen_invalid_coordinates():
    """Test that tap_android_screen validates coordinates."""
    # Call the function with negative coordinates and check that it raises the expected error
    with pytest.raises(ValueError, match="Coordinates must be non-negative"):
        await tap_android_screen(-10, 200)


@pytest.mark.asyncio
async def test_find_element_by_description():
    """Test that find_element_by_description calls take_android_screenshot and find_element_coordinates_by_description correctly."""
    mock_element_info = {
        "x": 100,
        "y": 200,
        "confidence": 0.9,
        "element_description": "Mock element",
    }

    with (
        patch("main.calibration.is_calibrated", return_value=True),
        patch(
            "main.take_android_screenshot",
            AsyncMock(return_value="mock_screenshot_base64"),
        ),
        patch(
            "main.find_element_coordinates_by_description",
            return_value=mock_element_info,
        ),
    ):

        # Call the function
        result = await find_element_by_description("button")

        # Check that the result is the mock element info
        assert result == mock_element_info


@pytest.mark.asyncio
async def test_find_element_by_description_not_calibrated():
    """Test that find_element_by_description raises an error when the system is not calibrated."""
    with patch("main.calibration.is_calibrated", return_value=False):
        # Call the function and check that it raises the expected error
        with pytest.raises(ValueError, match="System needs to be calibrated first"):
            await find_element_by_description("button")


@pytest.mark.asyncio
async def test_tap_element_by_description():
    """Test that tap_element_by_description calls find_element_by_description and tap_android_screen correctly."""
    mock_element_info = {
        "x": 100,
        "y": 200,
        "confidence": 0.9,
        "element_description": "Mock element",
    }

    with (
        patch("main.calibration.is_calibrated", return_value=True),
        patch(
            "main.find_element_by_description",
            AsyncMock(return_value=mock_element_info),
        ),
        patch(
            "main.tap_android_screen", AsyncMock(return_value="Tapped at (100, 200)")
        ),
    ):

        # Call the function
        result = await tap_element_by_description("button")

        # Check that the result contains the expected information
        assert "Tapped element 'Mock element'" in result
        assert "(100, 200)" in result
        assert "0.90" in result  # Formatted confidence


@pytest.mark.asyncio
async def test_tap_element_by_description_not_calibrated():
    """Test that tap_element_by_description raises an error when the system is not calibrated."""
    with patch("main.calibration.is_calibrated", return_value=False):
        # Call the function and check that it raises the expected error
        with pytest.raises(ValueError, match="System needs to be calibrated first"):
            await tap_element_by_description("button")


@pytest.mark.asyncio
async def test_calibrate():
    """Test that calibrate loads calibration data and calculates scaling factors correctly."""
    mock_calibration_points = [
        {"description": "Element 1", "x": 100, "y": 200},
        {"description": "Element 2", "x": 300, "y": 400},
    ]
    mock_scaling_factors = (1.1, 1.2)

    with (
        patch("os.path.exists", return_value=True),
        patch(
            "main.calibration.load_calibration_data",
            return_value=mock_calibration_points,
        ),
        patch(
            "main.calibration.calculate_scaling_factors",
            AsyncMock(return_value=mock_scaling_factors),
        ),
    ):

        # Call the function
        result = await calibrate("test_calibration.csv")

        # Check that the result contains the scaling factors
        assert "Calibration complete" in result
        assert "x=1.100" in result
        assert "y=1.200" in result


@pytest.mark.asyncio
async def test_send_keys():
    """Test that send_keys calls the ADB command correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        result = await send_keys("hello world")

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "input" in args
        assert "text" in args
        assert "hello world" in args

        # Check that the result is a confirmation message
        assert "Sent keystrokes 'hello world'" in result


@pytest.mark.asyncio
async def test_send_keys_with_device_id():
    """Test that send_keys includes the device ID when provided."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function with a device ID
        await send_keys("hello world", "test_device")

        # Check that the correct command was executed with the device ID
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert args[1] == "-s"
        assert args[2] == "test_device"


@pytest.mark.asyncio
async def test_send_keys_empty_text():
    """Test that send_keys validates that text is not empty."""
    # Call the function with empty text and check that it raises the expected error
    with pytest.raises(ValueError, match="Text cannot be empty"):
        await send_keys("")


@pytest.mark.asyncio
async def test_send_keys_error():
    """Test that send_keys handles errors correctly."""
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"ADB error"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        # Call the function and check that it raises the expected error
        with pytest.raises(RuntimeError, match="ADB input text command failed"):
            await send_keys("hello world")
