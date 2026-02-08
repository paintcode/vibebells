"""
CSV Export Formatter
Formats arrangement data into CSV format for download
"""

import csv
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExportFormatter:
    """Format arrangement data for CSV export"""
    
    @staticmethod
    def format_to_csv(arrangement, players, filename, strategy, swap_counts=None):
        """
        Format arrangement into CSV text.
        
        Args:
            arrangement: Dict mapping player names to assignment dicts
            players: List of player configs with name and experience
            filename: Original uploaded filename
            strategy: Strategy used (e.g., 'balanced', 'experienced_first')
            swap_counts: Optional dict mapping player names to swap counts
            
        Returns:
            CSV text content as string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Create mapping of player names to experience levels
        player_experience = {p['name']: p['experience'] for p in players}
        
        # Section 1: Metadata
        writer.writerow(['Metadata'])
        writer.writerow(['Uploaded File', filename])
        writer.writerow(['Strategy', strategy])
        writer.writerow(['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])  # Blank line
        
        # Section 2: Player Assignments
        writer.writerow(['Players'])
        writer.writerow(['Player', 'Experience', 'Left Hand', 'Right Hand', 'Bell Swaps'])
        
        for player_name in sorted(arrangement.keys()):
            player_data = arrangement[player_name]
            left_hand = player_data.get('left_hand', [])
            right_hand = player_data.get('right_hand', [])
            
            # Use actual swap count from calculation if available, otherwise fallback
            if swap_counts and player_name in swap_counts:
                swaps = swap_counts[player_name]
            else:
                swaps = ExportFormatter._calculate_swaps(left_hand, right_hand)
            
            experience = player_experience.get(player_name, 'unknown')
            
            writer.writerow([
                player_name,
                experience,
                ' '.join(sorted(left_hand)) if left_hand else '',
                ' '.join(sorted(right_hand)) if right_hand else '',
                swaps
            ])
        
        writer.writerow([])  # Blank line
        
        # Section 3: All Bells Used (sorted by pitch)
        writer.writerow(['All Bells (sorted by pitch)'])
        all_bells = ExportFormatter._extract_all_bells(arrangement)
        sorted_bells = ExportFormatter._sort_bells_by_pitch(all_bells)
        for bell in sorted_bells:
            writer.writerow([bell])
        
        return output.getvalue()
    
    @staticmethod
    def _calculate_swaps(left_hand, right_hand):
        """
        Calculate number of bell swaps needed per player.
        A swap occurs when a player has bells in both hands that aren't played together,
        requiring them to put down one bell to pick up another.
        
        Args:
            left_hand: List of bells in left hand
            right_hand: List of bells in right hand
            
        Returns:
            Integer count of swaps (0 if all bells in one hand, or if <= 2 total)
        """
        left_count = len(left_hand)
        right_count = len(right_hand)
        total_bells = left_count + right_count
        
        # No swaps if 0, 1, or 2 bells total
        if total_bells <= 2:
            return 0
        
        # No swaps if all bells in one hand (no need to switch hands)
        if left_count == 0 or right_count == 0:
            return 0
        
        # If bells in both hands, estimate swaps based on total minus what fits in one hand
        # Conservative estimate: (total_bells - 2) swaps minimum
        return max(1, total_bells - 2)
    
    @staticmethod
    def _extract_all_bells(arrangement):
        """Extract all unique bells from arrangement"""
        all_bells = set()
        for player_data in arrangement.values():
            left_hand = player_data.get('left_hand', [])
            right_hand = player_data.get('right_hand', [])
            all_bells.update(left_hand)
            all_bells.update(right_hand)
        return all_bells
    
    @staticmethod
    def _sort_bells_by_pitch(bells):
        """
        Sort bells by pitch (C4, D4, E4, etc.)
        Scientific pitch notation: note + octave number
        Order: C < D < E < F < G < A < B
        """
        note_order = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}
        
        def parse_pitch(bell):
            """Parse bell notation (e.g., 'C4') into sortable tuple"""
            if not bell or len(bell) < 2:
                return (999, 999)  # Invalid bells sort last
            
            note = bell[0].upper()
            octave_str = bell[1:]
            
            # Handle sharps/flats: C#4 -> C4 with +0.5
            modifier = 0
            if len(octave_str) > 1:
                if octave_str[0] in ['#', '♯']:
                    modifier = 0.5
                    octave_str = octave_str[1:]
                elif octave_str[0] in ['b', '♭']:
                    modifier = -0.5
                    octave_str = octave_str[1:]
            
            try:
                octave = int(octave_str)
                note_num = note_order.get(note, 7)  # Invalid notes sort last
                return (octave, note_num + modifier)
            except ValueError:
                return (999, 999)  # Invalid bells sort last
        
        return sorted(bells, key=parse_pitch)
