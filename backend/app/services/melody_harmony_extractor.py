"""
Melody and Harmony Extraction Service

Identifies melody notes (primary notes) vs harmony notes (supporting notes)
based on timing, frequency, and pitch patterns.
"""

class MelodyHarmonyExtractor:
    """Extract melody and harmony from parsed music data"""
    
    @staticmethod
    def extract(notes):
        """
        Extract melody and harmony from notes.
        
        Heuristics:
        - Melody: notes with longest duration or highest pitch in each time group
        - Harmony: supporting notes that occur simultaneously
        
        Args:
            notes: List of note dicts with 'pitch', 'duration', 'offset'
            
        Returns:
            Dict with 'melody' and 'harmony' note lists
        """
        
        if not notes:
            return {'melody': [], 'harmony': []}
        
        # Group notes by offset (simultaneous notes)
        time_groups = {}
        for note in notes:
            offset = note.get('offset', 0)
            if offset not in time_groups:
                time_groups[offset] = []
            time_groups[offset].append(note)
        
        melody = []
        harmony = []
        
        # For each time group, identify melody vs harmony
        for offset in sorted(time_groups.keys()):
            group = time_groups[offset]
            
            if len(group) == 1:
                # Single note at this time = melody
                melody.append(group[0])
            else:
                # Multiple notes: highest pitch is likely melody
                # Sort by pitch descending
                sorted_group = sorted(group, key=lambda n: n.get('pitch', 0), reverse=True)
                
                # First note (highest) is melody
                melody.append(sorted_group[0])
                
                # Rest are harmony
                harmony.extend(sorted_group[1:])
        
        return {
            'melody': melody,
            'harmony': harmony,
            'melody_pitches': list(set([n['pitch'] for n in melody])),
            'harmony_pitches': list(set([n['pitch'] for n in harmony]))
        }
    
    @staticmethod
    def get_note_frequencies(notes):
        """Get frequency count for each note"""
        frequencies = {}
        for note in notes:
            pitch = note.get('pitch')
            if pitch:
                frequencies[pitch] = frequencies.get(pitch, 0) + 1
        return frequencies
