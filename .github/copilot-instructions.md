# Vibebells Development Guide

## Project Overview

Vibebells is a handbell arrangement generator that takes MIDI or MusicXML files and produces optimized bell assignments for players based on their experience level. The system has three main components:

1. **Backend (Flask + Python)**: Music parsing, bell assignment algorithms, validation
2. **Frontend (Next.js + React)**: Web UI for file upload, player configuration, and arrangement display
3. **Desktop (Electron)**: Desktop wrapper that bundles backend and serves frontend locally

## Build, Test, and Lint Commands

### Backend (Python)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Run tests
pytest tests/                           # All tests
pytest test_services.py                 # Single file
pytest test_services.py::test_function  # Single test
pytest -v                               # Verbose output

# Run server
python run.py  # Starts on http://localhost:5000
```

### Frontend (Next.js)
```bash
cd frontend
npm install

# Development
npm run dev    # http://localhost:3000
npm run build  # Production build
npm start      # Run production build

# Linting
npm run lint
```

### Desktop (Electron)
```bash
cd desktop
npm install

# Development (requires backend + frontend running)
npm run dev

# Build
scripts\build-desktop.bat  # Windows automated build
npm run build:win          # Windows only
npm run build:mac          # macOS only
npm run build:linux        # Linux only

# E2E Tests (Playwright)
npm run test:e2e           # Run all tests
npm run test:e2e:headed    # Watch tests run
npm run test:e2e:ui        # Interactive test UI
npm run test:e2e:debug     # Debug mode

# Icon generation
npm run generate-icons
```

## Architecture

### Bell Assignment Flow
```
Upload File → Parse MIDI/MusicXML → Extract Melody/Harmony
    ↓
Generate 3 Strategies → Resolve Conflicts → Validate & Score
    ↓
Display Results with Hand Assignments and Swap Counts
```

### Three-Tier Strategy System
The core `bell_assignment.py` implements three distinct strategies:
- **experienced_first**: Assigns melody notes to experienced players first
- **balanced**: Distributes notes evenly by frequency across all players
- **min_transitions**: Minimizes hand swaps using `swap_cost_calculator.py`

All strategies respect experience-level constraints (experienced=5 bells, intermediate=3, beginner=2).

### Multi-Process Desktop Architecture
In production, Electron spawns two processes:
1. **Python backend**: Bundled with PyInstaller as `vibebells-backend.exe` in `resources/backend/`
2. **Frontend server**: Static Next.js build served on `http://localhost:3001`

The main process (`main.js`) manages lifecycle, health checks, and IPC. The preload script (`preload.js`) provides secure file dialog APIs to the renderer.

### Data Flow: Assignments Structure
```javascript
{
  'Player 1': {
    bells: ['C4', 'E4', 'G4'],      // All bells for this player
    left_hand: ['C4', 'G4'],         // Even indices in bells array
    right_hand: ['E4']               // Odd indices in bells array
  }
}
```

Hand assignment follows a simple rule: even indices (0, 2, 4...) = left hand, odd indices (1, 3, 5...) = right hand.

### Quality Scoring Components
Each arrangement receives a 0-100 score based on:
- **Distribution (25%)**: Even spread of bells across players
- **Occupancy (25%)**: Percentage of players with bells
- **Utilization (25%)**: Average bells per player vs capacity
- **Melody Coverage (25%)**: Percentage of melody notes assigned

See `arrangement_validator.py` for scoring implementation.

## Key Conventions

### Backend Service Organization
Services follow a pipeline pattern in `backend/app/services/`:
1. `file_handler.py` - File validation and UUID naming
2. `midi_parser.py` / `musicxml_parser.py` - Format-specific parsers
3. `music_parser.py` - Unified parser interface
4. `melody_harmony_extractor.py` - Melody identification
5. `bell_assignment.py` - Core algorithm (3 strategies)
6. `swap_cost_calculator.py` - Hand swap optimization
7. `conflict_resolver.py` - Deduplication and balancing
8. `arrangement_validator.py` - Validation and scoring
9. `swap_counter.py` - Hand transfer counting for export
10. `export_formatter.py` - CSV export formatting
11. `arrangement_generator.py` - Orchestrates the pipeline
12. `routes.py` - Flask API endpoints

Each service is designed to be testable in isolation with well-defined inputs/outputs.

### Frontend Environment Detection
The frontend detects whether it's running in Electron or a browser:
```javascript
import { isElectron } from './lib/electron';

// Conditional rendering
{isElectron() && <ElectronButton />}
{!isElectron() && <BrowserButton />}
```

Use this pattern when adding features that need platform-specific implementations (e.g., file dialogs, window controls).

### Electron IPC Security Pattern
All file operations use the secure IPC bridge in `preload.js`:
```javascript
// Expose APIs via contextBridge (preload.js)
contextBridge.exposeInMainWorld('electron', {
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
  readFile: (filePath) => ipcRenderer.invoke('file:read', filePath)
});

// Use in renderer (page.js)
const filePath = await window.electron.openFileDialog();
const result = await window.electron.readFile(filePath);
```

Never expose `ipcRenderer` directly. Always use `contextBridge` with specific APIs.

### Test File Mocking for E2E
Playwright tests mock file dialogs using a registry pattern:
```javascript
// In test (e2e/02-ui-workflow.spec.js)
await mockFileDialog(electronApp, 'path/to/test.mid');
await page.click('button.electron-file-btn');
// File dialog result is automatically mocked

// Mock implementation (e2e/helpers/electron-helpers.js)
// Registers mock return values in preload.js mock registry
```

This avoids spawning actual file dialogs during headless testing.

### Experience-Level Constraints
When modifying bell assignment logic, always respect the capacity limits defined in `bell_assignment.py`:
- Experienced players: 5 bells maximum
- Intermediate players: 3 bells maximum
- Beginner players: 2 bells maximum

These are enforced in all three strategies. The system will auto-expand player count if capacity is insufficient.

### Backend Port Configuration
Backend is hardcoded to port 5000 in `backend/run.py` and `desktop/main.js`. Changing this requires updates in:
- `backend/run.py` - Flask run configuration
- `desktop/main.js` - BACKEND_PORT constant
- `desktop/playwright.config.js` - baseURL

Frontend development server uses port 3000, production desktop uses port 3001.

## Reference Documentation

- **Algorithm Design**: `bell-assignment-strategy.md` - Original algorithm specification
- **E2E Testing**: `E2E_TESTING_SUMMARY.md` - Playwright test infrastructure
- **Project Status**: `PROJECT_STATUS.md` - Architecture and current state
- **Desktop Build**: `desktop/README.md` - Build instructions for all platforms

## Common Pitfalls

### Windows Path Handling
Use `path.join()` or `path.resolve()` instead of string concatenation. The codebase runs on Windows, macOS, and Linux.

### React 'use client' Directive
All interactive components in `frontend/app/` must have `'use client';` at the top. Next.js App Router uses server components by default.

### Electron App Cleanup in Tests
Always use the helper functions in `e2e/helpers/electron-helpers.js` for test cleanup. Raw `electronApp.close()` can leave zombie processes. Use `cleanupElectronApp()` instead.

### PyInstaller Hidden Imports
When adding new Python dependencies, update `backend/vibebells-backend.spec` with hidden imports. Flask extensions and music21 submodules often need explicit inclusion.

### CSV Injection Prevention
The CSV export in `export_formatter.py` sanitizes cell values to prevent formula injection. When adding new exported fields, use the `_sanitize_csv_value()` helper.
