# Desktop Deployment Plan: Tauri Alternative

**Status**: Draft Proposal  
**Created**: 2026-02-08  
**Alternative to**: Electron approach (see DESKTOP_DEPLOYMENT_PLAN.md)

## Executive Summary

This document outlines an alternative desktop deployment strategy using **Tauri 2.0** instead of Electron. Tauri offers significantly smaller bundle sizes (~75MB vs ~170MB) by using the operating system's native webview instead of bundling Chromium. However, it requires Rust development and more substantial code changes.

### Key Differences from Electron

| Aspect | Tauri | Electron |
|--------|-------|----------|
| **Bundle Size** | ~75MB | ~170MB |
| **Memory Usage** | ~50-100MB | ~100-200MB |
| **Runtime** | Native webview | Bundled Chromium |
| **Backend Language** | Rust | Node.js |
| **Learning Curve** | Steep (Rust required) | Moderate |
| **Code Changes** | Moderate-High | Minimal |
| **Maturity** | Growing (v2.0 released 2024) | Very mature |
| **Python Integration** | Via sidecar process | Native subprocess |

## Architecture Overview

```
Desktop App Structure (Tauri):
┌──────────────────────────────────────────┐
│   Tauri Core (Rust main process)         │
│  - Spawns Python sidecar process         │
│  - Serves Next.js static build           │
│  - Handles native features via commands  │
│  - Uses OS native webview                │
└──────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌──────────────┐    ┌─────────────────────┐
│  Next.js UI  │◄───┤ Flask Backend       │
│  (webview)   │    │ (sidecar process)   │
│              │    │ localhost:5000      │
└──────────────┘    └─────────────────────┘
```

### Key Architectural Differences

1. **Rust Core**: Main application logic in Rust (Tauri commands)
2. **Native Webview**: Uses WebView2 (Windows), WebKit (macOS), WebKitGTK (Linux)
3. **Sidecar Process**: Python backend runs as managed sidecar (more integrated than Electron subprocess)
4. **IPC**: Tauri's type-safe command system (Rust functions called from JS)

## Technology Stack

### Required Tools
- **Rust** (1.70+) - Core Tauri runtime
- **Node.js** (20+) - Frontend build tools
- **Python** (3.11+) - Backend application
- **PyInstaller** - Bundle Python backend
- **Tauri CLI** - Build and package

### Platform Requirements
- **Windows**: WebView2 Runtime (pre-installed on Windows 11, auto-installed on 10)
- **macOS**: WebKit (built-in)
- **Linux**: WebKitGTK 4.1+

## Detailed Implementation Plan

### Phase 1: Setup Tauri Project (2-3 days)

#### 1.1 Install Rust and Tauri CLI
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Tauri CLI
cargo install tauri-cli

# Or via npm
npm install -g @tauri-apps/cli
```

#### 1.2 Initialize Tauri Project
```bash
cd vibebells
npm install @tauri-apps/api @tauri-apps/plugin-shell @tauri-apps/plugin-dialog @tauri-apps/plugin-fs
cargo tauri init
```

Configuration prompts:
- App name: `Vibebells`
- Window title: `Vibebells - Handbell Arrangement Generator`
- Web assets location: `frontend/out`
- Dev server URL: `http://localhost:3000`
- Frontend dev command: `npm run dev --prefix frontend`
- Frontend build command: `npm run build --prefix frontend`

#### 1.3 Project Structure
```
vibebells/
├── src-tauri/              # Tauri Rust code
│   ├── src/
│   │   ├── main.rs         # Entry point, window setup
│   │   ├── commands.rs     # Tauri commands (IPC)
│   │   ├── sidecar.rs      # Python process management
│   │   └── lib.rs          # Library exports
│   ├── Cargo.toml          # Rust dependencies
│   ├── tauri.conf.json     # Tauri configuration
│   └── icons/              # App icons
├── backend/                # Existing Python backend
├── frontend/               # Existing Next.js frontend
└── scripts/                # Build scripts
```

### Phase 2: Configure Python Sidecar (2-3 days)

#### 2.1 Bundle Python Backend with PyInstaller

Create `backend/backend.spec`:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app/__init__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/services/*.py', 'app/services'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'werkzeug',
        'mido',
        'music21',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='vibebells-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for debugging initially
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='vibebells-backend',
)
```

Build script `scripts/build-backend.sh`:
```bash
#!/bin/bash
set -e

echo "Building Python backend..."
cd backend

# Install dependencies
pip install pyinstaller

# Build executable
pyinstaller backend.spec --clean

# Copy to Tauri resources
mkdir -p ../src-tauri/binaries
cp dist/vibebells-backend ../src-tauri/binaries/vibebells-backend-x86_64-pc-windows-msvc.exe

echo "Backend built successfully"
```

#### 2.2 Configure Tauri Sidecar

Update `src-tauri/tauri.conf.json`:
```json
{
  "productName": "Vibebells",
  "version": "1.0.0",
  "identifier": "com.vibebells.app",
  "build": {
    "beforeBuildCommand": "npm run build --prefix frontend",
    "beforeDevCommand": "npm run dev --prefix frontend",
    "devUrl": "http://localhost:3000",
    "frontendDist": "../frontend/out"
  },
  "bundle": {
    "active": true,
    "targets": ["nsis", "msi", "dmg", "appimage"],
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "resources": [],
    "externalBin": [
      "binaries/vibebells-backend"
    ],
    "windows": {
      "webviewInstallMode": {
        "type": "downloadBootstrapper"
      },
      "wix": {
        "language": "en-US"
      }
    }
  },
  "app": {
    "windows": [
      {
        "title": "Vibebells",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "security": {
      "csp": "default-src 'self'; connect-src 'self' http://localhost:5000"
    }
  }
}
```

#### 2.3 Implement Sidecar Management in Rust

Create `src-tauri/src/sidecar.rs`:
```rust
use tauri::Manager;
use std::process::{Command, Child};
use std::sync::Mutex;

pub struct PythonBackend {
    process: Mutex<Option<Child>>,
}

impl PythonBackend {
    pub fn new() -> Self {
        Self {
            process: Mutex::new(None),
        }
    }

    pub fn start(&self, app_handle: &tauri::AppHandle) -> Result<(), String> {
        let resource_path = app_handle
            .path()
            .resolve("binaries/vibebells-backend", tauri::path::BaseDirectory::Resource)
            .map_err(|e| e.to_string())?;

        let child = Command::new(resource_path)
            .spawn()
            .map_err(|e| format!("Failed to start Python backend: {}", e))?;

        *self.process.lock().unwrap() = Some(child);

        // Wait for backend to be ready (poll localhost:5000)
        std::thread::sleep(std::time::Duration::from_secs(2));

        Ok(())
    }

    pub fn stop(&self) {
        if let Some(mut child) = self.process.lock().unwrap().take() {
            let _ = child.kill();
        }
    }
}

impl Drop for PythonBackend {
    fn drop(&mut self) {
        self.stop();
    }
}
```

### Phase 3: Implement Tauri Commands (1-2 days)

Create `src-tauri/src/commands.rs`:
```rust
use tauri::command;

#[command]
pub fn get_backend_url() -> String {
    "http://localhost:5000".to_string()
}

#[command]
pub async fn check_backend_health() -> Result<bool, String> {
    let client = reqwest::Client::new();
    match client
        .get("http://localhost:5000/api/health")
        .send()
        .await
    {
        Ok(response) => Ok(response.status().is_success()),
        Err(_) => Ok(false),
    }
}

#[command]
pub fn open_file_dialog() -> Result<Option<String>, String> {
    use tauri::api::dialog::blocking::FileDialogBuilder;
    
    let file = FileDialogBuilder::new()
        .add_filter("MIDI Files", &["mid", "midi"])
        .pick_file();
    
    Ok(file.map(|p| p.to_string_lossy().to_string()))
}

#[command]
pub fn save_file_dialog(default_name: String) -> Result<Option<String>, String> {
    use tauri::api::dialog::blocking::FileDialogBuilder;
    
    let file = FileDialogBuilder::new()
        .set_file_name(&default_name)
        .add_filter("CSV Files", &["csv"])
        .save_file();
    
    Ok(file.map(|p| p.to_string_lossy().to_string()))
}
```

Update `src-tauri/src/main.rs`:
```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod sidecar;

use tauri::Manager;

fn main() {
    let backend = sidecar::PythonBackend::new();

    tauri::Builder::default()
        .setup(|app| {
            // Start Python backend
            backend.start(&app.handle())?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_backend_url,
            commands::check_backend_health,
            commands::open_file_dialog,
            commands::save_file_dialog,
        ])
        .on_window_event(|event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                // Backend cleanup handled by Drop trait
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

Update `src-tauri/Cargo.toml`:
```toml
[package]
name = "vibebells"
version = "1.0.0"
edition = "2021"

[dependencies]
tauri = { version = "2.0", features = ["protocol-asset", "shell-open"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
reqwest = { version = "0.11", features = ["blocking", "json"] }

[build-dependencies]
tauri-build = { version = "2.0", features = [] }

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
```

### Phase 4: Update Frontend for Tauri (1 day)

#### 4.1 Install Tauri API
```bash
cd frontend
npm install @tauri-apps/api @tauri-apps/plugin-dialog @tauri-apps/plugin-shell
```

#### 4.2 Update API Calls

Create `frontend/app/lib/tauri.js`:
```javascript
let tauriInvoke = null;
let tauriDialog = null;

// Dynamically import Tauri APIs only in desktop mode
if (typeof window !== 'undefined' && window.__TAURI__) {
  import('@tauri-apps/api/core').then(module => {
    tauriInvoke = module.invoke;
  });
  import('@tauri-apps/plugin-dialog').then(module => {
    tauriDialog = module;
  });
}

export const isTauriApp = () => {
  return typeof window !== 'undefined' && window.__TAURI__;
};

export const getBackendUrl = async () => {
  if (isTauriApp() && tauriInvoke) {
    return await tauriInvoke('get_backend_url');
  }
  return 'http://localhost:5000';
};

export const checkBackendHealth = async () => {
  if (isTauriApp() && tauriInvoke) {
    return await tauriInvoke('check_backend_health');
  }
  // Fallback for web mode
  try {
    const response = await fetch('http://localhost:5000/api/health');
    return response.ok;
  } catch {
    return false;
  }
};

export const openFileDialog = async () => {
  if (isTauriApp() && tauriDialog) {
    const file = await tauriDialog.open({
      multiple: false,
      filters: [{
        name: 'MIDI Files',
        extensions: ['mid', 'midi']
      }]
    });
    return file;
  }
  return null; // Fall back to HTML file input
};

export const saveFileDialog = async (defaultName) => {
  if (isTauriApp() && tauriDialog) {
    const file = await tauriDialog.save({
      defaultPath: defaultName,
      filters: [{
        name: 'CSV Files',
        extensions: ['csv']
      }]
    });
    return file;
  }
  return null; // Fall back to browser download
};
```

#### 4.3 Update Components to Use Tauri API

Modify `frontend/app/page.js`:
```javascript
import { isTauriApp, openFileDialog } from './lib/tauri';

// In handleFileUpload function:
const handleFileUpload = async (event) => {
  let file;
  
  if (isTauriApp()) {
    // Use Tauri file dialog
    const filePath = await openFileDialog();
    if (!filePath) return;
    
    // Read file using Tauri FS plugin
    const { readBinaryFile } = await import('@tauri-apps/plugin-fs');
    const fileData = await readBinaryFile(filePath);
    file = new File([fileData], filePath.split('/').pop());
  } else {
    // Use standard HTML file input
    file = event.target.files[0];
  }
  
  // Rest of existing upload logic...
};
```

#### 4.4 Update Export Logic

Modify `frontend/app/components/ArrangementDisplay.js`:
```javascript
import { isTauriApp, saveFileDialog } from '../lib/tauri';

const handleExportCSV = async () => {
  try {
    // ... existing API call to get CSV data ...
    
    if (isTauriApp()) {
      // Use Tauri save dialog
      const filePath = await saveFileDialog(filename);
      if (!filePath) return;
      
      // Write file using Tauri FS plugin
      const { writeTextFile } = await import('@tauri-apps/plugin-fs');
      await writeTextFile(filePath, csvData);
      
      alert('CSV exported successfully!');
    } else {
      // Existing browser download logic
      const blob = new Blob([csvData], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      // ... rest of existing code ...
    }
  } catch (error) {
    console.error('Export failed:', error);
  }
};
```

### Phase 5: Build Configuration (1-2 days)

#### 5.1 Create Build Script

Create `scripts/build-tauri.sh`:
```bash
#!/bin/bash
set -e

echo "=== Building Vibebells Desktop (Tauri) ==="

# Step 1: Build Python backend
echo "Step 1: Building Python backend..."
./scripts/build-backend.sh

# Step 2: Build Next.js frontend (static export)
echo "Step 2: Building Next.js frontend..."
cd frontend
npm run build
cd ..

# Step 3: Build Tauri app
echo "Step 3: Building Tauri desktop app..."
cd src-tauri
cargo tauri build

echo "=== Build complete ==="
echo "Installers located in: src-tauri/target/release/bundle/"
```

#### 5.2 Update Next.js Configuration

Ensure `frontend/next.config.js` has static export:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // Required for Tauri
  images: {
    unoptimized: true, // Required for static export
  },
  // Remove basePath and assetPrefix for Tauri
};

module.exports = nextConfig;
```

#### 5.3 Platform-Specific Builds

**Windows**:
```bash
cargo tauri build --target x86_64-pc-windows-msvc
# Outputs: NSIS installer (.exe) and MSI
```

**macOS**:
```bash
# Intel
cargo tauri build --target x86_64-apple-darwin

# Apple Silicon
cargo tauri build --target aarch64-apple-darwin

# Universal binary
cargo tauri build --target universal-apple-darwin
# Outputs: DMG and .app bundle
```

**Linux**:
```bash
cargo tauri build --target x86_64-unknown-linux-gnu
# Outputs: AppImage and .deb
```

### Phase 6: Advanced Features (1-2 days)

#### 6.1 Application Menu

Update `src-tauri/tauri.conf.json`:
```json
{
  "app": {
    "menu": {
      "items": [
        {
          "id": "file",
          "text": "File",
          "submenu": [
            {
              "id": "open",
              "text": "Open MIDI...",
              "accelerator": "CmdOrCtrl+O"
            },
            {
              "id": "export",
              "text": "Export CSV...",
              "accelerator": "CmdOrCtrl+E"
            },
            { "type": "separator" },
            {
              "id": "quit",
              "text": "Quit",
              "accelerator": "CmdOrCtrl+Q"
            }
          ]
        },
        {
          "id": "help",
          "text": "Help",
          "submenu": [
            {
              "id": "about",
              "text": "About Vibebells"
            }
          ]
        }
      ]
    }
  }
}
```

#### 6.2 Auto-Updater (Tauri's built-in)

Add to `src-tauri/Cargo.toml`:
```toml
[dependencies]
tauri = { version = "2.0", features = ["updater"] }
```

Create `src-tauri/src/updater.rs`:
```rust
use tauri::Updater;

pub async fn check_for_updates(app: tauri::AppHandle) {
    let updater = app.updater();
    
    match updater.check().await {
        Ok(Some(update)) => {
            println!("Update available: {}", update.version());
            // Prompt user to install update
        }
        Ok(None) => println!("App is up to date"),
        Err(e) => eprintln!("Failed to check for updates: {}", e),
    }
}
```

#### 6.3 System Tray (Optional)

Add to `src-tauri/tauri.conf.json`:
```json
{
  "app": {
    "trayIcon": {
      "iconPath": "icons/icon.png",
      "tooltip": "Vibebells",
      "menuOnLeftClick": false
    }
  }
}
```

### Phase 7: Testing & Debugging (2-3 days)

#### 7.1 Development Mode
```bash
# Terminal 1: Start Python backend
cd backend
python -m flask run

# Terminal 2: Start Tauri dev mode (will start Next.js automatically)
cd src-tauri
cargo tauri dev
```

#### 7.2 Debug Configuration

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Tauri Development",
      "type": "lldb",
      "request": "launch",
      "program": "${workspaceFolder}/src-tauri/target/debug/vibebells",
      "args": [],
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

#### 7.3 Testing Checklist
- [ ] Python backend starts automatically
- [ ] Backend health check works
- [ ] MIDI file upload (both native dialog and web fallback)
- [ ] Arrangement generation
- [ ] CSV export (both native save dialog and browser download)
- [ ] All three strategies work
- [ ] Window resizing/minimizing
- [ ] Application menu items
- [ ] Quit cleanly (backend process terminates)

### Phase 8: Code Signing & Distribution (1-2 days)

#### 8.1 Windows Code Signing

Obtain code signing certificate, then:
```bash
# Set environment variables
export TAURI_SIGNING_PRIVATE_KEY="path/to/key.pfx"
export TAURI_SIGNING_PRIVATE_KEY_PASSWORD="password"

cargo tauri build
```

#### 8.2 macOS Code Signing & Notarization

```bash
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" \
  "src-tauri/target/release/bundle/macos/Vibebells.app"

# Create DMG
cargo tauri build

# Notarize with Apple
xcrun notarytool submit \
  "src-tauri/target/release/bundle/dmg/Vibebells_1.0.0_x64.dmg" \
  --apple-id "your@email.com" \
  --password "app-specific-password" \
  --team-id "TEAMID" \
  --wait

# Staple notarization
xcrun stapler staple "src-tauri/target/release/bundle/dmg/Vibebells_1.0.0_x64.dmg"
```

#### 8.3 Linux AppImage

No signing required, but should test on multiple distributions:
- Ubuntu 20.04, 22.04, 24.04
- Fedora 38+
- Arch Linux

## Code Changes Required

### Summary of Changes

| Component | Change Level | Details |
|-----------|--------------|---------|
| **Backend** | None | Existing Flask app works as-is |
| **Frontend** | Moderate | Add Tauri API wrappers, conditional logic for desktop vs web |
| **Build** | High | New Rust codebase, Tauri configuration, build scripts |
| **Deployment** | High | New installers, code signing, sidecar management |

### Specific Frontend Changes

1. **Add Tauri API wrapper** (`frontend/app/lib/tauri.js`) - ~150 lines
2. **Update file upload** in `page.js` - ~30 lines modified
3. **Update CSV export** in `ArrangementDisplay.js` - ~25 lines modified
4. **Add health check UI** - ~50 lines new
5. **Next.js config** - ~3 lines modified

Total frontend changes: ~250 lines (mostly new, minimal modifications to existing)

### New Rust Code

1. **Main entry point** (`main.rs`) - ~50 lines
2. **Sidecar management** (`sidecar.rs`) - ~80 lines
3. **Tauri commands** (`commands.rs`) - ~100 lines
4. **Configuration** (`tauri.conf.json`) - ~150 lines
5. **Cargo manifest** (`Cargo.toml`) - ~30 lines

Total Rust code: ~410 lines (all new)

## Timeline & Effort Estimate

### Detailed Timeline

| Phase | Task | Days | Skills Required |
|-------|------|------|----------------|
| 1 | Setup Tauri Project | 2-3 | Rust basics, CLI tools |
| 2 | Configure Python Sidecar | 2-3 | PyInstaller, process management |
| 3 | Implement Tauri Commands | 1-2 | Rust, async programming |
| 4 | Update Frontend | 1 | JavaScript, React |
| 5 | Build Configuration | 1-2 | Shell scripting, build tools |
| 6 | Advanced Features | 1-2 | Rust, Tauri APIs |
| 7 | Testing & Debugging | 2-3 | Cross-platform testing |
| 8 | Code Signing & Distribution | 1-2 | Platform-specific tools |
| **Total** | **Full Implementation** | **11-18 days** | **Rust, JavaScript, DevOps** |

### Learning Curve

If team is **new to Rust**:
- Add 3-5 days for Rust fundamentals
- Add 1-2 days for Tauri-specific concepts
- **Total with learning**: 15-25 days

If team **knows Rust**:
- Follow timeline as stated: 11-18 days

## Comparison: Tauri vs Electron

### Advantages of Tauri

✅ **Smaller bundle size**: 75MB vs 170MB (2.3x smaller)  
✅ **Lower memory usage**: ~50-100MB vs 100-200MB  
✅ **Faster startup**: Native webview loads faster  
✅ **More secure**: Smaller attack surface, no Node.js in frontend  
✅ **Modern architecture**: Type-safe IPC, better async handling  
✅ **Better resource usage**: Native OS components  

### Disadvantages of Tauri

❌ **Requires Rust knowledge**: Steeper learning curve  
❌ **More code changes**: Need to write Rust integration layer  
❌ **Less mature**: Tauri 2.0 released 2024 vs Electron's 10+ years  
❌ **Smaller ecosystem**: Fewer plugins and examples  
❌ **WebView inconsistencies**: Different rendering across platforms  
❌ **Debugging complexity**: Rust debugging less familiar to web devs  

### When to Choose Tauri

Choose Tauri if:
- Bundle size is critical (distribution over internet, bandwidth constraints)
- Team has Rust experience or is willing to learn
- Performance and memory usage are priorities
- You want a modern, secure architecture
- You're building from scratch or can afford moderate refactoring

Choose Electron if:
- Team is pure JavaScript/Python (no Rust experience)
- Need fastest time to market with minimal changes
- Rely on Electron-specific plugins
- Need maximum stability and community support
- Bundle size is not a concern

### Cost-Benefit Analysis

| Metric | Tauri | Electron |
|--------|-------|----------|
| **Development Time** | 11-18 days (or 15-25 with learning) | 8-12 days |
| **Bundle Size** | 75MB ⭐⭐⭐⭐⭐ | 170MB ⭐⭐⭐ |
| **Memory Usage** | 50-100MB ⭐⭐⭐⭐⭐ | 100-200MB ⭐⭐⭐ |
| **Learning Curve** | Steep ⭐⭐ | Moderate ⭐⭐⭐⭐ |
| **Code Changes** | Moderate-High ⭐⭐ | Minimal ⭐⭐⭐⭐⭐ |
| **Maturity** | Growing ⭐⭐⭐ | Very mature ⭐⭐⭐⭐⭐ |
| **Security** | Excellent ⭐⭐⭐⭐⭐ | Good ⭐⭐⭐⭐ |

## Technical Considerations

### Python Sidecar vs Subprocess

**Tauri Sidecar** (managed process):
- Configured in `tauri.conf.json`
- Automatic lifecycle management
- Better integration with Tauri's resource system
- Cleaner shutdown handling

**Electron Subprocess** (manual management):
- Spawned via Node.js `child_process`
- Manual cleanup required
- More flexible but requires more code

### WebView Differences

| Platform | WebView | Chromium Version | Compatibility |
|----------|---------|------------------|---------------|
| Windows | WebView2 | Latest Edge | Excellent (Edge Chromium) |
| macOS | WebKit | Safari version | Good (some CSS differences) |
| Linux | WebKitGTK | Varies by distro | Fair (older WebKit on older distros) |

**Testing strategy**:
- Develop on Windows (most consistent with Chromium)
- Test CSS/layout on macOS early
- Test on oldest supported Linux distros (Ubuntu 20.04)

### Cross-Platform Build Pipeline

Recommended CI/CD approach:
```yaml
# .github/workflows/build.yml
name: Build Desktop Apps

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - uses: dtolnay/rust-toolchain@stable
      - run: npm install
      - run: npm run build:tauri
      - uses: actions/upload-artifact@v3
        with:
          name: windows-installer
          path: src-tauri/target/release/bundle/

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - uses: dtolnay/rust-toolchain@stable
      - run: npm install
      - run: npm run build:tauri
      - uses: actions/upload-artifact@v3
        with:
          name: macos-installer
          path: src-tauri/target/release/bundle/

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - uses: dtolnay/rust-toolchain@stable
      - run: sudo apt-get update
      - run: sudo apt-get install -y libwebkit2gtk-4.1-dev
      - run: npm install
      - run: npm run build:tauri
      - uses: actions/upload-artifact@v3
        with:
          name: linux-installer
          path: src-tauri/target/release/bundle/
```

## Migration Path: Electron to Tauri

If you start with Electron and later want to migrate to Tauri:

### Compatible Components
- ✅ Frontend code (Next.js) - works in both
- ✅ Python backend - works in both
- ✅ API endpoints - identical
- ✅ Business logic - unchanged

### Must Rewrite
- ❌ Main process logic (Node.js → Rust)
- ❌ IPC calls (Electron IPC → Tauri commands)
- ❌ Native integrations (Electron APIs → Tauri plugins)

### Estimated Migration Effort
If you build Electron first and migrate later: **6-10 days**

The frontend changes are identical, but you'll rewrite the main process logic from Node.js to Rust.

## Recommendations

### For Vibebells Project

Given your current status:
- ✅ Working Next.js frontend
- ✅ Stable Python backend
- ✅ No Rust experience mentioned
- ⚠️ Desktop deployment is optional/future consideration

**Recommendation**: **Start with Electron** (DESKTOP_DEPLOYMENT_PLAN.md)

Reasoning:
1. **Faster delivery**: 8-12 days vs 11-18 days (or 15-25 with learning)
2. **Lower risk**: No Rust learning curve, minimal code changes
3. **Proven Python integration**: Well-documented subprocess patterns
4. **Easier maintenance**: Team stays in JavaScript/Python comfort zone

### When to Reconsider Tauri

Reconsider Tauri if:
- Bundle size becomes a critical issue (e.g., need to distribute over slow networks)
- Team gains Rust expertise (e.g., hires Rust developer)
- Performance profiling shows memory/CPU issues with Electron
- You're starting a v2.0 rewrite with time to invest

### Hybrid Approach

You could also:
1. **Start with Electron** (Phase 1: 8-12 days)
2. Ship v1.0 desktop app quickly
3. **Migrate to Tauri** in v2.0 (Phase 2: 6-10 days)
4. Market v2.0 as "smaller, faster, rewritten in Rust"

Total time: 14-22 days, but split across two releases.

## Next Steps

If you choose Tauri:

1. **Install Rust toolchain** (1 hour)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Complete Rust basics tutorial** (1-2 days)
   - The Rust Book: https://doc.rust-lang.org/book/
   - Focus on: ownership, borrowing, error handling, async/await

3. **Initialize Tauri project** (0.5 days)
   ```bash
   cargo tauri init
   ```

4. **Follow Phase 1-8 implementation** (10-16 days)

5. **Test on all target platforms** (2-3 days)

If you'd like me to start implementing the Tauri approach, let me know and I'll begin with Phase 1.

## Appendix: Resources

### Documentation
- Tauri Docs: https://tauri.app/
- Tauri + Next.js: https://tauri.app/guides/frontend/nextjs/
- Rust Book: https://doc.rust-lang.org/book/
- PyInstaller: https://pyinstaller.org/

### Example Projects
- Tauri + Next.js template: https://github.com/tauri-apps/tauri/tree/dev/examples/next.js
- Tauri + Python sidecar: https://github.com/tauri-apps/tauri/discussions/4510

### Community
- Tauri Discord: https://discord.gg/tauri
- GitHub Discussions: https://github.com/tauri-apps/tauri/discussions
