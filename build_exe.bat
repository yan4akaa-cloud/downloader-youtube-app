@echo off
echo ================================================
echo Building standalone EXE file...
echo ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo Checking if PyInstaller is installed...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo Building executable...
echo This may take a few minutes...
echo.

python -m PyInstaller --onefile --windowed --name "VideoDownloader" main.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ================================================
echo Build completed successfully!
echo ================================================
echo.
echo Your executable file is located at:
echo dist\VideoDownloader.exe
echo.
echo NOTE: You still need FFmpeg installed on the target system!
echo.
pause
