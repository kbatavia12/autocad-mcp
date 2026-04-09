# AutoCAD MCP — Setup Guide
### No Python knowledge required · Windows Only · ~5 minutes

---

## What this does

This package adds **AutoCAD control to Claude Desktop**. Once set up, you can type natural-language prompts like *"draw a 4800×3600mm bedroom with a king bed, wardrobe, and all AIA layers"* and Claude will draw it directly in your open AutoCAD drawing.

**Requirements:**
- Windows 10 or 11
- AutoCAD 2016 or later (any version — LT is **not** supported, it lacks COM automation)
- [Claude Desktop](https://claude.ai/download) installed and logged in
- Internet connection for the first install only

---

## Step 1 — Download the project

If you're reading this, you probably already have the folder. If not:

1. Go to **https://github.com/kbatavia12/autocad-mcp**
2. Click the green **Code** button → **Download ZIP**
3. Unzip it anywhere (e.g. `C:\Users\YourName\autocad-mcp`)

> **Tip:** Don't put it in a folder with spaces in the path (e.g. avoid `C:\My Projects\autocad-mcp`). Use `C:\autocad-mcp` or `C:\Users\YourName\Documents\autocad-mcp` instead.

---

## Step 2 — Install Python (if you don't have it)

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **Download Python 3.11.x** button
3. Run the installer
4. **CRITICAL:** On the first screen, tick ✅ **"Add Python to PATH"** before clicking Install

> You can check if Python is already installed by opening the Start menu, typing `cmd`, and running `python --version`. If you see a version number like `Python 3.11.5`, you're good.

---

## Step 3 — Run the installer

1. Open the `autocad-mcp` folder
2. Double-click **`install.bat`**
3. If Windows shows a blue "Windows protected your PC" warning, click **More info → Run anyway** (this is normal for scripts not signed by a corporation)
4. The installer will:
   - Create a private Python environment
   - Download and install all required packages
   - Register the COM bridge for AutoCAD
   - Write the Claude Desktop configuration file
5. Read the on-screen messages — it will tell you if anything goes wrong

The whole process takes about 1–2 minutes.

---

## Step 4 — Restart Claude Desktop

The config change only takes effect after a full restart:

1. Find the **Claude icon in your Windows taskbar** (bottom-right, near the clock)
2. Right-click it → **Quit** (or Exit)
3. Open **Claude Desktop** again from the Start menu

---

## Step 5 — Verify it's working

1. **Open AutoCAD** and have a drawing open (even a blank one)
2. In Claude Desktop, click the **⊕ (plus)** or **🔨 (hammer)** icon in the chat input box
3. You should see **"autocad-id"** listed as a tool server with all the tools

Try this first prompt:
> *"Set up AIA standard layers for a new interior design project"*

Claude should respond and you should see 23 new layers appear in AutoCAD.

---

## Troubleshooting

### "Tools not showing up in Claude"

**Most likely cause:** Claude Desktop wasn't fully quit and restarted.

- Open **Task Manager** (Ctrl+Shift+Esc)
- Find any `Claude.exe` processes and end them all
- Open Claude Desktop fresh from the Start menu

---

### "Error connecting to AutoCAD"

AutoCAD must be **open and running** before you ask Claude to draw anything. Claude connects to the already-running AutoCAD — it cannot open AutoCAD itself.

- Open AutoCAD
- Open or create a drawing (even `File → New`)
- Then ask Claude

---

### "AutoCAD LT" users

AutoCAD LT **does not support COM automation** and cannot work with this MCP. You need the full AutoCAD product. This MCP is tested with AutoCAD 2019–2024.

---

### The installer shows an error about pywin32

Run this manually:
1. Open the Start menu and type `cmd`
2. Right-click **Command Prompt** → **Run as Administrator**
3. Paste this (change the path to match where you put the folder):
   ```
   C:\autocad-mcp\venv\Scripts\python.exe C:\autocad-mcp\venv\Scripts\pywin32_postinstall.py -install
   ```
4. Restart Claude Desktop

---

### I already have other MCPs configured

The installer backs up your existing `claude_desktop_config.json` before writing a new one. Find the backup at:
```
C:\Users\YourName\AppData\Roaming\Claude\claude_desktop_config.json.backup
```

To add the AutoCAD MCP alongside your existing MCPs, open the config file in Notepad and manually add the `"autocad-id"` section inside the existing `"mcpServers": { }` block. The file is standard JSON format.

---

### Finding the config file manually

The Claude Desktop config lives at:
```
C:\Users\YourName\AppData\Roaming\Claude\claude_desktop_config.json
```

To get there: press `Win + R`, type `%APPDATA%\Claude`, press Enter.

The file should look like this after the installer runs:
```json
{
  "mcpServers": {
    "autocad-id": {
      "command": "C:\\autocad-mcp\\venv\\Scripts\\python.exe",
      "args": ["C:\\autocad-mcp\\server.py"]
    }
  }
}
```

---

## Quick-start prompts to try

Once everything is working, here are some great first prompts:

```
Set up AIA standard layers for a new interior design project
```
```
Draw a 4800×3600mm bedroom with 150mm walls at coordinates (0,0)
```
```
Place a king-size bed centred against the north wall of the bedroom
```
```
Draw a complete kitchen layout — galley style, 3600mm long
```
```
Create a tile grid with 600×600mm tiles across the floor,
centred, with 3mm grout joints
```
```
Draw the elevation height standards for the kitchen wall —
show all ergonomic reference lines
```
```
Set up a 1:50 orthographic layout with plan, front, and side views
```
```
Create a full room schedule table for the apartment layout
```

---

## Updating to the latest version

1. Download the latest ZIP from GitHub (same link as Step 1)
2. Replace all files in the folder **except** for the `venv` folder (you can keep your existing environment)
3. Restart Claude Desktop

Or if you're familiar with Git:
```
cd C:\autocad-mcp
git pull origin main
```

---

## Uninstalling

1. Delete the `autocad-mcp` folder
2. Open `%APPDATA%\Claude\claude_desktop_config.json` in Notepad
3. Remove the `"autocad-id"` section
4. Restart Claude Desktop

---

*226 tools · 19 modules · Tailored for Interior Design workflows*
*Built for B.Des (Interior Design) curriculum, Savitribai Phule Pune University 2025 Pattern*
