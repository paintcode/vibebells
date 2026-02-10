# Phase 8.3: Backend Bundling with PyInstaller
**Date**: 2026-02-09  
**Status**: In Progress

---

## Overview

Bundle the Python Flask backend into a standalone executable that can be distributed with the Electron app. This eliminates the need for users to have Python installed.

---

## Goals

1. Create standalone backend executable (no Python installation required)
2. Include all dependencies (Flask, mido, music21, numpy)
3. Optimize bundle size
4. Test backend runs independently
5. Integrate with Electron main process

---

## Implementation Steps

### Step 1: Install PyInstaller ✅

```bash
cd backend
pip install pyinstaller
```

**Verify installation**:
```bash
pyinstaller --version
```

---

### Step 2: Create PyInstaller Spec File

Create `backend/run.spec` with:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),  # Include app directory
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'mido',
        'music21',
        'numpy',
        'werkzeug',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',  # Not needed
        'matplotlib',  # Not needed
        'scipy',  # Not needed unless music21 needs it
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='vibebells-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for logging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../desktop/assets/icon.ico'  # Optional
)
```

**Key Settings**:
- `datas`: Include `app/` directory with all services
- `hiddenimports`: Explicitly include all dependencies
- `excludes`: Remove unused packages to reduce size
- `upx=True`: Enable compression
- `console=True`: Show console for debugging (can disable later)

---

### Step 3: Test PyInstaller Build

```bash
cd backend
pyinstaller run.spec
```

**Expected Output**:
```
Building EXE from EXE-00.toc completed successfully.
```

**Result**:
- `backend/dist/vibebells-backend.exe` (Windows)
- `backend/dist/vibebells-backend` (macOS/Linux)

**Test Standalone**:
```bash
cd backend/dist
./vibebells-backend
```

Should see:
```
 * Running on http://127.0.0.1:5000
```

Test endpoint:
```bash
curl http://localhost:5000/api/health
# Should return: {"status":"healthy"}
```

---

### Step 4: Optimize Bundle Size

**Check Initial Size**:
```bash
du -h backend/dist/vibebells-backend.exe
# Expected: 100-200 MB (music21 is large)
```

**Optimization Strategies**:

1. **Exclude Unnecessary Packages**:
   - music21 includes large corpus files
   - Add to spec: `excludes=['music21.corpus']`

2. **Use `--onefile` for single executable**:
   - Already configured in spec

3. **Enable UPX Compression**:
   - Already enabled: `upx=True`

4. **Remove Debug Info**:
   - Set `debug=False`, `strip=True` (Linux/macOS)

**Updated spec with optimizations**:
```python
excludes=[
    'tkinter',
    'matplotlib',
    'scipy',
    'music21.corpus',  # Large corpus files not needed
    'music21.documentation',
    'IPython',
    'jupyter',
],
```

---

### Step 5: Integrate with Electron

The Electron main.js is already configured to use bundled backend.

**Verify main.js logic** (lines 43-166):
```javascript
function startBackend() {
  const isDev = !app.isPackaged;
  
  if (isDev) {
    // Development: Python from system
    pythonProcess = spawn('python', ['-m', 'flask', 'run'], {
      cwd: backendPath,
      env: { ...process.env, FLASK_APP: 'run.py' }
    });
  } else {
    // Production: Bundled executable
    const exeName = process.platform === 'win32' 
      ? 'vibebells-backend.exe' 
      : 'vibebells-backend';
    const backendExe = path.join(process.resourcesPath, 'backend', exeName);
    
    pythonProcess = spawn(backendExe, [], {
      env: { ...process.env }
    });
  }
  
  // Health check logic...
}
```

**Update Electron package.json** to copy bundled backend:
```json
"build": {
  "extraResources": [
    {
      "from": "../backend/dist/",
      "to": "backend",
      "filter": ["**/*"]
    }
  ]
}
```

---

### Step 6: Update Build Script

Update `scripts/build-desktop.bat`:

```batch
@echo off
echo ============================================
echo Building Vibebells Desktop Application
echo ============================================

echo.
echo [1/4] Building Python Backend...
cd backend
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Python virtual environment not found
    exit /b 1
)

call venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller run.spec --clean

if not exist "dist\vibebells-backend.exe" (
    echo ERROR: Backend build failed
    exit /b 1
)
echo ✓ Backend bundled: dist\vibebells-backend.exe

echo.
echo [2/4] Building Next.js Frontend...
cd ..\frontend
set BUILD_ELECTRON=true
call npm run build

if not exist "out\index.html" (
    echo ERROR: Frontend build failed
    exit /b 1
)
echo ✓ Frontend built: out\

echo.
echo [3/4] Copying to Desktop App...
cd ..\desktop
if not exist "build" mkdir build
xcopy /E /I /Y ..\frontend\out build
echo ✓ Frontend copied to desktop\build\

echo.
echo [4/4] Building Electron App...
call npm run build:win

if not exist "dist\*.exe" (
    echo ERROR: Electron build failed
    exit /b 1
)
echo ✓ Electron app built: desktop\dist\

echo.
echo ============================================
echo Build Complete! 🎉
echo ============================================
echo.
echo Installer: desktop\dist\vibebells-setup.exe
echo Portable: desktop\dist\vibebells-portable.exe
echo.
```

---

## Testing Checklist

### Local Backend Test
- [ ] Backend builds successfully with PyInstaller
- [ ] Executable runs without Python installed
- [ ] Health endpoint responds: http://localhost:5000/api/health
- [ ] File upload works
- [ ] Arrangement generation works
- [ ] CSV export works
- [ ] No import errors in logs
- [ ] Check executable size (target: <150 MB)

### Electron Integration Test
- [ ] Dev mode: spawns Python from system
- [ ] Dev mode: backend starts successfully
- [ ] Dev mode: frontend connects to backend
- [ ] Production mode: spawns bundled executable
- [ ] Production mode: backend starts from bundle
- [ ] Production mode: health checks pass
- [ ] Production mode: all features work
- [ ] Logs show no errors

### Cross-Platform Test (if applicable)
- [ ] Windows: .exe runs
- [ ] macOS: Unix binary runs
- [ ] Linux: Unix binary runs

---

## Common Issues & Solutions

### Issue 1: ModuleNotFoundError

**Symptom**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Add to spec file:
```python
datas=[('app', 'app')],
```

---

### Issue 2: music21 Missing Files

**Symptom**: music21 crashes with missing corpus files

**Solution**: Either:
1. Include corpus: `datas=[('venv/Lib/site-packages/music21/corpus', 'music21/corpus')]`
2. Or exclude corpus and test if MusicXML still works without it

---

### Issue 3: Large Bundle Size (>300 MB)

**Solution**: Exclude heavy packages:
```python
excludes=[
    'music21.corpus',
    'music21.documentation',
    'matplotlib',
    'scipy',
    'tkinter',
]
```

---

### Issue 4: Flask Not Finding Templates/Static

**Symptom**: 404 errors for static files

**Solution**: Backend doesn't serve static files (frontend does), so this shouldn't occur

---

### Issue 5: Permission Denied (Linux/macOS)

**Symptom**: Can't execute bundled binary

**Solution**:
```bash
chmod +x backend/dist/vibebells-backend
```

---

## Expected Results

### Bundle Size Targets

| Platform | Size | Acceptable |
|----------|------|------------|
| Windows | 100-150 MB | ✅ |
| macOS | 80-120 MB | ✅ |
| Linux | 80-120 MB | ✅ |

### Performance

- **Startup Time**: <5 seconds
- **First Request**: <1 second
- **Memory Usage**: 50-100 MB

---

## Directory Structure After Build

```
vibebells/
├── backend/
│   ├── run.spec                     # NEW - PyInstaller spec
│   ├── dist/
│   │   └── vibebells-backend.exe    # NEW - Bundled executable
│   └── build/                       # NEW - Build artifacts (can delete)
├── desktop/
│   ├── dist/
│   │   ├── vibebells-setup.exe      # FINAL - Windows installer
│   │   └── vibebells-portable.exe   # FINAL - Portable app
│   └── build/
│       └── index.html               # Frontend static files
└── scripts/
    └── build-desktop.bat            # UPDATED - Full build process
```

---

## Success Criteria

✅ Backend builds with PyInstaller  
✅ Executable runs without Python installed  
✅ All API endpoints work  
✅ Bundle size <150 MB  
✅ Electron spawns backend successfully  
✅ Health checks pass  
✅ End-to-end workflow works (upload → generate → export)

---

## Next Steps After Phase 8.3

**Phase 8.4**: Production Build
- Build Next.js static export
- Package with Electron Builder
- Create installers for Windows
- Test on clean Windows machine

**Phase 8.5**: Icons & Branding (Optional)
- Create icon.ico, icon.png
- Generate platform-specific formats
- Update package.json with icon paths

---

## Status: Ready to Start

**Current Step**: Install PyInstaller and create spec file

**Estimated Time**: 30-60 minutes
