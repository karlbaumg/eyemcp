# EyeMCP Scripts

This directory contains utility scripts for the EyeMCP project.

## Available Scripts

### setup_android.sh

This script automates the setup process for Android device interaction:

1. Disconnects any connected ADB devices
2. Starts the EyeMCP server using 'lim run android'
3. Enables tap visualization and pointer location on the connected Android device
4. Configures additional helpful developer settings

#### Usage

```bash
./scripts/setup_android.sh
```

#### What it does

- Disconnects any existing ADB connections
- Starts the EyeMCP server in the background with proper logging
- Checks if the server is already running to prevent duplicate instances
- Enables tap visualization (shows circles where screen is touched)
- Enables pointer location (shows touch coordinates at top of screen)
- Ensures developer options are enabled
- Configures the screen to stay on while charging
- Saves the server PID for later use by stop_server.sh

#### How to stop

To stop the EyeMCP server, use the stop_server.sh script:

```bash
./scripts/stop_server.sh
```

This script will:
- Find the running server process
- Gracefully terminate the server
- Clean up the PID file
- Verify the server has stopped

You can also manually stop it using the PID that was displayed when starting:

```bash
kill <PID>
```

To disable the visual indicators:

```bash
# Disable tap visualization
adb shell settings put system show_touches 0

# Disable pointer location
adb shell settings put system pointer_location 0
```

### stop_server.sh

This script stops the EyeMCP server that was started by setup_android.sh.

#### Usage

```bash
./scripts/stop_server.sh
```

#### What it does

- Checks if the server is running by looking for the PID file
- If the server is running, sends a SIGTERM signal to gracefully stop it
- Waits for the server to terminate
- If the server doesn't terminate within 10 seconds, forces termination with SIGKILL
- Verifies that the server has stopped
- Cleans up the PID file

### test_setup.sh

This script tests the functionality of setup_android.sh without actually running the EyeMCP server. It's useful for verifying ADB commands work correctly.

#### Usage

```bash
./scripts/test_setup.sh
```

#### What it does

- Checks if ADB is installed and available
- Verifies that an Android device is connected
- Tests the ADB disconnect command
- Tests enabling tap visualization
- Tests enabling pointer location
- Tests enabling developer options
- Tests setting the screen to stay on while charging

## Adding New Scripts

When adding new scripts to this directory:

1. Make sure to add a shebang line (e.g., `#!/bin/bash`)
2. Include documentation at the top of the script
3. Make the script executable with `chmod +x scripts/your_script.sh`
4. Update this README.md file with information about the new script
