"""PERFORMANCE: fast-path execution and smart compression.

Optimizations for speed, reduced token usage, and fewer API calls.
"""
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import eyes
import hands

# Fast-path common workflows
FAST_PATHS = {
    "open terminal": [
        {"tool": "open_app", "args": {"name": "gnome-terminal"}},
        {"tool": "see_windows", "args": {}}
    ],
    "open browser": [
        {"tool": "open_app", "args": {"name": "firefox"}},
        {"tool": "see_windows", "args": {}}
    ]
}

def compress_screen_state(screen: str, max_lines: int = 5) -> str:
    """Compress screen state to reduce token usage."""
    lines = screen.split('\n')
    if len(lines) <= max_lines:
        return screen
    return '\n'.join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more windows)"

def execute_parallel(actions: List[dict]) -> List[str]:
    """Execute independent actions in parallel for speed."""
    independent_tools = {"screenshot", "get_screen_geometry", "list_apps"}
    
    parallel_actions = [a for a in actions if a.get("tool") in independent_tools]
    if not parallel_actions:
        return []
    
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for action in parallel_actions:
            t = action.get("tool")
            if t == "screenshot":
                futures.append(executor.submit(hands.screenshot, action.get("args", {}).get("path")))
            elif t == "get_screen_geometry":
                futures.append(executor.submit(hands.get_screen_geometry))
            elif t == "list_apps":
                futures.append(executor.submit(hands.list_apps))
        
        for future in futures:
            results.append(future.result())
    
    return results

def smart_history_filter(history: List[dict], max_entries: int = 2) -> List[dict]:
    """Keep only relevant history to reduce token usage."""
    if len(history) <= max_entries:
        return history
    # Keep first and last entries, skip middle
    return [history[0]] + history[-max_entries+1:]

def detect_fast_path(task: str) -> Optional[List[dict]]:
    """Detect if task matches a known fast-path workflow."""
    task_lower = task.lower()
    for pattern, actions in FAST_PATHS.items():
        if pattern in task_lower:
            return actions
    return None
