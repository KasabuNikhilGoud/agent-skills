"""OPTIMIZER: reduce tool calls through batching and caching.

Inspired by usecomputer's coordination patterns and Hermes Agent's
efficient action batching. Reduces API calls by combining related
operations and caching expensive queries.
"""
import time
from typing import Dict, List, Any, Optional
from functools import lru_cache


class ToolOptimizer:
    """Optimizes tool execution by batching and caching."""

    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: float = 2.0  # Cache for 2 seconds
        self.last_screen_state: Optional[str] = None
        self.last_window_list: Optional[List] = None
        self.cache_time: float = 0

    def is_cache_valid(self) -> bool:
        """Check if cache is still valid based on TTL."""
        return time.time() - self.cache_time < self.cache_ttl

    def invalidate_cache(self):
        """Invalidate the cache when screen state changes."""
        self.cache.clear()
        self.last_screen_state = None
        self.last_window_list = None
        self.cache_time = 0

    def batch_actions(self, actions: List[dict]) -> List[dict]:
        """Combine compatible actions into batches.

        Rules:
        - Multiple clicks can be batched
        - Mouse moves can be combined with clicks
        - Text typing can be batched
        - Key presses can be batched
        """
        if not actions:
            return []

        batches = []
        current_batch = []

        for action in actions:
            tool = action.get("tool")

            # Cannot batch these - they must be separate
            if tool in ["open_app", "run_command", "screenshot", "list_apps"]:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                batches.append([action])
                continue

            # Try to add to current batch
            if not current_batch:
                current_batch.append(action)
            elif self._can_batch(current_batch[-1], action):
                current_batch.append(action)
            else:
                batches.append(current_batch)
                current_batch = [action]

        if current_batch:
            batches.append(current_batch)

        return batches

    def _can_batch(self, prev_action: dict, curr_action: dict) -> bool:
        """Check if two actions can be batched together."""
        prev_tool = prev_action.get("tool")
        curr_tool = curr_action.get("tool")

        # Same tool can be batched
        if prev_tool == curr_tool:
            return True

        # Click after move can be batched
        if prev_tool == "hover" and curr_tool == "click":
            return True

        # Type text can be batched with keys
        if prev_tool == "type_text" and curr_tool == "press":
            return True

        return False

    def optimize_action(self, action: dict) -> dict:
        """Optimize a single action by adding smart defaults."""
        tool = action.get("tool")
        args = action.get("args", {})

        # Add default delays for smoother execution
        if tool in ["click", "double_click", "right_click"]:
            args.setdefault("delay", 50)

        if tool == "type_text":
            args.setdefault("delay", 40)

        if tool == "scroll":
            args.setdefault("direction", "down")
            args.setdefault("clicks", 1)

        if tool == "drag":
            # Validate drag coordinates
            x1, y1 = args.get("x1", 0), args.get("y1", 0)
            x2, y2 = args.get("x2", 0), args.get("y2", 0)
            if x1 == x2 and y1 == y2:
                # No movement, convert to click
                return {"tool": "click", "args": {"x": x1, "y": y1}}

        return {"tool": tool, "args": args}

    def suggest_batch(self, task: str, history: List[dict]) -> Optional[List[dict]]:
        """Suggest a batch of actions based on task and history.

        This is a heuristic - the brain can choose to use it or not.
        """
        suggestions = []

        # If task involves typing text, suggest combining multiple characters
        if "type" in task.lower() or "enter" in task.lower():
            # Check if we have recent type_text calls
            recent_types = [h for h in history[-3:] if "type_text" in str(h)]
            if len(recent_types) >= 2:
                suggestions.append({
                    "tool": "type_text",
                    "args": {"text": "", "delay": 40},
                    "hint": "Combine multiple type_text calls into one"
                })

        # If task involves navigation, suggest move+click batch
        if "click" in task.lower() or "select" in task.lower():
            suggestions.append({
                "tool": "click",
                "args": {"x": 0, "y": 0, "delay": 50},
                "hint": "Use hover before click for better accuracy"
            })

        return suggestions if suggestions else None


# Global optimizer instance
optimizer = ToolOptimizer()


def get_cached_screen_state(get_state_func) -> str:
    """Get screen state with caching to avoid redundant queries."""
    if optimizer.is_cache_valid() and optimizer.last_screen_state:
        return optimizer.last_screen_state

    state = get_state_func()
    optimizer.last_screen_state = state
    optimizer.cache_time = time.time()
    return state


def get_cached_window_list(get_list_func) -> List:
    """Get window list with caching to avoid redundant queries."""
    if optimizer.is_cache_valid() and optimizer.last_window_list:
        return optimizer.last_window_list

    windows = get_list_func()
    optimizer.last_window_list = windows
    optimizer.cache_time = time.time()
    return windows


def should_invalidate_cache(action: dict) -> bool:
    """Determine if an action should invalidate the cache."""
    tool = action.get("tool")
    # These actions change screen state
    return tool in ["click", "type_text", "press", "scroll", "drag",
                    "open_app", "close_window", "move_window", "resize_window"]
