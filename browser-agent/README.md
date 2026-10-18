# Browser Agent - Complete Web Browser Automation Skill System

An open-source web browser agent system with modular skills for autonomous browser automation. Built on top of the **agent-browser** CLI (Vercel) and **Playwright**, organized as OpenClaw-compatible skills with clean folder structure, markdown docs, and runnable examples.

## Architecture

```
browser-agent/
├── agent/              # Core agent engine
│   ├── instructions.md # System prompt + persona
│   └── browser.py      # Browser automation engine
├── skills/             # Modular skills (OpenClaw SKILL.md format)
│   ├── search/         # Web search, multi-engine, results extraction
│   ├── navigation/     # Page navigation, tabs, sessions, history
│   ├── form-fill/      # Form detection, smart fill, submit
│   ├── extract/        # Data extraction, PDFs, tables, lists
│   ├── auth/           # Login flows, session save/load, SSO
│   ├── signup/         # Account creation, email verify, onboarding
│   └── monitor/        # Page watcher, change detection, polling
├── scripts/            # Runnable scripts
│   ├── browser_agent.py  # Main agent runner
│   ├── install.sh        # Dependency installer
│   └── run.sh            # Quick run wrapper
└── docs/               # Documentation
    ├── getting-started.md
    ├── api-reference.md
    └── examples.md
```

## Quick Start

```bash
# Install dependencies
bash scripts/install.sh

# Run the browser agent
python3 scripts/browser_agent.py --url https://example.com --task "search for something"

# Run tests
python3 scripts/test_interact.py
```

## Skills Overview

| Skill | Description | Commands |
|-------|-------------|----------|
| **search** | Multi-engine search, result extraction | `search`, `search-images`, `search-news` |
| **navigation** | Page nav, tabs, sessions, history | `goto`, `back`, `tabs`, `sessions` |
| **form-fill** | Form detection, smart fill, submit | `fill`, `select`, `submit`, `detect-forms` |
| **extract** | Data extraction from pages | `extract`, `snapshot`, `pdf`, `screenshot` |
| **auth** | Login flows, session management | `login`, `state-save`, `state-load` |
| **signup** | Account creation, verify, onboard | `signup`, `verify-email`, `onboard` |
| **monitor** | Page watching, change detection | `watch`, `poll`, `diff` |
| **interact** | Human-like interactions (scroll, keyboard, mouse) | `scroll`, `press`, `hover`, `drag`, `type_human` |
| **shell** | Linux shell command execution with safety | `run_cmd` |

## Integration

This system works with:
- **OpenClaw** - Load skills into `~/.openclaw/skills/` directory
- **Opencode** - Uses `opencode run` for AI reasoning
- **agent-browser** (Vercel) - CLI integration for fast browser control
- **Standalone** - Run directly with Python + Playwright

## License

Apache 2.0
