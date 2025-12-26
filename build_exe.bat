@echo off
echo ========================================
echo Building VideoDownloader.exe - Enhanced Edition
echo ========================================
echo.

REM Удаляем старые сборки
if exist "build" rmdir /S /Q "build"
if exist "dist" rmdir /S /Q "dist"

echo Cleaning old builds... Done
echo.

REM Устанавливаем зависимости
echo Installing dependencies...
python -m pip install -r requirements.txt
python -m pip install pyinstaller
echo.

echo Building with PyInstaller...
echo.

REM Собираем в ПАПКУ (более стабильно чем --onefile)
python -m PyInstaller --windowed ^
    --name "VideoDownloader" ^
    --add-data "themes.py;." ^
    --hidden-import=tkinterdnd2 ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    main.py

echo.
if exist "dist\VideoDownloader\VideoDownloader.exe" (
    echo ========================================
    echo Build successful!
    echo ========================================
    echo.
    echo EXE location: dist\VideoDownloader\VideoDownloader.exe
    echo.
    echo You can now run: dist\VideoDownloader\VideoDownloader.exe
    echo.
    echo NOTE: Распространяйте всю папку dist\VideoDownloader\
) else (
    echo ========================================
    echo Build failed!
    echo ========================================
    echo Please check the error messages above
)

pause
