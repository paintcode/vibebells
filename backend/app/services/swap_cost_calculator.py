"""
Swap Cost Calculator

Calculates the cost of assigning bells to player hands, prioritizing
assignments that minimize the number of hand swaps needed during performance.
"""

import logging

logger = logging.getLogger(__name__)


class SwapCostCalculator:
    """Calculate hand swap costs for bell assignments"""
    
    @staticmethod
    def calculate_swap_cost(bell_pitch, notes):
        """
        Calculate how frequently a bell is played (occurrence count).
        Lower frequency = lower swap cost = better candidate for extra bells.
        
        Args:
            bell_pitch: Integer MIDI pitch
            notes: List of note dicts with 'pitch' and 'time' keys
            
        Returns:
            Integer count of occurrences (0 = not in notes)
        """
        return sum(1 for n in notes if n.get('pitch') == bell_pitch)
    
    @staticmethod
    def calculate_swap_cost_for_player(player_assignment, new_bell_pitch, notes):
        """
        Calculate swap cost if new_bell_pitch is added to player.
        
        Simulates hand assignments using index-based rule:
        - Index 0, 2, 4... → left hand
        - Index 1, 3, 5... → right hand
        
        Counts how many times the player needs to swap hands during performance.
        
        Args:
            player_assignment: Dict with 'bells', 'left_hand', 'right_hand'
            new_bell_pitch: Integer MIDI pitch of candidate bell
            notes: All notes from music file with timing info
            
        Returns:
            Integer representing number of hand swaps needed (0 = no swaps)
        """
        # Build complete bell list with new bell
        all_bells = player_assignment.get('bells', []) + [new_bell_pitch]
        
        # Filter notes to only those played by this player
        player_notes = [n for n in notes if n.get('pitch') in all_bells]
        
        if len(player_notes) <= 1:
            return 0  # 0 or 1 notes = no swaps needed
        
        # Sort by time to get chronological order
        player_notes.sort(key=lambda n: n.get('time', 0))
        
        # Create hand map using index-based rule
        hand_map = {}  # pitch -> hand ('left' or 'right')
        for idx, pitch in enumerate(all_bells):
            hand_map[pitch] = 'left' if idx % 2 == 0 else 'right'
        
        # Count swaps by tracking active hand transitions
        swaps = 0
        current_hand = None
        
        for note in player_notes:
            pitch = note.get('pitch')
            required_hand = hand_map.get(pitch)
            
            # If hand changes and we were already using a hand, it's a swap
            if current_hand is not None and current_hand != required_hand:
                swaps += 1
            
            current_hand = required_hand
        
        logger.debug(
            f"Swap cost for pitch {new_bell_pitch}: {swaps} swaps "
            f"across {len(player_notes)} notes"
        )
        
        return swaps
    
    @staticmethod
    def calculate_temporal_gaps(bell_pitch, notes):
        """
        Calculate average time gap between occurrences of a bell.
        
        Larger gaps = note is temporally separated = better candidate for extra bells
        (less likelihood of needing to swap back and forth).
        
        Args:
            bell_pitch: Integer MIDI pitch
            notes: List of note dicts with 'time' key
            
        Returns:
            Float representing average gap in ticks (inf if only 1 occurrence)
        """
        bell_notes = [n for n in notes if n.get('pitch') == bell_pitch]
        
        if len(bell_notes) <= 1:
            return float('inf')  # Single occurrence - best candidate
        
        times = sorted([n.get('time', 0) for n in bell_notes])
        gaps = [times[i + 1] - times[i] for i in range(len(times) - 1)]
        
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        logger.debug(f"Temporal gap for pitch {bell_pitch}: {avg_gap:.1f} ticks")
        
        return avg_gap
    
    @staticmethod
    def score_bell_for_player(
        player_assignment,
        new_bell_pitch,
        notes,
        weights=None,
        max_bells=8
    ):
        """
        Comprehensive score for assigning a bell to a player.
        Lower score = better assignment.
        
        Scoring combines three factors:
        1. Swap cost: How many hand swaps this bell would need
        2. Frequency: How often the bell is played (rare is better)
        3. Isolation: How temporally separated from other player bells
        
        Args:
            player_assignment: Dict with 'bells', 'left_hand', 'right_hand'
            new_bell_pitch: Integer MIDI pitch of candidate bell
            notes: All notes from music file
            weights: Dict with 'swap', 'frequency', 'isolation' weights (default: 50/30/20)
            max_bells: Maximum bells per player (default: 8)
            
        Returns:
            Float score in range [0, 1] where 0 is best
        """
        if weights is None:
            weights = {'swap': 0.5, 'frequency': 0.3, 'isolation': 0.2}
        
        # Check player has capacity
        if len(player_assignment.get('bells', [])) >= max_bells:
            return float('inf')  # Can't assign - at capacity
        
        # Component 1: Swap cost (0-1, lower is better)
        swap_cost = SwapCostCalculator.calculate_swap_cost_for_player(
            player_assignment, new_bell_pitch, notes
        )
        # Normalize: assume typical player won't have > 10 swaps
        swap_score = min(swap_cost / 10.0, 1.0)
        
        # Component 2: Frequency (0-1, lower is better because rare bells are safer)
        frequency = SwapCostCalculator.calculate_swap_cost(new_bell_pitch, notes)
        total_notes = len(notes)
        
        if total_notes > 0:
            # Normalize to 0-1 where 1 is very frequent (half of all notes)
            frequency_score = min(frequency / (total_notes / 2), 1.0)
        else:
            frequency_score = 0.0
        
        # Component 3: Temporal isolation (0-1, lower is better because well-separated is safer)
        gap = SwapCostCalculator.calculate_temporal_gaps(new_bell_pitch, notes)
        
        if gap == float('inf'):
            isolation_score = 0.0  # Single occurrence - best case
        else:
            # Normalize gap: larger gaps are better (lower score)
            # Assume typical max gap is 10000 ticks
            isolation_score = max(0.0, 1.0 - (gap / 10000.0))
        
        # Weighted combination (all components 0-1, result is 0-1)
        total_score = (
            weights['swap'] * swap_score +
            weights['frequency'] * frequency_score +
            weights['isolation'] * isolation_score
        )
        
        logger.debug(
            f"Score for pitch {new_bell_pitch}: swap={swap_score:.2f} "
            f"freq={frequency_score:.2f} iso={isolation_score:.2f} "
            f"total={total_score:.2f}"
        )
        
        return total_score
