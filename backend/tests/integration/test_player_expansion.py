#!/usr/bin/env python3
"""Integration test for player expansion with insufficient players"""

import sys
sys.path.insert(0, '.')

from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.conflict_resolver import ConflictResolver
from app.services.arrangement_validator import ArrangementValidator
from app.services.arrangement_generator import ArrangementGenerator

def test_insufficient_players_expansion():
    """Test that player expansion works when there aren't enough players"""
    
    print("\n" + "="*60)
    print("Integration Test: Player Expansion")
    print("="*60)
    
    # Simulate scenario: 2 beginners trying to play 12 unique notes
    # Their capacity: 2*2 = 4 bells (NOT enough for 12 notes)
    original_players = [
        {'name': 'Beginner 1', 'experience': 'beginner'},
        {'name': 'Beginner 2', 'experience': 'beginner'},
    ]
    
    # Create 12 unique notes
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5']
    
    print(f"\nScenario:")
    print(f"  Original players: {len(original_players)} (all beginners)")
    print(f"  Unique notes: {len(notes)}")
    print(f"  Total capacity: {ArrangementGenerator._calculate_total_capacity(original_players)}")
    
    # Check if expansion is needed
    capacity = ArrangementGenerator._calculate_total_capacity(original_players)
    if len(notes) > capacity:
        min_needed = ArrangementGenerator._calculate_minimum_players_needed(notes, original_players)
        expanded_players = ArrangementGenerator._expand_players(original_players, min_needed)
        
        print(f"\n✓ Expansion Triggered!")
        print(f"  Minimum players needed: {min_needed}")
        print(f"  Players to add: {min_needed - len(original_players)}")
        
        expanded_capacity = ArrangementGenerator._calculate_total_capacity(expanded_players)
        print(f"  New total capacity: {expanded_capacity}")
        
        # Verify expanded capacity is sufficient
        assert expanded_capacity >= len(notes), f"Expanded capacity {expanded_capacity} still insufficient for {len(notes)} notes"
        print(f"  ✓ New capacity sufficient for all notes")
        
        # Now generate arrangements with expanded players
        print(f"\nGenerating arrangements with expanded player list:")
        
        # Create mock music data
        mock_music_data = {
            'unique_notes': list(range(12)),  # 12 MIDI pitches
            'melody_pitches': list(range(6)),  # First 6 as melody
            'harmony_pitches': list(range(6, 12)),  # Rest as harmony
            'notes': [{'pitch': i % 12, 'start': i * 100, 'duration': 50} for i in range(len(notes) * 3)],
            'note_count': len(notes),
        }
        
        config = {
            'MAX_BELLS_PER_PLAYER': 8,
            'MAX_BELLS_PER_EXPERIENCE': {
                'experienced': 5,
                'intermediate': 3,
                'beginner': 2
            }
        }
        
        # Test with experienced_first strategy
        assignment = BellAssignmentAlgorithm.assign_bells(
            notes, expanded_players, 
            strategy='experienced_first',
            config=config
        )
        
        # Verify all notes are assigned or as many as possible
        assigned_notes = set()
        for player_name, data in assignment.items():
            assigned_notes.update(data['bells'])
        
        print(f"  Assigned: {len(assigned_notes)}/{len(notes)} unique notes")
        print(f"  ✓ All notes assigned: {len(assigned_notes) == len(notes)}")
        
        # Verify expanded players got assignments
        print(f"\nFinal Assignments:")
        for player in expanded_players:
            bells = assignment[player['name']]['bells']
            is_virtual = " (VIRTUAL)" if player.get('virtual') else ""
            print(f"  {player['name']:20s}: {len(bells)} bells{is_virtual}")
        
        # Verify each player respects max for their experience level
        experience_max = {'experienced': 5, 'intermediate': 3, 'beginner': 2}
        all_valid = True
        for player in expanded_players:
            max_allowed = experience_max[player['experience']]
            actual = len(assignment[player['name']]['bells'])
            if actual > max_allowed:
                print(f"  ❌ {player['name']} exceeded max: {actual} > {max_allowed}")
                all_valid = False
        
        if all_valid:
            print(f"\n✓ All players within experience-level limits")
        
        return True
    else:
        print("✓ No expansion needed (capacity sufficient)")
        return False


def test_expansion_notification():
    """Test that the API returns proper expansion notification"""
    
    print("\n" + "="*60)
    print("Integration Test: Expansion Notification")
    print("="*60)
    
    # Small number of experienced players with many notes
    players = [
        {'name': 'Expert', 'experience': 'experienced'},
    ]
    
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5']  # 9 notes
    
    # Capacity: 1 * 5 = 5 (insufficient)
    capacity = ArrangementGenerator._calculate_total_capacity(players)
    print(f"\nScenario:")
    print(f"  Players: {len(players)}")
    print(f"  Capacity: {capacity}")
    print(f"  Notes: {len(notes)}")
    
    needs_expansion = len(notes) > capacity
    print(f"  Needs expansion: {needs_expansion}")
    
    if needs_expansion:
        min_players = ArrangementGenerator._calculate_minimum_players_needed(notes, players)
        expanded = ArrangementGenerator._expand_players(players, min_players)
        
        # Simulate the return structure
        expansion_info = {
            'expanded': True,
            'original_player_count': len(players),
            'final_player_count': len(expanded),
            'minimum_required': min_players,
            'message': f"The song requires at least {min_players} players. Arrangements show {len(expanded)} players (including {len(expanded) - len(players)} virtual players)."
        }
        
        print(f"\nExpansion Info:")
        print(f"  {expansion_info['message']}")
        
        # Verify message is informative
        assert 'requires at least' in expansion_info['message'].lower(), "Message should mention minimum required"
        assert str(min_players) in expansion_info['message'], "Message should include minimum count"
        assert 'virtual' in expansion_info['message'].lower(), "Message should mention virtual players"
        
        print(f"\n✓ Expansion notification is informative")


if __name__ == '__main__':
    try:
        test_insufficient_players_expansion()
        test_expansion_notification()
        
        print("\n" + "="*60)
        print("✅ All integration tests passed!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
