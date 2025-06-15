#!/bin/bash
# stop_server.sh
#
# This script stops the limbar server that was started by setup_android.sh
#
# Usage: ./scripts/stop_server.sh

# Exit on error
set -e

echo "=== Stopping limbar Server ==="

# Check if PID file exists
if [ ! -f "logs/server_pid.txt" ]; then
    echo "No server PID file found. Server may not be running."
    
    # Check if we can find the process anyway
    if pgrep -f "lim run android" > /dev/null; then
        LIM_PID=$(pgrep -f "lim run android")
        echo "Found running server with PID: $LIM_PID"
    else
        echo "No running limbar server found."
        exit 0
    fi
else
    # Read PID from file
    LIM_PID=$(cat logs/server_pid.txt)
    echo "Found server PID: $LIM_PID"
    
    # Check if process with this PID exists
    if ! ps -p $LIM_PID > /dev/null; then
        echo "Process with PID $LIM_PID is not running."
        echo "Cleaning up PID file..."
        rm logs/server_pid.txt
        exit 0
    fi
fi

# Stop the server
echo "Stopping limbar server (PID: $LIM_PID)..."
kill $LIM_PID

# Wait for the process to terminate
echo "Waiting for server to stop..."
for i in {1..10}; do
    if ! ps -p $LIM_PID > /dev/null; then
        echo "Server stopped successfully."
        break
    fi
    sleep 1
    
    # If we've waited too long, try SIGKILL
    if [ $i -eq 10 ]; then
        echo "Server is not responding. Forcing termination..."
        kill -9 $LIM_PID
        sleep 1
    fi
done

# Verify server has stopped
if ps -p $LIM_PID > /dev/null; then
    echo "Warning: Failed to stop server. Please manually kill process $LIM_PID."
else
    echo "Server stopped successfully."
    # Clean up PID file
    if [ -f "logs/server_pid.txt" ]; then
        rm logs/server_pid.txt
    fi
fi

echo "=== Server Shutdown Complete ==="
