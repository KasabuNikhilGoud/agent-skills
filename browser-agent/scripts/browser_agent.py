#!/usr/bin/env python3
"""
Browser Agent - Complete Web Browser Automation System
======================================================
Integrates search, navigation, form-fill, extract, auth, signup, and monitor skills.
Uses opencode for AI reasoning via 'opencode run' subprocess.
Can also work standalone with direct Playwright control.

Usage:
  python3 browser_agent.py --url https://example.com --task "fill contact form"
"""

import sys
import os
import json
import re
import argparse
import subprocess
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
except ImportError:
    print("ERROR: playwright not installed. Run: pip3 install playwright && python3 -m playwright install chromium")
    sys.exit(1)


OPCODE_BIN = os.getenv("OPCODE_BIN") or os.environ.get("HOME", "") and os.path.expanduser("~/.local/bin/opencode") or "opencode"
SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")


# ─── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""

@dataclass
class FormField:
    selector: str
    label: str = ""
    type: str = "text"
    placeholder: str = ""

@dataclass
class Form:
    selector: str
    fields: list = field(default_factory=list)

@dataclass
class PageState:
    url: str
    title: str
    html: str = ""
    elements: list = field(default_factory=list)


# ─── Helpers ────────────────────────────────────────────────────────────────────

def strip_ansi(s: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', s).strip()

def load_skill_md(name: str) -> str:
    path = os.path.join(SKILLS_DIR, name, "SKILL.md")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ""

def ask_llm(prompt: str, timeout: int = 60) -> str:
    """Send prompt to opencode and get response."""
    try:
        result = subprocess.run(
            [OPCODE_BIN, "run", prompt],
            capture_output=True, text=True, timeout=timeout
        )
        return strip_ansi(result.stdout)
    except FileNotFoundError:
        return json.dumps({"action": "done", "summary": "opencode not found"})
    except subprocess.TimeoutExpired:
        return json.dumps({"action": "done", "summary": "opencode timed out"})


# ─── Browser Agent ──────────────────────────────────────────────────────────────

class BrowserAgent:
    def __init__(self, url: str = "", headless: bool = True,
                 viewport: tuple = (1280, 800), timeout: int = 30):
        self.url = url
        self.headless = headless
        self.viewport = viewport
        self.timeout = timeout
        self._play = None
        self._browser = None
        self._page = None
        self._context = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.close()

    def start(self):
        self._play = sync_playwright().__enter__()
        self._browser = self._play.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        self._context = self._browser.new_context(
            viewport={"width": self.viewport[0], "height": self.viewport[1]},
            user_agent=("Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36")
        )
        self._page = self._context.new_page()
        if self.url:
            self.goto(self.url)

    def close(self):
        try:
            if self._browser:
                self._browser.close()
        except: pass
        try:
            if self._play:
                self._play.__exit__(None, None, None)
        except: pass

    # ── Page Methods ──

    def goto(self, url: str):
        self._page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
        time.sleep(1)

    def wait(self, seconds: float = 1):
        time.sleep(seconds)

    def snapshot(self) -> PageState:
        """Get current page state as structured data."""
        data = self._page.evaluate("""() => {
            const info = [];
            const sel = 'input, textarea, select, button, a, form, [role=button], [tabindex]';
            document.querySelectorAll(sel).forEach(el => {
                const d = {};
                d.t = el.tagName.toLowerCase();
                if (el.id) d.id = el.id;
                if (el.placeholder) d.ph = el.placeholder;
                if (el.type) d.ty = el.type;
                if (el.value) d.v = String(el.value).substring(0,40);
                if (el.href) d.hr = el.href;
                if (el.textContent) d.tx = el.textContent.trim().substring(0,30);
                if (el.tagName === 'SELECT') {
                    d.opts = [];
                    for (let i=0; i<el.options.length; i++) d.opts.push(el.options[i].value);
                }
                if (el.id) {
                    const lb = el.closest('form')?.querySelector('label[for=\"'+el.id+'\"]');
                    if (lb) d.lb = lb.textContent.trim();
                }
                info.push(d);
            });
            return JSON.stringify({
                url: window.location.href,
                title: document.title,
                elements: info
            });
        }""")
        parsed = json.loads(data)
        return PageState(
            url=parsed["url"],
            title=parsed["title"],
            elements=parsed.get("elements", [])
        )

    def fill(self, selector: str, value: str) -> bool:
        el = self._page.query_selector(selector)
        if el:
            el.fill(value)
            return True
        for e in self._page.query_selector_all("input, textarea"):
            for attr in ["id", "name", "placeholder"]:
                val = e.get_attribute(attr) or ""
                search = selector.strip("#.")
                if search in val or selector.replace("input", "") in val:
                    e.fill(value)
                    return True
        return False

    def click(self, selector: str) -> bool:
        el = self._page.query_selector(selector)
        if el:
            el.click()
            return True
        txt = selector.lower().strip("button'\"")
        for b in self._page.query_selector_all("button, a, [role=button]"):
            bt = (b.text_content() or "").strip().lower()
            if txt in bt:
                b.click()
                return True
        return False

    def select(self, selector: str, value: str) -> bool:
        try:
            self._page.select_option(selector, value)
            return True
        except:
            return False

    def screenshot(self, path: str = "screenshot.png", full_page: bool = True):
        self._page.screenshot(path=path, full_page=full_page)

    def pdf(self, path: str = "page.pdf"):
        self._page.pdf(path=path)

    def evaluate(self, js: str):
        return self._page.evaluate(js)

    # ── Human-like Interaction Methods ──

    def scroll(self, direction: str = "down", amount: int = 400) -> str:
        """Mouse-wheel scroll in given direction."""
        dx, dy = 0, 0
        if direction == "down":
            dy = amount
        elif direction == "up":
            dy = -amount
        elif direction == "right":
            dx = amount
        elif direction == "left":
            dx = -amount
        self._page.mouse.wheel(dx, dy)
        return f"Scrolled {direction} by {amount}px"

    def scroll_to(self, selector: str) -> str:
        """Scroll element into view if needed."""
        el = self._page.query_selector(selector)
        if el:
            el.scroll_into_view_if_needed()
            return f"Scrolled to {selector}"
        return f"Element {selector} not found"

    def press(self, key: str) -> str:
        """Press keyboard key or combo (e.g., 'Enter', 'Control+a', 'Escape')."""
        self._page.keyboard.press(key)
        return f"Pressed {key}"

    def hover(self, selector: str) -> str:
        """Mouse over element (for menus, tooltips)."""
        el = self._page.query_selector(selector)
        if el:
            el.hover()
            return f"Hovered over {selector}"
        return f"Element {selector} not found"

    def drag(self, source_selector: str, target_selector: str) -> str:
        """HTML5-style drag from source to target."""
        src = self._page.query_selector(source_selector)
        dst = self._page.query_selector(target_selector)
        if src and dst:
            src.hover()
            self._page.mouse.down()
            dst.hover()
            self._page.mouse.up()
            return f"Dragged {source_selector} to {target_selector}"
        return f"Source or target element not found"

    def double_click(self, selector: str) -> str:
        """Double-click on element."""
        el = self._page.query_selector(selector)
        if el:
            el.dblclick()
            return f"Double-clicked {selector}"
        return f"Element {selector} not found"

    def right_click(self, selector: str) -> str:
        """Right-click (context menu) on element."""
        el = self._page.query_selector(selector)
        if el:
            el.click(button="right")
            return f"Right-clicked {selector}"
        return f"Element {selector} not found"

    def type_human(self, selector: str, text: str, delay_ms: int = 50) -> str:
        """Click element and type character by character with delay."""
        el = self._page.query_selector(selector)
        if el:
            el.click()
            self._page.keyboard.type(text, delay=delay_ms)
            return f"Typed '{text}' into {selector} with {delay_ms}ms delay"
        return f"Element {selector} not found"

    def clear(self, selector: str) -> str:
        """Clear input field (select-all + delete)."""
        el = self._page.query_selector(selector)
        if el:
            el.fill("")
            return f"Cleared {selector}"
        return f"Element {selector} not found"

    def wait_for(self, selector: str, timeout_s: int = 10) -> bool:
        """Wait for selector to appear; return True if found, False on timeout."""
        try:
            self._page.wait_for_selector(selector, timeout=timeout_s * 1000)
            return True
        except PwTimeout:
            return False

    # ── Shell Command Execution ──

    def run_cmd(self, command: str, timeout_s: int = 30) -> dict:
        """Run shell command with safety checks. Returns dict with cmd, stdout, stderr, returncode."""
        # Safety deny-list (dangerous commands)
        deny_patterns = [
            "rm -rf /",           # Recursive delete from root
            "mkfs",               # Filesystem formatting
            "dd of=/dev/",        # Direct disk writes
            ":(){",               # Fork bomb pattern
            "shutdown",           # System shutdown
            "reboot",             # System reboot
            "halt",               # System halt
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

    # ── Search Skill ──

    def search(self, query: str, engine: str = "duckduckgo", count: int = 10):
        engines = {
            "duckduckgo": f"https://duckduckgo.com/?q={urllib.parse.quote(query)}",
            "google": f"https://google.com/search?q={urllib.parse.quote(query)}",
            "bing": f"https://bing.com/search?q={urllib.parse.quote(query)}",
            "brave": f"https://search.brave.com/search?q={urllib.parse.quote(query)}",
        }
        url = engines.get(engine, engines["duckduckgo"])
        self.goto(url)
        self.wait(2)

        html = self._page.content()
        results = []
        for a in self._page.query_selector_all("a[href]"):
            href = a.get_attribute("href") or ""
            text = (a.text_content() or "").strip()
            if href.startswith("http") and text:
                results.append(SearchResult(title=text[:100], url=href))
                if len(results) >= count:
                    break
        return results

    def search_pdfs(self, query: str):
        return self.search(f"{query} filetype:pdf", count=20)

    # ── Navigation Skill ──

    def new_tab(self, url: str = ""):
        page = self._context.new_page()
        if url:
            page.goto(url, wait_until="networkidle")
        return page

    def switch_tab(self, index: int):
        pages = self._context.pages
        if 0 <= index < len(pages):
            self._page = pages[index]
            self._page.bring_to_front()

    def get_tabs(self):
        return list(self._context.pages)

    def back(self):
        self._page.go_back()

    def forward(self):
        self._page.go_forward()

    def refresh(self):
        self._page.reload()

    # ── Form Fill Skill ──

    def detect_forms(self) -> list:
        forms = []
        for form_el in self._page.query_selector_all("form"):
            sel = form_el.get_attribute("id") or form_el.get_attribute("name") or ""
            if sel:
                sel = f"#{sel}" if form_el.get_attribute("id") else f"[name='{sel}']"
            else:
                sel = "form"
            form = Form(selector=sel)
            for field in form_el.query_selector_all("input, textarea, select"):
                fsel = ""
                if field.get_attribute("id"):
                    fsel = f"#{field.get_attribute('id')}"
                elif field.get_attribute("name"):
                    fsel = f"[name='{field.get_attribute('name')}']"
                else:
                    continue
                label_text = ""
                fid = field.get_attribute("id")
                if fid:
                    lbl = form_el.query_selector(f"label[for='{fid}']")
                    if lbl:
                        label_text = (lbl.text_content() or "").strip()
                form.fields.append(FormField(
                    selector=fsel,
                    label=label_text,
                    type=field.get_attribute("type") or "text",
                    placeholder=field.get_attribute("placeholder") or ""
                ))
            forms.append(form)
        return forms

    def smart_fill(self, data: dict):
        forms = self.detect_forms()
        if not forms:
            return False
        form = forms[0]
        for field in form.fields:
            label_lower = (field.label + " " + field.placeholder).lower()
            val = None
            for key, v in data.items():
                if key.lower() in label_lower or key.lower() in field.selector.lower():
                    val = v
                    break
            if val:
                self.fill(field.selector, str(val))
        return True

    def submit(self):
        for btn in self._page.query_selector_all("button[type=submit], input[type=submit]"):
            btn.click()
            return True
        return False

    # ── Extract Skill ──

    def extract_text(self, selector: str = None) -> str:
        if selector:
            el = self._page.query_selector(selector)
            return (el.text_content() or "").strip() if el else ""
        return (self._page.text_content() or "").strip()

    def extract_links(self) -> list:
        links = []
        for a in self._page.query_selector_all("a[href]"):
            href = a.get_attribute("href") or ""
            text = (a.text_content() or "").strip()
            if href and not href.startswith("#"):
                links.append({"text": text[:80], "url": href})
        return links

    def extract_table(self, selector: str) -> list:
        rows = []
        table = self._page.query_selector(selector)
        if table:
            for tr in table.query_selector_all("tr"):
                cells = [td.text_content().strip() for td in tr.query_selector_all("td, th")]
                if cells:
                    rows.append(cells)
        return rows

    # ── Auth Skill ──

    def login(self, url: str, username: str, password: str):
        self.goto(url)
        self.wait(2)
        state = self.snapshot()
        prompt = f"""Task: Log into {url} with username '{username}' and password '{password}'.
Current page elements: {json.dumps([vars(e) for e in state.elements])}
Return a JSON array of actions to fill the login form and submit it.
Use realistic selectors based on the page elements.
Example: [{{"action":"fill","selector":"#email","value":"{username}"}},{{"action":"fill","selector":"#password","value":"{password}"}},{{"action":"click","selector":"button[type=submit]","value":""}}]"""
        response = ask_llm(prompt)
        try:
            plan = json.loads(re.sub(r'```(?:json)?\n?', '', response))
            if isinstance(plan, list):
                for step in plan:
                    self._execute_action(step)
                    self.wait(1)
        except: pass

    def save_state(self, name: str):
        path = os.path.expanduser(f"~/.browser-agent/sessions/{name}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._context.storage_state(path=path)

    def load_state(self, name: str):
        path = os.path.expanduser(f"~/.browser-agent/sessions/{name}.json")
        if os.path.exists(path):
            self._context.add_cookies(json.load(open(path)).get("cookies", []))
            self.refresh()

    # ── Signup Skill ──

    def signup(self, url: str, data: dict = None):
        self.goto(url)
        self.wait(2)
        if not data:
            import random
            r = random.randint(1000, 9999)
            data = {
                "name": f"Test User {r}",
                "email": f"testuser{r}@mailinator.com",
                "password": f"TestPass{r}!",
            }
        self.smart_fill(data)
        self.submit()

    # ── AI Decision ──

    def decide_next_action(self, state: PageState, task: str) -> list:
        elements_json = json.dumps([{
            "tag": e.get("t", ""),
            "id": e.get("id", ""),
            "label": e.get("lb", ""),
            "placeholder": e.get("ph", ""),
            "type": e.get("ty", ""),
            "text": e.get("tx", ""),
            "options": e.get("opts", []),
            "href": e.get("hr", ""),
        } for e in state.elements])

        prompt = f"""Task: {task}
Current page URL: {state.url}
Title: {state.title}
Page elements: {elements_json}

Create a step-by-step plan as a JSON array of actions to complete the task.
Available actions:
- fill: {{"action":"fill","selector":"css-selector","value":"text"}}
- click: {{"action":"click","selector":"css-selector"}}
- select: {{"action":"select","selector":"css-selector","value":"option"}}
- goto: {{"action":"goto","value":"url"}}
- scroll: {{"action":"scroll","value":"down/up/left/right","amount":400}}
- scroll_to: {{"action":"scroll_to","selector":"css-selector"}}
- press: {{"action":"press","value":"key"}} (e.g., "Enter", "Escape", "Control+a")
- hover: {{"action":"hover","selector":"css-selector"}}
- drag: {{"action":"drag","selector":"source","target":"target"}}
- double_click: {{"action":"double_click","selector":"css-selector"}}
- right_click: {{"action":"right_click","selector":"css-selector"}}
- type: {{"action":"type","selector":"css-selector","value":"text","delay_ms":50}}
- clear: {{"action":"clear","selector":"css-selector"}}
- wait: {{"action":"wait","selector":"css-selector","timeout_s":10}}
- cmd: {{"action":"cmd","value":"shell command","timeout_s":30}}

Use realistic dummy data for forms. Return ONLY the JSON array, no other text."""
        response = ask_llm(prompt)
        response = re.sub(r'```(?:json)?\n?', '', response).strip()
        try:
            plan = json.loads(response)
            if isinstance(plan, list):
                return plan
        except: pass
        return []

    def _execute_action(self, action: dict) -> bool:
        at = action.get("action", "")
        sel = action.get("selector", "")
        val = action.get("value", "")
        amt = action.get("amount", 400)
        tgt = action.get("target", "")
        if at == "fill":
            return self.fill(sel, val)
        elif at == "click":
            return self.click(sel)
        elif at == "select":
            return self.select(sel, val)
        elif at == "goto":
            self.goto(val or sel)
            return True
        elif at == "scroll":
            self.scroll(direction=val, amount=amt)
            return True
        elif at == "scroll_to":
            self.scroll_to(sel)
            return True
        elif at == "press":
            self.press(val)
            return True
        elif at == "hover":
            self.hover(sel)
            return True
        elif at == "drag":
            self.drag(sel, tgt)
            return True
        elif at == "double_click":
            self.double_click(sel)
            return True
        elif at == "right_click":
            self.right_click(sel)
            return True
        elif at == "type":
            delay = action.get("delay_ms", 50)
            self.type_human(sel, val, delay_ms=delay)
            return True
        elif at == "clear":
            self.clear(sel)
            return True
        elif at == "wait":
            timeout = action.get("timeout_s", 10)
            return self.wait_for(sel, timeout_s=timeout)
        elif at == "cmd":
            timeout = action.get("timeout_s", 30)
            self.run_cmd(val, timeout_s=timeout)
            return True
        return True

    def run_task(self, task: str, max_steps: int = 20, verbose: bool = False):
        if not self._page:
            self.start()

        print(f"Target: {self.url}")
        print(f"Task: {task}")
        print("Analyzing page...")
        state = self.snapshot()
        plan = self.decide_next_action(state, task)

        if not plan:
            print("Could not generate plan. Running with snapshot analysis only.")
            return

        print(f"\nPlan ({len(plan)} steps):")
        for i, step in enumerate(plan, 1):
            print(f"  {i}. {step.get('action')}: {step.get('selector', '')} {step.get('value', '')}")

        print("\nExecuting...")
        for i, step in enumerate(plan, 1):
            if verbose:
                print(f"  [{i}/{len(plan)}] {step.get('action')} {step.get('selector', '')}")
            ok = self._execute_action(step)
            if not ok and verbose:
                print(f"    Warning: action may have failed")
            self.wait(1)

        self.wait(2)
        final_state = self.snapshot()
        print(f"\nFinal: {final_state.title}")
        print(f"URL: {final_state.url}")


# ─── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Browser Agent - Web Automation")
    parser.add_argument("--url", required=True, help="Starting URL")
    parser.add_argument("--task", required=True, help="Task description")
    parser.add_argument("--headless", action="store_true", default=True,
                       help="Run headless (default: True)")
    parser.add_argument("--visible", action="store_false", dest="headless",
                       help="Show browser window")
    parser.add_argument("--viewport", default="1280x800", help="Viewport size (WxH)")
    parser.add_argument("--timeout", type=int, default=30, help="Page load timeout (s)")
    parser.add_argument("--verbose", action="store_true", help="Detailed logs")
    parser.add_argument("--output", help="Save screenshot to file")
    args = parser.parse_args()

    w, h = map(int, args.viewport.split("x"))
    agent = BrowserAgent(url=args.url, headless=args.headless,
                         viewport=(w, h), timeout=args.timeout)

    try:
        agent.run_task(args.task, verbose=args.verbose)
        if args.output:
            agent.screenshot(args.output)
    finally:
        agent.close()


if __name__ == "__main__":
    main()
