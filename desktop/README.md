# Vibebells Desktop Application

Desktop version of the Vibebells handbell arrangement generator using Electron.

## Development

### Prerequisites
- Node.js 18+
- Python 3.8+

### Running in Development Mode

The desktop app needs both the backend and frontend running:

1. **Start the Python backend** (terminal 1):
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   python run.py
   ```

2. **Start the Next.js frontend** (terminal 2):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Start Electron** (terminal 3):
   ```bash
   cd desktop
   npm install
   npm run dev
   ```

The Electron app will load the Next.js dev server at http://localhost:3000 and connect to the Flask backend at http://localhost:5000.

## Building for Production

### Automated Build Script (Windows)

The easiest way to build on Windows is using the provided script:

```bash
scripts\build-desktop.bat
```

This script automatically:
1. Builds the Python backend with PyInstaller
2. Builds the Next.js frontend
3. Copies the frontend to desktop/build
4. Packages the Electron app

Output: `desktop/dist/Vibebells Setup 1.0.1.exe` (installer) and `Vibebells 1.0.1.exe` (portable)

### Manual Build Steps

#### Windows Build

```bash
cd frontend
npm run build
xcopy /E /I out ..\desktop\build

cd ..\backend
pip install pyinstaller
pyinstaller vibebells-backend.spec

cd ..\desktop
npm run build:win
```

Output: `desktop/dist/Vibebells Setup 1.0.1.exe` (installer) and `Vibebells 1.0.1.exe` (portable)

### macOS Build (on macOS)

```bash
cd frontend
npm run build
cp -r out ../desktop/build

cd ../backend
pip install pyinstaller
pyinstaller vibebells-backend.spec

cd ../desktop
npm run build:mac
```

Output: `desktop/dist/Vibebells-1.0.1.dmg`

### Linux Build

```bash
cd frontend
npm run build
cp -r out ../desktop/build

cd ../backend
pip install pyinstaller
pyinstaller vibebells-backend.spec

cd ../desktop
npm run build:linux
```

Output: `desktop/dist/Vibebells-1.0.1.AppImage` and `.deb`

## Features

- Native file dialogs for music file upload and CSV export
- Application menu with About dialog
- Cross-platform support (Windows, macOS, Linux)
- Bundled Python backend (no separate installation needed)
- Offline operation

## Architecture

```
Electron Main Process (main.js)
├── Spawns Python backend subprocess
├── Creates window loading static Next.js build
├── Provides IPC bridge (preload.js) for:
│   ├── File dialogs
│   └── File reading
└── Handles app lifecycle

Frontend (Next.js static build)
└── Communicates with backend via fetch to localhost:5000

Backend (PyInstaller executable)
└── Flask API server with music processing
```

## Testing

```bash
cd desktop
npm test              # Run all E2E tests
npm run test:headed   # Watch tests run
npm run test:ui       # Interactive test UI
```

**Test Suite**: 16/16 passing (5 API tests + 11 UI tests)

## Icon Generation

To regenerate app icons:

```bash
cd desktop
npm run generate-icons
```

This creates platform-specific icons from `desktop/assets/handbell-icon-full-cropped.png`.

## Troubleshooting

### Backend doesn't start
- Check Python is installed: `python --version`
- Verify backend works standalone: `cd backend && python run.py`
- Check Electron console for error messages (Help > Toggle Developer Tools)

### Frontend doesn't load
- Verify Next.js build succeeded: check `desktop/build/` contains HTML files
- Clear cache: delete `desktop/build/` and rebuild frontend
- Check DevTools Network tab for failed requests

### Build errors
- Clear all build artifacts: delete `frontend/.next/`, `frontend/out/`, `desktop/build/`, `desktop/dist/`
- Reinstall dependencies: `npm install` in frontend and desktop
- Ensure Python backend builds: `cd backend && pyinstaller vibebells-backend.spec`
