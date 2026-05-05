@echo off
title Textube - Restart Server

:: ポート5000を使っているPIDを取得してkill
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000 "') do (
    taskkill /PID %%p /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

:: 非表示で再起動
start "" "%~dp0start_hidden.vbs"

echo Server restarted.
timeout /t 2 /nobreak >nul
