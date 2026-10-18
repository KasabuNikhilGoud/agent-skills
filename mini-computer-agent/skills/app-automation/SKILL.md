---
name: app-automation
description: Automate common desktop application workflows
when: document, spreadsheet, presentation, email, office
---

# Application Automation

## Steps
1. Use list_apps to see available applications
2. Use open_app to launch the target application
3. Wait for window to appear (check with see_windows)
4. Use focus_window to activate the application
5. Use type_text to enter content
6. Use press for keyboard shortcuts (Ctrl+S to save, etc.)
7. Use click for menu items and buttons
8. Use close_window when done

## Common Apps
- LibreOffice Calc: `libreoffice --calc`
- LibreOffice Writer: `libreoffice --writer`
- LibreOffice Impress: `libreoffice --impress`
- File Manager: `pcmanfm`
- Text Editor: `gedit` or `mousepad`

## Keyboard Shortcuts
- Ctrl+S: Save
- Ctrl+C: Copy
- Ctrl+V: Paste
- Ctrl+O: Open
- Ctrl+N: New
- Ctrl+Q: Quit
