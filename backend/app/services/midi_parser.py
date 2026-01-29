"""
MIDI File Parser
Extracts notes, timing, and structure from MIDI files.
"""

import mido
import logging

logger = logging.getLogger(__name__)

class MIDIParser:
    """Parse MIDI files using mido"""
    
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
            mid = mido.MidiFile(filepath)
            
            notes = []
            tempo_microseconds = 500000  # Default: 120 BPM
            ticks_per_beat = mid.ticks_per_beat
            
            # First pass: extract tempo and collect all note events
            note_on_events = {}  # {(track_idx, pitch): (velocity, tick)}
            
            for track_idx, track in enumerate(mid.tracks):
                current_tick = 0
                
                for msg in track:
                    current_tick += msg.time
                    
                    # Extract tempo
                    if msg.type == 'set_tempo':
                        tempo_microseconds = msg.tempo
                    
                    # Collect note on events
                    elif msg.type == 'note_on' and msg.velocity > 0:
                        key = (track_idx, msg.note)
                        note_on_events[key] = (msg.velocity, current_tick)
                    
                    # Process note off events or note_on with velocity 0
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        key = (track_idx, msg.note)
                        if key in note_on_events:
                            velocity, tick_on = note_on_events[key]
                            duration = current_tick - tick_on
                            notes.append({
                                'pitch': msg.note,
                                'velocity': velocity,
                                'time': tick_on,
                                'offset': tick_on,
                                'duration': max(1, duration)  # Minimum 1 tick
                            })
                            del note_on_events[key]
            
            # Handle any remaining note_on events without matching note_off
            for (track_idx, pitch), (velocity, tick_on) in note_on_events.items():
                notes.append({
                    'pitch': pitch,
                    'velocity': velocity,
                    'time': tick_on,
                    'offset': tick_on,
                    'duration': 1  # Default if no note_off
                })
            
            if not notes:
                raise ValueError("No notes found in MIDI file")
            
            # Convert microseconds per beat to BPM
            # BPM = 60,000,000 / microseconds per beat
            tempo_bpm = 60000000 / tempo_microseconds if tempo_microseconds > 0 else 120
            
            # Calculate unique notes
            pitches = [n['pitch'] for n in notes]
            unique_pitches = list(set(pitches))
            
            logger.info(f"MIDI parse: {len(unique_pitches)} unique notes, {len(notes)} events, tempo {tempo_bpm:.1f} BPM, ticks_per_beat {ticks_per_beat}")
            
            return {
                'notes': notes,
                'unique_notes': unique_pitches,
                'note_count': len(unique_pitches),
                'total_note_events': len(notes),
                'format': 'midi',
                'tempo': int(tempo_bpm),
                'ticks_per_beat': ticks_per_beat
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
