# EyeMCP: Android Screen Interaction via Vision AI

EyeMCP is an MCP server that provides tools for interacting with Android devices using vision AI. It allows you to describe screens, find elements by description, and tap elements based on their descriptions.

## Features

- **Screen Description**: Get detailed descriptions of what's visible on the Android screen
- **Element Finding**: Find UI elements based on textual descriptions
- **Element Tapping**: Tap UI elements based on textual descriptions
- **Coordinate Calibration**: Calibrate the coordinate system for accurate element targeting

## Project Structure

```
eyemcp/
├── main.py              # Entry point and MCP server implementation
├── vision.py            # Vision AI functionality for screen analysis
├── calibration.py       # Coordinate calibration system
├── calibration.csv      # Default calibration reference points
├── pyproject.toml       # Project dependencies and configuration
├── .env.example         # Example environment variables
├── scripts/             # Utility scripts
│   ├── setup_android.sh # Script to setup Android device for interaction
│   └── README.md        # Documentation for scripts
└── tests/               # Test suite
    ├── conftest.py      # Pytest configuration
    ├── test_main.py     # Tests for main.py
    ├── test_vision.py   # Tests for vision.py
    └── test_calibration.py  # Tests for calibration.py
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

3. Connect an Android device via ADB

## Utility Scripts

The project includes utility scripts to help with common tasks:

### Android Device Setup

To quickly set up an Android device for interaction:

```bash
./scripts/setup_android.sh
```

This script:
- Disconnects any connected ADB devices
- Starts the EyeMCP server
- Enables tap visualization and pointer location on the device
- Configures additional helpful developer settings

See `scripts/README.md` for more details.

## Testing

The project includes a comprehensive test suite using pytest. To run the tests:

```bash
pytest
```

For more details about the test suite, see [TESTING.md](TESTING.md).

## Usage with MCP Inspector

### Initial Setup

1. Start the MCP server:
   ```bash
   python main.py
   ```

2. Connect to the server in the MCP Inspector

3. Run the calibration tool first:
   ```json
   {
     "tool": "calibrate",
     "args": {
       "calibration_file": "calibration.csv"
     }
   }
   ```
   This will navigate to the home screen and calibrate the coordinate system using the reference points in the calibration file.

### Using the Tools

#### Describe Screen

Get a detailed description of all interactive elements on the screen:

```json
{
  "tool": "describe_screen",
  "args": {}
}
```

Optional parameters:
- `device_id`: Specify a device ID if multiple devices are connected

#### Find Element by Description

Find an element on the screen based on a textual description:

```json
{
  "tool": "find_element_by_description",
  "args": {
    "description": "Settings icon in the top right corner"
  }
}
```

This returns a JSON object with:
- `x`: X-coordinate of the element's center
- `y`: Y-coordinate of the element's center
- `confidence`: Confidence score (0.0-1.0)
- `element_description`: Description of the found element

#### Tap Element by Description

Find and tap an element based on a textual description:

```json
{
  "tool": "tap_element_by_description",
  "args": {
    "description": "Login button at the bottom of the screen"
  }
}
```

#### Direct Coordinate Tapping

Tap at specific coordinates:

```json
{
  "tool": "tap_android_screen",
  "args": {
    "x": 360,
    "y": 800
  }
}
```

### Calibration Tools

#### Calibrate Coordinate System

Calibrate the coordinate system using a calibration file:

```json
{
  "tool": "calibrate",
  "args": {
    "calibration_file": "calibration.csv",
    "device_id": null
  }
}
```

## Tips for Effective Use

1. **Always calibrate first**: Run the calibration tool before using any coordinate-based operations to ensure accuracy.

2. **Be specific in descriptions**: When using `find_element_by_description` or `tap_element_by_description`, provide detailed descriptions that uniquely identify the element.

3. **Check confidence scores**: The `find_element_by_description` tool returns a confidence score. If it's low (< 0.7), the element might not be correctly identified.

4. **Use relative positions**: Include relative positions in your descriptions (e.g., "button at the bottom of the screen" or "icon in the top-right corner").

5. **Handle errors gracefully**: The tools will raise exceptions if elements can't be found or if descriptions are ambiguous.

## Troubleshooting

- **Calibration fails**: Ensure your device is on the home screen and that the elements in the calibration file are visible.
- **Elements not found**: Try providing more detailed descriptions or check if the element is actually visible on the screen.
- **ADB connection issues**: Verify that your device is properly connected and authorized for ADB.
