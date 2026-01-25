#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  SPECTRE | Advanced System Interface | USB Calling Card                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import curses
import os
import sys
import time
import getpass
import socket
import subprocess
import pty
import select
import threading
import json
import random
from collections import deque
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM INFO
# ═══════════════════════════════════════════════════════════════════════════════
USER = getpass.getuser()
HOST = socket.gethostname()
PLATFORM = sys.platform.upper()
HOME = os.path.expanduser("~")
HOME = os.path.expanduser("~")
START_TIME = time.time()
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".spectre.json")

# ═══════════════════════════════════════════════════════════════════════════════
# PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════
def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {"theme": 0, "path": HOME}

def save_config(theme_idx, path):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"theme": theme_idx, "path": path}, f)
    except: pass

# ═══════════════════════════════════════════════════════════════════════════════
# EVENT LOGGING
# ═══════════════════════════════════════════════════════════════════════════════
class EventManager:
    def __init__(self):
        self.events = deque(maxlen=20)
        self.add("System initialized.")
        self.flavor_messages = [
            "Encrypted connection established", "Scanning local subnet...", 
            "Packet intercepted [TCP/80]", "Brute-force mitigation active",
            "Rootkit check: Clean", "Public IP hidden", "Proxy chain: 3 nodes",
            "Handshake captured", "Buffer flushed", "Daemon restarted"
        ]
        self.last_flavor = time.time()
    
    def add(self, msg, type="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.events.appendleft(f"[{ts}] {msg}")
    
    def get_latest(self):
        return self.events[0] if self.events else ""
    
    def update(self):
        # Insert random flavor text every 10-30 seconds
        if time.time() - self.last_flavor > random.randint(10, 30):
            self.last_flavor = time.time()
            self.add(random.choice(self.flavor_messages), "FLAVOR")

EVENTS = EventManager()

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR THEMES - Aesthetic & Pastel
# ═══════════════════════════════════════════════════════════════════════════════
THEMES = {
    "ghost": {"primary": curses.COLOR_WHITE, "secondary": curses.COLOR_CYAN, "accent": curses.COLOR_WHITE},
    "mint": {"primary": curses.COLOR_GREEN, "secondary": curses.COLOR_WHITE, "accent": curses.COLOR_CYAN},
    "lavender": {"primary": curses.COLOR_MAGENTA, "secondary": curses.COLOR_WHITE, "accent": curses.COLOR_WHITE},
    "ocean": {"primary": curses.COLOR_BLUE, "secondary": curses.COLOR_WHITE, "accent": curses.COLOR_CYAN},
    "sunset": {"primary": curses.COLOR_YELLOW, "secondary": curses.COLOR_RED, "accent": curses.COLOR_MAGENTA},
    "nord": {"primary": curses.COLOR_CYAN, "secondary": curses.COLOR_BLUE, "accent": curses.COLOR_WHITE},
    "mono": {"primary": curses.COLOR_WHITE, "secondary": curses.COLOR_WHITE, "accent": curses.COLOR_WHITE},
}
THEME_NAMES = list(THEMES.keys())

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM STATS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def get_network_info():
    info = {"ssid": "N/A", "ip": "N/A", "gateway": "N/A"}
    try:
        result = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0: info["ssid"] = result.stdout.strip() or "Ethernet"
    except: pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["ip"] = s.getsockname()[0]
        s.close()
    except: pass
    return info

def ping_host(host="8.8.8.8"):
    try:
        result = subprocess.run(["ping", "-c", "1", "-W", "1", host], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'time=' in line:
                    return f"{float(line.split('time=')[1].split()[0]):.1f}ms"
    except: pass
    return "---"

def get_cpu_usage():
    try:
        with open('/proc/stat', 'r') as f:
            fields = f.readline().split()[1:]
            return 100 - (int(fields[3]) * 100 // sum(int(x) for x in fields))
    except: return 0

def get_memory_usage():
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            total, avail = int(lines[0].split()[1]), int(lines[2].split()[1])
            used = total - avail
            return f"{used//1048576}G/{total//1048576}G", (used*100)//total
    except: return "N/A", 0

def get_disk_usage():
    try:
        st = os.statvfs('/')
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        pct = (used * 100) // total
        return f"{used//1073741824}G/{total//1073741824}G", pct
    except: return "N/A", 0

def get_load_avg():
    try:
        with open('/proc/loadavg', 'r') as f:
            return f.read().split()[0]
    except: return "0.00"

class NetSpeed:
    def __init__(self):
        self.last_rx, self.last_tx, self.last_time = 0, 0, 0
        self.down_speed, self.up_speed = "0 B/s", "0 B/s"
    
    def get_bytes(self):
        rx, tx = 0, 0
        try:
            with open('/proc/net/dev', 'r') as f:
                for line in f.readlines()[2:]:
                    parts = line.split()
                    if parts[0].rstrip(':') not in ['lo']:
                        rx += int(parts[1])
                        tx += int(parts[9])
        except: pass
        return rx, tx
    
    def format_speed(self, bps):
        if bps >= 1048576: return f"{bps/1048576:.1f}MB/s"
        elif bps >= 1024: return f"{bps/1024:.1f}KB/s"
        else: return f"{bps:.0f}B/s"
    
    def update(self):
        now = time.time()
        rx, tx = self.get_bytes()
        if self.last_time > 0:
            elapsed = now - self.last_time
            if elapsed > 0:
                self.down_speed = self.format_speed((rx - self.last_rx) / elapsed)
                self.up_speed = self.format_speed((tx - self.last_tx) / elapsed)
        self.last_rx, self.last_tx, self.last_time = rx, tx, now
        return self.down_speed, self.up_speed

NET_SPEED = NetSpeed()

# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED MONITORING
# ═══════════════════════════════════════════════════════════════════════════════
def get_cpu_temp():
    try:
        for i in range(10):
            path = f'/sys/class/thermal/thermal_zone{i}/temp'
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f"{int(f.read().strip()) / 1000:.1f}°C"
    except: pass
    return "N/A"

def get_gpu_usage():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu', 
                                '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            return f"{parts[0].strip()}% {parts[1].strip()}°C"
    except: pass
    return "N/A"

def get_battery():
    try:
        for bat in ['BAT0', 'BAT1', 'battery']:
            path = f'/sys/class/power_supply/{bat}'
            if os.path.exists(path):
                with open(f'{path}/capacity', 'r') as f:
                    cap = f.read().strip()
                try:
                    with open(f'{path}/status', 'r') as f:
                        s = f.read().strip()
                        status = "⚡" if s == "Charging" else "🔋" if s == "Discharging" else "✓"
                except: status = "?"
                return f"{cap}% {status}"
    except: pass
    return "N/A"

def get_open_ports():
    ports = []
    try:
        result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True, timeout=2)
        for line in result.stdout.split('\n')[1:]:
            if 'LISTEN' in line:
                parts = line.split()
                if len(parts) >= 5:
                    addr = parts[4].split(':')[-1]
                    if addr.isdigit(): ports.append(addr)
    except: pass
    return ports[:6] if ports else ["None"]

def get_connections():
    try:
        result = subprocess.run(['ss', '-t', 'state', 'established'], capture_output=True, text=True, timeout=2)
        return str(max(0, len(result.stdout.strip().split('\n')) - 1))
    except: return "0"

def get_disk_io():
    try:
        with open('/proc/diskstats', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 14 and parts[2] in ['sda', 'nvme0n1', 'vda']:
                    return f"R:{int(parts[5])*512//1073741824}G W:{int(parts[9])*512//1073741824}G"
    except: pass
    return "N/A"

def get_per_core_cpu():
    cores = []
    try:
        with open('/proc/stat', 'r') as f:
            for line in f:
                if line.startswith('cpu') and line[3].isdigit():
                    parts = line.split()[1:]
                    total = sum(int(x) for x in parts)
                    idle = int(parts[3])
                    cores.append(100 - (idle * 100 // total) if total > 0 else 0)
    except: pass
    return cores[:4] if cores else [0]

def get_processes():
    """Get list of processes with PID, name, CPU%, time."""
    procs = []
    try:
        result = subprocess.run(['ps', '-eo', 'pid,comm,%cpu,etime', '--sort=-%cpu'],
                               capture_output=True, text=True, timeout=3)
        for line in result.stdout.strip().split('\n')[1:51]:
            parts = line.split()
            if len(parts) >= 4:
                procs.append({
                    'pid': parts[0],
                    'name': parts[1][:15],
                    'cpu': parts[2],
                    'time': parts[3]
                })
    except: pass
    return procs

def scan_network():
    """Scan local network for devices."""
    devices = []
    try:
        # Get local IP range
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=2)
        subnet = None
        for line in result.stdout.split('\n'):
            if 'src' in line and 'default' not in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if '/' in p and '.' in p:
                        subnet = p
                        break
        
        if subnet:
            # Use arp-scan or fall back to arp
            try:
                result = subprocess.run(['arp-scan', '-l'], capture_output=True, text=True, timeout=10)
                for line in result.stdout.split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 3 and '.' in parts[0]:
                        devices.append({
                            'ip': parts[0],
                            'mac': parts[1][:17],
                            'vendor': parts[2][:20] if len(parts) > 2 else 'Unknown'
                        })
            except:
                # Fallback to arp cache
                result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=3)
                for line in result.stdout.split('\n')[1:]:
                    parts = line.split()
                    if len(parts) >= 3 and '.' in parts[0]:
                        devices.append({
                            'ip': parts[0],
                            'mac': parts[2][:17] if len(parts) > 2 else 'N/A',
                            'vendor': 'Unknown'
                        })
    except: pass
    return devices[:20]

def read_file_preview(filepath, max_lines=50):
    """Read file for preview."""
    try:
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            if size > 1048576:  # > 1MB
                return ["[File too large to preview]", f"Size: {size//1048576}MB"]
            
            # Check if binary
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:
                    return ["[Binary file]", f"Size: {size} bytes"]
            
            # Read text
            with open(filepath, 'r', errors='replace') as f:
                lines = f.readlines()[:max_lines]
                return [l.rstrip()[:200] for l in lines]
    except Exception as e:
        return [f"[Error: {e}]"]
    return ["[Cannot preview]"]



# ═══════════════════════════════════════════════════════════════════════════════
# ASCII LOGO
# ═══════════════════════════════════════════════════════════════════════════════
LOGO = [
    "███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗",
    "██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝",
    "███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗  ",
    "╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝  ",
    "███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗",
    "╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝",
]

# ═══════════════════════════════════════════════════════════════════════════════
# FILESYSTEM BROWSER
# ═══════════════════════════════════════════════════════════════════════════════
class FileBrowser:
    def __init__(self):
        self.path = HOME
        self.selected = 0
        self.scroll = 0
        self.items = []
        self.selected_file = None  # For preview
        self.refresh()
    
    def refresh(self):
        try:
            entries = os.listdir(self.path)
            dirs = sorted([d for d in entries if os.path.isdir(os.path.join(self.path, d))])
            files = sorted([f for f in entries if os.path.isfile(os.path.join(self.path, f))])
            self.items = [("📁", "..", True)] if self.path != "/" else []
            self.items += [("📂", d + "/", True) for d in dirs]
            self.items += [("📄", f, False) for f in files]
        except:
            self.items = [("❌", "Permission denied", False)]
        self.selected = min(self.selected, max(0, len(self.items) - 1))
        self.selected_file = None
    
    def up(self):
        if self.selected > 0:
            self.selected -= 1
            self._update_selection()
    
    def down(self):
        if self.selected < len(self.items) - 1:
            self.selected += 1
            self._update_selection()
    
    def _update_selection(self):
        if self.items:
            icon, name, is_dir = self.items[self.selected]
            if not is_dir:
                self.selected_file = os.path.join(self.path, name)
            else:
                self.selected_file = None
    
    def enter(self):
        if not self.items: return
        icon, name, is_dir = self.items[self.selected]
        if is_dir:
            if name == "..":
                self.path = os.path.dirname(self.path) or "/"
            else:
                new = os.path.join(self.path, name.rstrip('/'))
                if os.access(new, os.R_OK): self.path = new
            self.selected = 0
            self.scroll = 0
            self.refresh()
            EVENTS.add(f"Dir: {self.path}")
        else:
            # Select file for preview
            self.selected_file = os.path.join(self.path, name)

# ═══════════════════════════════════════════════════════════════════════════════
# TERMINAL WITH PROC COMMAND
# ═══════════════════════════════════════════════════════════════════════════════
class Terminal:
    def __init__(self):
        self.output = [
            "╔═══════════════════════════════════════════════════╗",
            f"║  SPECTRE Terminal | {USER}@{HOST}                 ║",
            "║  Commands: help, proc, scan, kill <pid>, clear    ║",
            "╚═══════════════════════════════════════════════════╝",
            "",
        ]
        self.cwd = os.getcwd()
        self.history = []
        self.hist_idx = -1
        self.input = ""
        self.cursor = 0
        self.scroll = 0
        self.should_exit = False
    
    def prompt(self):
        return f"{USER}@{HOST}:{self.cwd.replace(HOME, '~')}$ "
    
    def execute(self, cmd):
        if not cmd.strip(): return
        
        self.scroll = 0
        
        self.history.append(cmd)
        self.hist_idx = -1
        self.output.append(f"{self.prompt()}{cmd}")
        
        cmd_lower = cmd.strip().lower()
        
        # Built-in: help
        if cmd_lower == "help":
            self.output.append("╔═════════ TERMINAL COMMANDS ═════════╗")
            self.output.append("║ proc       - List active processes  ║")
            self.output.append("║ scan       - Network device scan    ║")
            self.output.append("║ kill <pid> - Terminate a process    ║")
            self.output.append("║ clear      - Clear terminal output  ║")
            self.output.append("║ cd <dir>   - Change directory       ║")
            self.output.append("║ ls, pwd    - Standard shell cmds    ║")
            self.output.append("║ about      - System details         ║")
            self.output.append("║ exit/quit  - Terminate SPECTRE      ║")
            self.output.append("╚═════════════════════════════════════╝")
        
        elif cmd_lower == "about":
            self.output.append(f"SPECTRE System Interface v5.1.0")
            self.output.append(f"Operator: {USER} // Protocol: GHOST")
            self.output.append(f"Last system breach: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
        elif cmd_lower in ["exit", "quit"]:
            self.output.append("Terminating session...")
            # We need a way to tell the TUI to stop.
            # Since Terminal is a component, we can use a flag.
            self.should_exit = True
            
        # Built-in: proc - list processes
        if cmd_lower == "proc":
            procs = get_processes()
            self.output.append(f"{'PID':<8} {'NAME':<16} {'CPU%':<8} {'TIME'}")
            self.output.append("-" * 45)
            for p in procs[:30]:
                self.output.append(f"{p['pid']:<8} {p['name']:<16} {p['cpu']:<8} {p['time']}")
        
        # Built-in: scan - network scan
        elif cmd_lower == "scan":
            self.output.append("Scanning network...")
            devices = scan_network()
            if devices:
                self.output.append(f"{'IP':<16} {'MAC':<18} {'VENDOR'}")
                self.output.append("-" * 55)
                for d in devices:
                    self.output.append(f"{d['ip']:<16} {d['mac']:<18} {d['vendor']}")
            else:
                self.output.append("No devices found (try: sudo arp-scan -l)")
        
        # Built-in: kill <pid>
        elif cmd_lower.startswith("kill "):
            pid = cmd.strip()[5:].strip()
            try:
                os.kill(int(pid), 9)
                self.output.append(f"Killed process {pid}")
            except Exception as e:
                self.output.append(f"Error: {e}")
        
        # cd command
        elif cmd_lower.startswith("cd "):
            path = cmd.strip()[3:].strip()
            if path == "~": path = HOME
            elif path.startswith("~/"): path = HOME + path[1:]
            elif not path.startswith("/"): path = os.path.join(self.cwd, path)
            if os.path.isdir(path):
                self.cwd = os.path.abspath(path)
            else:
                self.output.append(f"cd: {path}: No such directory")
        
        elif cmd_lower == "cd":
            self.cwd = HOME
        
        elif cmd_lower == "clear":
            self.output = []
        
        else:
            # Check for interactive commands
            parts = cmd.split()
            base_cmd = parts[0]
            
            # Expanded list of interactive tools
            interactive_tools = [
                'vim', 'vi', 'nano', 'emacs', 'joe', 'jed',
                'htop', 'top', 'btop', 'nvtop', 'atop', 'glances',
                'less', 'more', 'man', 'info',
                'ssh', 'sftp', 'ftp', 'telnet', 'nc',
                'python', 'python3', 'ipython', 'node', 'ruby', 'perl', 'php', 'lua',
                'bash', 'sh', 'zsh', 'fish', 'dash', 'ksh', 'csh', 'tcsh',
                'tmux', 'screen', 'zellij',
                'sudo', 'su', 'doas',
                'git', 'docker', 'kubectl', 'ping', 'traceroute', 'watch',
                'mc', 'ranger', 'nnn', 'lf', 'fdisk', 'cfdisk', 'gdisk', 'parted',
                'lynx', 'w3m', 'links', 'elinks',
                'opencode', 'micro'
            ]
            
            # Force interactive with '!' prefix
            force_interactive = False
            if cmd.startswith('!'):
                cmd = cmd[1:].strip()
                force_interactive = True
            
            if force_interactive or base_cmd in interactive_tools:
                try:
                    # Suspend curses
                    curses.endwin()
                    # Run interactive command
                    subprocess.call(cmd, shell=True, cwd=self.cwd)
                    # Restore curses
                    stdscr = curses.initscr()
                    curses.curs_set(0)
                    curses.noecho()
                    curses.cbreak()
                    stdscr.keypad(True)
                    stdscr.nodelay(True)
                    self.output.append(f"[Exited {base_cmd if not force_interactive else 'interactive mode'}]")
                except Exception as e:
                    self.output.append(f"[Error: {e}]")
            else:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                           timeout=10, cwd=self.cwd, env={**os.environ, "TERM": "xterm"})
                    if result.stdout:
                        for line in result.stdout.rstrip().split('\n'):
                            self.output.append(line)
                    if result.stderr:
                        for line in result.stderr.rstrip().split('\n'):
                            self.output.append(f"[err] {line}")
                except subprocess.TimeoutExpired:
                    self.output.append("[Timeout after 10s]")
                except Exception as e:
                    self.output.append(f"[Error: {e}]")
        
        if len(self.output) > 500:
            self.output = self.output[-500:]
        self.input = ""
        self.cursor = 0
        self.should_exit = False
    
    def type_key(self, ch):
        if ch == 10 or ch == 13:
            self.execute(self.input)
        elif ch == 127 or ch == curses.KEY_BACKSPACE or ch == 8:
            if self.cursor > 0:
                self.input = self.input[:self.cursor-1] + self.input[self.cursor:]
                self.cursor -= 1
        elif ch == curses.KEY_LEFT:
            if self.cursor > 0: self.cursor -= 1
        elif ch == curses.KEY_RIGHT:
            if self.cursor < len(self.input): self.cursor += 1
        elif ch == curses.KEY_UP:
            if self.history and self.hist_idx < len(self.history) - 1:
                self.hist_idx += 1
                self.input = self.history[-(self.hist_idx + 1)]
                self.cursor = len(self.input)
        elif ch == curses.KEY_DOWN:
            if self.hist_idx > 0:
                self.hist_idx -= 1
                self.input = self.history[-(self.hist_idx + 1)]
                self.cursor = len(self.input)
            elif self.hist_idx == 0:
                self.hist_idx = -1
                self.input = ""
                self.cursor = 0
        elif 32 <= ch <= 126:
            self.input = self.input[:self.cursor] + chr(ch) + self.input[self.cursor:]
            self.cursor += 1

# ═══════════════════════════════════════════════════════════════════════════════
# TUI ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class SpectreTUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.active_pane = 1  # 0=fs, 1=terminal
        self.file_browser = FileBrowser()
        self.terminal = Terminal()
        
        # Load Persistence
        config = load_config()
        self.theme_idx = config.get("theme", 0)
        saved_path = config.get("path", HOME)
        if os.path.isdir(saved_path):
            self.file_browser.path = saved_path
            self.terminal.cwd = saved_path
            
        self.last_stats = 0
        
        curses.start_color()
        curses.use_default_colors()
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        print('\033[?1003h') # Enable mouse tracking
        
        self.apply_theme()
        self.stdscr.bkgd(' ', curses.color_pair(1))
        self.height, self.width = stdscr.getmaxyx()
        
        self.net_info = get_network_info()
        self.ping = ping_host()
        self.down_speed, self.up_speed = NET_SPEED.update()
    
    def apply_theme(self):
        theme = THEMES[THEME_NAMES[self.theme_idx]]
        curses.init_pair(1, theme["primary"], curses.COLOR_BLACK)
        curses.init_pair(2, theme["secondary"], curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, theme["accent"], curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_BLACK, theme["primary"])
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)
        
        self.GREEN = curses.color_pair(1) | curses.A_BOLD
        self.CYAN = curses.color_pair(2) | curses.A_BOLD
        self.RED = curses.color_pair(3) | curses.A_BOLD
        self.YELLOW = curses.color_pair(4) | curses.A_BOLD
        self.WHITE = curses.color_pair(5) | curses.A_BOLD
        self.INV = curses.color_pair(6) | curses.A_BOLD
        self.INV_WHITE = curses.color_pair(7) | curses.A_BOLD
        self.DIM = curses.color_pair(1)
    
    def cycle_theme(self):
        self.theme_idx = (self.theme_idx + 1) % len(THEME_NAMES)
        self.apply_theme()
        EVENTS.add(f"Theme changed to {THEME_NAMES[self.theme_idx].upper()}")
    
    def safe_addstr(self, y, x, text, attr=0):
        if 0 <= y < self.height and 0 <= x < self.width:
            try:
                self.stdscr.addstr(y, x, text[:self.width-x-1], attr)
            except: pass
    
    def draw_box(self, y, x, h, w, title="", active=False):
        color = self.WHITE if active else self.GREEN
        self.safe_addstr(y, x, "╔" + "═" * (w-2) + "╗", color)
        for i in range(1, h-1):
            self.safe_addstr(y+i, x, "║" + " " * (w-2) + "║", color)
        self.safe_addstr(y+h-1, x, "╚" + "═" * (w-2) + "╝", color)
        if title:
            self.safe_addstr(y, x+2, f"╣ {title} ╠", color)
    
    def draw_logo(self, y, x, h, w):
        self.draw_box(y, x, h, w, "SPECTRE")
        ly = y + 2
        for i, line in enumerate(LOGO):
            lx = x + (w - len(line)) // 2
            if lx > x and ly + i < y + h - 1:
                self.safe_addstr(ly + i, max(x+1, lx), line[:w-2], self.GREEN)
        
        # Theme selector
        theme_y = y + h - 3
        self.safe_addstr(theme_y, x + 2, "Theme [^T]:", self.DIM)
        self.safe_addstr(theme_y, x + 13, THEME_NAMES[self.theme_idx].upper(), self.CYAN)
        

    
    def draw_stats(self, y, x, h, w):
        self.draw_box(y, x, h, w, "SYSTEM")
        
        now = time.time()
        if now - self.last_stats > 5:
            self.last_stats = now
            self.net_info = get_network_info()
            self.ping = ping_host()
            self.down_speed, self.up_speed = NET_SPEED.update()
        
        cpu = get_cpu_usage()
        mem_str, mem_pct = get_memory_usage()
        disk_str, disk_pct = get_disk_usage()
        load = get_load_avg()
        
        stats = [
            ("USER", USER, self.CYAN),
            ("HOST", HOST, self.CYAN),
            ("CPU", f"{cpu}%", self.GREEN if cpu < 80 else self.RED),
            ("MEM", f"{mem_str} ({mem_pct}%)", self.GREEN if mem_pct < 80 else self.RED),
            ("DISK", f"{disk_str} ({disk_pct}%)", self.GREEN if disk_pct < 90 else self.RED),
            ("LOAD", load, self.YELLOW),
            ("SSID", self.net_info.get("ssid", "N/A"), self.WHITE),
            ("IP", self.net_info.get("ip", "N/A"), self.WHITE),
            ("DOWN", self.down_speed, self.CYAN),
            ("UP", self.up_speed, self.CYAN),
            ("PING", self.ping, self.GREEN if "ms" in str(self.ping) else self.RED),
        ]
        
        # Check for system events
        if cpu > 80: EVENTS.add(f"Cpu Spike Detected: {cpu}%", "WARN")
        if mem_pct > 85: EVENTS.add("Memory Critical", "WARN")
        
        for i, (k, v, color) in enumerate(stats):
            if y + 1 + i < y + h - 1:
                self.safe_addstr(y+1+i, x+2, f"{k}:", self.DIM)
                self.safe_addstr(y+1+i, x+7, str(v)[:w-9], color)
    
    def draw_monitor(self, y, x, h, w):
        self.draw_box(y, x, h, w, "MONITOR")
        row = 1
        
        now = time.time()
        # Cache monitor stats to avoid UI lag
        if not hasattr(self, 'mon_cache'):
            self.mon_cache = {
                'temp': "N/A", 'gpu': "N/A", 'bat': "N/A",
                'conns': "0", 'ports': [], 'dio': "N/A", 'cores': [],
                'last_upd': 0
            }
            
        if now - self.mon_cache['last_upd'] > 2:
            self.mon_cache['temp'] = get_cpu_temp()
            self.mon_cache['gpu'] = get_gpu_usage()
            self.mon_cache['bat'] = get_battery()
            self.mon_cache['conns'] = get_connections()
            self.mon_cache['ports'] = get_open_ports()
            self.mon_cache['dio'] = get_disk_io()
            self.mon_cache['cores'] = get_per_core_cpu()
            self.mon_cache['last_upd'] = now
        
        c = self.mon_cache
        items = [
            ("TEMP", c['temp']), ("GPU", c['gpu']), ("BAT", c['bat']),
            ("CONN", c['conns']), ("PORT", ",".join(c['ports'][:3])), ("I/O", c['dio']),
        ]
        
        for k, v in items:
            if y + row < y + h - 1:
                self.safe_addstr(y+row, x+2, f"{k}:", self.DIM)
                self.safe_addstr(y+row, x+7, str(v)[:w-9], self.CYAN)
                row += 1
        
        # Core bars
        self.safe_addstr(y+row, x+2, "CORE:", self.DIM)
        row += 1
        bar_w = w - 8
        for i, usage in enumerate(c['cores']):
            if y + row < y + h - 1:
                filled = int((usage / 100) * bar_w) if bar_w > 0 else 0
                bar = "█" * filled + "░" * (bar_w - filled)
                color = self.GREEN if usage < 70 else self.YELLOW if usage < 90 else self.RED
                self.safe_addstr(y+row, x+3, f"{i}:", self.DIM)
                self.safe_addstr(y+row, x+5, bar[:bar_w], color)
                row += 1
    
    def draw_time(self, y, x, h, w):
        self.draw_box(y, x, h, w, "TIME")
        now = datetime.now()
        cy = y + h // 2 - 1
        self.safe_addstr(cy, x + (w-8)//2, now.strftime("%H:%M:%S"), self.GREEN)
        self.safe_addstr(cy+1, x + (w-10)//2, now.strftime("%Y-%m-%d"), self.CYAN)
        self.safe_addstr(cy+2, x + (w-len(now.strftime("%A")))//2, now.strftime("%A"), self.DIM)
    
    def draw_filesystem(self, y, x, h, w):
        self.draw_box(y, x, h, w, "FILESYSTEM", active=(self.active_pane == 0))
        
        path = self.file_browser.path
        if len(path) > w - 6: path = "..." + path[-(w-9):]
        self.safe_addstr(y+1, x+2, path, self.CYAN)
        
        visible = h - 4
        items = self.file_browser.items
        sel = self.file_browser.selected
        
        if sel >= self.file_browser.scroll + visible:
            self.file_browser.scroll = sel - visible + 1
        if sel < self.file_browser.scroll:
            self.file_browser.scroll = sel
        
        start = self.file_browser.scroll
        for i in range(min(visible, len(items) - start)):
            idx = start + i
            if idx < len(items):
                icon, name, is_dir = items[idx]
                row = y + 2 + i
                color = self.CYAN if is_dir else self.DIM if name.startswith('.') else self.WHITE
                text = f"  {icon} {name}"[:w-4]
                if idx == sel:
                    self.safe_addstr(row, x+2, " " * (w-4), self.INV_WHITE)
                    self.safe_addstr(row, x+2, f"▸{text[1:]}", self.INV_WHITE)
                else:
                    self.safe_addstr(row, x+2, text, color)
    
    def draw_terminal(self, y, x, h, w):
        self.draw_box(y, x, h, w, "TERMINAL", active=(self.active_pane == 1))
        
        visible = h - 4
        # Clamp scroll
        max_scroll = max(0, len(self.terminal.output) - visible)
        self.terminal.scroll = max(0, min(self.terminal.scroll, max_scroll))
        
        # Determine lines to show
        if self.terminal.scroll > 0:
            start = -(visible + self.terminal.scroll)
            end = -self.terminal.scroll
            lines = self.terminal.output[start:end]
            # Draw scroll indicator
            ind = f" ▴ {self.terminal.scroll} "
            self.safe_addstr(y, x + w - len(ind) - 2, ind, self.YELLOW)
        else:
            lines = self.terminal.output[-visible:]
            
        for i, line in enumerate(lines):
            if y + 1 + i < y + h - 3:
                color = self.RED if '[err]' in line or 'Error' in line else self.WHITE
                self.safe_addstr(y+1+i, x+2, line[:w-4], color)
        
        prompt = self.terminal.prompt()
        input_y = y + h - 2
        self.safe_addstr(input_y, x+2, f"{prompt}{self.terminal.input}"[:w-4], self.GREEN)
        
        if self.active_pane == 1:
            cursor_x = x + 2 + len(prompt) + self.terminal.cursor
            if cursor_x < x + w - 2:
                self.safe_addstr(input_y, cursor_x, "█", self.WHITE)
    
    def draw_preview(self, y, x, h, w):
        """Draw file preview panel."""
        self.draw_box(y, x, h, w, "PREVIEW")
        
        if self.file_browser.selected_file:
            filepath = self.file_browser.selected_file
            fname = os.path.basename(filepath)
            self.safe_addstr(y+1, x+2, fname[:w-4], self.CYAN)
            
            lines = read_file_preview(filepath, h-4)
            for i, line in enumerate(lines):
                if y + 2 + i < y + h - 1:
                    self.safe_addstr(y+2+i, x+2, line[:w-4], self.WHITE)
        else:
            self.safe_addstr(y+h//2, x+2, "Select a file to preview", self.DIM)
    
    def draw_status(self, y):
        theme_str = THEME_NAMES[self.theme_idx].upper()
        # Left side: Controls
        ctrl = f" TAB:Switch │ ^T:Theme │ PgUp/Dn:Scroll │ Q:Exit "
        self.safe_addstr(y, 0, ctrl, self.INV)
        
        # Right side: Event Ticker
        # available width
        ticker_w = self.width - len(ctrl) - 2
        if ticker_w > 10:
            latest = EVENTS.get_latest()
            self.safe_addstr(y, len(ctrl) + 1, f" ⚡ {latest:<{ticker_w}}", self.INV)
    
    def draw(self):
        self.stdscr.erase()
        h, w = self.height, self.width
        
        row1_h = 14
        row2_h = h - row1_h - 1
        
        # Dynamic layout based on width
        if w > 90:
            logo_w = 64  # Enough for Logo only
        else:
            logo_w = max(30, min(64, w - 25)) 
            
        remaining = w - logo_w
        
        # Row 1 Rendering with responsive panels
        self.draw_logo(0, 0, row1_h, logo_w)
        
        if remaining > 60:
            # Show Stats, Monitor, Time
            pw = remaining // 3
            self.draw_stats(0, logo_w, row1_h, pw)
            self.draw_monitor(0, logo_w + pw, row1_h, pw)
            self.draw_time(0, logo_w + pw * 2, row1_h, w - (logo_w + pw * 2))
        elif remaining > 40:
            # Show Stats and Time
            pw = remaining // 2
            self.draw_stats(0, logo_w, row1_h, pw)
            self.draw_time(0, logo_w + pw, row1_h, w - (logo_w + pw))
        else:
            # Show only Time
            self.draw_time(0, logo_w, row1_h, remaining)
        
        # Row 2: Filesystem | Terminal | Preview (if file selected)
        if self.file_browser.selected_file:
            fs_w = w // 4
            preview_w = w // 4
            term_w = w - fs_w - preview_w
            self.draw_filesystem(row1_h, 0, row2_h, fs_w)
            self.draw_terminal(row1_h, fs_w, row2_h, term_w)
            self.draw_preview(row1_h, fs_w + term_w, row2_h, preview_w)
        else:
            fs_w = w // 3
            term_w = w - fs_w
            self.draw_filesystem(row1_h, 0, row2_h, fs_w)
            self.draw_terminal(row1_h, fs_w, row2_h, term_w)
        
        self.draw_status(h - 1)
        self.stdscr.refresh()
    
    def handle_key(self, key):
        if key == ord('q') or key == ord('Q'):
            self.running = False
        elif key == 20:  # Ctrl+T
            self.cycle_theme()
        elif key == 9:  # TAB
            self.active_pane = 1 - self.active_pane
        elif key == curses.KEY_RESIZE:
            self.height, self.width = self.stdscr.getmaxyx()
        elif self.active_pane == 0:
            if key == curses.KEY_UP:
                self.file_browser.up()
            elif key == curses.KEY_DOWN:
                self.file_browser.down()
            elif key == 10:
                self.file_browser.enter()
        elif self.active_pane == 1:
            if key == curses.KEY_PPAGE:
                self.terminal.scroll += 10
            elif key == curses.KEY_NPAGE:
                self.terminal.scroll -= 10
            else:
                self.terminal.type_key(key)
        
        elif key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, state = curses.getmouse()
                if state & curses.BUTTON1_CLICKED:
                    # Detect panel click
                    row1_h = 14
                    if my >= row1_h:
                        if mx < self.width // 3:
                            self.active_pane = 0
                        else:
                            self.active_pane = 1
            except: pass
    
    def run(self):
        last_draw = 0
        while self.running:
            try:
                key = self.stdscr.getch()
                if key != -1:
                    self.handle_key(key)
            except: pass
            
            # Update background events
            EVENTS.update()
            
            now = time.time()
            if now - last_draw >= 0.05:
                last_draw = now
                self.draw()
                # Check for exit flag
                if self.terminal.should_exit:
                    self.running = False
            else:
                time.sleep(0.01)
        
        # Save state on exit
        save_config(self.theme_idx, self.file_browser.path)

# ═══════════════════════════════════════════════════════════════════════════════
# LOADING
# ═══════════════════════════════════════════════════════════════════════════════
def loading(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    GREEN = curses.color_pair(1) | curses.A_BOLD
    
    h, w = stdscr.getmaxyx()
    stdscr.bkgd(' ', curses.color_pair(1))
    
    stages = ["Initializing...", "Loading modules...", "Starting services...", "Ready."]
    
    for i, stage in enumerate(stages):
        stdscr.erase()
        header = "⚡ SPECTRE ⚡"
        try: stdscr.addstr(h//3, (w-len(header))//2, header, GREEN)
        except: pass
        
        bar_w = min(40, w - 20)
        prog = (i + 1) / len(stages)
        bar = "█" * int(bar_w * prog) + "░" * (bar_w - int(bar_w * prog))
        try: stdscr.addstr(h//2, (w-bar_w-10)//2, f"[{bar}] {int(prog*100):3d}%", GREEN)
        except: pass
        
        try: stdscr.addstr(h//2 + 2, (w-len(stage))//2, stage, GREEN)
        except: pass
        
        stdscr.refresh()
        time.sleep(0.15)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main(stdscr):
    loading(stdscr)
    SpectreTUI(stdscr).run()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n\033[1;32m>>> SPECTRE terminated. <<<\033[0m\n")
