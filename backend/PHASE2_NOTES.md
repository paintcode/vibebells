# Phase 2: Music Parsing Implementation

## Overview
Phase 2 implements comprehensive music file parsing for both MIDI and MusicXML formats. The system extracts note data, identifies melody vs. harmony, and calculates note frequencies for bell arrangement generation.

## Components

### 1. MIDI Parser (`midi_parser.py`)
- Extracts note events from MIDI files
- Captures velocity, timing, and pitch information
- Handles tempo events
- Converts MIDI pitch numbers to note names (e.g., 60 → C4)

**Key Features:**
- Velocity filtering (only velocity > 0 counts as note on)
- Tempo extraction from MIDI SetTempoEvent
- Tick-based timing preservation

### 2. MusicXML Parser (`musicxml_parser.py`)
- Uses music21 library for robust parsing
- Extracts both single notes and chords
- Captures duration information
- Handles complex musical structures

**Key Features:**
- Chord detection and member note extraction
- Duration in quarter lengths (for timing analysis)
- Tempo extraction from score elements

### 3. Melody/Harmony Extractor (`melody_harmony_extractor.py`)
- Separates melody notes from harmony notes
- Uses intelligent heuristics:
  - Single notes at a time = melody
  - Multiple simultaneous notes: highest pitch = melody
  - Other notes = harmony
- Calculates note frequencies

**Output includes:**
- Melody pitch list (primary melodic line)
- Harmony pitch list (supporting voices)
- Frequency counts for each note

### 4. Main Music Parser (`music_parser.py`)
- Routes to appropriate format-specific parser
- Integrates melody/harmony extraction
- Returns comprehensive music data structure

**Returned Data Structure:**
```python
{
    'notes': [...],                    # All note events
    'unique_notes': [...],             # List of unique MIDI pitches
    'note_count': int,                 # Count of unique notes
    'melody_pitches': [...],           # Melody notes only
    'harmony_pitches': [...],          # Harmony notes only
    'frequencies': {...},              # Count per note
    'format': 'midi' or 'musicxml',
    'tempo': int                       # BPM
}
```

## Integration with Bell Assignment

The arrangement generator now uses melody information to prioritize melody note assignment:
- Experienced players get melody notes first
- Intermediate/beginner players get supporting harmony notes
- Three strategies respect melody priorities:
  1. **experienced_first**: Priority notes to experienced players
  2. **balanced**: Distribute priority notes evenly
  3. **min_transitions**: Minimize player switches for priority notes

## Testing

To test the MIDI parser:
```bash
cd backend
python create_test_midi.py  # Creates test_song.mid
python -c "from app.services.midi_parser import MIDIParser; data = MIDIParser.parse('test_song.mid'); print(data)"
```

## Supported Formats

| Format | Extension | Parser | Validation |
|--------|-----------|--------|-----------|
| MIDI | .mid, .midi | MIDIParser | File must contain note events |
| MusicXML | .musicxml, .xml | MusicXMLParser | Must parse with music21 |

## Error Handling

- Empty files: Raises "No notes found"
- Invalid format: Raises specific error from parser
- Malformed data: Caught and re-raised with context
- Missing melody: Gracefully handles files with only chords

## Performance Notes

- MIDI parsing: O(n) where n = number of events
- MusicXML parsing: Depends on music21 (generally O(n × m) where m = complexity)
- Memory: Stores all notes in memory (suitable for typical songs < 1000 notes)
