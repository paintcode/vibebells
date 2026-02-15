<div align="center">
  <img src="desktop/assets/icon-256.png" alt="Vibebells Icon" width="128" height="128">
  <h1>Vibebells - Handbell Arrangement Generator</h1>
  <p><strong>Automated handbell arrangements from MIDI and MusicXML files</strong></p>
  
  [![Desktop App](https://img.shields.io/badge/Desktop-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=flat-square)](desktop/)
  [![Tests](https://img.shields.io/badge/Tests-16%2F16%20Passing-success?style=flat-square)](#testing)
  [![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
</div>

---

## Overview

A desktop and web application that generates handbell arrangements for songs. Upload a MIDI or MusicXML file, configure players by experience level, and get multiple arrangement strategies with quality scoring and sustainability recommendations.

## ✨ Features

- 🖥️ **Desktop Application**: Native Windows, macOS, and Linux apps with Electron
- 🎵 **Music Parsing**: Supports MIDI and MusicXML formats
- 🎯 **Multiple Strategies**: Three arrangement algorithms (experienced-first, balanced, min-transitions)
- 📊 **Quality Scoring**: 0-100 score based on distribution, occupancy, utilization, and melody coverage
- 🔍 **Sustainability Analysis**: Bell spacing and reachability recommendations for player comfort
- ⚖️ **Conflict Resolution**: Automatic deduplication and balancing of arrangements
- 💎 **Modern UI**: Next.js 15 with App Router and React 19
- 🔔 **Multi-Bell Support**: Players can manage up to 5 bells with hand assignment optimization
- 🔄 **Hand Swap Tracking**: Displays swap counts for each player to minimize bell transfers
- 👥 **Experience-Level Constraints**: Automatic player expansion when capacity is insufficient
- 📥 **CSV Export**: Download arrangements for printing or sharing
- ✅ **Comprehensive Testing**: 16/16 E2E tests passing with Playwright

## 🚀 Getting Started

### Desktop Application (Recommended)

Download the latest release for your platform:

- **Windows**: `Vibebells Setup 1.0.0.exe` or `Vibebells 1.0.0.exe` (portable)
- **macOS**: `Vibebells-1.0.0.dmg` (coming soon)
- **Linux**: `Vibebells-1.0.0.AppImage` or `.deb` (coming soon)

Double-click to install and run. The app includes a bundled Python backend (no installation needed), native file dialogs and menus, and works completely offline.

See [desktop/README.md](desktop/README.md) for build instructions.

### Web Development Setup

**Prerequisites:**
- Node.js 18+ and npm
- Python 3.8+
- MIDI or MusicXML files to arrange

**First-time setup:**

1. **Backend** (Terminal 1):
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows - or: source venv/bin/activate (macOS/Linux)
   pip install -r requirements.txt
   python run.py
   ```
   Backend runs on http://localhost:5000

2. **Frontend** (Terminal 2):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend runs on http://localhost:3000

**Subsequent runs:**
```bash
# Terminal 1
cd backend && venv\Scripts\activate && python run.py

# Terminal 2
cd frontend && npm run dev
```

## 📖 Using the Application

1. **Upload Music**: Click "Choose File" and select a MIDI or MusicXML file (max 5MB)
   - Supported formats: MIDI (.mid, .midi), MusicXML (.xml, .musicxml)
2. **Configure Players**: Adjust number of players (default: 8) and set experience levels
   - Experience levels: Beginner (2 bells max), Intermediate (3 bells max), Experienced (5 bells max)
3. **Generate Arrangements**: Click "Generate Arrangements"
4. **Review Results**: 
   - View quality score (0-100)
   - Check bell assignments and hand positions for each player
   - Review swap counts to understand bell transfer frequency
   - Read sustainability recommendations
   - Compare different strategies
5. **Export**: Download arrangement as CSV for printing or sharing

## Configuration

### Backend (.env)

```
FLASK_ENV=development
FLASK_DEBUG=1
MAX_FILE_SIZE=5242880  # 5MB in bytes
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Bell Assignment Constraints

- **Max bells per player**: Up to 5 bells (dependent on experience level: experienced=5, intermediate=3, beginner=2)
- **Simultaneous bells**: Maximum 2 per hand (hard constraint)
- **Player count**: 1-20 (auto-expanded if insufficient capacity)
- **File size limit**: 5MB
- **Supported formats**: MIDI (.mid, .midi), MusicXML (.xml, .musicxml)

## Troubleshooting

### Backend won't start
```bash
# Check Python version (need 3.8+)
python --version

# Verify virtual environment activation
python -c "import sys; print(sys.prefix)"  # Should show venv path

# Try reinstalling dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Frontend shows "Connection refused"
- Ensure backend is running on port 5000
- Check CORS settings in `.env` (should include `http://localhost:3000`)
- Clear browser cache and restart frontend
- Check browser console (F12) for network errors

### Next.js dev server won't start
```bash
# Check Node version (need 18+)
node --version

# Clear Next.js cache
rm -rf .next  # or: Remove-Item .next -Recurse (Windows)

# Reinstall dependencies
rm package-lock.json node_modules  # or Windows equivalent
npm install
npm run dev
```

### File upload fails
- Check file size (max 5MB)
- Verify file format (MIDI or MusicXML)
- Check browser console for error messages

### Quality scores seem off
- Ensure all pitches are valid (scientific pitch notation)
- Check melody extraction heuristics
- See `arrangement_validator.py` for scoring formula

## Development

### Testing

**Desktop E2E Tests** (16/16 passing - 100%):
```bash
cd desktop
npm install
npm test           # Run all tests
npm run test:headed  # Watch tests run
npm run test:ui     # Interactive UI
```

**Backend Unit Tests**:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pytest tests/
```

Test coverage:
- 5 API integration tests (health, generation, strategies, export)
- 11 UI workflow tests (launch, upload, config, generation, export)
- 13 SwapCounter unit tests
- 11 ExportFormatter unit tests
- 2 multi-bell integration tests

See [E2E_TESTING_SUMMARY.md](E2E_TESTING_SUMMARY.md) and [TESTING_SUMMARY.md](TESTING_SUMMARY.md) for details.

### Key Documentation

- [`bell-assignment-strategy.md`](bell-assignment-strategy.md) - Algorithm design
- [`desktop/README.md`](desktop/README.md) - Desktop app build and configuration
- [`E2E_TESTING_SUMMARY.md`](E2E_TESTING_SUMMARY.md) - E2E testing infrastructure
- [`TESTING_SUMMARY.md`](TESTING_SUMMARY.md) - Production testing results

## Architecture

### Backend Flow

```
Upload File
    ↓
File Validation
    ↓
MIDI/MusicXML Parsing → Extract melody/harmony
    ↓
Bell Assignment (3 strategies)
    ↓
Conflict Resolution → Deduplication & Balancing
    ↓
Arrangement Validation → Quality Scoring (0-100)
    ↓
Sustainability Check → Recommendations
    ↓
Return to Frontend
```

### Quality Score Calculation

- **Distribution (25%)**: Even bell spread across players
- **Occupancy (25%)**: Player utilization (0-2 bells)
- **Utilization (25%)**: Ratio of used players to total players
- **Melody (25%)**: Coverage of melody notes in arrangement

Total: 0-100 (higher is better)

## Technology Stack

- **Desktop**: Electron, Electron Builder (NSIS, portable, DMG, AppImage)
- **Frontend**: Next.js (App Router), React, CSS Grid/Flexbox
- **Backend**: Flask, Python 3.8+, PyInstaller (standalone executable)
- **Music Parsing**: mido (MIDI), music21 (MusicXML)
- **Testing**: Playwright (E2E), pytest (unit/integration)
- **File Upload**: Multipart form data
- **CORS**: Flask-CORS

## License

MIT License

Copyright (c) 2026 Marie Danenhower

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For help, feedback, or to report issues:
- **GitHub Issues**: https://github.com/paintcode/vibebells
- **Documentation**: See the docs in this repository
