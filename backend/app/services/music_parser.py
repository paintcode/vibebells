"""
Main Music Parser
Routes parsing to appropriate format-specific parsers.
"""

from app.services.file_handler import FileHandler
from app.services.midi_parser import MIDIParser
from app.services.musicxml_parser import MusicXMLParser
from app.services.melody_harmony_extractor import MelodyHarmonyExtractor

class MusicParser:
    """Parse MIDI and MusicXML files to extract notes and structure"""
    
    def parse(self, filepath):
        """Parse music file and extract notes with melody/harmony separation"""
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
        """Parse MIDI file and extract notes"""
        try:
            data = MIDIParser.parse(filepath)
            
            # Extract melody and harmony
            melody_harmony = MelodyHarmonyExtractor.extract(data['notes'])
            
            # Get frequencies
            frequencies = MelodyHarmonyExtractor.get_note_frequencies(data['notes'])
            
            return {
                'notes': data['notes'],
                'unique_notes': data['unique_notes'],
                'note_count': data['note_count'],
                'total_note_events': data['total_note_events'],
                'melody_pitches': melody_harmony['melody_pitches'],
                'harmony_pitches': melody_harmony['harmony_pitches'],
                'frequencies': frequencies,
                'format': 'midi',
                'tempo': data.get('tempo', 120)
            }
        except Exception as e:
            raise Exception(f"Error parsing MIDI file: {str(e)}")
    
    def _parse_musicxml(self, filepath):
        """Parse MusicXML file and extract notes"""
        try:
            data = MusicXMLParser.parse(filepath)
            
            # Extract melody and harmony
            melody_harmony = MelodyHarmonyExtractor.extract(data['notes'])
            
            # Get frequencies
            frequencies = MelodyHarmonyExtractor.get_note_frequencies(data['notes'])
            
            return {
                'notes': data['notes'],
                'unique_notes': data['unique_notes'],
                'note_count': data['note_count'],
                'total_note_events': data['total_note_events'],
                'melody_pitches': melody_harmony['melody_pitches'],
                'harmony_pitches': melody_harmony['harmony_pitches'],
                'frequencies': frequencies,
                'chords': data.get('chords', []),
                'format': 'musicxml',
                'tempo': data.get('tempo', 120)
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
    
    @staticmethod
    def note_name_to_pitch(note_name):
        """Convert note name to MIDI pitch number"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Parse note name (e.g., "C4", "C#5", "Db3")
        # Handle both sharp (#) and flat (b) notation
        if len(note_name) < 2:
            raise ValueError(f"Invalid note name: {note_name}")
        
        # Find where octave number starts
        note_part = note_name[:-1]
        octave = int(note_name[-1])
        
        # Normalize note (handle flats as sharps)
        note_part = note_part.replace('b', '#')
        
        # For flat notation, adjust pitch
        if 'b' in note_name:
            if note_part in note_names:
                pitch = note_names.index(note_part)
                pitch -= 1  # Flat lowers the note
                if pitch < 0:
                    pitch += 12
                    octave -= 1
            else:
                raise ValueError(f"Invalid note name: {note_name}")
        else:
            if note_part not in note_names:
                raise ValueError(f"Invalid note name: {note_name}")
            pitch = note_names.index(note_part)
        
        return (octave + 1) * 12 + pitch


