@echo off
title Textube Setup

echo ========================================
echo    Textube - Setup
echo ========================================
echo.

echo Installing required packages...
echo.

pip install flask flask-cors youtube-transcript-api

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed.
    echo Make sure Python is installed.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run start_server.bat
echo 2. Load extension folder in Chrome
echo    (chrome://extensions -> Load unpacked)
echo 3. Open YouTube and extract subtitles!
echo.
pause
