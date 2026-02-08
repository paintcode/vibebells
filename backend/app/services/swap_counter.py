"""
Swap Counter - Calculate actual hand swaps needed for an arrangement

A swap occurs when a player must put down one bell to pick up another
because they need to play a bell not currently in their hands.
"""

import logging

logger = logging.getLogger(__name__)


class SwapCounter:
    """Calculate actual number of hand swaps needed for each player"""
    
    @staticmethod
    def calculate_swaps_for_arrangement(assignment, music_data):
        """
        Calculate the number of hand swaps needed for each player in an arrangement.
        
        A swap occurs when:
        1. Player has more than 2 bells assigned
        2. Player needs to play a bell not currently in their hands
        3. Player must drop one bell from a hand to pick up another
        
        Args:
            assignment: Dict mapping player names to {'bells', 'left_hand', 'right_hand'}
            music_data: Dict with 'notes' list containing pitch and timing
            
        Returns:
            Dict mapping player names to swap counts
        """
        swap_counts = {}
        
        if not music_data or 'notes' not in music_data:
            # No timing data, return 0 swaps for all
            for player_name in assignment.keys():
                swap_counts[player_name] = 0
            return swap_counts
        
        # Get all notes with timing in chronological order
        all_notes = music_data['notes']
        if not all_notes:
            for player_name in assignment.keys():
                swap_counts[player_name] = 0
            return swap_counts
        
        # Convert note names to pitches for matching
        note_to_pitch = {}
        from app.services.music_parser import MusicParser
        
        for player_name, player_data in assignment.items():
            left_hand = player_data.get('left_hand', [])
            right_hand = player_data.get('right_hand', [])
            all_bells = set(left_hand) | set(right_hand)
            
            # If player has 2 or fewer bells, no swaps possible
            if len(all_bells) <= 2:
                swap_counts[player_name] = 0
                continue
            
            # Build pitch-to-note-name mapping for this player's bells
            bell_pitches = set()
            for bell_name in all_bells:
                try:
                    pitch = MusicParser.note_name_to_pitch(bell_name)
                    bell_pitches.add(pitch)
                except:
                    logger.warning(f"Could not convert bell name {bell_name} to pitch")
            
            # Get notes played by this player, in chronological order
            player_notes = [n for n in all_notes if n.get('pitch') in bell_pitches]
            player_notes.sort(key=lambda n: n.get('time', 0))
            
            if len(player_notes) <= 1:
                swap_counts[player_name] = 0
                continue
            
            # Build hand map for bells
            hand_map = {}  # pitch -> 'left' or 'right'
            for bell_name in left_hand:
                try:
                    pitch = MusicParser.note_name_to_pitch(bell_name)
                    hand_map[pitch] = 'left'
                except:
                    pass
            for bell_name in right_hand:
                try:
                    pitch = MusicParser.note_name_to_pitch(bell_name)
                    hand_map[pitch] = 'right'
                except:
                    pass
            
            # Count swaps: when player needs to switch which bell they're holding
            swaps = SwapCounter._count_swaps_for_player(player_notes, hand_map)
            swap_counts[player_name] = swaps
        
        return swap_counts
    
    @staticmethod
    def _count_swaps_for_player(player_notes, hand_map):
        """
        Count swaps for a single player based on their actual note sequence.
        
        Algorithm:
        1. Player starts with 2 bells held (first 2 unique pitches)
        2. For each note in sequence:
           - If holding it: play it
           - If not holding it: drop the bell needed furthest in future, pick up needed bell (1 swap)
        3. Look ahead to determine which bell to drop (greedy algorithm: drop bell with furthest next appearance)
        
        Example: A-B-C-B-A
        - Start: holding A (left), B (right)
        - Note A: already holding, play
        - Note B: already holding, play
        - Note C: not holding, look ahead:
          - A next appears at position 4
          - B next appears at position 3
          - Drop A (needed at 4, which is further), pick up C (1 swap)
        - Note B: already holding, play
        - Note A: not holding, look ahead:
          - B next appears: never (no more notes)
          - Drop B, pick up A (1 swap)
        - Total: 2 swaps
        
        Args:
            player_notes: List of notes (dicts with 'pitch', 'duration', 'time') in chronological order
            hand_map: Dict mapping pitch -> 'left' or 'right' (predetermined hand assignments)
            
        Returns:
            Integer count of swaps
        """
        if len(player_notes) <= 1:
            return 0
        
        # Get pitches in order (may have duplicates)
        pitches = [note.get('pitch') for note in player_notes]
        
        # Get unique pitches in order of first appearance
        unique_pitches = []
        seen = set()
        for pitch in pitches:
            if pitch not in seen:
                unique_pitches.append(pitch)
                seen.add(pitch)
        
        if len(unique_pitches) <= 2:
            # Can hold 2 bells (1 per hand), no swaps needed
            return 0
        
        # Initialize: player holds first 2 unique pitches
        holding = set(unique_pitches[:2])
        swaps = 0
        
        # Process each note in the sequence
        for i, pitch in enumerate(pitches):
            if pitch not in holding:
                # Need to swap: figure out which bell to drop
                # Drop the bell that's needed furthest in the future
                
                # Find next occurrence of each bell we're currently holding
                next_positions = {}
                for held_pitch in holding:
                    next_pos = None
                    for j in range(i + 1, len(pitches)):
                        if pitches[j] == held_pitch:
                            next_pos = j
                            break
                    next_positions[held_pitch] = next_pos
                
                # Drop the bell with furthest next appearance (or never appears again)
                # Sort by: None (never appears) first, then by position (furthest first)
                held_list = list(holding)
                held_list.sort(key=lambda p: (next_positions[p] is not None, -next_positions[p] if next_positions[p] is not None else -1))
                
                bell_to_drop = held_list[0]  # First in sorted list (furthest away or never needed)
                
                holding.remove(bell_to_drop)
                holding.add(pitch)
                swaps += 1
        
        return swaps
