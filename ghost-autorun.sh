#!/bin/bash
# GHOST PROTOCOL - USB Auto-Run Script
# This is triggered by udev when the USB is plugged in

# Get the USB mount point
USB_MOUNT=$(findmnt -rn -S LABEL=vault -o TARGET 2>/dev/null || echo "/media/$USER/vault")

# Wait for mount
sleep 2

# Check if ghost.py exists
if [ -f "$USB_MOUNT/ghost.py" ]; then
    # Launch in a new fullscreen terminal
    export DISPLAY=:0
    
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --full-screen -- bash -c "python3 '$USB_MOUNT/ghost.py'"
    elif command -v konsole &> /dev/null; then
        konsole --fullscreen -e bash -c "python3 '$USB_MOUNT/ghost.py'"
    elif command -v xfce4-terminal &> /dev/null; then
        xfce4-terminal --fullscreen -e "python3 '$USB_MOUNT/ghost.py'"
    elif command -v xterm &> /dev/null; then
        xterm -fullscreen -e "python3 '$USB_MOUNT/ghost.py'"
    fi
fi
