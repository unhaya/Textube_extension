@echo off
title Textube - Add to Startup

echo ========================================
echo    Textube - Add to Startup
echo ========================================
echo.

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_FILE=%~dp0start_hidden.vbs"
set "SHORTCUT=%STARTUP%\Textube_Server.lnk"

echo Creating startup shortcut...
echo.

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%VBS_FILE%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Textube Server Auto Start'; $s.Save()"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create shortcut
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Registration Complete!
echo ========================================
echo.
echo Textube server will auto-start
echo when Windows starts (hidden).
echo.
echo To remove: run remove_from_startup.bat
echo.
pause
