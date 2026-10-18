"""ERROR HANDLING: detect, classify, and recover from errors.

Inspired by Hermes Agent's error recovery patterns and OpenClaw's safety
mechanisms. Provides retry logic, error classification, and automatic
recovery strategies for common desktop automation failures.
"""
import time
from typing import Optional, Callable, Any
from enum import Enum


class ErrorType(Enum):
    """Classification of error types for targeted recovery."""
    TIMEOUT = "timeout"
    WINDOW_NOT_FOUND = "window_not_found"
    APP_LAUNCH_FAILED = "app_launch_failed"
    COMMAND_FAILED = "command_failed"
    INVALID_COORDINATES = "invalid_coordinates"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"


class AgentError(Exception):
    """Base exception for agent errors with recovery suggestions."""
    def __init__(self, message: str, error_type: ErrorType,
                 recoverable: bool = True, recovery_hint: str = ""):
        super().__init__(message)
        self.error_type = error_type
        self.recoverable = recoverable
        self.recovery_hint = recovery_hint


def classify_error(error_msg: str, tool: str) -> ErrorType:
    """Classify an error message into a type for targeted recovery."""
    msg_lower = error_msg.lower()

    if "timeout" in msg_lower or "timed out" in msg_lower:
        return ErrorType.TIMEOUT
    if "no window" in msg_lower or "not found" in msg_lower and "window" in msg_lower:
        return ErrorType.WINDOW_NOT_FOUND
    if "launch" in msg_lower and "failed" in msg_lower:
        return ErrorType.APP_LAUNCH_FAILED
    if "permission" in msg_lower or "denied" in msg_lower:
        return ErrorType.PERMISSION_DENIED
    if "command" in msg_lower and "failed" in msg_lower:
        return ErrorType.COMMAND_FAILED
    if "coordinate" in msg_lower or "position" in msg_lower:
        return ErrorType.INVALID_COORDINATES

    return ErrorType.UNKNOWN


def get_recovery_strategy(error_type: ErrorType) -> str:
    """Return a recovery strategy hint for the given error type."""
    strategies = {
        ErrorType.TIMEOUT: "Wait longer before retrying, or check if the system is responsive",
        ErrorType.WINDOW_NOT_FOUND: "List windows first to verify the target exists, or try opening the app",
        ErrorType.APP_LAUNCH_FAILED: "Check if the app is installed, try alternative launch command, or verify allowlist",
        ErrorType.COMMAND_FAILED: "Verify command syntax, check permissions, or try a simpler command",
        ErrorType.INVALID_COORDINATES: "Get screen geometry first, ensure coordinates are within bounds",
        ErrorType.PERMISSION_DENIED: "Check allowlist in config.py, or run with appropriate permissions",
        ErrorType.UNKNOWN: "Review the error message and try a different approach",
    }
    return strategies.get(error_type, "Unknown error - review and retry")


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    tool: str = "unknown"
) -> Any:
    """Execute a function with exponential backoff retry logic.

    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay after each retry
        tool: Tool name for error classification

    Returns:
        Function result on success

    Raises:
        AgentError: If all retries are exhausted
    """
    last_error = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_error = e
            error_type = classify_error(str(e), tool)
            recovery_hint = get_recovery_strategy(error_type)

            if attempt == max_retries:
                raise AgentError(
                    f"Failed after {max_retries} retries: {str(e)}",
                    error_type=error_type,
                    recoverable=False,
                    recovery_hint=recovery_hint
                )

            print(f"[retry] Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            print(f"[retry] Recovery hint: {recovery_hint}")
            time.sleep(delay)
            delay *= backoff_factor

    raise AgentError(
        f"Unexpected error in retry logic: {str(last_error)}",
        error_type=ErrorType.UNKNOWN,
        recoverable=False
    )


def validate_coordinates(x: int, y: int, screen_w: int = 1920, screen_h: int = 1080) -> bool:
    """Validate that coordinates are within screen bounds."""
    return 0 <= x <= screen_w and 0 <= y <= screen_h


def format_error_for_brain(error: AgentError) -> str:
    """Format an error for the LLM brain to understand and potentially recover."""
    return (
        f"ERROR: {str(error)}\n"
        f"Type: {error.error_type.value}\n"
        f"Recoverable: {error.recoverable}\n"
        f"Suggestion: {error.recovery_hint}"
    )
