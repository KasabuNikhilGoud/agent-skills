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

def focus_window(keyword: str) -> str:
    """Focus the first window whose title contains keyword."""
    win = eyes.find_window(keyword)
    if not win:
        return f"No window found matching '{keyword}'"
    run(f"xdotool windowactivate {win['id']}")
    return f"Focused window: {win['name']}"

def move_window(keyword: str, x: int, y: int) -> str:
    """Move the first window matching keyword to position (x, y)."""
    win = eyes.find_window(keyword)
    if not win:
        return f"No window found matching '{keyword}'"
    run(f"xdotool windowmove {win['id']} {x} {y}")
    return f"Moved window '{win['name']}' to ({x}, {y})"

def resize_window(keyword: str, w: int, h: int) -> str:
    """Resize the first window matching keyword to w x h pixels."""
    win = eyes.find_window(keyword)
    if not win:
        return f"No window found matching '{keyword}'"
    run(f"xdotool windowsize {win['id']} {w} {h}")
    return f"Resized window '{win['name']}' to {w}x{h}"

def close_window(keyword: str) -> str:
    """Close the first window matching keyword."""
    win = eyes.find_window(keyword)
    if not win:
        return f"No window found matching '{keyword}'"
    run(f"xdotool windowclose {win['id']}")
    return f"Closed window: {win['name']}"

def drag(x1: int, y1: int, x2: int, y2: int) -> str:
    """Click and drag from (x1, y1) to (x2, y2)."""
    run(f"xdotool mousedown 1")
    run(f"xdotool mousemove {x2} {y2}")
    run(f"xdotool mouseup 1")
    return f"Dragged from ({x1}, {y1}) to ({x2}, {y2})"

def scroll(direction: str, clicks: int = 1) -> str:
    """Scroll mouse wheel: direction='up' or 'down', clicks=number of scroll steps."""
    button = "4" if direction.lower() == "up" else "5"
    run(f"xdotool click --repeat {clicks} --delay 100 {button}")
    return f"Scrolled {direction} {clicks} times"

def run_command(cmd: str) -> str:
    """Execute a shell command and return its output."""
    result = run(cmd, timeout=30)
    return f"Command output: {result}"

def list_apps() -> str:
    """List all running applications with their window counts."""
    apps = eyes.list_apps()
    if not apps:
        return "No applications found"
    lines = [f"- {a['name']} ({a['windows']} window{'s' if a['windows'] > 1 else ''})" for a in apps]
    return "Running applications:\n" + "\n".join(lines)

def focus_app(name: str) -> str:
    """Focus an application by name (activates its first window)."""
    win = eyes.find_window(name)
    if not win:
        return f"No window found matching '{name}'"
    run(f"xdotool windowactivate {win['id']}")
    return f"Focused application: {win['name']}"

def get_screen_geometry() -> str:
    """Get screen resolution and geometry information."""
    geo = eyes.get_screen_geometry()
    return f"Screen: {geo['width']}x{geo['height']}"

def hover(x: int, y: int) -> str:
    """Move mouse to position without clicking."""
    run(f"xdotool mousemove {x} {y}")
    return f"Hovered at ({x}, {y})"

def right_click(x: int, y: int) -> str:
    """Right-click at pixel coordinates."""
    run(f"xdotool mousemove {x} {y} click 3")
    return f"Right-clicked at ({x}, {y})"

def double_click(x: int, y: int) -> str:
    """Double-click at pixel coordinates."""
    run(f"xdotool mousemove {x} {y} click --repeat 2 --delay 100 1")
    return f"Double-clicked at ({x}, {y})"

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
- focus_window(keyword): focus the first window whose title contains keyword
- move_window(keyword, x, y): move the first window matching keyword to position (x, y)
- resize_window(keyword, w, h): resize the first window matching keyword to w x h pixels
- close_window(keyword): close the first window matching keyword
- drag(x1, y1, x2, y2): click and drag from (x1, y1) to (x2, y2)
- scroll(direction, clicks): scroll mouse wheel, direction='up' or 'down', clicks=number of steps
- run_command(cmd): execute a shell command and return its output
- list_apps(): list all running applications with their window counts
- focus_app(name): focus an application by name (activates its first window)
- get_screen_geometry(): get screen resolution and geometry information
- hover(x, y): move mouse to position without clicking
- right_click(x, y): right-click at pixel coordinates
- double_click(x, y): double-click at pixel coordinates
"""
