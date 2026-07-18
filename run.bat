@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

rem ============================================================
rem  My Network Monitor launch script (Codecider Lab)
rem
rem  Usage:
rem    run.bat            Actual capture (auto-requests admin privileges, requires Npcap)
rem    run.bat --demo     Demo mode (check the UI without Npcap/privileges)
rem    run.bat --config config.toml   Specify a configuration file
rem ============================================================

rem --- Check whether demo mode is requested ---
set "DEMO=0"
for %%A in (%*) do (
    if /I "%%~A"=="--demo" set "DEMO=1"
)

rem --- Actual capture needs admin privileges -> elevate and relaunch ---
if "%DEMO%"=="0" (
    net session >nul 2>&1
    if errorlevel 1 (
        echo [info] Actual packet capture requires administrator privileges. Attempting to elevate...
        powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
        exit /b 0
    )
)

rem --- Check for Python ---
where python >nul 2>&1
if errorlevel 1 (
    echo [error] Python could not be found. Install Python 3.12 or later and add it to PATH.
    pause
    exit /b 1
)

rem --- First-time virtual environment setup ---
set "VENV_PY=.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo [setup] Creating the virtual environment ^(first time only, takes a few minutes^)...
    python -m venv .venv || goto :error
    "%VENV_PY%" -m pip install --upgrade pip
    "%VENV_PY%" -m pip install -r requirements.txt || goto :error
    echo [setup] Installation complete.
)

rem --- Run ---
echo [run] Launching My Network Monitor...
"%VENV_PY%" -m my_network_monitor.main %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [warn] The application exited with code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%

:error
echo.
echo [error] An error occurred during environment setup. Check the messages above.
pause
exit /b 1
