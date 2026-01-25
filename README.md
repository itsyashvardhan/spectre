# ⚡ SPECTRE System Interface

A high-fidelity, native terminal-based hacker calling card and system monitoring dashboard.

## Features

- **Dynamic TUI**: Advanced curses-based interface with responsive panels.
- **System Monitoring**: Real-time CPU, RAM, Disk, Load, and Network stats.
- **Advanced Hardware**: CPU Temperature, GPU usage (nvidia), Battery status, and Disk I/O.
- **Rotating ASCII Globe**: Real-time animated globe for that elite hacker aesthetic.
- **Arsenal Panel**: Visual representation of your core tools and technologies.
- **Integrated Terminal**: Fully functional sub-shell with built-in commands (`proc`, `scan`, `help`).
- **File Browser**: Interactive filesystem browser with file preview panel.
- **Aesthetic Themes**: Cycle through 7 beautiful color themes (Ghost, Mint, Lavender, Nord, etc.).
- **Mouse Support**: Toggle focus between panels using your mouse.

## Usage

### Linux/Mac
```bash
./run.sh
# or
python3 ghost.py
```

### Windows
```batch
run.bat
# or
python ghost.py
```

## Commands (Inside Interface)

- **TAB**: Switch focus between File Browser and Terminal
- **Ctrl+T**: Cycle through available themes
- **Mouse Click**: Select panels or files
- **Q** or **exit**: Close the application
- **Terminal built-ins**: `proc`, `scan`, `kill`, `help`, `about`

## Customization

Edit `ghost.py` to tailor the interface:
- **Logo**: Modify the `LOGO` constant for a custom banner.
- **Arsenal**: Update the `ARSENAL` list for your specific toolset.
- **Themes**: Add custom color hexes to the `THEMES` dictionary.

---

```
╔═══════════════════════════════════╗
║  SPECTRE SYSTEM v5.1.0            ║
║  Yashvardhan Singh // @yashvs     ║
╚═══════════════════════════════════╝
```
