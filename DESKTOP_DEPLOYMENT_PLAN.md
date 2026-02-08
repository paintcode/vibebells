# Desktop Application Deployment Plan
## Handbell Arrangement Generator

---

## Current Architecture

**Frontend**: Next.js 15 (App Router) + React 19  
**Backend**: Flask (Python) + mido, music21  
**Communication**: REST API (HTTP)  
**Current Deployment**: Separate dev servers (localhost:3000 + localhost:5000)

---

## Technology Options Analysis

### Option 1: Electron + Python Backend ⭐ **RECOMMENDED**

**Architecture**: Electron app bundles Next.js build + spawns Python subprocess

**Pros**:
- ✅ **Cross-platform** (Windows, macOS, Linux)
- ✅ **Mature ecosystem** with excellent documentation
- ✅ **Well-established** Python integration patterns
- ✅ **Large community** and support resources
- ✅ **Auto-updates** built-in (electron-updater)
- ✅ **Code signing** tools available for all platforms
- ✅ **Native file dialogs** for MIDI/CSV file handling
- ✅ Can bundle Python runtime with PyInstaller/cx_Freeze

**Cons**:
- ❌ **Large bundle size** (~150-200MB with Python)
- ❌ **Memory usage** (Chromium + Python backend)
- ❌ **Startup time** slightly slower
- ❌ **License considerations** (Electron is MIT, but Chromium has restrictions)

**Best for**: Production-ready cross-platform desktop app with professional features

---

### Option 2: Tauri + Python Backend 🚀 **MODERN ALTERNATIVE**

**Architecture**: Rust-based desktop shell + system webview + Python subprocess

**Pros**:
- ✅ **Tiny bundle size** (~10-20MB smaller than Electron)
- ✅ **Fast startup** and low memory usage
- ✅ **Cross-platform** (Windows, macOS, Linux)
- ✅ **Modern** and actively developed
- ✅ **Secure** by default (sandboxed communication)
- ✅ Uses system webview (WebView2 on Windows, WebKit on macOS)

**Cons**:
- ❌ **Rust required** for custom integrations (learning curve)
- ❌ **Less mature** than Electron (fewer examples)
- ❌ **Python integration** not as well-documented
- ❌ **System webview variations** across platforms

**Best for**: Modern apps prioritizing small bundle size and performance

---

### Option 3: PyWebView + Flask 🐍 **PYTHON-NATIVE**

**Architecture**: Pure Python desktop app with embedded webview

**Pros**:
- ✅ **Native Python** integration (no subprocess needed)
- ✅ **Simple architecture** (one process)
- ✅ **Lightweight** compared to Electron
- ✅ **Cross-platform** with minimal setup
- ✅ **No Node.js** build process needed

**Cons**:
- ❌ **Next.js incompatible** (would need to rebuild frontend in vanilla React or Vue)
- ❌ **Less mature** than Electron
- ❌ **Limited** native UI capabilities
- ❌ **System webview variations** cause inconsistencies

**Best for**: Simple Python apps, not ideal for existing Next.js app

---

### Option 4: WebView2 (Windows Only) 🪟

**Architecture**: .NET or Python app with embedded Edge WebView2

**Pros**:
- ✅ **Small bundle** (uses system browser)
- ✅ **Native Windows** integration
- ✅ **Modern Edge** engine (Chromium-based)
- ✅ **Fast performance**

**Cons**:
- ❌ **Windows only** (no macOS/Linux)
- ❌ **Requires WebView2** runtime (usually pre-installed on Windows 11)
- ❌ **Python integration** requires subprocess

**Best for**: Windows-only deployment with tight OS integration

---

### Option 5: Qt (PySide6/PyQt6) with QtWebEngine 🖥️

**Architecture**: Native Python desktop app with embedded browser engine

**Pros**:
- ✅ **Native Python** integration
- ✅ **Professional UI** capabilities
- ✅ **Cross-platform**
- ✅ **Rich desktop features** (system tray, native menus, etc.)

**Cons**:
- ❌ **Qt licensing** complexity (GPL or commercial)
- ❌ **Large dependencies** (Qt libraries)
- ❌ **Learning curve** for Qt framework
- ❌ **Next.js compatibility** requires serving or static export

**Best for**: Enterprise apps needing advanced desktop features

---

## Recommended Approach: Electron + Python

### Why Electron?

For your handbell arrangement generator:

1. **Minimal code changes** - Keep Next.js frontend as-is
2. **Python backend preserved** - Music parsing libraries work unchanged
3. **Professional packaging** - DMG for macOS, NSIS installer for Windows, AppImage for Linux
4. **File handling** - Native dialogs for MIDI upload, CSV export
5. **Cross-platform** - Deploy to all major OSes from same codebase
6. **Proven pattern** - Many apps use Electron + Python (e.g., VS Code uses Electron, many data science tools embed Python)

---

## Implementation Plan: Electron + Python

### Phase 1: Project Setup ✨

**1.1 Initialize Electron Project**
```bash
mkdir desktop
cd desktop
npm init -y
npm install electron electron-builder electron-packager
npm install --save-dev @electron/rebuild
```

**1.2 Create Electron Main Process** (`desktop/main.js`)
- Initialize BrowserWindow
- Load Next.js build (production) or dev server (development)
- Spawn Python Flask backend as subprocess
- Handle window lifecycle (minimize, maximize, close)

**1.3 Create Preload Script** (`desktop/preload.js`)
- Expose safe IPC channels to renderer
- Handle file system operations
- Bridge for backend communication

**1.4 Package.json Scripts**
```json
{
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "pack": "electron-builder --dir",
    "dist": "electron-builder"
  }
}
```

---

### Phase 2: Next.js Build Integration 🎨

**2.1 Export Next.js as Static Site**

Update `frontend/next.config.js`:
```javascript
module.exports = {
  output: 'export',  // Static HTML export
  distDir: '../desktop/build',  // Output to Electron folder
  images: {
    unoptimized: true  // Required for static export
  }
}
```

Build frontend:
```bash
cd frontend
npm run build  # Outputs to desktop/build/
```

**2.2 Alternative: Run Next.js Dev Server**

For development mode, spawn Next.js dev server alongside backend:
```javascript
// In main.js
const nextDevServer = spawn('npm', ['run', 'dev'], {
  cwd: path.join(__dirname, '../frontend'),
  shell: true
});
```

**Decision**: Use static export for production, dev server for development

---

### Phase 3: Python Backend Integration 🐍

**3.1 Bundle Python Runtime**

Use **PyInstaller** to create standalone Python executable:

```bash
cd backend
pip install pyinstaller
pyinstaller --onefile --add-data "app:app" run.py
```

This creates `dist/run.exe` (Windows) or `dist/run` (macOS/Linux) containing:
- Python runtime
- All dependencies (Flask, mido, music21, etc.)
- Backend application code

**3.2 Electron Spawns Python Process**

```javascript
// desktop/main.js
const { spawn } = require('child_process');
const path = require('path');

let pythonProcess = null;

function startBackend() {
  const isDev = process.env.NODE_ENV === 'development';
  
  if (isDev) {
    // Development: Use Python from system
    pythonProcess = spawn('python', ['run.py'], {
      cwd: path.join(__dirname, '../backend'),
      env: { ...process.env, FLASK_ENV: 'production' }
    });
  } else {
    // Production: Use bundled Python executable
    const pythonExe = path.join(
      process.resourcesPath,
      'backend',
      process.platform === 'win32' ? 'run.exe' : 'run'
    );
    pythonProcess = spawn(pythonExe, [], {
      env: { ...process.env, FLASK_ENV: 'production' }
    });
  }
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
  
  // Wait for backend to be ready
  return new Promise((resolve) => {
    setTimeout(resolve, 3000);  // Or poll http://localhost:5000/api/health
  });
}

function stopBackend() {
  if (pythonProcess) {
    pythonProcess.kill();
  }
}

app.on('before-quit', stopBackend);
```

**3.3 Configure Backend for Desktop**

Update `backend/config.py`:
```python
class DesktopConfig(Config):
    """Configuration for desktop application"""
    DEBUG = False
    TESTING = False
    # Allow only local connections
    ALLOWED_ORIGINS = ['http://localhost:3000', 'file://*']
    # Use app data directory for uploads
    UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), '.vibebells', 'uploads')
```

---

### Phase 4: Build Configuration 📦

**4.1 Electron Builder Config** (`desktop/electron-builder.json`)

```json
{
  "appId": "com.vibebells.app",
  "productName": "Vibebells",
  "directories": {
    "output": "dist",
    "buildResources": "assets"
  },
  "files": [
    "main.js",
    "preload.js",
    "build/**/*",
    "assets/**/*"
  ],
  "extraResources": [
    {
      "from": "../backend/dist/run.exe",
      "to": "backend/run.exe",
      "filter": ["**/*"]
    }
  ],
  "win": {
    "target": ["nsis", "portable"],
    "icon": "assets/icon.ico"
  },
  "mac": {
    "target": ["dmg", "zip"],
    "icon": "assets/icon.icns",
    "category": "public.app-category.music"
  },
  "linux": {
    "target": ["AppImage", "deb"],
    "icon": "assets/icon.png",
    "category": "Audio"
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true
  }
}
```

**4.2 Build Scripts**

```bash
# Build everything
npm run build:all

# Steps:
# 1. Build Next.js frontend (static export)
cd frontend && npm run build

# 2. Build Python backend (PyInstaller)
cd backend && pyinstaller run.spec

# 3. Package Electron app
cd desktop && npm run dist
```

---

### Phase 5: Native Features 🎁

**5.1 File Dialogs**

Replace browser file input with native dialogs:

```javascript
// In main process
const { dialog } = require('electron');

ipcMain.handle('select-midi-file', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: 'Music Files', extensions: ['mid', 'midi', 'musicxml', 'xml'] }
    ]
  });
  
  if (!result.canceled) {
    return result.filePaths[0];
  }
  return null;
});
```

Update frontend to use Electron IPC:
```javascript
// In renderer process
const { ipcRenderer } = window.electron;

async function handleFileSelect() {
  const filePath = await ipcRenderer.invoke('select-midi-file');
  if (filePath) {
    // Upload to backend
    const file = await fetch(filePath).then(r => r.blob());
    // ... existing upload logic
  }
}
```

**5.2 Native Menus**

```javascript
const { Menu } = require('electron');

const template = [
  {
    label: 'File',
    submenu: [
      {
        label: 'Open MIDI...',
        accelerator: 'CmdOrCtrl+O',
        click: () => { /* trigger file open */ }
      },
      {
        label: 'Export CSV...',
        accelerator: 'CmdOrCtrl+E',
        click: () => { /* trigger export */ }
      },
      { type: 'separator' },
      { role: 'quit' }
    ]
  },
  {
    label: 'Edit',
    submenu: [
      { role: 'undo' },
      { role: 'redo' },
      { type: 'separator' },
      { role: 'cut' },
      { role: 'copy' },
      { role: 'paste' }
    ]
  },
  {
    label: 'View',
    submenu: [
      { role: 'reload' },
      { role: 'toggleDevTools' },
      { type: 'separator' },
      { role: 'resetZoom' },
      { role: 'zoomIn' },
      { role: 'zoomOut' }
    ]
  },
  {
    label: 'Help',
    submenu: [
      {
        label: 'Documentation',
        click: () => { /* open docs */ }
      },
      {
        label: 'About Vibebells',
        click: () => { /* show about dialog */ }
      }
    ]
  }
];

const menu = Menu.buildFromTemplate(template);
Menu.setApplicationMenu(menu);
```

**5.3 Auto-Updates** (Optional)

```javascript
const { autoUpdater } = require('electron-updater');

autoUpdater.on('update-available', () => {
  dialog.showMessageBox({
    type: 'info',
    title: 'Update Available',
    message: 'A new version is available. Download now?',
    buttons: ['Yes', 'No']
  }).then(result => {
    if (result.response === 0) {
      autoUpdater.downloadUpdate();
    }
  });
});
```

---

### Phase 6: Distribution 🚀

**6.1 Code Signing**

**macOS**:
```bash
# Sign the app
electron-builder --mac --publish never
# Requires: Apple Developer account + certificates
```

**Windows**:
```bash
# Sign the installer
electron-builder --win --publish never
# Requires: Code signing certificate from CA (e.g., DigiCert, Sectigo)
```

**6.2 Packaging**

Outputs:
- **Windows**: `Vibebells-Setup-1.0.0.exe` (NSIS installer) + portable .exe
- **macOS**: `Vibebells-1.0.0.dmg` + .zip
- **Linux**: `Vibebells-1.0.0.AppImage` + .deb

**6.3 Distribution Channels**

- **Direct download**: Host on website (vibebells.com/download)
- **Microsoft Store**: Package as MSIX
- **Mac App Store**: Requires additional sandboxing
- **Snapcraft** (Linux): Publish to Snap Store
- **GitHub Releases**: Use electron-builder --publish option

---

## Bundle Size Estimates

### Electron + Python
- **Electron runtime**: ~120MB (Chromium + Node.js)
- **Next.js build**: ~5MB (optimized production build)
- **Python runtime**: ~30-50MB (embedded Python + dependencies)
- **Backend code**: ~10MB (mido, music21, Flask)
- **Total**: ~165-185MB

### Tauri + Python (if chosen instead)
- **Tauri runtime**: ~5-10MB (Rust executable)
- **System webview**: 0MB (uses OS browser)
- **Next.js build**: ~5MB
- **Python runtime**: ~30-50MB
- **Backend code**: ~10MB
- **Total**: ~50-75MB

---

## Development Workflow

### Local Development
```bash
# Terminal 1: Backend
cd backend && python run.py

# Terminal 2: Frontend dev server
cd frontend && npm run dev

# Terminal 3: Electron (loads from localhost:3000)
cd desktop && npm start
```

### Production Build
```bash
# Automated build script
./build-desktop.sh  # or build-desktop.bat

# Manual steps:
cd frontend && npm run build  # Static export
cd ../backend && pyinstaller run.spec  # Bundle Python
cd ../desktop && npm run dist  # Package Electron
```

---

## Testing Strategy

1. **Unit tests**: Continue using existing backend tests
2. **Integration tests**: Test Electron ↔ Python communication
3. **E2E tests**: Spectron (deprecated) or Playwright for Electron
4. **Manual testing**: Test on all target platforms (Windows, macOS, Linux)

---

## Security Considerations

1. **Context isolation**: Enable in Electron (default in v12+)
2. **Node integration**: Disable in renderer process
3. **Preload script**: Use for safe IPC
4. **Content Security Policy**: Restrict loaded content
5. **Python subprocess**: Bind only to localhost
6. **File system**: Limit access to app-specific directories

---

## Cost & Effort Estimate

| Task | Time Estimate |
|------|---------------|
| Electron setup | 1-2 days |
| Next.js static export | 0.5 days |
| Python integration | 1-2 days |
| Native features (menus, dialogs) | 1 day |
| Build configuration | 1 day |
| Testing on all platforms | 2-3 days |
| Code signing setup | 1-2 days |
| Documentation | 1 day |
| **Total** | **8-12 days** |

---

## Alternatives Comparison

| Feature | Electron | Tauri | PyWebView | Qt |
|---------|----------|-------|-----------|-----|
| Bundle size | 165MB | 75MB | 80MB | 150MB |
| Cross-platform | ✅ | ✅ | ✅ | ✅ |
| Python integration | ⭐ Good | ⚠️ Medium | ⭐ Native | ⭐ Native |
| Next.js compatible | ✅ Yes | ✅ Yes | ❌ No | ⚠️ Limited |
| Maturity | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ |
| Learning curve | Low | Medium | Low | High |
| Community support | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ |

---

## Recommendation Summary

**For Vibebells**: Use **Electron + Python subprocess**

**Reasons**:
1. ✅ Keep existing Next.js + Flask architecture intact
2. ✅ Cross-platform with minimal platform-specific code
3. ✅ Mature ecosystem with extensive documentation
4. ✅ Professional packaging and distribution tools
5. ✅ Proven pattern for Python integration
6. ✅ Native desktop features (file dialogs, menus, etc.)
7. ✅ Can implement auto-updates easily

**Acceptable tradeoff**: Larger bundle size (~170MB) for significantly faster development and better compatibility.

**Alternative** (if bundle size is critical): **Tauri**, but requires Rust knowledge for advanced integrations.

---

## Next Steps

1. Review this plan and confirm approach
2. Set up Electron project structure
3. Create build pipeline for bundling Python
4. Test desktop packaging on target platforms
5. Implement native features (file dialogs, etc.)
6. Set up distribution infrastructure

Would you like me to start implementing the Electron integration?
