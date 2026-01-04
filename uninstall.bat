@echo off
title Textube - Uninstall

echo ========================================
echo    Textube - Uninstall
echo ========================================
echo.

:: Remove from startup
echo [1/2] Removing auto-startup...
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Textube_Server.lnk"

if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo       Auto-startup removed.
) else (
    echo       Not registered in startup.
)
echo.

:: Stop running server
echo [2/2] Stopping server...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Textube*" >nul 2>&1
echo       Server stopped (if running).
echo.

:: Done
echo ========================================
echo    Uninstall Complete
echo ========================================
echo.
echo What was removed:
echo   - Auto-startup registration
echo   - Running server process
echo.
echo What remains (delete manually if needed):
echo   - This folder and all files
echo   - Python libraries (flask, etc.)
echo   - Chrome extension (remove from chrome://extensions)
echo.
echo ========================================
pause
