@echo off
REM Build script for Vibebells Desktop (Windows)

echo ============================================
echo Building Vibebells Desktop Application
echo ============================================

echo.
echo [1/4] Building Python Backend...
cd backend

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Python virtual environment not found at backend\venv\
    echo Please run: cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    cd ..
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        cd ..
        exit /b 1
    )
)

REM Build with spec file
echo Building backend with PyInstaller...
pyinstaller run.spec --clean
if errorlevel 1 (
    echo ERROR: Backend build failed
    cd ..
    exit /b 1
)

REM Verify output
if not exist "dist\vibebells-backend.exe" (
    echo ERROR: Backend executable not created
    cd ..
    exit /b 1
)

echo ✓ Backend bundled: dist\vibebells-backend.exe
for %%F in (dist\vibebells-backend.exe) do echo    Size: %%~zF bytes
cd ..

echo.
echo [2/4] Building Next.js Frontend...
cd frontend
set BUILD_ELECTRON=true
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed
    cd ..
    exit /b 1
)

if not exist "out\index.html" (
    echo ERROR: Frontend build output not found
    cd ..
    exit /b 1
)

echo ✓ Frontend built: out\
cd ..

echo.
echo [3/4] Copying to Desktop App...
cd desktop
if not exist "build" mkdir build
xcopy /E /I /Y ..\frontend\out build
if errorlevel 1 (
    echo ERROR: Failed to copy frontend build
    cd ..
    exit /b 1
)
echo ✓ Frontend copied to desktop\build\

echo.
echo [4/4] Building Electron App...
call npm run build:win
if errorlevel 1 (
    echo ERROR: Electron build failed
    cd ..
    exit /b 1
)

REM Verify Electron output
if not exist "dist\*.exe" (
    echo ERROR: Electron installer not created
    cd ..
    exit /b 1
)

echo ✓ Electron app built: desktop\dist\
cd ..

echo.
echo ============================================
echo Build Complete! 🎉
echo ============================================
echo.
echo Outputs:
for %%F in (desktop\dist\*.exe) do echo   - %%~nxF (%%~zF bytes)
echo.
echo To test: Run the installer or portable EXE from desktop\dist\
echo.
