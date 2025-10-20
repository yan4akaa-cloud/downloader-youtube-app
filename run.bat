@echo off
echo Starting YouTube ^& Pinterest Video Downloader...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please run install.bat first.
    pause
    exit /b 1
)

python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start!
    echo Make sure all dependencies are installed.
    echo Run install.bat if you haven't already.
    pause
    exit /b 1
)

