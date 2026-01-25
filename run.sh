#!/bin/bash
# GHOST PROTOCOL - Linux Fullscreen Launcher
# Opens a fullscreen terminal and runs ghost.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect available terminal emulator and launch fullscreen
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --full-screen -- bash -c "cd '$SCRIPT_DIR' && python3 ghost.py; exec bash"
elif command -v konsole &> /dev/null; then
    konsole --fullscreen -e bash -c "cd '$SCRIPT_DIR' && python3 ghost.py"
elif command -v xfce4-terminal &> /dev/null; then
    xfce4-terminal --fullscreen -e "bash -c 'cd \"$SCRIPT_DIR\" && python3 ghost.py'"
elif command -v xterm &> /dev/null; then
    xterm -fullscreen -e "cd '$SCRIPT_DIR' && python3 ghost.py"
elif command -v kitty &> /dev/null; then
    kitty --start-as=fullscreen bash -c "cd '$SCRIPT_DIR' && python3 ghost.py"
elif command -v alacritty &> /dev/null; then
    alacritty -o window.startup_mode=Fullscreen -e bash -c "cd '$SCRIPT_DIR' && python3 ghost.py"
else
    # Fallback - just run in current terminal
    cd "$SCRIPT_DIR"
    python3 ghost.py
fi
