"""HANDS: the tools that act on the computer.
Each function returns a TEXT report (that's what the LLM brain reads)."""
import subprocess, time, os

DISPLAY = os.environ.get("DISPLAY", ":1")

def run(cmd, timeout=15):
    """Run a shell command with the desktop display attached."""
    env = {**os.environ, "DISPLAY": DISPLAY}
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout, env=env)
    return (p.stdout + p.stderr).strip()

def open_app(name: str) -> str:
    """Launch an app in the background, e.g. 'firefox', 'libreoffice --calc'."""
    run(f"setsid {name} >/dev/null 2>&1 &", timeout=5)
    time.sleep(3)
    return f"Launched: {name}"

def see_windows() -> str:
    """EYES: list every window on screen as text. This replaces a screenshot."""
    out = run("xdotool search --onlyvisible --name '' getwindowname %@ 2>/dev/null | sort -u")
    return out or "(no windows found)"

def click(x: int, y: int) -> str:
    run(f"xdotool mousemove {x} {y} click 1")
    return f"Clicked ({x}, {y})"

def type_text(text: str) -> str:
    run(f"xdotool type --delay 40 {sh(text)}")
    return f"Typed: {text}"

def press(key: str) -> str:
    run(f"xdotool key {key}")
    return f"Pressed {key}"

def screenshot(path="/tmp/shot.png") -> str:
    run(f"import -window root {path}")   # ImageMagick
    return f"Screenshot saved: {path}"

def sh(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"

# The tool catalog the brain is told about (plain text = the "skill" description)
TOOLS = """
- open_app(name): launch an application, e.g. open_app("libreoffice --calc")
- see_windows(): list visible window titles (use this to check what happened)
- click(x, y): left-click at pixel coordinates
- type_text(text): type a string into the focused window
- press(key): press a key, e.g. "Return", "ctrl+s", "alt+F4"
- screenshot(path): save a PNG of the screen
"""
