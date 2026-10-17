"""HANDS: the tools that act on the computer.
Each function returns a TEXT report (that's what the LLM brain reads)."""
import subprocess, time, os

import eyes

DISPLAY = os.environ.get("DISPLAY", ":1")

# Maps an app launch command to the keyword its window title should contain.
WINDOW_HINTS = {
    "gnome-terminal": "terminal",
    "xfce4-terminal": "terminal",
    "libreoffice --calc": "calc",
    "libreoffice --writer": "writer",
    "libreoffice --impress": "impress",
    "firefox": "firefox",
    "chromium": "chromium",
    "pcmanfm": "pcmanfm",
}

def run(cmd, timeout=15):
    """Run a shell command with the desktop display attached."""
    env = {**os.environ, "DISPLAY": DISPLAY}
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout, env=env)
    return (p.stdout + p.stderr).strip()

def open_app(name: str, wait_secs: int = 8) -> str:
    """Launch an app, then wait until its window actually appears.

    Launching alone is not enough: the brain needs to KNOW the app opened
    before it types into it. We poll the window list until a window whose
    title matches the app appears, or the timeout runs out.
    """
    run(f"setsid {name} >/dev/null 2>&1 &", timeout=5)
    hint = WINDOW_HINTS.get(name, name.split()[0])
    deadline = time.time() + wait_secs
    while time.time() < deadline:
        time.sleep(0.5)
        win = eyes.find_window(hint)
        if win:
            return f"Launched and verified: {name} (window '{win['name']}')"
    return (f"Launched {name}, but no window matching '{hint}' appeared "
            f"within {wait_secs}s")

def see_windows() -> str:
    """EYES: kept as a thin wrapper for backwards compatibility."""
    return eyes.screen_state()

def click(x: int, y: int) -> str:
    run(f"xdotool mousemove {x} {y} click 1")
    return f"Clicked ({x}, {y})"

def type_text(text: str) -> str:
    run(f"xdotool type --delay 40 {sh(text)}")
    return f"Typed: {text}"

def press(key: str) -> str:
    """Press a key or combo, e.g. "Return", "ctrl+s", "alt+F4"."""
    run(f"xdotool key {key}")
    return f"Pressed {key}"

def screenshot(path="/tmp/shot.png") -> str:
    run(f"import -window root {path}")   # ImageMagick
    return f"Screenshot saved: {path}"

def sh(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"

# The tool catalog the brain is told about (plain text = the "skill" description)
TOOLS = """
- open_app(name): launch an application and verify its window appeared,
  e.g. open_app("libreoffice --calc")
- see_windows(): text report of visible windows with position, size, focus
- find_window(keyword): first window whose title contains keyword, or null
- click(x, y): left-click at pixel coordinates
- type_text(text): type a string into the focused window
- press(key): press a key or combo, e.g. "Return", "ctrl+s", "alt+F4"
- screenshot(path): save a PNG of the screen
"""
