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
                except (ValueError, KeyError) as e:
                    logger.warning(f"Could not convert bell name {bell_name} to pitch: {e}")
            
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
                except (ValueError, KeyError) as e:
                    logger.debug(f"Could not convert left hand bell name {bell_name} to pitch: {e}")
            for bell_name in right_hand:
                try:
                    pitch = MusicParser.note_name_to_pitch(bell_name)
                    hand_map[pitch] = 'right'
                except (ValueError, KeyError) as e:
                    logger.debug(f"Could not convert right hand bell name {bell_name} to pitch: {e}")
            
            # Count swaps: when player needs to switch which bell they're holding
            swaps = SwapCounter._count_swaps_for_player(player_notes, hand_map)
            swap_counts[player_name] = swaps
        
        return swap_counts
    
    @staticmethod
    def _count_swaps_for_player(player_notes, hand_map):
        """
        Count swaps for a single player based on their actual note sequence.
        
        Algorithm:
        1. Player starts with 2 bells held (one per hand, based on hand_map)
        2. For each note in sequence:
           - If holding it: play it
           - If not holding it: swap the bell in the required hand (1 swap)
        3. Only swap within the hand that is assigned to play the required bell
        
        Example: A-B-C-B-A where A is left hand, B is right hand, C is left hand
        - Start: holding A (left), B (right)
        - Note A: already holding in left, play
        - Note B: already holding in right, play
        - Note C: not holding, but assigned to left hand, swap A for C in left (1 swap)
        - Note B: already holding in right, play
        - Note A: not holding, but assigned to left hand, swap C for A in left (1 swap)
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
        
        # Initialize: player holds first unique pitch for each hand
        holding_left = None
        holding_right = None
        for pitch in unique_pitches:
            hand = hand_map.get(pitch, 'left')  # Default to left if not specified
            if hand == 'left' and holding_left is None:
                holding_left = pitch
            elif hand == 'right' and holding_right is None:
                holding_right = pitch
            
            # Stop once we have one pitch for each hand
            if holding_left is not None and holding_right is not None:
                break
        
        swaps = 0
        
        # Process each note in the sequence
        for pitch in pitches:
            required_hand = hand_map.get(pitch, 'left')  # Default to left if not specified
            
            if required_hand == 'left':
                if holding_left != pitch:
                    # Need to swap in left hand
                    holding_left = pitch
                    swaps += 1
            else:  # right hand
                if holding_right != pitch:
                    # Need to swap in right hand
                    holding_right = pitch
                    swaps += 1
        
        return swaps
