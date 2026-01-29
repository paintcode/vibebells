from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.music_parser import MusicParser

class ArrangementGenerator:
    """Generate bell arrangements based on music data and player configuration"""
    
    def generate(self, music_data, players):
        """Generate multiple arrangement options
        
        Args:
            music_data: Dict with parsed music info including melody/harmony
            players: List of player dicts with 'name' and 'experience'
            
        Returns:
            List of arrangements with assignments
            
        Raises:
            ValueError: If validation fails
        """
        
        if not music_data or 'unique_notes' not in music_data:
            raise ValueError("Invalid music data")
        
        if not players:
            raise ValueError("At least one player is required")
        
        if not music_data['unique_notes']:
            raise ValueError("No notes found in music file")
        
        # Convert MIDI pitches to note names
        unique_notes = [MusicParser.pitch_to_note_name(p) for p in music_data['unique_notes']]
        
        # Prioritize melody notes if available
        melody_notes = []
        if music_data.get('melody_pitches'):
            melody_notes = [MusicParser.pitch_to_note_name(p) for p in music_data['melody_pitches']]
        
        # Generate multiple arrangements with different strategies
        arrangements = []
        strategies = ['experienced_first', 'balanced', 'min_transitions']
        
        for strategy in strategies:
            try:
                assignment = BellAssignmentAlgorithm.assign_bells(
                    unique_notes, 
                    players, 
                    strategy=strategy,
                    priority_notes=melody_notes
                )
                arrangements.append({
                    'strategy': strategy,
                    'assignments': assignment
                })
            except Exception as e:
                # Log error but continue with other strategies
                import logging
                logging.warning(f"Failed to generate {strategy} arrangement: {str(e)}")
        
        if not arrangements:
            raise Exception("Failed to generate any arrangements")
        
        return arrangements


