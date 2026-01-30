from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.music_parser import MusicParser
from app.services.conflict_resolver import ConflictResolver
from app.services.arrangement_validator import ArrangementValidator
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class ArrangementGenerator:
    """Generate bell arrangements based on music data and player configuration"""
    
    def generate(self, music_data, players):
        """Generate multiple arrangement options with validation
        
        Args:
            music_data: Dict with parsed music info including melody/harmony
            players: List of player dicts with 'name' and 'experience'
            
        Returns:
            List of arrangements with assignments, scores, and metadata
            
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
        
        logger.info(f"Generating arrangements for {len(unique_notes)} unique notes with {len(players)} players")
        
        # Generate multiple arrangements with different strategies
        arrangements = []
        strategies = [
            ('experienced_first', 'Prioritize melody for experienced players'),
            ('balanced', 'Evenly distribute melody notes'),
            ('min_transitions', 'Minimize player transitions'),
        ]
        
        for strategy, description in strategies:
            try:
                # Build config dict from Flask config
                config = {
                    'MAX_BELLS_PER_PLAYER': current_app.config.get('MAX_BELLS_PER_PLAYER', 8),
                    'HAND_GAP_THRESHOLD_BEATS': current_app.config.get('HAND_GAP_THRESHOLD_BEATS', 1.0)
                }
                
                assignment = BellAssignmentAlgorithm.assign_bells(
                    unique_notes, 
                    players, 
                    strategy=strategy,
                    priority_notes=melody_notes,
                    config=config,
                    note_timings=music_data.get('notes')  # Pass note timing data
                )
                
                # Resolve any conflicts
                assignment = ConflictResolver.resolve_duplicates(assignment)
                assignment = ConflictResolver.balance_assignments(assignment)
                assignment = ConflictResolver.optimize_for_experience(assignment, players)
                
                # Validate arrangement (including hand constraints)
                validation = ArrangementValidator.validate(assignment)
                sustainability = ArrangementValidator.sustainability_check(assignment, music_data)
                quality_score = ArrangementValidator.calculate_quality_score(assignment, music_data)
                
                arrangements.append({
                    'strategy': strategy,
                    'description': description,
                    'assignments': assignment,
                    'validation': validation,
                    'sustainability': sustainability,
                    'quality_score': quality_score,
                    'note_count': len(unique_notes),
                    'melody_count': len(melody_notes),
                    'players': len(players)
                })
                
                logger.info(f"✓ Generated {strategy} arrangement (score: {quality_score:.0f})")
                
            except Exception as e:
                logger.warning(f"Failed to generate {strategy} arrangement: {str(e)}")
        
        if not arrangements:
            raise Exception("Failed to generate any arrangements")
        
        # Sort by quality score (descending)
        arrangements.sort(key=lambda a: a['quality_score'], reverse=True)
        
        logger.info(f"Generated {len(arrangements)} arrangements, best score: {arrangements[0]['quality_score']:.0f}")
        
        return arrangements



