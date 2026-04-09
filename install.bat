@echo off
setlocal EnableDelayedExpansion
title AutoCAD MCP Installer

echo.
echo ============================================================
echo   AutoCAD MCP Installer
echo   Interior Design Tools for Claude Desktop
echo ============================================================
echo.

REM ── Figure out where this script lives ───────────────────────
set "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo [Step 1/6] Checking for Python 3.10+...
echo.

REM ── Check Python is installed ────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python was NOT found on your computer.
    echo.
    echo  Please install Python 3.11 from:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During install, tick the checkbox that says
    echo  "Add Python to PATH" before clicking Install.
    echo.
    echo  After installing Python, run this installer again.
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Found Python %PYVER%

REM ── Check minimum version ────────────────────────────────────
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if %PY_MAJOR% LSS 3 (
    echo  ERROR: Python 3.10 or higher is required. Please upgrade.
    pause
    exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
    echo  ERROR: Python 3.10 or higher is required. You have %PYVER%.
    echo  Download the latest Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  Python version OK.
echo.
echo [Step 2/6] Creating virtual environment...
echo.

REM ── Create venv ──────────────────────────────────────────────
if exist "%SCRIPT_DIR%\venv" (
    echo  Virtual environment already exists, skipping creation.
) else (
    python -m venv "%SCRIPT_DIR%\venv"
    if %errorlevel% neq 0 (
        echo  ERROR: Failed to create virtual environment.
        echo  Try running: python -m pip install --upgrade pip
        pause
        exit /b 1
    )
    echo  Virtual environment created.
)

echo.
echo [Step 3/6] Installing dependencies (mcp, pywin32)...
echo  This may take a minute...
echo.

REM ── Install packages ─────────────────────────────────────────
"%SCRIPT_DIR%\venv\Scripts\pip.exe" install --upgrade pip --quiet
"%SCRIPT_DIR%\venv\Scripts\pip.exe" install -r "%SCRIPT_DIR%\requirements.txt" --quiet

if %errorlevel% neq 0 (
    echo  ERROR: Package installation failed.
    echo  Check your internet connection and try again.
    pause
    exit /b 1
)
echo  Dependencies installed.

echo.
echo [Step 4/6] Running pywin32 post-install (required for AutoCAD COM)...
echo.

REM ── pywin32 post-install ─────────────────────────────────────
"%SCRIPT_DIR%\venv\Scripts\python.exe" "%SCRIPT_DIR%\venv\Scripts\pywin32_postinstall.py" -install >nul 2>&1
if %errorlevel% neq 0 (
    REM Try the Scripts\Lib location as fallback
    for /r "%SCRIPT_DIR%\venv" %%f in (pywin32_postinstall.py) do (
        "%SCRIPT_DIR%\venv\Scripts\python.exe" "%%f" -install >nul 2>&1
    )
)
echo  pywin32 COM registration complete.

echo.
echo [Step 5/6] Locating Claude Desktop config file...
echo.

REM ── Find Claude Desktop config ───────────────────────────────
set "CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json"
set "CLAUDE_CONFIG_DIR=%APPDATA%\Claude"

if not exist "%CLAUDE_CONFIG_DIR%" (
    echo  Creating Claude config folder...
    mkdir "%CLAUDE_CONFIG_DIR%"
)

REM Build the python path string (double backslashes for JSON)
set "PYTHON_PATH=%SCRIPT_DIR%\venv\Scripts\python.exe"
set "SERVER_PATH=%SCRIPT_DIR%\server.py"

REM Convert single backslashes to double for JSON
set "PYTHON_PATH_JSON=%PYTHON_PATH:\=\\%"
set "SERVER_PATH_JSON=%SERVER_PATH:\=\\%"

echo.
echo [Step 6/6] Writing Claude Desktop configuration...
echo.

REM ── Backup existing config if present ────────────────────────
if exist "%CLAUDE_CONFIG%" (
    echo  Found existing Claude config. Backing it up...
    copy "%CLAUDE_CONFIG%" "%CLAUDE_CONFIG%.backup" >nul
    echo  Backup saved to: %CLAUDE_CONFIG%.backup
    echo.
    echo  WARNING: This will add the AutoCAD MCP to your existing config.
    echo  If you have other MCPs configured, they will be preserved in the backup.
    echo  You may need to manually merge the files if needed.
    echo.
)

REM ── Write new config ─────────────────────────────────────────
(
echo {
echo   "mcpServers": {
echo     "autocad-id": {
echo       "command": "%PYTHON_PATH_JSON%",
echo       "args": ["%SERVER_PATH_JSON%"]
echo     }
echo   }
echo }
) > "%CLAUDE_CONFIG%"

echo  Config written to: %CLAUDE_CONFIG%

echo.
echo ============================================================
echo   INSTALLATION COMPLETE!
echo ============================================================
echo.
echo   What to do next:
echo.
echo   1. Make sure AutoCAD is running (open any drawing)
echo.
echo   2. RESTART Claude Desktop completely:
echo      - Right-click the Claude icon in the system tray
echo      - Click "Quit" or "Exit"
echo      - Open Claude Desktop again from the Start menu
echo.
echo   3. In Claude Desktop, look for the hammer icon (tools)
echo      in the chat box — it should show AutoCAD tools.
echo.
echo   4. Try saying: "Set up AIA standard layers for a new
echo      interior design project"
echo.
echo   If it doesn't work, see SETUP.md for troubleshooting.
echo.
echo ============================================================
echo.
pause
