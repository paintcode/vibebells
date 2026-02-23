from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.music_parser import MusicParser
from app.services.conflict_resolver import ConflictResolver
from app.services.arrangement_validator import ArrangementValidator
from app.services.swap_counter import SwapCounter
from app.services.simulation_builder import SimulationBuilder
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
            Dict with 'arrangements' list, 'expanded' flag, and 'minimum_players' recommendation
            
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
        
        # Check if we have sufficient player capacity
        players_expanded = False
        minimum_required_players = None
        expanded_players = players
        
        total_capacity = self._calculate_total_capacity(players)
        if len(unique_notes) > total_capacity:
            minimum_required_players = self._calculate_minimum_players_needed(unique_notes, players)
            logger.warning(f"Insufficient player capacity ({total_capacity}) for {len(unique_notes)} notes. Minimum required: {minimum_required_players}")
            expanded_players = self._expand_players(players, minimum_required_players)
            players_expanded = True
            logger.info(f"Expanded to {len(expanded_players)} total players (added {len(expanded_players) - len(players)} virtual players)")
        
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
                    'MAX_BELLS_PER_EXPERIENCE': current_app.config.get('MAX_BELLS_PER_EXPERIENCE', {
                        'experienced': 5,
                        'intermediate': 3,
                        'beginner': 2
                    }),
                    'HAND_GAP_THRESHOLD_BEATS': current_app.config.get('HAND_GAP_THRESHOLD_BEATS', 1.0)
                }
                
                # Build frequency map from note data
                note_frequencies = {}
                if music_data.get('notes'):
                    for note in music_data['notes']:
                        note_pitch = note.get('pitch')
                        if note_pitch:
                            note_name = MusicParser.pitch_to_note_name(note_pitch)
                            note_frequencies[note_name] = note_frequencies.get(note_name, 0) + 1
                
                assignment = BellAssignmentAlgorithm.assign_bells(
                    unique_notes, 
                    expanded_players,  # Use expanded players if needed
                    strategy=strategy,
                    priority_notes=melody_notes,
                    config=config,
                    note_timings=music_data.get('notes'),  # Pass note timing data
                    note_frequencies=note_frequencies  # Pass frequency data
                )
                
                # Resolve any conflicts
                assignment = ConflictResolver.resolve_duplicates(assignment)
                assignment = ConflictResolver.balance_assignments(assignment)
                assignment = ConflictResolver.optimize_for_experience(assignment, expanded_players)
                
                # Validate arrangement (including hand constraints)
                validation = ArrangementValidator.validate(assignment)
                sustainability = ArrangementValidator.sustainability_check(assignment, music_data)
                quality_score = ArrangementValidator.calculate_quality_score(assignment, music_data)
                
                # Calculate actual swaps for each player based on note sequence
                swap_counts = SwapCounter.calculate_swaps_for_arrangement(assignment, music_data)

                try:
                    simulation = SimulationBuilder.build(music_data, assignment)
                except Exception as sim_err:
                    logger.warning(f"Failed to build simulation for {strategy}: {sim_err}")
                    simulation = None

                arrangements.append({
                    'strategy': strategy,
                    'description': description,
                    'assignments': assignment,
                    'swaps': swap_counts,  # New: actual swap counts per player
                    'simulation': simulation,
                    'validation': validation,
                    'sustainability': sustainability,
                    'quality_score': quality_score,
                    'note_count': len(unique_notes),
                    'melody_count': len(melody_notes),
                    'players': len(expanded_players)
                })
                
                logger.info(f"✓ Generated {strategy} arrangement (score: {quality_score:.0f})")
                
            except Exception as e:
                logger.warning(f"Failed to generate {strategy} arrangement: {str(e)}")
        
        if not arrangements:
            raise Exception("Failed to generate any arrangements")
        
        # Sort by quality score (descending)
        arrangements.sort(key=lambda a: a['quality_score'], reverse=True)
        
        logger.info(f"Generated {len(arrangements)} arrangements, best score: {arrangements[0]['quality_score']:.0f}")
        
        return {
            'arrangements': arrangements,
            'expanded': players_expanded,
            'minimum_players': minimum_required_players,
            'original_player_count': len(players),
            'final_player_count': len(expanded_players)
        }
    
    @staticmethod
    def _calculate_total_capacity(players):
        """Calculate total bell capacity based on player experience levels.
        
        Experience-level max bells:
        - Experienced: 5
        - Intermediate: 3
        - Beginner: 2
        """
        
        experience_max = {'experienced': 5, 'intermediate': 3, 'beginner': 2}
        total = 0
        
        for player in players:
            exp = player.get('experience', 'beginner')
            total += experience_max.get(exp, 2)
        
        return total
    
    @staticmethod
    def _calculate_minimum_players_needed(unique_notes, original_players):
        """Calculate minimum number of players needed to assign all notes.
        
        Assumes virtual players will be added as intermediate players (3 bells max).
        Uses current player distribution to estimate.
        """
        
        # Calculate current distribution
        exp_count = sum(1 for p in original_players if p.get('experience') == 'experienced')
        inter_count = sum(1 for p in original_players if p.get('experience') == 'intermediate')
        beginner_count = sum(1 for p in original_players if p.get('experience') == 'beginner')
        
        total_notes = len(unique_notes)
        current_capacity = ArrangementGenerator._calculate_total_capacity(original_players)
        
        # If we have capacity, no expansion needed
        if total_notes <= current_capacity:
            return len(original_players)
        
        # Calculate how many more bells we need
        needed_bells = total_notes - current_capacity
        
        # Add virtual players as intermediate (3 bells each)
        virtual_intermediate = (needed_bells + 2) // 3  # Round up division
        
        return len(original_players) + virtual_intermediate
    
    @staticmethod
    def _expand_players(original_players, target_count):
        """Expand player list by adding virtual intermediate players.
        
        Virtual players are created with experience='intermediate' and default name generation.
        """
        
        if target_count <= len(original_players):
            return original_players
        
        expanded = list(original_players)
        current_count = len(original_players)
        
        for i in range(current_count, target_count):
            expanded.append({
                'name': f'Virtual Player {i + 1}',
                'experience': 'intermediate',
                'virtual': True
            })
        
        logger.info(f"Expanded player list from {current_count} to {target_count} (added {target_count - current_count} virtual players)")
        
        return expanded
