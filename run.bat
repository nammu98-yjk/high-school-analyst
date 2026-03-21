@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   ANALYSIS SERVER STARTING... (PORT: 8295)
echo ============================================================
echo.

:: Clean up port 8295 if needed
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8295 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Run Server
set PYTHONUNBUFFERED=1
python run_server.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server failed to start.
    echo Please check if Python is installed.
    pause
)

pause
