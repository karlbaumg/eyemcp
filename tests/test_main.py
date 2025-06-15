import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import base64
from main import (
    take_android_screenshot,
    describe_visible_elements,
    tap_screen,
    tap_element_fallback,
    input_text,
    capture_screenshot,
    get_device_info,
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
async def test_describe_visible_elements():
    """Test that describe_visible_elements calls take_android_screenshot and describe_screen_interactions correctly."""
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
        result = await describe_visible_elements()

        # Check that the result is the mock description
        assert result == "Mock screen description"


@pytest.mark.asyncio
async def test_tap_screen():
    """Test that tap_screen calls the ADB command correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        result = await tap_screen(100, 200)

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
async def test_tap_screen_invalid_coordinates():
    """Test that tap_screen validates coordinates."""
    # Call the function with negative coordinates and check that it raises the expected error
    with pytest.raises(ValueError, match="Coordinates must be non-negative"):
        await tap_screen(-10, 200)


@pytest.mark.asyncio
async def test_tap_element_fallback():
    """Test that tap_element_fallback calls find_element_coordinates_by_description and tap_screen correctly."""
    mock_element_info = {
        "x": 100,
        "y": 200,
        "confidence": 0.9,
        "element_description": "Mock element",
    }

    with (
        patch(
            "main.take_android_screenshot",
            AsyncMock(return_value="mock_screenshot_base64"),
        ),
        patch(
            "main.find_element_coordinates_by_description",
            return_value=mock_element_info,
        ),
        patch("main.tap_screen", AsyncMock(return_value="Tapped at (100, 200)")),
    ):

        # Call the function
        result = await tap_element_fallback("button")

        # Check that the result contains the expected information
        assert "Tapped element 'Mock element'" in result
        assert "(100, 200)" in result
        assert "0.90" in result  # Formatted confidence


@pytest.mark.asyncio
async def test_input_text():
    """Test that input_text calls the ADB command correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        result = await input_text("hello world")

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "input" in args
        assert "text" in args
        assert "hello world" in args

        # Check that the result is a confirmation message
        assert "Sent keystrokes 'hello world'" in result


# This test is no longer applicable - the input_text function doesn't support device_id
# parameter since all tools exposed via MCP should not have device_id field
@pytest.mark.skip("input_text no longer supports device_id parameter")
@pytest.mark.asyncio
async def test_input_text_with_device_id():
    """Test that input_text includes the device ID when provided."""
    pass


@pytest.mark.asyncio
async def test_input_text_empty_text():
    """Test that input_text validates that text is not empty."""
    # Call the function with empty text and check that it raises the expected error
    with pytest.raises(ValueError, match="Text cannot be empty"):
        await input_text("")


@pytest.mark.asyncio
async def test_input_text_error():
    """Test that input_text handles errors correctly."""
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"ADB error"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        # Call the function and check that it raises the expected error
        with pytest.raises(RuntimeError, match="ADB input text command failed"):
            await input_text("hello world")


@pytest.mark.asyncio
async def test_capture_screenshot():
    """Test that capture_screenshot calls the ADB command correctly and returns an Image object."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"mock_png_data", b""))

    # Mock the Image class
    mock_image = MagicMock()

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec,
        patch("main.Image", return_value=mock_image) as mock_image_class,
    ):
        # Call the function
        result = await capture_screenshot()

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "exec-out" in args
        assert "screencap" in args
        assert "-p" in args

        # Check that Image was constructed with the raw PNG data
        mock_image_class.assert_called_once_with(data=b"mock_png_data", format="PNG")

        # Check that the result is the mock Image object
        assert result == mock_image


@pytest.mark.asyncio
async def test_capture_screenshot_error():
    """Test that capture_screenshot handles errors correctly."""
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"ADB error"))

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_process),
        # We don't need to mock Image here since the exception should be raised before it's used
    ):
        # Call the function and check that it raises the expected error
        with pytest.raises(RuntimeError, match="ADB screenshot command failed"):
            await capture_screenshot()


@pytest.mark.asyncio
async def test_get_device_info():
    """Test that get_device_info returns device properties with the expected structure."""
    # Call the function and check the returned data structure
    result = await get_device_info()

    # Check that the result is a dictionary with the expected keys
    assert isinstance(result, dict)

    # Verify structure only, not exact values
    assert "screen_dimensions" in result
    assert isinstance(result["screen_dimensions"], dict)
    assert "width" in result["screen_dimensions"]
    assert "height" in result["screen_dimensions"]

    assert "android_version" in result
    assert isinstance(result["android_version"], dict)

    assert isinstance(result.get("device_model", ""), str)
    assert isinstance(result.get("manufacturer", ""), str)
    assert isinstance(result.get("build_id", ""), str)

    # Check battery structure if present
    if "battery" in result:
        assert isinstance(result["battery"], dict)

    # Check memory structure if present
    if "memory" in result:
        assert isinstance(result["memory"], dict)


@pytest.mark.asyncio
async def test_get_device_info_command_failures():
    """Test that get_device_info handles command failures gracefully."""
    # Mock the asyncio subprocess with all commands failing
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"Command failed"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        # Call the function
        result = await get_device_info()

        # Check that the function returns a dictionary even with failures
        assert isinstance(result, dict)

        # The dictionary should be mostly empty or contain default values
        if "screen_dimensions" in result:
            assert isinstance(result["screen_dimensions"], dict)
        if "android_version" in result:
            assert result["android_version"].get("release", "") == ""
        if "battery" in result:
            assert isinstance(result["battery"], dict)


@pytest.mark.asyncio
async def test_run_adb_command():
    """Test that run_adb_command calls the ADB command correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"mock command output", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        from main import run_adb_command

        result = await run_adb_command("devices")

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert args[1] == "devices"

        # Check that the result is the command output
        assert result == "mock command output"


@pytest.mark.asyncio
async def test_run_adb_command_complex():
    """Test that run_adb_command handles complex commands with multiple arguments correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(
        return_value=(b"package:com.android.example", b"")
    )

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function with a complex command
        from main import run_adb_command

        result = await run_adb_command("shell pm list packages com.android")

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert args[1] == "shell"
        assert args[2] == "pm"
        assert args[3] == "list"
        assert args[4] == "packages"
        assert args[5] == "com.android"

        # Check that the result is the command output
        assert result == "package:com.android.example"


@pytest.mark.asyncio
async def test_run_adb_command_empty():
    """Test that run_adb_command validates that command is not empty."""
    # Call the function with empty command and check that it raises the expected error
    from main import run_adb_command

    with pytest.raises(ValueError, match="Command cannot be empty"):
        await run_adb_command("")

    with pytest.raises(ValueError, match="Command cannot be empty"):
        await run_adb_command("   ")


@pytest.mark.asyncio
async def test_run_adb_command_error():
    """Test that run_adb_command handles errors correctly."""
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"ADB error message"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        # Call the function and check that it raises the expected error
        from main import run_adb_command

        with pytest.raises(RuntimeError, match="ADB command failed"):
            await run_adb_command("some-invalid-command")
