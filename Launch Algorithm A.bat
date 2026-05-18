@echo off
:: Launch the Algorithm A web app in your default browser.
:: Double-click this file to start — no command line knowledge needed.

setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Prefer the project's own virtual environment
set "STREAMLIT=%SCRIPT_DIR%.venv\Scripts\streamlit.exe"

if not exist "%STREAMLIT%" (
    :: Fall back to streamlit on PATH (Anaconda, global install, etc.)
    where streamlit >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo  ERROR: streamlit not found.
        echo.
        echo  Please set up the project environment first:
        echo.
        echo    python -m venv .venv
        echo    .venv\Scripts\activate
        echo    pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    set "STREAMLIT=streamlit"
)

echo.
echo  Starting Algorithm A web app ...
echo  Open your browser at:  http://localhost:8501
echo  Press Ctrl+C to stop.
echo.
"%STREAMLIT%" run app.py
pause
