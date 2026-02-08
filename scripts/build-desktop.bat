@echo off
REM Build script for Vibebells Desktop (Windows)

echo ========================================
echo Building Vibebells Desktop Application
echo ========================================

echo.
echo Step 1: Building Next.js frontend...
cd frontend
set BUILD_ELECTRON=true
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed
    exit /b 1
)

echo.
echo Step 2: Copying frontend build to desktop...
xcopy /E /I /Y out ..\desktop\build
if errorlevel 1 (
    echo ERROR: Failed to copy frontend build
    exit /b 1
)
cd ..

echo.
echo Step 3: Building Python backend (requires PyInstaller)...
cd backend

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip not found. Please install Python with pip.
    cd ..
    exit /b 1
)

REM Check and install PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        cd ..
        exit /b 1
    )
    echo PyInstaller installed successfully
)

REM Verify required packages are installed
echo Checking backend dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo ERROR: Flask not installed. Run: pip install -r requirements.txt
    cd ..
    exit /b 1
)

pip show mido >nul 2>&1
if errorlevel 1 (
    echo ERROR: mido not installed. Run: pip install -r requirements.txt
    cd ..
    exit /b 1
)

REM Create simple spec for PyInstaller
echo Creating PyInstaller executable...
pyinstaller --name=run --onefile --hidden-import=flask --hidden-import=flask_cors --hidden-import=mido --hidden-import=music21 --hidden-import=werkzeug.security --add-data "app;app" -c run.py
if errorlevel 1 (
    echo ERROR: Backend build failed
    cd ..
    exit /b 1
)

REM Verify output exists
if not exist "dist\run.exe" (
    echo ERROR: Backend executable not created
    cd ..
    exit /b 1
)

echo Backend built successfully: dist\run.exe
cd ..

echo.
echo Step 4: Ready to package with Electron Builder
echo Run: cd desktop ^&^& npm run build
echo.
echo ========================================
echo Build preparation complete!
echo ========================================
