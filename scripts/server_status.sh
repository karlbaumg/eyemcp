#!/bin/bash
# server_status.sh
#
# This script checks the status of the limbar server
#
# Usage: ./scripts/server_status.sh

echo "=== limbar Server Status ==="

# Check if PID file exists
if [ -f "logs/server_pid.txt" ]; then
    LIM_PID=$(cat logs/server_pid.txt)
    echo "Server PID file found: $LIM_PID"
    
    # Check if process with this PID exists
    if ps -p $LIM_PID > /dev/null; then
        echo "✓ Server is running with PID: $LIM_PID"
        
        # Get process details
        echo ""
        echo "Process details:"
        ps -p $LIM_PID -o pid,ppid,user,%cpu,%mem,start,time,command
        
        # Check log file
        if [ -f "logs/limbar_server.log" ]; then
            echo ""
            echo "Log file exists: $(pwd)/logs/limbar_server.log"
            echo "Last 5 lines of log:"
            tail -n 5 logs/limbar_server.log
        else
            echo ""
            echo "No log file found at: $(pwd)/logs/limbar_server.log"
        fi
    else
        echo "✗ Process with PID $LIM_PID is not running."
        echo "The PID file may be stale. You can remove it with:"
        echo "rm logs/server_pid.txt"
    fi
else
    echo "No server PID file found at: $(pwd)/logs/server_pid.txt"
    
    # Check if we can find the process anyway
    if pgrep -f "lim run android" > /dev/null; then
        LIM_PID=$(pgrep -f "lim run android")
        echo "✓ Server is running with PID: $LIM_PID (PID file missing)"
        echo ""
        echo "Process details:"
        ps -p $LIM_PID -o pid,ppid,user,%cpu,%mem,start,time,command
    else
        echo "✗ No running limbar server found."
    fi
fi

# Check Android device connection
echo ""
echo "Android device status:"
adb devices -l

# Check tap visualization and pointer location settings
echo ""
echo "Android settings:"
SHOW_TOUCHES=$(adb shell settings get system show_touches 2>/dev/null)
POINTER_LOCATION=$(adb shell settings get system pointer_location 2>/dev/null)

if [ -n "$SHOW_TOUCHES" ]; then
    if [ "$SHOW_TOUCHES" = "1" ]; then
        echo "✓ Tap visualization: ENABLED"
    else
        echo "✗ Tap visualization: DISABLED"
    fi
else
    echo "? Tap visualization: UNKNOWN (could not retrieve setting)"
fi

if [ -n "$POINTER_LOCATION" ]; then
    if [ "$POINTER_LOCATION" = "1" ]; then
        echo "✓ Pointer location: ENABLED"
    else
        echo "✗ Pointer location: DISABLED"
    fi
else
    echo "? Pointer location: UNKNOWN (could not retrieve setting)"
fi

echo ""
echo "=== Status Check Complete ==="
