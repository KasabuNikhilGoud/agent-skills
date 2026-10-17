#!/usr/bin/env python3
"""THE AGENT LOOP: observe -> think -> act -> repeat.
Run:  python3 agent.py "open a terminal and type hello"

Observation now comes from eyes.py: window titles plus position, size and
which window is active, as plain text.
"""
import sys, hands, brain, eyes

def run_tool(action: dict) -> str:
    t, a = action.get("tool"), action.get("args", {})
    f = {"open_app": lambda: hands.open_app(a["name"]),
         "see_windows": lambda: eyes.screen_state(),
         "find_window": lambda: str(eyes.find_window(a["keyword"])),
         "click": lambda: hands.click(a["x"], a["y"]),
         "type_text": lambda: hands.type_text(a["text"]),
         "press": lambda: hands.press(a["key"]),
         "screenshot": lambda: hands.screenshot(a.get("path"))}.get(t)
    return f() if f else f"Unknown tool: {t}"

def main(task: str, max_steps: int = 8):
    history, step = [], 0
    while step < max_steps:
        screen = eyes.screen_state()                     # 1. OBSERVE
        action = brain.next_step(task, screen, history)  # 2. THINK
        print(f"[{step}] -> {action}")
        if action.get("tool") == "done":
            print("TASK COMPLETE"); break
        result = run_tool(action)                        # 3. ACT
        print(f"    {result}")
        history.append({"action": str(action), "result": result})
        step += 1

if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "open a terminal and type hello")
