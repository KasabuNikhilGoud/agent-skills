"""BRAIN: turns a task + screen state into the next tool call (one JSON action).

Four interchangeable brains:
- opencode: shells out to the `opencode` CLI - no API key in your code,
  works wherever `opencode run` is authenticated (same pattern as the
  repo's web_agent.py)
- openai: any OpenAI-compatible API via OPENAI_API_KEY / OPENAI_BASE_URL
- scripted: a fixed plan, for offline demos and tests
- manual: reads one JSON action per line from stdin, so a human (or another
  AI) can drive the loop step by step
"""
import json
import os
import re
import subprocess

import hands

SYSTEM = f"""You are a computer-use agent controlling a Linux desktop.
You NEVER see images. You get a TEXT report of the screen and must reply
with exactly ONE JSON action on a single line.
Available tools:
{hands.TOOLS}
Reply format: {{"tool": "...", "args": {{...}}}}
When the task is finished reply: {{"tool": "done"}}
"""

ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def parse_action(reply: str) -> dict:
    """Extract the first JSON object from a model reply.

    Models love to wrap JSON in chatter ("Sure! Here you go: {...}"), so we
    scan for the outermost {...} block, strip ANSI colors, and validate that
    the result has a "tool" key. Raises ValueError with a clear message so
    the caller can feed the error back to the model.
    """
    reply = ANSI.sub("", reply).strip()
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object found in reply: {reply[:200]!r}")
    try:
        action = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in reply: {e}")
    if "tool" not in action:
        raise ValueError(f"action has no 'tool' key: {action!r}")
    return action


def _prompt(task: str, screen: str, history: list, guidance: str = "") -> str:
    parts = [f"TASK: {task}"]
    if guidance:
        parts.append(f"SUGGESTED SKILL:\n{guidance}")
    parts.append(f"SCREEN:\n{screen}")
    if history:
        parts.append("HISTORY (last 3):\n" + "\n".join(
            f"- {h['action']} -> {h['result']}" for h in history[-3:]))
    return "\n\n".join(parts) + "\n\nNext action (one JSON line):"


def opencode_next_step(task, screen, history, guidance="") -> dict:
    """Ask the opencode CLI for the next action (no API key needed)."""
    cmd = ["opencode", "run"]
    if os.environ.get("OPENCODE_MODEL"):
        cmd += ["-m", os.environ["OPENCODE_MODEL"]]
    cmd.append(SYSTEM + "\n\n" + _prompt(task, screen, history, guidance))
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return parse_action(proc.stdout + proc.stderr)


def llm_next_step(task, screen, history, guidance="") -> dict:
    """Ask an OpenAI-compatible API for the next action."""
    from openai import OpenAI
    client = OpenAI(base_url=os.environ.get("OPENAI_BASE_URL"))
    r = client.chat.completions.create(
        model=os.environ.get("MODEL", "gpt-4o-mini"),
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user",
                   "content": _prompt(task, screen, history, guidance)}],
        temperature=0)
    return parse_action(r.choices[0].message.content)


def scripted_next_step(task, screen, history, guidance="") -> dict:
    """Demo brain (no API key needed): follows a fixed plan for one task."""
    plan = [
        {"tool": "open_app", "args": {"name": "gnome-terminal"}},
        {"tool": "see_windows", "args": {}},
        {"tool": "type_text", "args": {"text": "echo 'my agent typed this'; date"}},
        {"tool": "press", "args": {"key": "Return"}},
        {"tool": "done", "args": {}},
    ]
    return plan[len(history)] if len(history) < len(plan) else {"tool": "done", "args": {}}


def manual_next_step(task, screen, history, guidance="") -> dict:
    """Read one JSON action from stdin - lets a human or AI drive the loop."""
    print(f"    screen:\n{screen}")
    line = input("action> ")
    return parse_action(line)


def next_step(which: str, task, screen, history, guidance="") -> dict:
    """Dispatch to the chosen brain. which: opencode|openai|scripted|manual|auto."""
    if which == "manual":
        return manual_next_step(task, screen, history, guidance)
    if which == "scripted":
        return scripted_next_step(task, screen, history, guidance)
    if which == "opencode":
        return opencode_next_step(task, screen, history, guidance)
    if which == "openai":
        return llm_next_step(task, screen, history, guidance)
    # auto: prefer a real LLM if an API key is configured, else scripted
    if os.environ.get("OPENAI_API_KEY"):
        return llm_next_step(task, screen, history, guidance)
    return scripted_next_step(task, screen, history, guidance)
