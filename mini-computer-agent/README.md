# mini-computer-agent

A computer-use agent that opens apps, clicks, and types on a Linux desktop.
Inspired by Hermes Agent, usecomputer, and OpenClaw patterns for efficient
desktop automation with error recovery and optimization.

## The architecture

```
task --> BRAIN --> one JSON action per turn --> HANDS (xdotool)
          ^                                        |
          +---- text report (windows, results) <---+
          OPTIMIZER: caching, batching, smart defaults
          ERROR HANDLER: retry logic, classification, recovery
```

The loop (`agent.py`): **observe -> think -> act -> repeat** until the brain
says `done` or the step limit is hit.

## Files

| File | Role |
|------|------|
| `hands.py` | EYES + HANDS: 20+ tools for desktop control |
| `brain.py` | THINK: `llm_next_step()` (real LLM) or `scripted_next_step()` (offline demo) |
| `agent.py` | the loop that wires eyes + brain + hands together |
| `eyes.py` | OBSERVE: window detection with wmctrl + xdotool fallback |
| `errors.py` | ERROR HANDLING: classification, retry logic, recovery strategies |
| `optimizer.py` | OPTIMIZATION: caching, batching, smart defaults |
| `config.py` | SAFETY: app allowlist, command safety checks |
| `skills.py` | SKILLS: skill file loader and matcher |
| `skills/` | SKILL.md files for common workflows |

## Run the offline demo (no API key needed)

```bash
export DISPLAY=:1
python3 agent.py "open a terminal and type hello"
```

The scripted brain opens gnome-terminal, reads the window list, types a
command and presses Enter -- proves the whole loop works without any API.

## Upgrade to a real LLM brain

```bash
pip install openai
export OPENAI_API_KEY=sk-...
export MODEL=gpt-4o-mini        # any OpenAI-compatible model
python3 agent.py "open libreoffice calc"
```

The brain receives the task + window list + previous results and must reply
with exactly one JSON action. That single constraint is what turns a chatbot
into an agent.

## Upgrade path (in order of payoff)

1. ~~**Better eyes** -- window titles + geometry (`wmctrl -l -G`), then the
   accessibility tree (`pyatspi`): every button and label as text.~~ ✅ **DONE**
2. **Vision fallback** -- send `screenshot()` output to a vision model only
   when text isn't enough. Slower and pricier; not the default.
3. ~~**Safety** -- allowlist of apps/commands, `--dry-run` flag, confirmation
   before destructive actions.~~ ✅ **DONE**
4. ~~**Skills** -- a `skills/` folder of `SKILL.md` files keyword-matched to the
   task and injected into the system prompt.~~ ✅ **DONE**
5. ~~**More tools** -- window management (focus, move, resize, close), drag,
   scroll, and shell command execution.~~ ✅ **DONE**
6. ~~**Error handling** -- retry logic, error classification, and recovery strategies.~~ ✅ **DONE**
7. ~~**Optimization** -- caching, batching, and smart defaults to reduce API calls.~~ ✅ **DONE**
