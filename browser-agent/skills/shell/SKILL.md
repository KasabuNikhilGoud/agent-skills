---
name: shell
description: Linux shell command execution with safety deny-list
commands:
  - run_cmd
---

# Shell Skill

Execute Linux shell commands with built-in safety protections. Useful for system checks, file operations, and integrating browser automation with local workflows.

## When to Use

- Running system commands (ls, df, grep, etc.)
- File system operations within safe bounds
- Checking system status or resources
- Integrating browser actions with local scripts

## Safety Deny-List

The following dangerous commands are **blocked** and will return an error:

- `rm -rf /` - Recursive delete from root
- `mkfs` - Filesystem formatting
- `dd of=/dev/` - Direct disk writes
- `:(){` - Fork bomb pattern
- `shutdown` - System shutdown
- `reboot` - System reboot
- `halt` - System halt

**Always** review commands before execution. The deny-list is a safety layer, not a substitute for caution.

## Commands

### `run_cmd <command> <timeout_s>`

Run shell command with safety checks. Returns dict with keys: `cmd`, `stdout`, `stderr`, `returncode`.

```python
result = browser.run_cmd("ls -la", timeout_s=30)
print(result["stdout"])
print(result["returncode"])
```

## Examples

```python
# Safe system checks
result = browser.run_cmd("df -h")
print(f"Disk usage: {result['stdout']}")

result = browser.run_cmd("free -m")
print(f"Memory: {result['stdout']}")

# File operations
result = browser.run_cmd("ls -lh /tmp")
files = result["stdout"].split("\n")

# Search and filter
result = browser.run_cmd("grep -r 'pattern' /path/to/dir")
matches = result["stdout"]

# Check command success
result = browser.run_cmd("test -f /etc/hosts")
if result["returncode"] == 0:
    print("File exists")

# Blocked command (returns error)
result = browser.run_cmd("rm -rf /")
print(result["stderr"])  # "Command denied by safety policy..."
```

## Return Format

```python
{
    "cmd": "ls -la",
    "stdout": "total 0\ndrwxr-xr-x ...",
    "stderr": "",
    "returncode": 0
}
```

- `returncode`: 0 for success, non-zero for errors, -1 for denied/timeout
- `stderr`: Error message if command failed or was denied
- `stdout`: Command output (stdout stream)
