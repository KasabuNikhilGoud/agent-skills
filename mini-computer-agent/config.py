"""SAFETY: what the agent may and may not do.

An agent that can click and type can also delete files. These checks run
BEFORE any action is executed, so a confused model can not talk its way
past them. Edit ALLOWED_APPS to match your machine.
"""

# Apps the agent is allowed to launch. Anything else is refused.
ALLOWED_APPS = {
    "gnome-terminal",
    "xfce4-terminal",
    "libreoffice --calc",
    "libreoffice --writer",
    "libreoffice --impress",
    "firefox",
    "chromium",
    "pcmanfm",
    "gedit",
    "mousepad",
    "xeyes",
}

# Set to True by the --dry-run CLI flag: print actions instead of executing.
DRY_RUN = False


def app_allowed(name: str) -> bool:
    return name.strip() in ALLOWED_APPS


def check_action(action: dict):
    """Return a refusal reason string, or None if the action is permitted."""
    if action.get("tool") == "open_app":
        name = (action.get("args") or {}).get("name", "")
        if not app_allowed(name):
            return (f"app '{name}' is not in the allowlist; allowed: "
                    f"{', '.join(sorted(ALLOWED_APPS))}")
    return None
