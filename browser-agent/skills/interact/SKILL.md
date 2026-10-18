---
name: interact
description: Human-like browser interactions (scroll, keyboard, mouse, drag-drop)
commands:
  - scroll
  - scroll_to
  - press
  - hover
  - drag
  - double_click
  - right_click
  - type_human
  - clear
  - wait_for
---

# Interact Skill

Human-like browser interactions for natural automation: scrolling, keyboard shortcuts, mouse gestures, drag-and-drop, and realistic typing.

## When to Use

- Scrolling through long pages or dynamic content
- Triggering menus or tooltips via hover
- Keyboard shortcuts and form navigation
- Drag-and-drop interfaces
- Realistic typing (human-speed with delays)
- Waiting for dynamic elements to appear

## Commands

### `scroll <direction> <amount>`

Mouse-wheel scroll. Directions: down, up, left, right.

```python
browser.scroll("down", 400)
browser.scroll("up", 200)
```

### `scroll_to <selector>`

Scroll element into view if needed.

```python
browser.scroll_to("#footer")
browser.scroll_to(".comment-section")
```

### `press <key>`

Press keyboard key or combo. Supports standard keys and modifiers.

```python
browser.press("Enter")
browser.press("Escape")
browser.press("Control+a")  # select all
browser.press("ArrowDown")
```

### `hover <selector>`

Mouse over element (triggers menus, tooltips).

```python
browser.hover("#menu-trigger")
browser.hover(".tooltip-target")
```

### `drag <source> <target>`

HTML5-style drag from source to target.

```python
browser.drag("#draggable", "#dropzone")
browser.drag(".item", ".container")
```

### `double_click <selector>`

Double-click on element.

```python
browser.double_click(".file")
browser.double_click("#edit-icon")
```

### `right_click <selector>`

Right-click (context menu) on element.

```python
browser.right_click(".row")
browser.right_click("#custom-menu")
```

### `type_human <selector> <text> <delay_ms>`

Click element and type character by character with delay (human-like).

```python
browser.type_human("#email", "user@example.com", delay_ms=50)
browser.type_human("#search", "query", delay_ms=100)
```

### `clear <selector>`

Clear input field.

```python
browser.clear("#username")
browser.clear("input[name=search]")
```

### `wait_for <selector> <timeout_s>`

Wait for selector to appear; returns True if found, False on timeout.

```python
found = browser.wait_for("#loading-complete", timeout_s=10)
if found:
    browser.click("#proceed")
```

## Examples

```python
# Infinite scroll feed
for i in range(5):
    browser.scroll("down", 500)
    browser.wait(1)

# Keyboard navigation
browser.press("Tab")
browser.press("Enter")

# Drag and drop file upload
browser.drag("#file-item", "#upload-zone")

# Realistic form fill
browser.type_human("#name", "John Doe", delay_ms=80)
browser.press("Tab")
browser.type_human("#email", "john@example.com", delay_ms=80)
browser.press("Enter")

# Wait for dynamic content
if browser.wait_for(".results-loaded", timeout_s=15):
    browser.extract_text(".results")
```
