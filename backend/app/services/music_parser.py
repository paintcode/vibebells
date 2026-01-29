import midi
from music21 import converter
from app.services.file_handler import FileHandler

class MusicParser:
    """Parse MIDI and MusicXML files to extract notes and structure"""
    
    def parse(self, filepath):
        """Parse music file and extract melody and harmony"""
        try:
            file_type = FileHandler.get_file_type(filepath)
        except ValueError as e:
            raise ValueError(f"Invalid file: {str(e)}")
        
        if file_type == 'midi':
            return self._parse_midi(filepath)
        elif file_type == 'musicxml':
            return self._parse_musicxml(filepath)
        else:
            raise ValueError(f"Unknown file type: {file_type}")
    
    def _parse_midi(self, filepath):
        """Parse MIDI file"""
        try:
            pattern = midi.read_midifile(filepath)
            
            notes = []
            for track in pattern:
                for event in track:
                    if isinstance(event, midi.NoteOnEvent) and event.velocity > 0:
                        notes.append({
                            'pitch': event.pitch,
                            'velocity': event.velocity,
                            'time': event.tick
                        })
            
            if not notes:
                raise ValueError("No notes found in MIDI file")
            
            unique_pitches = list(set([n['pitch'] for n in notes]))
            
            return {
                'notes': notes,
                'unique_notes': unique_pitches,
                'note_count': len(unique_pitches),
                'format': 'midi'
            }
        except Exception as e:
            raise Exception(f"Error parsing MIDI file: {str(e)}")
    
    def _parse_musicxml(self, filepath):
        """Parse MusicXML file"""
        try:
            score = converter.parse(filepath)
            
            notes = []
            for element in score.flatten().notes:
                if hasattr(element, 'pitch'):
                    notes.append({
                        'pitch': element.pitch.midi,
                        'duration': element.duration.quarterLength,
                        'offset': element.offset
                    })
            
            if not notes:
                raise ValueError("No notes found in MusicXML file")
            
            unique_pitches = list(set([n['pitch'] for n in notes]))
            
            return {
                'notes': notes,
                'unique_notes': unique_pitches,
                'note_count': len(unique_pitches),
                'format': 'musicxml'
            }
        except Exception as e:
            raise Exception(f"Error parsing MusicXML file: {str(e)}")
    
    @staticmethod
    def pitch_to_note_name(pitch):
        """Convert MIDI pitch number to note name"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note = note_names[pitch % 12]
        return f"{note}{octave}"

