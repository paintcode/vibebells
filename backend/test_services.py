"""
Unit tests for SwapCounter and ExportFormatter
"""

import unittest
from io import StringIO
import csv
from datetime import datetime

# Test imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.swap_counter import SwapCounter
from app.services.export_formatter import ExportFormatter


class TestSwapCounter(unittest.TestCase):
    """Test cases for SwapCounter._count_swaps_for_player"""
    
    def test_no_notes(self):
        """Empty note list should return 0 swaps"""
        result = SwapCounter._count_swaps_for_player([], {})
        self.assertEqual(result, 0)
    
    def test_single_note(self):
        """Single note requires no swaps"""
        notes = [{'pitch': 60, 'time': 0}]
        result = SwapCounter._count_swaps_for_player(notes, {})
        self.assertEqual(result, 0)
    
    def test_two_unique_pitches(self):
        """Two unique pitches (1 per hand) requires no swaps"""
        notes = [
            {'pitch': 60, 'time': 0},  # C4
            {'pitch': 62, 'time': 1},  # D4
            {'pitch': 60, 'time': 2},  # C4
            {'pitch': 62, 'time': 3},  # D4
        ]
        hand_map = {60: 'left', 62: 'right'}
        result = SwapCounter._count_swaps_for_player(notes, hand_map)
        self.assertEqual(result, 0, "Two bells (1 per hand) should need 0 swaps")
    
    def test_three_unique_pitches_simple(self):
        """Three unique pitches: C-D-E-D-C requires 2 swaps"""
        notes = [
            {'pitch': 60, 'time': 0},  # C4
            {'pitch': 62, 'time': 1},  # D4
            {'pitch': 64, 'time': 2},  # E4 (need to pick up)
            {'pitch': 62, 'time': 3},  # D4
            {'pitch': 60, 'time': 4},  # C4 (need to pick up)
        ]
        hand_map = {60: 'left', 62: 'right', 64: 'right'}
        result = SwapCounter._count_swaps_for_player(notes, hand_map)
        self.assertEqual(result, 2, "C-D-E-D-C should need 2 swaps")
    
    def test_three_unique_pitches_clustered(self):
        """Three bells but clustered: C-D-E should need 1 swap"""
        notes = [
            {'pitch': 60, 'time': 0},  # C4 (start holding)
            {'pitch': 62, 'time': 1},  # D4 (start holding)
            {'pitch': 64, 'time': 2},  # E4 (need to swap, drop C or D, pick E)
        ]
        hand_map = {60: 'left', 62: 'right', 64: 'right'}
        result = SwapCounter._count_swaps_for_player(notes, hand_map)
        self.assertEqual(result, 1, "C-D-E should need 1 swap")
    
    def test_single_bell_repeated(self):
        """Single bell played multiple times: no swaps"""
        notes = [
            {'pitch': 60, 'time': 0},
            {'pitch': 60, 'time': 1},
            {'pitch': 60, 'time': 2},
        ]
        result = SwapCounter._count_swaps_for_player(notes, {60: 'left'})
        self.assertEqual(result, 0)
    
    def test_alternating_two_bells(self):
        """Alternating between 2 bells: no swaps"""
        notes = [
            {'pitch': 60, 'time': 0},
            {'pitch': 62, 'time': 1},
            {'pitch': 60, 'time': 2},
            {'pitch': 62, 'time': 3},
            {'pitch': 60, 'time': 4},
        ]
        hand_map = {60: 'left', 62: 'right'}
        result = SwapCounter._count_swaps_for_player(notes, hand_map)
        self.assertEqual(result, 0)
    
    def test_four_unique_pitches(self):
        """Four bells: A-B-C-D requires swaps"""
        notes = [
            {'pitch': 60, 'time': 0},  # A (hold)
            {'pitch': 62, 'time': 1},  # B (hold)
            {'pitch': 64, 'time': 2},  # C (swap #1)
            {'pitch': 65, 'time': 3},  # D (swap #2)
        ]
        hand_map = {60: 'left', 62: 'right', 64: 'right', 65: 'left'}
        result = SwapCounter._count_swaps_for_player(notes, hand_map)
        self.assertEqual(result, 2, "A-B-C-D should need 2 swaps")
    
    def test_optimal_greedy_choice(self):
        """Greedy should choose to drop bell needed furthest away"""
        notes = [
            {'pitch': 60, 'time': 0},  # C (start holding)
            {'pitch': 62, 'time': 1},  # D (start holding)
            {'pitch': 64, 'time': 2},  # E (need C at 4, D at 5, drop C)
            {'pitch': 62, 'time': 3},  # D
            {'pitch': 60, 'time': 4},  # C (need to swap)
            {'pitch': 62, 'time': 5},  # D
        ]
        hand_map = {60: 'left', 62: 'right', 64: 'right'}
        result = SwapCounter._count_swaps_for_player(notes, hand_map)
        # At pos 2: drop C (needed at 4), pick E → swap 1
        # At pos 4: drop E (never needed again), pick C → swap 2
        self.assertEqual(result, 2)
    
    def test_complex_sequence(self):
        """A-B-C-A-B-C-A-B-C with 3 bells"""
        notes = [
            {'pitch': 60, 'time': 0},  # A
            {'pitch': 62, 'time': 1},  # B
            {'pitch': 64, 'time': 2},  # C (swap #1)
            {'pitch': 60, 'time': 3},  # A
            {'pitch': 62, 'time': 4},  # B (swap #2, need to drop C and pick B back)
            {'pitch': 64, 'time': 5},  # C (swap #3)
            {'pitch': 60, 'time': 6},  # A
            {'pitch': 62, 'time': 7},  # B (swap #4)
            {'pitch': 64, 'time': 8},  # C (swap #5)
        ]
        hand_map = {60: 'left', 62: 'right', 64: 'right'}
        result = SwapCounter._count_swaps_for_player(notes, hand_map)
        # This will have multiple swaps due to the pattern
        self.assertGreater(result, 0, "Complex pattern should need swaps")


class TestExportFormatter(unittest.TestCase):
    """Test cases for ExportFormatter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_arrangement = {
            'Player 1': {
                'bells': ['C4', 'D4', 'E4'],
                'left_hand': ['C4', 'D4'],
                'right_hand': ['E4']
            },
            'Player 2': {
                'bells': ['F4', 'G4'],
                'left_hand': ['F4'],
                'right_hand': ['G4']
            }
        }
        
        self.sample_players = [
            {'name': 'Player 1', 'experience': 'experienced'},
            {'name': 'Player 2', 'experience': 'beginner'}
        ]
    
    def test_csv_structure_has_sections(self):
        """CSV should have metadata, players, and bells sections"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced'
        )
        
        lines = csv_content.strip().split('\n')
        self.assertIn('Metadata', csv_content)
        self.assertIn('Players', csv_content)
        self.assertIn('All Bells', csv_content)
    
    def test_csv_metadata_section(self):
        """Metadata section should contain filename and strategy"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test_song.mid',
            'experienced_first'
        )
        
        self.assertIn('test_song.mid', csv_content)
        self.assertIn('experienced_first', csv_content)
    
    def test_csv_players_section(self):
        """Players section should list all players"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced'
        )
        
        self.assertIn('Player 1', csv_content)
        self.assertIn('Player 2', csv_content)
        self.assertIn('experienced', csv_content)
        self.assertIn('beginner', csv_content)
    
    def test_bell_sorting_by_pitch(self):
        """Bells should be sorted by pitch (C4, D4, E4, F4, G4, etc.)"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced'
        )
        
        # Extract bells section
        bells_section_start = csv_content.find('All Bells')
        bells_section = csv_content[bells_section_start:]
        
        lines = bells_section.split('\n')
        bells = [line.strip() for line in lines[1:] if line.strip() and line.strip() not in ['All Bells']]
        
        # Check order: C4 < D4 < E4 < F4 < G4
        self.assertEqual(bells[0], 'C4')
        self.assertEqual(bells[1], 'D4')
        self.assertEqual(bells[2], 'E4')
        self.assertEqual(bells[3], 'F4')
        self.assertEqual(bells[4], 'G4')
    
    def test_hand_assignments_displayed(self):
        """CSV should show left and right hand assignments"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced'
        )
        
        # Should contain hand assignments
        self.assertIn('C4 D4', csv_content)  # Player 1 left hand
        self.assertIn('E4', csv_content)      # Player 1 right hand
        self.assertIn('F4', csv_content)      # Player 2 left hand
        self.assertIn('G4', csv_content)      # Player 2 right hand
    
    def test_swap_counts_with_data(self):
        """CSV should include swap counts when provided"""
        swap_counts = {
            'Player 1': 2,
            'Player 2': 0
        }
        
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced',
            swap_counts
        )
        
        self.assertIn('2', csv_content)  # Player 1's swaps
        self.assertIn('0', csv_content)  # Player 2's swaps
    
    def test_swap_counts_fallback(self):
        """CSV should fallback to calculation if swap_counts not provided"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced'
            # No swap_counts provided
        )
        
        # Should still have a swaps column with values
        self.assertIn('Bell Swaps', csv_content)
    
    def test_special_characters_in_filename(self):
        """Filenames with special characters should be handled"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'my-song (remix).mid',
            'balanced'
        )
        
        self.assertIn('my-song', csv_content)
    
    def test_empty_hands(self):
        """Players with empty hands should show as blank"""
        arrangement = {
            'Player 1': {
                'bells': ['C4'],
                'left_hand': ['C4'],
                'right_hand': []
            }
        }
        
        players = [{'name': 'Player 1', 'experience': 'beginner'}]
        
        csv_content = ExportFormatter.format_to_csv(
            arrangement,
            players,
            'test.mid',
            'balanced'
        )
        
        # Should have the left hand bell but empty right hand
        self.assertIn('C4', csv_content)
    
    def test_all_bells_extraction(self):
        """All unique bells should be extracted and included"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced'
        )
        
        # All 5 unique bells should be in the output
        for bell in ['C4', 'D4', 'E4', 'F4', 'G4']:
            self.assertIn(bell, csv_content)
    
    def test_csv_parseable(self):
        """Output should be valid CSV (parseable by csv module)"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced'
        )
        
        # Try to parse as CSV
        reader = csv.reader(StringIO(csv_content))
        rows = list(reader)
        
        # Should have multiple rows
        self.assertGreater(len(rows), 10)
    
    def test_timestamp_in_metadata(self):
        """Metadata section should include a timestamp"""
        csv_content = ExportFormatter.format_to_csv(
            self.sample_arrangement,
            self.sample_players,
            'test.mid',
            'balanced'
        )
        
        # Should contain "Generated" with a timestamp
        self.assertIn('Generated', csv_content)
        # Should have year-month-day format
        self.assertRegex(csv_content, r'\d{4}-\d{2}-\d{2}')


class TestSwapCounterIntegration(unittest.TestCase):
    """Integration tests for swap counting with real data"""
    
    def test_calculate_swaps_for_arrangement(self):
        """Test full arrangement swap calculation"""
        arrangement = {
            'Player 1': {
                'bells': ['C4', 'D4'],
                'left_hand': ['C4'],
                'right_hand': ['D4']
            }
        }
        
        # Music data: only 2 unique pitches
        music_data = {
            'notes': [
                {'pitch': 60, 'time': 0},
                {'pitch': 62, 'time': 1},
                {'pitch': 60, 'time': 2},
            ]
        }
        
        swaps = SwapCounter.calculate_swaps_for_arrangement(arrangement, music_data)
        
        self.assertIn('Player 1', swaps)
        self.assertEqual(swaps['Player 1'], 0, "2 bells should need 0 swaps")
    
    def test_calculate_swaps_missing_music_data(self):
        """Should handle missing music data gracefully"""
        arrangement = {
            'Player 1': {
                'bells': ['C4'],
                'left_hand': ['C4'],
                'right_hand': []
            }
        }
        
        swaps = SwapCounter.calculate_swaps_for_arrangement(arrangement, {})
        
        self.assertIn('Player 1', swaps)
        self.assertEqual(swaps['Player 1'], 0)


if __name__ == '__main__':
    unittest.main()
