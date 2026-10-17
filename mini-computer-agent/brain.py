"""BRAIN: turns a task + what the screen shows into the next tool call.

In a real agent this is one LLM API call. Set OPENAI_API_KEY (+OPENAI_BASE_URL
for any OpenAI-compatible provider) and llm_next_step() is used.
With no key, scripted_next_step() runs a tiny keyword demo brain so you can
still test the eyes/hands loop end-to-end."""
import json, os, re, hands

SYSTEM = f"""You are a computer-use agent. You control a Linux desktop.
You NEVER see images; you read text reports and reply with ONE action.
Available tools:
{hands.TOOLS}
Reply with a single line of JSON, nothing else:
{{"tool": "...", "args": {{...}}}}
Reply {{"tool": "done"}} when the task is finished."""

def llm_next_step(task: str, screen: str, history: list) -> dict:
    from openai import OpenAI
    client = OpenAI(base_url=os.environ.get("OPENAI_BASE_URL"))
    msgs = [{"role": "system", "content": SYSTEM}]
    for h in history:
        msgs.append({"role": "assistant", "content": h["action"]})
        msgs.append({"role": "user", "content": h["result"]})
    msgs.append({"role": "user", "content": f"TASK: {task}\n\nSCREEN:\n{screen}"})
    r = client.chat.completions.create(model=os.environ.get("MODEL", "gpt-4o-mini"),
                                       messages=msgs, temperature=0)
    return json.loads(r.choices[0].message.content)

def scripted_next_step(task: str, screen: str, history: list) -> dict:
    """Demo brain (no API key needed): follows a fixed plan for one task."""
    plan = [
        {"tool": "open_app",   "args": {"name": "gnome-terminal"}},
        {"tool": "see_windows", "args": {}},
        {"tool": "type_text",  "args": {"text": "echo 'my agent typed this'; date"}},
        {"tool": "press",      "args": {"key": "Return"}},
        {"tool": "done",       "args": {}},
    ]
    return plan[len(history)] if len(history) < len(plan) else {"tool": "done", "args": {}}

def next_step(task, screen, history):
    if os.environ.get("OPENAI_API_KEY"):
        return llm_next_step(task, screen, history)
    return scripted_next_step(task, screen, history)
