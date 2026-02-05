# Vibebells - Handbell Arrangement Generator

A web application that generates handbell arrangements for songs. Upload a MIDI or MusicXML file, configure players by experience level, and get multiple arrangement strategies with quality scoring and sustainability recommendations.

> **Note**: As of February 2026, the frontend has been migrated from deprecated Create React App to **Next.js 15** with App Router for better performance, maintainability, and long-term support.

## Features

- **Music Parsing**: Supports MIDI and MusicXML formats
- **Multiple Strategies**: Three arrangement algorithms (experienced-first, balanced, min-transitions)
- **Quality Scoring**: 0-100 score based on distribution, occupancy, utilization, and melody coverage
- **Sustainability Analysis**: Bell spacing and reachability recommendations for player comfort
- **Conflict Resolution**: Automatic deduplication and balancing of arrangements
- **Web UI**: Next.js 15 with App Router, modern React 19 interface with real-time feedback
- **Multi-Bell Support**: Players can manage up to 5 bells with hand assignment optimization
- **Experience-Level Constraints**: Automatic player expansion when capacity is insufficient

## Project Structure

```
vibebells/
├── frontend/                 # Next.js 15 application (App Router)
│   ├── app/
│   │   ├── components/
│   │   │   ├── FileUpload.js       # Music file upload
│   │   │   ├── FileUpload.css
│   │   │   ├── PlayerConfig.js     # Player configuration
│   │   │   ├── PlayerConfig.css
│   │   │   ├── ArrangementDisplay.js   # Results display
│   │   │   └── ArrangementDisplay.css
│   │   ├── layout.js         # Root layout component
│   │   ├── page.js           # Home page component
│   │   ├── page.css
│   │   └── globals.css       # Global styles
│   ├── public/
│   ├── next.config.js
│   ├── package.json
│   └── .gitignore
├── backend/                  # Flask API
│   ├── app/
│   │   ├── services/
│   │   │   ├── file_handler.py
│   │   │   ├── midi_parser.py
│   │   │   ├── musicxml_parser.py
│   │   │   ├── melody_harmony_extractor.py
│   │   │   ├── music_parser.py
│   │   │   ├── bell_assignment.py
│   │   │   ├── conflict_resolver.py
│   │   │   ├── arrangement_validator.py
│   │   │   ├── arrangement_generator.py
│   │   │   ├── routes.py
│   │   │   └── __init__.py
│   │   ├── config.py
│   │   └── __init__.py
│   ├── run.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   └── venv/                # Virtual environment (created during setup)
├── bell-assignment-strategy.md  # Algorithm documentation
└── README.md
```

## Prerequisites

- **Node.js** 18+ and **npm** (for frontend - Next.js 15 requires Node 18+)
- **Python** 3.8+ (for backend)
- MIDI or MusicXML files to arrange

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env if needed (default settings should work)
   ```

5. **Start the Flask server**:
   ```bash
   python run.py
   ```
   Server runs on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory** (in a new terminal):
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the Next.js development server**:
   ```bash
   npm run dev
   ```
   App opens at `http://localhost:3000`

4. **Build for production**:
   ```bash
   npm run build
   npm start
   ```

## Running the Application

### Full Setup (First Time)

```bash
# Terminal 1: Start Backend
cd backend
python -m venv venv
venv\Scripts\activate  # or: source venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
python run.py

# Terminal 2: Start Frontend
cd frontend
npm install
npm run dev
```

### Quick Start (After Initial Setup)

```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate  # or: source venv/bin/activate (macOS/Linux)
python run.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

## Using the Application

1. **Upload Music**: Click "Choose File" and select a MIDI or MusicXML file (max 5MB)
2. **Configure Players**: Enter number of players (1-20)
3. **Generate Arrangements**: Click "Generate Arrangements"
4. **Review Results**: 
   - View quality score (0-100)
   - Check bell assignments for each player
   - Read sustainability recommendations
   - Compare different strategies

## API Endpoints

### POST `/api/generate-arrangements`

Generate arrangements for a music file.

**Request**:
```json
{
  "file": <binary MIDI/MusicXML file>,
  "num_players": 4,
  "strategy": "balanced"
}
```

**Strategy options**: `experienced_first`, `balanced`, `min_transitions`

**Response**:
```json
{
  "arrangements": [
    {
      "strategy": "balanced",
      "assignments": {
        "Player 1": ["C4", "D4"],
        "Player 2": ["E4"],
        "Player 3": ["G4", "A4"],
        "Player 4": []
      },
      "quality_score": 82,
      "validation": {
        "valid": true,
        "issues": [],
        "warnings": []
      },
      "sustainability": {
        "sustainable": true,
        "recommendations": ["Bell spacing optimal"]
      }
    }
  ],
  "metadata": {
    "total_notes": 32,
    "unique_pitches": 12,
    "duration_seconds": 120
  }
}
```

## Configuration

### Backend (.env)

```
FLASK_ENV=development
FLASK_DEBUG=1
MAX_FILE_SIZE=5242880  # 5MB in bytes
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Bell Assignment Constraints

- **Max bells per player**: Dependent on experience level (experienced=5, intermediate=3, beginner=2)
- **Simultaneous bells**: Maximum 2 per hand (hard constraint)
- **Player count**: 1-20 (auto-expanded if insufficient capacity)
- **File size limit**: 5MB
- **Supported formats**: MIDI, MusicXML (.xml, .musicxml)

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

### Project Phases

- **Phase 1**: ✅ Core infrastructure (Flask, React, file handling)
- **Phase 2**: ✅ Music parsing (MIDI, MusicXML)
- **Phase 3**: ✅ Algorithm implementation (3 strategies, quality scoring, validation)
- **Phase 4**: ✅ Multi-bell assignment with hand optimization
- **Phase 5**: ✅ Hand swap optimization (minimize bell transfers)
- **Phase 6**: ✅ Experience-level constraints and player expansion
- **Phase 6.5**: ✅ Next.js 15 migration from deprecated Create React App
- **Phase 7**: 🔄 Export features (PDF, player parts, sheet music)
- **Phase 8**: 📋 Testing suite (unit, integration, end-to-end)

### Key Documentation

- [`bell-assignment-strategy.md`](bell-assignment-strategy.md) - Algorithm design
- [`PHASE3_SUMMARY.md`](PHASE3_SUMMARY.md) - Latest implementation details
- [`PROJECT_STATUS.md`](PROJECT_STATUS.md) - Current status and roadmap

### Running Tests

(Tests will be added in Phase 5)

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

- **Frontend**: Next.js 15 (App Router), React 19, CSS Grid/Flexbox
- **Backend**: Flask, Python 3.8+
- **Music Parsing**: mido (MIDI), music21 (MusicXML)
- **File Upload**: Multipart form data
- **CORS**: Flask-CORS

## License

[Add license information]

## Contributing

[Add contribution guidelines]

## Support

For issues or questions, please refer to the documentation files or check the browser console for error messages.
