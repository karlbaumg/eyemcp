# EyeMCP: Android Screen Interaction via Vision AI

EyeMCP is an MCP server that provides tools for interacting with Android devices using vision AI. It allows you to describe screens, find elements by description, and tap elements based on their descriptions.

## Features

- **Screen Description**: Get detailed descriptions of what's visible on the Android screen
- **Element Finding**: Find UI elements based on textual descriptions
- **Element Tapping**: Tap UI elements based on textual descriptions

## Project Structure

```
eyemcp/
├── main.py              # Entry point and MCP server implementation
├── vision.py            # Vision AI functionality for screen analysis
├── pyproject.toml       # Project dependencies and configuration
├── .env.example         # Example environment variables
├── scripts/             # Utility scripts
│   ├── setup_android.sh # Script to setup Android device for interaction
│   └── README.md        # Documentation for scripts
└── tests/               # Test suite
    ├── conftest.py      # Pytest configuration
    ├── test_main.py     # Tests for main.py
    └── test_vision.py   # Tests for vision.py
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

#### Analyze Screen Detail

Analyze specific visual details on the screen based on a prompt:

```json
{
  "tool": "analyze_screen_detail",
  "args": {
    "prompt": "What color is the login button and does it have rounded corners?"
  }
}
```

This tool is useful for getting detailed information about UI elements' visual appearance, such as:
- Colors of specific elements
- Shape characteristics (rounded corners, borders, etc.)
- Typography details (font sizes, styles, etc.)
- Spacing and layout information
- Visual design patterns and consistency

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

#### Send Keystrokes

Send a series of keystrokes to the device:

```json
{
  "tool": "send_keys",
  "args": {
    "text": "https://example.com"
  }
}
```

Optional parameters:
- `device_id`: Specify a device ID if multiple devices are connected

This tool is useful for entering text such as URLs, search terms, or login credentials.

#### Run Arbitrary ADB Command

Execute any ADB command directly:

```json
{
  "tool": "run_adb_command",
  "args": {
    "command": "shell pm list packages"
  }
}
```

This tool allows running any ADB command and returns its output. It's useful for:
- Listing installed packages
- Checking device properties
- Managing apps and settings
- Running shell commands
- Other advanced ADB operations not covered by specialized tools

Note: The `command` should NOT include the 'adb' prefix as it's automatically added. For example, use `shell pm list packages` instead of `adb shell pm list packages`.

#### Swipe Actions

##### Swipe Up

Perform a standard swipe up gesture (scrolls down content):

```json
{
  "tool": "swipe_up",
  "args": {}
}
```

This performs a swipe from coordinates (360,1000) to (360,500) in 100ms, useful for scrolling down lists, pages, and content.

##### Swipe Down

Perform a standard swipe down gesture (scrolls up content):

```json
{
  "tool": "swipe_down",
  "args": {}
}
```

This performs a swipe from coordinates (360,500) to (360,1000) in 100ms, useful for scrolling up lists, pages, and content.

##### Custom Swipe

Perform a swipe between custom coordinates:

```json
{
  "tool": "custom_swipe",
  "args": {
    "x1": 100,
    "y1": 500,
    "x2": 600,
    "y2": 500
  }
}
```

This performs a swipe from coordinates (x1,y1) to (x2,y2) in 100ms, useful for custom gesture actions like horizontal scrolling, precise positioning, or advanced gestures.


## Tips for Effective Use

1. **Be specific in descriptions**: When using `find_element_by_description` or `tap_element_by_description`, provide detailed descriptions that uniquely identify the element.

2. **Check confidence scores**: The `find_element_by_description` tool returns a confidence score. If it's low (< 0.7), the element might not be correctly identified.

3. **Use relative positions**: Include relative positions in your descriptions (e.g., "button at the bottom of the screen" or "icon in the top-right corner").

4. **Be precise with visual analysis prompts**: When using `analyze_screen_detail`, ask specific questions about visual aspects to get the most accurate and useful responses.

5. **Handle errors gracefully**: The tools will raise exceptions if elements can't be found or if descriptions are ambiguous.

## Troubleshooting

- **Elements not found**: Try providing more detailed descriptions or check if the element is actually visible on the screen.
- **ADB connection issues**: Verify that your device is properly connected and authorized for ADB.
