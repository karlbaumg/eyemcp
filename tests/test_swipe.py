import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from main import swipe_up, swipe_down, custom_swipe


@pytest.mark.asyncio
async def test_swipe_up():
    """Test that swipe_up calls the ADB command correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        result = await swipe_up()

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "shell" in args
        assert "input" in args
        assert "swipe" in args
        assert "360" in args  # start x
        assert "1000" in args  # start y
        assert "360" in args  # end x
        assert "500" in args  # end y
        assert "100" in args  # duration

        # Check that the result is a confirmation message
        assert "Performed swipe up from (360, 1000) to (360, 500)" in result


@pytest.mark.asyncio
async def test_swipe_up_error():
    """Test that swipe_up handles errors correctly."""
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"ADB error"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        # Call the function and check that it raises the expected error
        with pytest.raises(RuntimeError, match="ADB swipe up command failed"):
            await swipe_up()


@pytest.mark.asyncio
async def test_swipe_down():
    """Test that swipe_down calls the ADB command correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        result = await swipe_down()

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "shell" in args
        assert "input" in args
        assert "swipe" in args
        assert "360" in args  # start x
        assert "500" in args  # start y
        assert "360" in args  # end x
        assert "1000" in args  # end y
        assert "100" in args  # duration

        # Check that the result is a confirmation message
        assert "Performed swipe down from (360, 500) to (360, 1000)" in result


@pytest.mark.asyncio
async def test_swipe_down_error():
    """Test that swipe_down handles errors correctly."""
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"ADB error"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        # Call the function and check that it raises the expected error
        with pytest.raises(RuntimeError, match="ADB swipe down command failed"):
            await swipe_down()


@pytest.mark.asyncio
async def test_custom_swipe():
    """Test that custom_swipe calls the ADB command correctly."""
    # Mock the asyncio subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        # Call the function
        result = await custom_swipe(100, 200, 300, 400)

        # Check that the correct command was executed
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "adb"
        assert "shell" in args
        assert "input" in args
        assert "swipe" in args
        assert "100" in args  # start x
        assert "200" in args  # start y
        assert "300" in args  # end x
        assert "400" in args  # end y
        assert "100" in args  # duration

        # Check that the result is a confirmation message
        assert "Performed custom swipe from (100, 200) to (300, 400)" in result


@pytest.mark.asyncio
async def test_custom_swipe_invalid_coordinates():
    """Test that custom_swipe validates coordinates."""
    # Call the function with negative coordinates and check that it raises the expected error
    with pytest.raises(ValueError, match="Coordinates must be non-negative"):
        await custom_swipe(-10, 200, 300, 400)

    with pytest.raises(ValueError, match="Coordinates must be non-negative"):
        await custom_swipe(10, -200, 300, 400)

    with pytest.raises(ValueError, match="Coordinates must be non-negative"):
        await custom_swipe(10, 200, -300, 400)

    with pytest.raises(ValueError, match="Coordinates must be non-negative"):
        await custom_swipe(10, 200, 300, -400)


@pytest.mark.asyncio
async def test_custom_swipe_error():
    """Test that custom_swipe handles errors correctly."""
    # Mock the asyncio subprocess with error
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"ADB error"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        # Call the function and check that it raises the expected error
        with pytest.raises(RuntimeError, match="ADB custom swipe command failed"):
            await custom_swipe(100, 200, 300, 400)
