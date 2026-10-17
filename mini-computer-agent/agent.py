#!/usr/bin/env python3
"""mini-computer-agent: observe -> think -> act -> repeat.

A small computer-use agent that opens apps, clicks and types on a Linux
desktop. See DESIGN.md for the architecture and EXAMPLES.md for transcripts.

Usage:
    python3 agent.py "open a terminal and type hello"
    python3 agent.py --brain opencode "open libreoffice calc"
    python3 agent.py --brain manual "open libreoffice calc"   # you drive it
    python3 agent.py --dry-run "open a terminal"              # print only
    python3 agent.py --list-skills
"""
import argparse
import sys

import brain
import config
import eyes
import hands


def run_tool(action: dict) -> str:
    t, a = action.get("tool"), action.get("args") or {}
    f = {"open_app": lambda: hands.open_app(a["name"]),
         "see_windows": lambda: eyes.screen_state(),
         "find_window": lambda: str(eyes.find_window(a["keyword"])),
         "click": lambda: hands.click(a["x"], a["y"]),
         "type_text": lambda: hands.type_text(a["text"]),
         "press": lambda: hands.press(a["key"]),
         "screenshot": lambda: hands.screenshot(a.get("path"))}.get(t)
    return f() if f else f"Unknown tool: {t}"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="mini computer-use agent",
        epilog="brains: opencode (CLI, no API key), openai (API key), "
               "scripted (offline demo), manual (you type JSON actions)")
    ap.add_argument("task", nargs="*", help="what the agent should do")
    ap.add_argument("--brain", default="auto",
                    choices=["auto", "opencode", "openai", "scripted", "manual"])
    ap.add_argument("--dry-run", action="store_true",
                    help="print actions without executing them")
    ap.add_argument("--max-steps", type=int, default=8,
                    help="safety cap on the loop (default 8)")
    args = ap.parse_args()

    config.DRY_RUN = args.dry_run
    task = " ".join(args.task) or "open a terminal and type hello"

    history = []
    for step in range(args.max_steps):
        screen = eyes.screen_state()                      # 1. OBSERVE
        try:
            action = brain.next_step(args.brain, task, screen, history)
        except ValueError as e:
            print(f"[error] brain output rejected: {e}")
            return 1
        print(f"[{step}] brain -> {action}")

        if action.get("tool") == "done":
            print("TASK COMPLETE")
            return 0

        refusal = config.check_action(action)             # 2. SAFETY GATE
        if refusal:
            result = f"REFUSED: {refusal}"
        elif config.DRY_RUN:
            result = f"(dry-run) would run: {action}"
        else:
            result = run_tool(action)                     # 3. ACT
        print(f"    result: {result}")

        history.append({"action": str(action), "result": result})
    print("Stopped: max steps reached")
    return 1


if __name__ == "__main__":
    sys.exit(main())
