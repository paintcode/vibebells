"""
MIDI File Parser
Extracts notes, timing, and structure from MIDI files.
"""

import midi
import logging

logger = logging.getLogger(__name__)

class MIDIParser:
    """Parse MIDI files"""
    
    @staticmethod
    def parse(filepath):
        """
        Parse MIDI file and extract notes with timing information.
        
        Args:
            filepath: Path to MIDI file
            
        Returns:
            Dict with notes list and metadata
            
        Raises:
            Exception: If file cannot be parsed
        """
        try:
            pattern = midi.read_midifile(filepath)
            
            notes = []
            tempo_microseconds = 500000  # Default: 120 BPM
            
            # First pass: extract tempo
            for track in pattern:
                for event in track:
                    if isinstance(event, midi.SetTempoEvent):
                        tempo_microseconds = event.data
                        break
            
            # Convert microseconds per beat to BPM
            # BPM = 60,000,000 / microseconds per beat
            tempo_bpm = 60000000 / tempo_microseconds if tempo_microseconds > 0 else 120
            
            # Second pass: pair NoteOn/NoteOff events to get durations
            for track in pattern:
                current_tick = 0
                note_on_map = {}  # Map pitch to (velocity, tick_on)
                
                for event in track:
                    current_tick += event.tick
                    
                    if isinstance(event, midi.NoteOnEvent):
                        if event.velocity > 0:
                            # Store note on for later pairing
                            if event.pitch not in note_on_map:
                                note_on_map[event.pitch] = (event.velocity, current_tick)
                        else:
                            # NoteOn with velocity 0 = NoteOff
                            if event.pitch in note_on_map:
                                velocity, tick_on = note_on_map[event.pitch]
                                duration = current_tick - tick_on
                                notes.append({
                                    'pitch': event.pitch,
                                    'velocity': velocity,
                                    'time': tick_on,
                                    'offset': tick_on,
                                    'duration': max(1, duration)  # Minimum 1 tick
                                })
                                del note_on_map[event.pitch]
                    
                    elif isinstance(event, midi.NoteOffEvent):
                        if event.pitch in note_on_map:
                            velocity, tick_on = note_on_map[event.pitch]
                            duration = current_tick - tick_on
                            notes.append({
                                'pitch': event.pitch,
                                'velocity': velocity,
                                'time': tick_on,
                                'offset': tick_on,
                                'duration': max(1, duration)
                            })
                            del note_on_map[event.pitch]
                
                # Handle any remaining NoteOn events without NoteOff
                for pitch, (velocity, tick_on) in note_on_map.items():
                    notes.append({
                        'pitch': pitch,
                        'velocity': velocity,
                        'time': tick_on,
                        'offset': tick_on,
                        'duration': 1  # Default if no NoteOff
                    })
            
            if not notes:
                raise ValueError("No notes found in MIDI file")
            
            # Calculate unique notes and frequencies
            pitches = [n['pitch'] for n in notes]
            unique_pitches = list(set(pitches))
            
            logger.info(f"MIDI parse: {len(unique_pitches)} unique notes, {len(notes)} events, tempo {tempo_bpm:.1f} BPM")
            
            return {
                'notes': notes,
                'unique_notes': unique_pitches,
                'note_count': len(unique_pitches),
                'total_note_events': len(notes),
                'format': 'midi',
                'tempo': int(tempo_bpm)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse MIDI file: {str(e)}", exc_info=True)
            raise Exception(f"Failed to parse MIDI file: {str(e)}")
    
    @staticmethod
    def pitch_to_note_name(pitch):
        """Convert MIDI pitch number to note name (e.g., 60 -> C4)"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note = note_names[pitch % 12]
        return f"{note}{octave}"
