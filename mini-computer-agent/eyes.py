"""EYES: turn the screen into structured text the brain can read.

Why text and not screenshots? A text report of the windows is cheap, exact
and works with any model. Vision is an optional upgrade, not the default.
"""
import os
import subprocess

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
