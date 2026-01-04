@echo off
title Textube - Remove from Startup

echo ========================================
echo    Textube - Remove from Startup
echo ========================================
echo.

set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Textube_Server.lnk"

if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo Removed from startup.
    echo.
    echo Auto-start is now disabled.
) else (
    echo Not registered in startup.
)

echo.
pause
