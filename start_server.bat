@echo off
title Textube Server

echo ========================================
echo    Textube Local Server
echo ========================================
echo.

cd /d "%~dp0server"

echo Starting server...
echo.

python server.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Server failed to start
    echo ========================================
    echo.
    echo Make sure Python is installed and run:
    echo pip install flask flask-cors youtube-transcript-api
    echo.
    pause
)
