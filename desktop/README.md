# Vibebells Desktop Application

Desktop version of the Handbell Arrangement Generator using Electron.

## Development

### Prerequisites
- Node.js 20+
- Python 3.11+
- Flask backend dependencies installed

### Running in Development Mode

1. **Start the Python backend** (in one terminal):
   ```bash
   cd backend
   python -m flask run
   ```

2. **Start the Next.js frontend** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Start Electron** (in a third terminal):
   ```bash
   cd desktop
   npm run dev
   ```

The Electron app will load the Next.js dev server at http://localhost:3000 and connect to the Flask backend at http://localhost:5000.

## Building for Production

### Quick Build (Windows)
```bash
# From project root
.\scripts\build-desktop.bat
cd desktop
npm run build:win
```

### Manual Build Steps

1. **Build Next.js frontend** (static export):
   ```bash
   cd frontend
   set BUILD_ELECTRON=true
   npm run build
   ```

2. **Copy frontend build to desktop**:
   ```bash
   xcopy /E /I frontend\out desktop\build
   ```

3. **Build Python backend** with PyInstaller:
   ```bash
   cd backend
   pip install pyinstaller
   pyinstaller --name=run --onefile --hidden-import=flask --hidden-import=flask_cors --hidden-import=mido --hidden-import=music21 --add-data "app;app" run.py
   ```

4. **Package with Electron Builder**:
   ```bash
   cd desktop
   npm run build
   ```

Output installers will be in `desktop/dist/`:
- Windows: `Vibebells Setup 1.0.0.exe` (NSIS installer) and `Vibebells 1.0.0.exe` (portable)

## Features

- ✅ Native file dialogs for MIDI upload and CSV export
- ✅ Application menu with keyboard shortcuts
- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ Bundled Python backend (no separate installation needed)
- ✅ Auto-updates support (can be configured)

## Architecture

```
Vibebells Desktop
├── Electron Shell (main.js)
│   ├── Spawns Python backend subprocess
│   ├── Creates native window with Next.js UI
│   └── Provides native file dialogs
├── Next.js Frontend (static build in build/)
│   └── React UI with API calls to localhost:5000
└── Python Backend (bundled executable)
    └── Flask API server with music processing
```

## Keyboard Shortcuts

- `Ctrl+O` / `Cmd+O` - Open MIDI file
- `Ctrl+E` / `Cmd+E` - Export CSV
- `Ctrl+Q` / `Cmd+Q` - Quit application
- `F12` - Toggle DevTools (development only)

## Configuration

### Backend Port
The backend runs on `localhost:5000` by default. To change:
1. Update `FLASK_RUN_PORT` in backend environment
2. Update connection in `desktop/main.js`

### Window Size
Default: 1200x800 (minimum: 800x600)
To change, edit `desktop/main.js`:
```javascript
mainWindow = new BrowserWindow({
  width: 1200,  // Change here
  height: 800,  // Change here
  // ...
});
```

## Troubleshooting

### Backend doesn't start
- Check Python is installed and in PATH
- Verify Flask backend works standalone: `cd backend && python run.py`
- Check console output in Electron DevTools

### Frontend doesn't load
- Verify Next.js builds successfully: `cd frontend && npm run build`
- Check `desktop/build/` contains the static files
- Enable DevTools (F12) to see console errors

### Build errors
- Ensure all dependencies are installed: `npm install` in both `frontend/` and `desktop/`
- Clear build caches: delete `frontend/.next/`, `frontend/out/`, `desktop/build/`
- Rebuild: `npm run build` in frontend, then copy to desktop

## Platform-Specific Notes

### Windows
- WebView2 is bundled with Electron (no separate installation)
- NSIS installer creates Start Menu shortcuts
- Portable version available for USB deployment

### macOS
- Code signing required for distribution (not for development)
- DMG provides drag-to-Applications install
- Notarization required for macOS 10.15+

### Linux
- AppImage is self-contained (no installation needed)
- .deb package for Debian/Ubuntu systems
- Requires WebKitGTK on some distributions

## Next Steps

- [ ] Create application icons (see `desktop/assets/README.md`)
- [ ] Configure auto-updater (optional)
- [ ] Set up code signing for distribution
- [ ] Create installers for all platforms
- [ ] Add application icon and branding
