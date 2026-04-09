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
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM ════════════════════════════════════════════════════════════
REM  STEP 0 — Request admin elevation (needed for Chocolatey
REM           and pywin32 COM registration)
REM ════════════════════════════════════════════════════════════
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  This installer needs administrator rights for two things:
    echo    - Installing Python via Chocolatey (if Python is missing)
    echo    - Registering the AutoCAD COM bridge (pywin32)
    echo.
    echo  A UAC prompt will appear. Click "Yes" to continue.
    echo.
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs -ArgumentList 'ELEVATED'"
    exit /b
)

REM ════════════════════════════════════════════════════════════
REM  STEP 1 — Python check → auto-install via Chocolatey
REM ════════════════════════════════════════════════════════════
echo [Step 1/6] Checking for Python 3.10+...
echo.

python --version >nul 2>&1
set PYTHON_FOUND=%errorlevel%

if %PYTHON_FOUND% equ 0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
    echo  Found Python !PYVER!
    goto :check_version
)

REM ── Python not found — install via Chocolatey ────────────────
echo  Python not found. Installing automatically via Chocolatey...
echo.

REM Check if Chocolatey is already installed
choco --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [1a] Chocolatey not found. Installing Chocolatey...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072; ^
         iex ((New-Object Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if !errorlevel! neq 0 (
        echo.
        echo  ERROR: Chocolatey installation failed.
        echo  Please install Python manually from: https://www.python.org/downloads/
        echo  Tick "Add Python to PATH" during install, then run this script again.
        pause
        exit /b 1
    )
    REM Refresh environment so choco is on PATH immediately
    call "%ALLUSERSPROFILE%\chocolatey\bin\refreshenv.cmd" >nul 2>&1
    set "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
    echo.
    echo  Chocolatey installed successfully.
    echo.
)

echo  [1b] Installing Python 3.11 via Chocolatey...
echo  (This downloads ~25 MB and may take a minute or two)
echo.
choco install python311 --version=3.11.9 -y --no-progress
if !errorlevel! neq 0 (
    REM Fallback: try generic python package
    choco install python -y --no-progress
    if !errorlevel! neq 0 (
        echo.
        echo  ERROR: Python installation via Chocolatey failed.
        echo  Please install Python manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM Refresh PATH so the newly installed Python is visible
call "%ALLUSERSPROFILE%\chocolatey\bin\refreshenv.cmd" >nul 2>&1
set "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin;C:\Python311;C:\Python311\Scripts;C:\Python3\;C:\Python3\Scripts"
REM Also check the standard choco install location
for /d %%d in ("C:\Python31*") do set "PATH=!PATH!;%%d;%%d\Scripts"

python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo  Python was installed but is not yet on PATH.
    echo  Please CLOSE this window and re-open it as Administrator,
    echo  then run install.bat again. (PATH refresh requires a new shell.)
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python !PYVER! installed and ready.

:check_version
REM ── Verify minimum version ───────────────────────────────────
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if !PY_MAJOR! LSS 3 (
    echo  ERROR: Python 3.10+ required. Found !PYVER!. Run: choco upgrade python -y
    pause & exit /b 1
)
if !PY_MAJOR! EQU 3 if !PY_MINOR! LSS 10 (
    echo  ERROR: Python 3.10+ required. Found !PYVER!.
    echo  Run:  choco install python311 -y
    pause & exit /b 1
)
echo  Python version OK.

REM ════════════════════════════════════════════════════════════
REM  STEP 2 — Create virtual environment
REM ════════════════════════════════════════════════════════════
echo.
echo [Step 2/6] Creating virtual environment...
echo.

if exist "%SCRIPT_DIR%\venv" (
    echo  Virtual environment already exists — skipping.
) else (
    python -m venv "%SCRIPT_DIR%\venv"
    if !errorlevel! neq 0 (
        echo  ERROR: Could not create venv. Try: python -m pip install --upgrade pip
        pause & exit /b 1
    )
    echo  Virtual environment created.
)

REM ════════════════════════════════════════════════════════════
REM  STEP 3 — Install Python packages
REM ════════════════════════════════════════════════════════════
echo.
echo [Step 3/6] Installing packages (mcp, pywin32)...
echo  This may take a minute...
echo.

"%SCRIPT_DIR%\venv\Scripts\pip.exe" install --upgrade pip --quiet
"%SCRIPT_DIR%\venv\Scripts\pip.exe" install -r "%SCRIPT_DIR%\requirements.txt"

if !errorlevel! neq 0 (
    echo.
    echo  ERROR: Package installation failed. Check internet and try again.
    pause & exit /b 1
)
echo  Packages installed.

REM ════════════════════════════════════════════════════════════
REM  STEP 4 — pywin32 COM registration
REM ════════════════════════════════════════════════════════════
echo.
echo [Step 4/6] Registering AutoCAD COM bridge (pywin32)...
echo.

set PYWIN32_SCRIPT=
for /r "%SCRIPT_DIR%\venv" %%f in (pywin32_postinstall.py) do (
    if not defined PYWIN32_SCRIPT set "PYWIN32_SCRIPT=%%f"
)

if defined PYWIN32_SCRIPT (
    "%SCRIPT_DIR%\venv\Scripts\python.exe" "%PYWIN32_SCRIPT%" -install
    echo  COM registration complete.
) else (
    echo  WARNING: pywin32_postinstall.py not found.
    echo  AutoCAD connection may not work. Try reinstalling with:
    echo    %SCRIPT_DIR%\venv\Scripts\pip.exe install pywin32 --force-reinstall
)

REM ════════════════════════════════════════════════════════════
REM  STEP 5 — Find Claude Desktop config (try all known paths)
REM ════════════════════════════════════════════════════════════
echo.
echo [Step 5/6] Locating Claude Desktop configuration...
echo.

set "CLAUDE_CONFIG="

REM ── Try every known location ─────────────────────────────────
set "CANDIDATE_1=%APPDATA%\Claude\claude_desktop_config.json"
set "CANDIDATE_2=%LOCALAPPDATA%\Claude\claude_desktop_config.json"
set "CANDIDATE_3=%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json"
set "CANDIDATE_4=%USERPROFILE%\AppData\Local\Claude\claude_desktop_config.json"
set "CANDIDATE_5=%APPDATA%\AnthropicClaude\claude_desktop_config.json"
set "CANDIDATE_6=%LOCALAPPDATA%\AnthropicClaude\claude_desktop_config.json"

for %%C in (
    "%CANDIDATE_1%"
    "%CANDIDATE_2%"
    "%CANDIDATE_3%"
    "%CANDIDATE_4%"
    "%CANDIDATE_5%"
    "%CANDIDATE_6%"
) do (
    if exist %%C (
        if not defined CLAUDE_CONFIG (
            set "CLAUDE_CONFIG=%%~C"
            echo  Found existing config at: %%~C
        )
    )
)

REM ── If config not found, search for the Claude folder anywhere ─
if not defined CLAUDE_CONFIG (
    echo  Config not found at standard paths. Searching...
    for /d %%d in (
        "%APPDATA%\*"
        "%LOCALAPPDATA%\*"
        "%USERPROFILE%\AppData\Roaming\*"
        "%USERPROFILE%\AppData\Local\*"
    ) do (
        if /i "%%~nxd"=="Claude" (
            if not defined CLAUDE_CONFIG (
                set "CLAUDE_CONFIG=%%~fd\claude_desktop_config.json"
                echo  Found Claude folder at: %%~fd
            )
        )
        if /i "%%~nxd"=="AnthropicClaude" (
            if not defined CLAUDE_CONFIG (
                set "CLAUDE_CONFIG=%%~fd\claude_desktop_config.json"
                echo  Found Claude folder at: %%~fd
            )
        )
    )
)

REM ── Still not found — ask the user to paste the path ─────────
if not defined CLAUDE_CONFIG (
    echo.
    echo  ┌─────────────────────────────────────────────────────┐
    echo  │  Could not find Claude Desktop config automatically.  │
    echo  │                                                       │
    echo  │  To find it:                                          │
    echo  │  1. Open Claude Desktop                               │
    echo  │  2. Click the menu (top-left) → Settings             │
    echo  │  3. Look for "Configuration file" path               │
    echo  │                                                       │
    echo  │  OR: Open Windows Explorer, paste this in the bar:   │
    echo  │      %%APPDATA%%                                         │
    echo  │  and look for a "Claude" or "AnthropicClaude" folder. │
    echo  └─────────────────────────────────────────────────────┘
    echo.
    set /p "USER_PATH=Paste the full path to your Claude config folder here: "
    REM Strip surrounding quotes if user pasted them
    set "USER_PATH=!USER_PATH:"=!"
    REM Strip trailing backslash
    if "!USER_PATH:~-1!"=="\" set "USER_PATH=!USER_PATH:~0,-1!"

    if exist "!USER_PATH!" (
        REM User gave the folder path
        set "CLAUDE_CONFIG=!USER_PATH!\claude_desktop_config.json"
        echo  Using: !CLAUDE_CONFIG!
    ) else if exist "!USER_PATH!\claude_desktop_config.json" (
        set "CLAUDE_CONFIG=!USER_PATH!\claude_desktop_config.json"
        echo  Using: !CLAUDE_CONFIG!
    ) else (
        REM Create it fresh at the path they gave
        echo  Folder not found — creating it at: !USER_PATH!
        mkdir "!USER_PATH!" >nul 2>&1
        set "CLAUDE_CONFIG=!USER_PATH!\claude_desktop_config.json"
    )
)

REM ── Ensure the config directory exists ───────────────────────
for %%F in ("!CLAUDE_CONFIG!") do set "CLAUDE_CONFIG_DIR=%%~dpF"
if not exist "!CLAUDE_CONFIG_DIR!" (
    echo  Creating config directory: !CLAUDE_CONFIG_DIR!
    mkdir "!CLAUDE_CONFIG_DIR!"
)

REM ════════════════════════════════════════════════════════════
REM  STEP 6 — Write Claude Desktop config
REM ════════════════════════════════════════════════════════════
echo.
echo [Step 6/6] Writing Claude Desktop configuration...
echo.

REM Build paths with double backslashes for JSON
set "PYTHON_PATH=%SCRIPT_DIR%\venv\Scripts\python.exe"
set "SERVER_PATH=%SCRIPT_DIR%\server.py"
set "PYTHON_PATH_JSON=%PYTHON_PATH:\=\\%"
set "SERVER_PATH_JSON=%SERVER_PATH:\=\\%"

REM Backup existing config
if exist "!CLAUDE_CONFIG!" (
    echo  Backing up existing config...
    copy "!CLAUDE_CONFIG!" "!CLAUDE_CONFIG!.backup" >nul
    echo  Backup saved: !CLAUDE_CONFIG!.backup
    echo.
    echo  NOTE: Your existing config has been replaced.
    echo  If you had other MCPs, copy them from the .backup file.
    echo.
)

REM Write new config
(
echo {
echo   "mcpServers": {
echo     "autocad-id": {
echo       "command": "%PYTHON_PATH_JSON%",
echo       "args": ["%SERVER_PATH_JSON%"]
echo     }
echo   }
echo }
) > "!CLAUDE_CONFIG!"

echo  Config written to: !CLAUDE_CONFIG!

REM ════════════════════════════════════════════════════════════
REM  DONE
REM ════════════════════════════════════════════════════════════
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
echo      - Open Claude Desktop again from Start menu
echo.
echo   3. Look for the hammer icon in the Claude chat box
echo      — it should show "autocad-id" tools.
echo.
echo   4. First prompt to try:
echo      "Set up AIA standard layers for a new interior design project"
echo.
echo   Config location: !CLAUDE_CONFIG!
echo.
echo   If something doesn't work, see SETUP.md for help.
echo ============================================================
echo.
pause
