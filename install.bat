@echo off
title Textube - Complete Installation

echo ========================================
echo    Textube - YouTube Subtitle Extractor
echo    Complete Installation
echo ========================================
echo.

:: Check Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH"
    echo during installation.
    echo.
    pause
    exit /b 1
)
echo       Python found!
echo.

:: Install dependencies
echo [2/4] Installing dependencies...
pip install flask flask-cors youtube-transcript-api >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies.
    echo Please run manually:
    echo pip install flask flask-cors youtube-transcript-api
    echo.
    pause
    exit /b 1
)
echo       Dependencies installed!
echo.

:: Register to startup
echo [3/4] Registering auto-startup...
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_FILE=%~dp0start_hidden.vbs"
set "SHORTCUT=%STARTUP%\Textube_Server.lnk"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%VBS_FILE%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Textube Server Auto Start'; $s.Save()" >nul 2>&1

if errorlevel 1 (
    echo       Warning: Auto-startup registration failed.
    echo       You can run add_to_startup.bat later.
) else (
    echo       Auto-startup registered!
)
echo.

:: Start server now
echo [4/4] Starting server...
start "" "%~dp0start_hidden.vbs"
echo       Server started in background!
echo.

:: Open Chrome extensions page
echo [5/5] Opening Chrome extensions page...
start "" "chrome://extensions"
echo       Chrome opened!
echo.

:: Done
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo In the Chrome window that just opened:
echo.
echo   1. Enable "Developer mode" (top right toggle)
echo   2. Click "Load unpacked"
echo   3. Select this folder:
echo.
echo      %~dp0extension
echo.
echo The server will auto-start when Windows boots.
echo.
echo ========================================
pause
