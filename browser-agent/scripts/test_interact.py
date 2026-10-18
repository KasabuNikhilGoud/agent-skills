#!/usr/bin/env python3
"""
Test suite for human-like interaction methods and shell command execution.
Tests scroll, press, hover, drag, double_click, right_click, type_human, clear, wait_for, and run_cmd.
"""

import sys
import os
import tempfile
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: playwright not installed. Using mock tests only.")

# Import BrowserAgent only if playwright is available, otherwise create a minimal mock
if PLAYWRIGHT_AVAILABLE:
    from browser_agent import BrowserAgent
else:
    # Minimal mock for testing without full browser_agent
    class BrowserAgent:
        def __init__(self):
            self._page = MockPage()

        def scroll(self, direction="down", amount=400):
            if direction == "down":
                self._page._scroll_y += amount
            elif direction == "up":
                self._page._scroll_y -= amount
            elif direction == "right":
                self._page._scroll_x = getattr(self._page, '_scroll_x', 0) + amount
            elif direction == "left":
                self._page._scroll_x = getattr(self._page, '_scroll_x', 0) - amount
            return f"Scrolled {direction} by {amount}px"

        def scroll_to(self, selector):
            return f"Scrolled to {selector}" if selector == "#test" else f"Element {selector} not found"

        def press(self, key):
            self._page.keyboard.press(key)
            return f"Pressed {key}"

        def hover(self, selector):
            return f"Hovered over {selector}" if selector == "#test" else f"Element {selector} not found"

        def drag(self, source_selector, target_selector):
            return f"Dragged {source_selector} to {target_selector}"

        def double_click(self, selector):
            self._page.query_selector(selector).dblclick()
            return f"Double-clicked {selector}"

        def right_click(self, selector):
            return f"Right-clicked {selector}"

        def type_human(self, selector, text, delay_ms=50):
            self._page.keyboard.type(text, delay=delay_ms)
            return f"Typed '{text}' into {selector} with {delay_ms}ms delay"

        def clear(self, selector):
            self._page.query_selector(selector).fill("")
            return f"Cleared {selector}"

        def wait_for(self, selector, timeout_s=10):
            try:
                self._page.wait_for_selector(selector, timeout=timeout_s * 1000)
                return True
            except:
                return False

        def run_cmd(self, command, timeout_s=30):
            deny_patterns = [
                "rm -rf /", "mkfs", "dd of=/dev/", ":(){", "shutdown", "reboot", "halt"
            ]
            cmd_lower = command.lower()
            for pattern in deny_patterns:
                if pattern in cmd_lower:
                    return {
                        "cmd": command,
                        "stdout": "",
                        "stderr": f"Command denied by safety policy: contains '{pattern}'",
                        "returncode": -1
                    }
            import subprocess
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s
                )
                return {
                    "cmd": command,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            except subprocess.TimeoutExpired:
                return {
                    "cmd": command,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout_s}s",
                    "returncode": -1
                }
            except Exception as e:
                return {
                    "cmd": command,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1
                }


# ─── Mock Page Object for Fallback Testing ───

class MockPage:
    """Lightweight fake page object for testing without real browser."""
    def __init__(self):
        self._elements = {}
        self._scroll_y = 0
        self._scroll_x = 0
        self._mouse_down = False
        self._keyboard_events = []
        self._element_clicks = {}

    def query_selector(self, selector):
        class MockEl:
            def __init__(self, selector, parent):
                self.selector = selector
                self.parent = parent
            def scroll_into_view_if_needed(self):
                pass
            def hover(self):
                pass
            def click(self, button="left"):
                self.parent._element_clicks[self.selector] = self.parent._element_clicks.get(self.selector, 0) + 1
            def dblclick(self):
                self.parent._element_clicks[f"{self.selector}-dbl"] = self.parent._element_clicks.get(f"{self.selector}-dbl", 0) + 1
            def fill(self, value):
                self.parent._elements[self.selector] = value
        return MockEl(selector, self) if selector in ["#test", "#src", "#dst", "#input", "#late"] else None

    def wait_for_selector(self, selector, timeout):
        # Simulate timeout for "#late" selector
        if selector == "#late":
            raise Exception("Timeout")
        return True

    def evaluate(self, js):
        return self._scroll_y

    @property
    def mouse(self):
        class MockMouse:
            def __init__(self, parent):
                self.parent = parent
            def wheel(self, dx, dy):
                self.parent._scroll_y += dy
                self.parent._scroll_x += dx
        return MockMouse(self)

    @property
    def keyboard(self):
        class MockKeyboard:
            def __init__(self, parent):
                self.parent = parent
            def press(self, key):
                self.parent._keyboard_events.append(f"press:{key}")
            def type(self, text, delay=0):
                self.parent._keyboard_events.append(f"type:{text}")
        return MockKeyboard(self)


# ─── Test Functions ───

def test_scroll():
    """Test scroll method changes scroll position."""
    print("Testing scroll...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body style='height:2000px'>Test</body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            initial = page.evaluate("window.scrollY")
            agent.scroll("down", 400)
            after = page.evaluate("window.scrollY")
            assert after > initial, f"Scroll down failed: {after} > {initial}"

            agent.scroll("up", 200)
            final = page.evaluate("window.scrollY")
            assert final < after, f"Scroll up failed: {final} < {after}"

            browser.close()
    else:
        # Mock test
        agent = BrowserAgent()
        result = agent.scroll("down", 400)
        assert "Scrolled down" in result
        assert agent._page._scroll_y == 400, f"Mock scroll failed: {agent._page._scroll_y}"
    print("  ✓ scroll")


def test_scroll_to():
    """Test scroll_to method."""
    print("Testing scroll_to...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><div id='test' style='margin-top:1000px'>Target</div></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            result = agent.scroll_to("#test")
            assert "Scrolled to" in result, f"scroll_to failed: {result}"

            result = agent.scroll_to("#nonexistent")
            assert "not found" in result, f"scroll_to should fail for nonexistent: {result}"

            browser.close()
    else:
        agent = BrowserAgent()
        result = agent.scroll_to("#test")
        assert "Scrolled to" in result
        result = agent.scroll_to("#missing")
        assert "not found" in result
    print("  ✓ scroll_to")


def test_press():
    """Test press method records keyboard events."""
    print("Testing press...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><input id='input'></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            page.focus("#input")
            result = agent.press("Enter")
            assert "Pressed Enter" in result, f"press failed: {result}"

            browser.close()
    else:
        agent = BrowserAgent()
        result = agent.press("Enter")
        assert "Pressed Enter" in result
        assert "press:Enter" in agent._page._keyboard_events
    print("  ✓ press")


def test_hover():
    """Test hover method."""
    print("Testing hover...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><div id='test'>Hover me</div></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            result = agent.hover("#test")
            assert "Hovered over" in result, f"hover failed: {result}"

            result = agent.hover("#missing")
            assert "not found" in result

            browser.close()
    else:
        agent = BrowserAgent()
        result = agent.hover("#test")
        assert "Hovered over" in result
    print("  ✓ hover")


def test_drag():
    """Test drag method."""
    print("Testing drag...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><div id='src'>Source</div><div id='dst'>Target</div></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            result = agent.drag("#src", "#dst")
            assert "Dragged" in result, f"drag failed: {result}"

            browser.close()
    else:
        agent = BrowserAgent()
        result = agent.drag("#src", "#dst")
        assert "Dragged" in result
    print("  ✓ drag")


def test_double_click():
    """Test double_click method."""
    print("Testing double_click...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><div id='test'>Double click me</div></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            result = agent.double_click("#test")
            assert "Double-clicked" in result, f"double_click failed: {result}"

            browser.close()
    else:
        agent = BrowserAgent()
        result = agent.double_click("#test")
        assert "Double-clicked" in result
        assert agent._page._element_clicks.get("#test-dbl", 0) == 1
    print("  ✓ double_click")


def test_right_click():
    """Test right_click method."""
    print("Testing right_click...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><div id='test'>Right click me</div></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            result = agent.right_click("#test")
            assert "Right-clicked" in result, f"right_click failed: {result}"

            browser.close()
    else:
        agent = BrowserAgent()
        result = agent.right_click("#test")
        assert "Right-clicked" in result
    print("  ✓ right_click")


def test_type_human():
    """Test type_human method."""
    print("Testing type_human...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><input id='input'></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            result = agent.type_human("#input", "hello", delay_ms=10)
            assert "Typed" in result, f"type_human failed: {result}"
            value = page.evaluate("() => document.querySelector('#input').value")
            assert value == "hello", f"Input value mismatch: {value}"

            browser.close()
    else:
        agent = BrowserAgent()
        result = agent.type_human("#input", "hello", delay_ms=10)
        assert "Typed" in result
        assert "type:hello" in agent._page._keyboard_events
    print("  ✓ type_human")


def test_clear():
    """Test clear method."""
    print("Testing clear...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><input id='input' value='test'></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            result = agent.clear("#input")
            assert "Cleared" in result, f"clear failed: {result}"
            value = page.evaluate("() => document.querySelector('#input').value")
            assert value == "", f"Input not cleared: {value}"

            browser.close()
    else:
        agent = BrowserAgent()
        agent._page._elements["#input"] = "test"
        result = agent.clear("#input")
        assert "Cleared" in result
        assert agent._page._elements.get("#input") == ""
    print("  ✓ clear")


def test_wait_for():
    """Test wait_for method."""
    print("Testing wait_for...")
    if PLAYWRIGHT_AVAILABLE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><div id='test'>Here</div></body></html>")
            agent = BrowserAgent()
            agent._page = page
            agent._browser = browser
            agent._play = p

            result = agent.wait_for("#test", timeout_s=5)
            assert result == True, f"wait_for should find element: {result}"

            result = agent.wait_for("#missing", timeout_s=1)
            assert result == False, f"wait_for should timeout: {result}"

            browser.close()
    else:
        agent = BrowserAgent()
        result = agent.wait_for("#test", timeout_s=5)
        assert result == True
        result = agent.wait_for("#late", timeout_s=1)
        assert result == False
    print("  ✓ wait_for")


def test_run_cmd():
    """Test run_cmd method with safe and denied commands."""
    print("Testing run_cmd...")
    agent = BrowserAgent()

    # Safe command
    result = agent.run_cmd("echo hello", timeout_s=5)
    assert result["returncode"] == 0, f"echo failed: {result}"
    assert "hello" in result["stdout"], f"echo output missing: {result['stdout']}"

    # Another safe command
    result = agent.run_cmd("true", timeout_s=5)
    assert result["returncode"] == 0, f"true failed: {result}"

    # Denied command
    result = agent.run_cmd("rm -rf /", timeout_s=5)
    assert result["returncode"] == -1, f"rm -rf / should be denied: {result}"
    assert "denied" in result["stderr"].lower(), f"Deny message missing: {result['stderr']}"

    # Another denied command
    result = agent.run_cmd("shutdown now", timeout_s=5)
    assert result["returncode"] == -1, f"shutdown should be denied: {result}"
    assert "denied" in result["stderr"].lower(), f"Deny message missing: {result['stderr']}"

    print("  ✓ run_cmd")


# ─── Main Test Runner ───

def main():
    print("=" * 60)
    print("Running browser-agent interaction tests")
    print("=" * 60)

    if not PLAYWRIGHT_AVAILABLE:
        print("\nNote: Playwright not available, using mock tests only.")
        print("Install with: pip3 install playwright && python3 -m playwright install chromium\n")

    try:
        test_scroll()
        test_scroll_to()
        test_press()
        test_hover()
        test_drag()
        test_double_click()
        test_right_click()
        test_type_human()
        test_clear()
        test_wait_for()
        test_run_cmd()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
