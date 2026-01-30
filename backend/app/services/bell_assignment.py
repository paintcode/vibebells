import logging
from app.services.music_parser import MusicParser

logger = logging.getLogger(__name__)

class BellAssignmentAlgorithm:
    """Implements the bell assignment algorithm with multi-bell support"""
    
    @staticmethod
    def assign_bells(notes, players, strategy='experienced_first', priority_notes=None, config=None, note_timings=None):
        """
        Assign bells to players based on strategy, supporting multiple bells per player.
        
        Args:
            notes: List of unique note names (e.g., ['C4', 'D4', 'E4'])
            players: List of player dicts with 'name' and 'experience'
            strategy: Assignment strategy ('experienced_first', 'balanced', 'min_transitions')
            priority_notes: Optional list of notes to prioritize (e.g., melody notes)
            config: Optional config dict with MAX_BELLS_PER_PLAYER
            note_timings: Optional list of full note dicts with timing info (for swap cost optimization)
        
        Returns:
            Dict mapping player names to assignment dicts with 'bells', 'left_hand', 'right_hand'
            
        Raises:
            ValueError: If validation fails
        """
        
        if not players:
            raise ValueError("At least one player is required")
        
        if not notes:
            raise ValueError("At least one note is required")
        
        if len(players) < 1:
            raise ValueError("Invalid player count")
        
        max_bells = config.get('MAX_BELLS_PER_PLAYER', 8) if config else 8
        
        # Initialize assignments with hand tracking
        assignments = {}
        for player in players:
            assignments[player['name']] = {
                'bells': [],
                'left_hand': [],
                'right_hand': []
            }
        
        player_bell_counts = {player['name']: 0 for player in players}
        
        # Sort players by experience
        experience_order = {'experienced': 0, 'intermediate': 1, 'beginner': 2}
        sorted_players = sorted(players, key=lambda p: experience_order.get(p.get('experience', 'beginner'), 2))
        
        if strategy == 'experienced_first':
            assignments = BellAssignmentAlgorithm._assign_experienced_first(
                notes, sorted_players, assignments, player_bell_counts, priority_notes, max_bells
            )
        elif strategy == 'balanced':
            assignments = BellAssignmentAlgorithm._assign_balanced(
                notes, sorted_players, assignments, player_bell_counts, priority_notes, max_bells
            )
        elif strategy == 'min_transitions':
            assignments = BellAssignmentAlgorithm._assign_min_transitions(
                notes, sorted_players, assignments, player_bell_counts, priority_notes, max_bells, note_timings
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Assign bells to specific hands
        assignments = BellAssignmentAlgorithm._assign_hands(assignments)
        
        return assignments
    
    @staticmethod
    def _assign_experienced_first(notes, players, assignments, counts, priority_notes=None, max_bells=8):
        """Assign bells ensuring every player gets at least 2, then extras to experienced players"""
        
        priority_notes = priority_notes or []
        all_notes = list(notes)
        assigned_notes = set()
        
        # Phase 1: Ensure every player gets at least 2 bells
        for _ in range(2):  # Two rounds to give each player 2 bells
            for player in players:
                if counts[player['name']] < 2 and all_notes:
                    # Prefer priority notes, then remaining
                    note = None
                    for n in priority_notes:
                        if n not in assigned_notes:
                            note = n
                            break
                    if not note:
                        for n in all_notes:
                            if n not in assigned_notes:
                                note = n
                                break
                    
                    if note:
                        assignments[player['name']]['bells'].append(note)
                        counts[player['name']] += 1
                        assigned_notes.add(note)
        
        # Phase 2: Assign remaining priority notes to experienced players
        for note in priority_notes:
            if note not in assigned_notes:
                assigned = False
                for player in players:
                    if counts[player['name']] < max_bells:
                        assignments[player['name']]['bells'].append(note)
                        counts[player['name']] += 1
                        assigned = True
                        assigned_notes.add(note)
                        break
        
        # Phase 3: Assign remaining notes
        for note in all_notes:
            if note not in assigned_notes:
                assigned = False
                for player in players:
                    if counts[player['name']] < max_bells:
                        assignments[player['name']]['bells'].append(note)
                        counts[player['name']] += 1
                        assigned = True
                        assigned_notes.add(note)
                        break
        
        unassigned_count = len(all_notes) - len(assigned_notes)
        if unassigned_count > 0:
            logger.warning(f"Could not assign {unassigned_count} notes due to player capacity limits")
        
        return assignments
    
    @staticmethod
    def _assign_balanced(notes, players, assignments, counts, priority_notes=None, max_bells=8):
        """Distribute notes evenly: ensure each player gets 2 bells first, then distribute extras"""
        
        priority_notes = priority_notes or []
        unassigned_notes = []
        all_notes = list(priority_notes) + [n for n in notes if n not in priority_notes]
        
        # Phase 1: Ensure every player gets at least 2 bells using round-robin
        note_idx = 0
        for _ in range(2):  # Two rounds to give each player 2 bells
            for player in players:
                if counts[player['name']] < 2 and note_idx < len(all_notes):
                    assignments[player['name']]['bells'].append(all_notes[note_idx])
                    counts[player['name']] += 1
                    note_idx += 1
        
        # Phase 2: Distribute remaining notes round-robin to all players
        while note_idx < len(all_notes):
            for player in players:
                if note_idx < len(all_notes) and counts[player['name']] < max_bells:
                    assignments[player['name']]['bells'].append(all_notes[note_idx])
                    counts[player['name']] += 1
                    note_idx += 1
        
        if note_idx < len(all_notes):
            logger.warning(f"Balanced strategy: Could not assign {len(all_notes) - note_idx} notes due to capacity")
        
        return assignments
    
    @staticmethod
    def _assign_min_transitions(notes, players, assignments, counts, priority_notes=None, max_bells=8, note_timings=None):
        """Assign notes with swap cost optimization: minimize hand swaps
        
        If note_timings provided, uses SwapCostCalculator to prefer bells
        that require fewer hand swaps when assigned to a player.
        """
        
        from app.services.swap_cost_calculator import SwapCostCalculator
        
        priority_notes = priority_notes or []
        all_notes = list(priority_notes) + [n for n in notes if n not in priority_notes]
        
        # Phase 1: Ensure every player gets at least 2 bells
        for _ in range(2):  # Two rounds to give each player 2 bells
            for note in all_notes:
                if all([counts[p['name']] >= 2 for p in players]):
                    # All players have 2 bells, move to phase 2
                    break
                
                # Find player with fewest bells
                min_player = min(players, key=lambda p: counts[p['name']])
                if counts[min_player['name']] < 2:
                    if note not in [b for p_data in assignments.values() for b in p_data['bells']]:
                        assignments[min_player['name']]['bells'].append(note)
                        counts[min_player['name']] += 1
        
        # Phase 2: Assign remaining notes with swap cost optimization (if timings available)
        remaining_notes = [n for n in all_notes if n not in [b for p_data in assignments.values() for b in p_data['bells']]]
        
        if note_timings and len(remaining_notes) > 0:
            # Convert note names to MIDI pitches for lookup
            pitch_to_name = {MusicParser.note_name_to_pitch(n): n for n in notes}
            
            for note in remaining_notes:
                best_player = None
                best_score = float('inf')
                
                # Find player with lowest swap cost for this note
                for player in players:
                    if counts[player['name']] < max_bells:
                        note_pitch = MusicParser.note_name_to_pitch(note)
                        score = SwapCostCalculator.score_bell_for_player(
                            assignments[player['name']],
                            note_pitch,
                            note_timings,
                            weights={'swap': 0.5, 'frequency': 0.3, 'isolation': 0.2}
                        )
                        
                        if score < best_score:
                            best_score = score
                            best_player = player
                
                if best_player:
                    assignments[best_player['name']]['bells'].append(note)
                    counts[best_player['name']] += 1
                else:
                    logger.warning(f"Could not assign {note} with swap optimization - all players at capacity")
        else:
            # Fallback to simple least-loaded strategy
            for note in remaining_notes:
                min_player = min(players, key=lambda p: counts[p['name']])
                if counts[min_player['name']] < max_bells:
                    assignments[min_player['name']]['bells'].append(note)
                    counts[min_player['name']] += 1
                else:
                    logger.warning(f"Could not assign {note} - all players at capacity")
        
        return assignments
    
    @staticmethod
    def _assign_hands(assignments):
        """Assign bells to specific hands (left, right) based on index.
        
        Strategy: Alternate left, right, left, right...
        - Index 0 → left hand
        - Index 1 → right hand
        - Index 2 → left hand
        - etc.
        """
        
        for player_name, player_data in assignments.items():
            for idx, bell in enumerate(player_data['bells']):
                if idx % 2 == 0:
                    player_data['left_hand'].append(bell)
                else:
                    player_data['right_hand'].append(bell)
        
        return assignments

