@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or newer from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

if not exist "%LocalAppData%\SOVRIVA\dependencies.ok" (
  echo Installing SOVRIVA Python dependencies...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
  )
  if not exist "%LocalAppData%\SOVRIVA" mkdir "%LocalAppData%\SOVRIVA"
  type nul > "%LocalAppData%\SOVRIVA\dependencies.ok"
)

echo SOVRIVA is starting at http://127.0.0.1:8765
start "SOVRIVA local server" cmd /k "cd /d "%~dp0" && python run.py"
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8765
pause
