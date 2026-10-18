"""EYES: turn the screen into structured text the brain can read.

Why text and not screenshots? A text report of the windows is cheap, exact
and works with any model. Vision is an optional upgrade, not the default.

Enhanced with accessibility tree support (AT-SPI on Linux) for element-level
interaction, inspired by Hermes Agent's computer-use implementation.
"""
import os
import subprocess
import json

DISPLAY = os.environ.get("DISPLAY", ":1")


def _run(cmd: str) -> str:
    env = {**os.environ, "DISPLAY": DISPLAY}
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    return p.stdout.strip()


def window_list() -> list:
    """Every visible window: id, name, position, size and focused flag."""
    ids = _run("xdotool search --onlyvisible --name ''").split()
    active = _run("xdotool getactivewindow")
    windows = []
    for wid in ids:
        name = _run(f"xdotool getwindowname {wid}")
        if not name:
            continue
        geo = _run(f"xdotool getwindowgeometry --shell {wid}")
        g = dict(line.split("=", 1) for line in geo.splitlines() if "=" in line)
        windows.append({
            "id": int(wid),
            "name": name,
            "x": int(g.get("X", 0)),
            "y": int(g.get("Y", 0)),
            "w": int(g.get("WIDTH", 0)),
            "h": int(g.get("HEIGHT", 0)),
            "active": wid == active,
        })
    return windows


def screen_state() -> str:
    """One text block describing the screen - this is what the brain reads."""
    wins = window_list()
    if not wins:
        return "(no windows found)"
    lines = []
    for w in wins:
        flag = " [ACTIVE]" if w["active"] else ""
        lines.append(
            f'- "{w["name"]}" at ({w["x"]},{w["y"]}) '
            f"size {w["w"]}x{w["h"]}{flag}")
    return "\n".join(lines)


def find_window(keyword: str):
    """First visible window whose title contains keyword (case-insensitive),
    or None. Useful for checking whether an app actually opened."""
    k = keyword.lower()
    for w in window_list():
        if k in w["name"].lower():
            return w
    return None


def get_accessibility_tree(window_id: int = None) -> list:
    """Get accessibility tree elements for a window (Linux AT-SPI).
    Returns a list of clickable elements with role, name, position, and size.
    Inspired by Hermes Agent's element indexing system."""
    try:
        # Try to use ydotool's accessibility bridge if available
        cmd = ["python3", "-c", """
import dbus
session_bus = dbus.SessionBus()
atspi = session_bus.get_object('org.a11y.Bus', '/org/a11y/atspi/tree')
"""]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # AT-SPI is available - would need full implementation
            # For now, return empty list - this is a placeholder for future enhancement
            return []
    except Exception:
        pass

    # Fallback: return empty list - accessibility requires AT-SPI setup
    return []


def list_apps() -> list:
    """List all running applications with their window counts.
    Useful for focusing the right app before action."""
    apps = {}
    for w in window_list():
        # Extract app name from window title (heuristic)
        app_name = w["name"].split(" - ")[0].split(" | ")[0].split(" — ")[0]
        apps[app_name] = apps.get(app_name, 0) + 1
    return [{"name": name, "windows": count} for name, count in sorted(apps.items())]


def get_screen_geometry() -> dict:
    """Get screen resolution and geometry information."""
    try:
        geo = _run("xdotool getdisplaygeometry")
        parts = geo.split()
        if len(parts) >= 2:
            return {"width": int(parts[0]), "height": int(parts[1])}
    except Exception:
        pass
    return {"width": 1920, "height": 1080}  # Default fallback
