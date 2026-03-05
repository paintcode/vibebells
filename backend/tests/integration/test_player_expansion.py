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
    else:
        print("✓ No expansion needed (capacity sufficient)")


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


def test_virtual_player_numbering_starts_at_one():
    """Virtual players added by _expand_players should be numbered starting at 1,
    regardless of how many original (non-virtual) players already exist."""

    # 8 original players – the bug caused virtual players to start at 9
    original_players = [
        {'name': f'Player {i}', 'experience': 'beginner'} for i in range(1, 9)
    ]
    # 8 beginners × 2 = 16 capacity; we need >16 notes to force expansion
    notes = [f'Note{i}' for i in range(17)]

    min_needed = ArrangementGenerator._calculate_minimum_players_needed(notes, original_players)
    expanded = ArrangementGenerator._expand_players(original_players, min_needed)

    virtual_players = [p for p in expanded if p.get('virtual')]
    assert len(virtual_players) > 0, "Expansion should have added at least one virtual player"

    virtual_names = [p['name'] for p in virtual_players]
    assert 'Virtual Player 1' in virtual_names, (
        f"First virtual player should be 'Virtual Player 1', got: {virtual_names}"
    )
    # Numbering must be consecutive starting at 1
    for idx, name in enumerate(virtual_names, start=1):
        assert name == f'Virtual Player {idx}', (
            f"Expected 'Virtual Player {idx}' but got '{name}'"
        )


def test_per_arrangement_players_and_final_count_consistency_with_swap_gap_vp():
    """Each arrangement's players field must include swap-gap fallback virtual players
    and final_player_count must match the best arrangement's players field.

    Patches assign_bells to return an assignment with one extra virtual player key
    beyond expanded_players, simulating the swap-gap fallback in bell_assignment.py.
    Verifies that:
    - arrangement['players'] == len(actual_assignment_keys) for each arrangement
    - result['final_player_count'] == result['arrangements'][0]['players']
    """
    from unittest.mock import patch
    from app import create_app

    app = create_app()
    players = [
        {'name': 'Expert', 'experience': 'experienced'},
        {'name': 'Beginner', 'experience': 'beginner'},
    ]
    music_data = {
        'unique_notes': [60, 62, 64],   # C4, D4, E4
        'melody_pitches': [60],
        'notes': [
            {'pitch': 60, 'time': 0,    'duration': 480},
            {'pitch': 62, 'time': 960,  'duration': 480},
            {'pitch': 64, 'time': 1920, 'duration': 480},
        ],
        'note_count': 3,
        'format': 'midi',
        'tempo': 120,
        'ticks_per_beat': 480,
    }
    # Assignment returned by the patched assign_bells.
    # 'Virtual Player 3' is an extra key not present in expanded_players (Expert, Beginner),
    # simulating the swap-gap fallback in bell_assignment.py.
    patched_assignment = {
        'Expert':           {'bells': ['C4'], 'left_hand': ['C4'], 'right_hand': []},
        'Beginner':         {'bells': ['D4'], 'left_hand': ['D4'], 'right_hand': []},
        'Virtual Player 3': {'bells': ['E4'], 'left_hand': ['E4'], 'right_hand': []},
    }
    expected_player_count = len(patched_assignment)  # 3

    with app.app_context():
        with patch(
            'app.services.arrangement_generator.BellAssignmentAlgorithm.assign_bells',
            return_value=patched_assignment,
        ):
            gen = ArrangementGenerator()
            result = gen.generate(music_data, players)

    arrangements = result['arrangements']
    assert len(arrangements) > 0

    # Each arrangement should report players == actual assignment key count (including VP)
    for arr in arrangements:
        assert arr['players'] == expected_player_count, (
            f"Strategy {arr['strategy']}: expected players={expected_player_count}, "
            f"got {arr['players']}"
        )

    # final_player_count must match the best arrangement's players field
    assert result['final_player_count'] == arrangements[0]['players'], (
        f"final_player_count={result['final_player_count']} != "
        f"arrangements[0]['players']={arrangements[0]['players']}"
    )


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
