#!/bin/bash
# start_android.sh
#
# This script automates the setup process for Android device interaction:
# 1. Disconnects any connected ADB devices
# 2. Starts the limbar server using 'lim run android'
# 3. Waits for an Android device to connect
# 4. Enables tap visualization and pointer location on the connected Android device
# 5. Installs all APK files from the apks/ directory
# 6. Adds all installed apps to the Android home screen
#
# Usage: ./scripts/start_android.sh

# Exit on error
set -e

echo "=== Android Device Setup Script ==="

# Step 1: Disconnect any connected ADB devices
echo "Disconnecting any connected ADB devices..."
adb disconnect

# Step 2: Start the limbar server
echo "Starting limbar server..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if the server is already running
if pgrep -f "lim run android" > /dev/null; then
    echo "limbar server is already running"
    LIM_PID=$(pgrep -f "lim run android")
else
    # Start the server with nohup to keep it running even if the terminal closes
    # Redirect output to a log file for debugging
    nohup lim run android > logs/limbar_server.log 2>&1 &
    LIM_PID=$!
    
    # Check if the server started successfully
    if ! ps -p $LIM_PID > /dev/null; then
        echo "Error: Failed to start limbar server"
        exit 1
    fi
    
    # Give the server a moment to start
    echo "Waiting for server to initialize..."
    sleep 2
    
    echo "limbar server started with PID: $LIM_PID"
    echo "Server logs are available at: $(pwd)/logs/limbar_server.log"
fi

# Step 3: Wait for Android device to connect
echo "Waiting for Android device to connect..."

# Function to check if a device is connected
check_device_connected() {
    DEVICES=$(adb devices | grep -v "List" | grep -v "^$" | wc -l)
    if [ "$DEVICES" -gt 0 ]; then
        return 0  # Device is connected
    else
        return 1  # No device connected
    fi
}

# Wait for device with timeout
TIMEOUT=30
ELAPSED=0
INTERVAL=2

while ! check_device_connected && [ $ELAPSED -lt $TIMEOUT ]; do
    echo "No device detected. Waiting... ($ELAPSED/$TIMEOUT seconds)"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if ! check_device_connected; then
    echo "Warning: No Android device detected after $TIMEOUT seconds."
    echo "ADB commands may fail. Please connect a device and try again."
    echo "You can check device status with: ./scripts/server_status.sh"
else
    echo "Android device connected:"
    adb devices -l
fi

# Step 4: Enable tap visualization and pointer location
echo "Configuring Android device settings..."
sleep 5

# Enable tap visualization (shows circles where screen is touched)
echo "Enabling tap visualization..."
adb shell settings put system show_touches 1

# Enable pointer location (shows touch coordinates at top of screen)
echo "Enabling pointer location..."
adb shell settings put system pointer_location 1

# Additional useful settings
# Enable developer options if not already enabled
echo "Ensuring developer options are enabled..."
adb shell settings put global development_settings_enabled 1

# Keep screen on while charging
echo "Setting screen to stay on while charging..."
adb shell settings put global stay_on_while_plugged_in 3

# Step 5: Install all APK files from the apks/ directory
echo "=== Installing APK files from apks/ directory ==="
APK_DIR="$(dirname "$(dirname "$0")")/apks"
APK_COUNT=$(find "$APK_DIR" -name "*.apk" | wc -l | tr -d '[:space:]')

if [ "$APK_COUNT" -eq 0 ]; then
    echo "No APK files found in $APK_DIR"
else
    echo "Found $APK_COUNT APK file(s) to install"
    
    # Loop through each APK file in the apks/ directory
    find "$APK_DIR" -name "*.apk" | while read apk_file; do
        echo "Installing: $(basename "$apk_file")"
        
        # Install APK using ADB
        adb install -r "$apk_file"
        
        # Get package name from the APK
        PACKAGE_NAME=$(aapt dump badging "$apk_file" | grep package | awk -F"'" '{print $2}')
        
        if [ -n "$PACKAGE_NAME" ]; then
            echo "Installed package: $PACKAGE_NAME"
            
            # Get main activity name
            MAIN_ACTIVITY=$(aapt dump badging "$apk_file" | grep -A1 "launchable-activity" | head -n1 | awk -F"'" '{print $2}')
            
            if [ -n "$MAIN_ACTIVITY" ]; then
                echo "Adding $PACKAGE_NAME to home screen (Lawnchair launcher)..."
                
                # Method 1: Launch app drawer on Lawnchair
                adb shell input keyevent KEYCODE_HOME
                sleep 1
                
                # Swipe up from bottom to middle to open app drawer (common gesture for Lawnchair)
                SCREEN_SIZE=$(adb shell wm size | grep -o '[0-9]*x[0-9]*')
                WIDTH=$(echo $SCREEN_SIZE | cut -d'x' -f1)
                HEIGHT=$(echo $SCREEN_SIZE | cut -d'x' -f2)
                
                CENTER_X=$((WIDTH / 2))
                BOTTOM_Y=$((HEIGHT - 100))
                CENTER_Y=$((HEIGHT / 2))
                
                # Open app drawer
                adb shell input swipe $CENTER_X $BOTTOM_Y $CENTER_X $CENTER_Y 300
                sleep 2
                
                # Method 2: Use Lawnchair's broadcast receiver to add shortcut (if available)
                echo "Attempting to add shortcut via intent broadcast..."
                adb shell am broadcast -a ch.deletescape.lawnchair.ADD_ITEM --es packageName "$PACKAGE_NAME" --es className "$MAIN_ACTIVITY"
                sleep 1
                
                # Method 3: Direct launch approach (fallback)
                echo "Launching app to ensure it appears in recents..."
                adb shell am start -n "$PACKAGE_NAME/$MAIN_ACTIVITY" -a android.intent.action.MAIN -c android.intent.category.LAUNCHER
                sleep 2
                
                # Go back to home
                adb shell input keyevent KEYCODE_HOME
                sleep 1
                
                # Inform user that manual pinning might be needed
                echo "Note: You may need to manually pin the app to home screen if automatic methods didn't work."
                echo "The app has been launched at least once and should appear in your app drawer."
            else
                echo "Could not determine main activity for $PACKAGE_NAME"
            fi
        else
            echo "Could not determine package name for $(basename "$apk_file")"
        fi
        
        echo "-------------------------"
    done
fi

echo "=== Setup Complete ==="
echo "limbar server is running in the background (PID: $LIM_PID)"
echo "Tap visualization and pointer location are enabled"
echo ""
echo "To check server status: ./scripts/server_status.sh"
echo "To stop the server: ./scripts/stop_server.sh"
echo "  or manually with: kill $LIM_PID"
echo ""
echo "To disable tap visualization: adb shell settings put system show_touches 0"
echo "To disable pointer location: adb shell settings put system pointer_location 0"

# Save the PID to a file for later use by stop_server.sh
echo $LIM_PID > logs/server_pid.txt
