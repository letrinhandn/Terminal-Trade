@echo off
REM Terminal Trade Launcher for Windows
REM Double-click this file to start Terminal Trade

echo Starting Terminal Trade...
echo.

REM Try different Python installations
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run_app.py
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        python3 run_app.py
    ) else (
        where py >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            py run_app.py
        ) else (
            echo ERROR: Python not found!
            echo Please install Python 3.11+ and add it to PATH
            echo Or run: python run_app.py manually
            pause
        )
    )
)

REM Keep window open if there was an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo App exited with error code %ERRORLEVEL%
    pause
)