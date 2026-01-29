"""
MusicXML File Parser
Extracts notes, timing, chords, and structure from MusicXML files.
"""

from music21 import converter, note, chord

class MusicXMLParser:
    """Parse MusicXML files"""
    
    @staticmethod
    def parse(filepath):
        """
        Parse MusicXML file and extract notes with timing and chord information.
        
        Args:
            filepath: Path to MusicXML file
            
        Returns:
            Dict with notes list and metadata
            
        Raises:
            Exception: If file cannot be parsed
        """
        try:
            score = converter.parse(filepath)
            
            notes = []
            chords_info = []
            
            # Extract all note elements
            for element in score.flatten().notesAndRests:
                if isinstance(element, chord.Chord):
                    # Handle chords
                    chord_pitches = [p.midi for p in element.pitches]
                    chord_entry = {
                        'pitches': chord_pitches,
                        'duration': element.duration.quarterLength,
                        'offset': element.offset,
                        'type': 'chord'
                    }
                    chords_info.append(chord_entry)
                    
                    # Add individual notes from chord
                    for pitch in element.pitches:
                        notes.append({
                            'pitch': pitch.midi,
                            'duration': element.duration.quarterLength,
                            'offset': element.offset,
                            'is_chord_member': True
                        })
                
                elif isinstance(element, note.Note):
                    # Handle single notes
                    notes.append({
                        'pitch': element.pitch.midi,
                        'duration': element.duration.quarterLength,
                        'offset': element.offset,
                        'is_chord_member': False
                    })
            
            if not notes:
                raise ValueError("No notes found in MusicXML file")
            
            # Calculate unique notes
            pitches = [n['pitch'] for n in notes]
            unique_pitches = list(set(pitches))
            
            # Get tempo info - search for MetronomeMark elements
            tempo = 120  # Default tempo in BPM
            try:
                from music21 import tempo as tempo_module
                metronome_marks = score.flatten().getElementsByClass(tempo_module.MetronomeMark)
                if metronome_marks:
                    tempo = int(metronome_marks[0].number)
            except Exception:
                # If MetronomeMark extraction fails, keep default
                pass
            
            return {
                'notes': notes,
                'unique_notes': unique_pitches,
                'note_count': len(unique_pitches),
                'total_note_events': len(notes),
                'chords': chords_info,
                'format': 'musicxml',
                'tempo': tempo
            }
            
        except Exception as e:
            raise Exception(f"Failed to parse MusicXML file: {str(e)}")
    
    @staticmethod
    def pitch_to_note_name(pitch):
        """Convert MIDI pitch number to note name (e.g., 60 -> C4)"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note_name = note_names[pitch % 12]
        return f"{note_name}{octave}"
