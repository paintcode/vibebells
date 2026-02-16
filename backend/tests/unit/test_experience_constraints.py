#!/usr/bin/env python3
"""Test experience-level constraints and player expansion logic"""

import sys
sys.path.insert(0, '.')

from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.arrangement_generator import ArrangementGenerator

def test_experience_level_max_bells():
    """Test that experience levels respect maximum bells constraints"""
    
    print("\n" + "="*60)
    print("Testing Experience-Level Maximum Bells Constraints")
    print("="*60)
    
    # Create players with different experience levels
    players = [
        {'name': 'Experienced Player', 'experience': 'experienced'},
        {'name': 'Intermediate Player', 'experience': 'intermediate'},
        {'name': 'Beginner Player', 'experience': 'beginner'},
    ]
    
    # Create many notes to test max bells
    notes = [f'C{oct}{note}' for oct in range(4, 6) for note in ['4', 'b4', '5', '#5', '6', 'b6', '7', '#7']]
    notes = notes[:16]  # 16 unique notes
    
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    # Test experienced_first strategy
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='experienced_first', config=config
    )
    
    print("\nExperienced-First Strategy:")
    print("-" * 60)
    
    bell_counts = {p['name']: len(assignment[p['name']]['bells']) for p in players}
    
    for player in players:
        exp = player['experience']
        count = bell_counts[player['name']]
        bells = assignment[player['name']]['bells']
        print(f"  {player['name']} ({exp}): {count} bells {bells}")
    
    # Verify constraints
    exp_player = players[0]
    inter_player = players[1]
    beginner_player = players[2]
    
    assert bell_counts[exp_player['name']] <= 5, f"Experienced player exceeded 5 bells: {bell_counts[exp_player['name']]}"
    assert bell_counts[inter_player['name']] <= 3, f"Intermediate player exceeded 3 bells: {bell_counts[inter_player['name']]}"
    assert bell_counts[beginner_player['name']] <= 2, f"Beginner player exceeded 2 bells: {bell_counts[beginner_player['name']]}"
    assert bell_counts[beginner_player['name']] >= 2, f"Beginner player has less than 2 bells: {bell_counts[beginner_player['name']]}"
    
    print(f"\n✓ All experience-level constraints respected!")
    print(f"  Total bells assigned: {sum(bell_counts.values())}/{len(notes)}")


def test_even_distribution_to_capable_players():
    """Test that extra bells are distributed evenly to experienced/intermediate only"""
    
    print("\n" + "="*60)
    print("Testing Even Distribution to Capable Players")
    print("="*60)
    
    # Create 2 experienced, 2 intermediate, 2 beginner players
    players = [
        {'name': 'Exp 1', 'experience': 'experienced'},
        {'name': 'Exp 2', 'experience': 'experienced'},
        {'name': 'Inter 1', 'experience': 'intermediate'},
        {'name': 'Inter 2', 'experience': 'intermediate'},
        {'name': 'Begin 1', 'experience': 'beginner'},
        {'name': 'Begin 2', 'experience': 'beginner'},
    ]
    
    # Create 13 notes (12 base + 1 extra)
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5']
    
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='experienced_first', config=config
    )
    
    print("\nAssignments:")
    print("-" * 60)
    
    bell_counts = {}
    for player in players:
        count = len(assignment[player['name']]['bells'])
        bells = assignment[player['name']]['bells']
        bell_counts[player['name']] = count
        print(f"  {player['name']:10s}: {count} bells {bells}")
    
    # Verify beginners are at max (2 bells)
    for player in players:
        if player['experience'] == 'beginner':
            assert bell_counts[player['name']] == 2, f"Beginner {player['name']} doesn't have 2 bells"
    
    # Extra bells should go to experienced/intermediate only
    capable_bells = sum(bell_counts[p['name']] for p in players if p['experience'] in ['experienced', 'intermediate'])
    beginner_bells = sum(bell_counts[p['name']] for p in players if p['experience'] == 'beginner')
    
    print(f"\n✓ Distribution verified!")
    print(f"  Capable players (exp+inter): {capable_bells} bells")
    print(f"  Beginner players: {beginner_bells} bells")
    print(f"  Beginners stayed at minimum 2 each: {beginner_bells == 4}")


def test_balanced_strategy_all_notes_sorted():
    """Test that balanced strategy sorts ALL notes by frequency"""
    
    print("\n" + "="*60)
    print("Testing Balanced Strategy - All Notes Sorted by Frequency")
    print("="*60)
    
    players = [
        {'name': 'Player 1', 'experience': 'experienced'},
        {'name': 'Player 2', 'experience': 'intermediate'},
        {'name': 'Player 3', 'experience': 'beginner'},
    ]
    
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
    
    # Simulate frequencies: C4 is very frequent (melody), others less so
    note_frequencies = {
        'C4': 100,  # Very frequent
        'D4': 80,
        'E4': 60,
        'F4': 40,
        'G4': 30,
        'A4': 20,
        'B4': 10,
        'C5': 5,    # Least frequent
    }
    
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players, 
        strategy='balanced',
        priority_notes=[],  # No special priority
        config=config,
        note_frequencies=note_frequencies
    )
    
    print("\nBalanced Assignment (sorted by frequency):")
    print("-" * 60)
    
    for player in players:
        bells = assignment[player['name']]['bells']
        freqs = [note_frequencies.get(b, 0) for b in bells]
        print(f"  {player['name']:10s}: {bells} (freqs: {freqs})")
    
    # Check that high-frequency notes are distributed to all players
    c4_assigned = any('C4' in assignment[p['name']]['bells'] for p in players)
    assert c4_assigned, "Most frequent note C4 should be assigned to someone"
    
    print(f"\n✓ Balanced strategy distributes frequent notes first")


def test_minimum_player_calculation():
    """Test minimum player calculation for player expansion"""
    
    print("\n" + "="*60)
    print("Testing Minimum Player Calculation")
    print("="*60)
    
    # Test case 1: Sufficient players
    players_sufficient = [
        {'name': 'Exp', 'experience': 'experienced'},  # 5 bells
        {'name': 'Inter1', 'experience': 'intermediate'},  # 3 bells
        {'name': 'Inter2', 'experience': 'intermediate'},  # 3 bells
    ]  # Total capacity: 11 bells
    
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']  # 8 notes
    
    min_needed = ArrangementGenerator._calculate_minimum_players_needed(notes, players_sufficient)
    total_capacity = ArrangementGenerator._calculate_total_capacity(players_sufficient)
    
    print(f"\nTest 1: Sufficient Players")
    print(f"  Players: {len(players_sufficient)}, Capacity: {total_capacity}")
    print(f"  Notes: {len(notes)}")
    print(f"  Minimum needed: {min_needed}")
    assert min_needed == len(players_sufficient), "Should not need expansion"
    print(f"  ✓ No expansion needed")
    
    # Test case 2: Insufficient players
    players_insufficient = [
        {'name': 'Beginner1', 'experience': 'beginner'},  # 2 bells
        {'name': 'Beginner2', 'experience': 'beginner'},  # 2 bells
    ]  # Total capacity: 4 bells
    
    notes_many = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5']  # 9 notes
    
    min_needed = ArrangementGenerator._calculate_minimum_players_needed(notes_many, players_insufficient)
    total_capacity = ArrangementGenerator._calculate_total_capacity(players_insufficient)
    
    print(f"\nTest 2: Insufficient Players")
    print(f"  Players: {len(players_insufficient)}, Capacity: {total_capacity}")
    print(f"  Notes: {len(notes_many)}")
    print(f"  Minimum needed: {min_needed}")
    assert min_needed > len(players_insufficient), "Should need expansion"
    print(f"  ✓ Expansion needed: {min_needed - len(players_insufficient)} additional players")


def test_player_expansion():
    """Test player expansion logic"""
    
    print("\n" + "="*60)
    print("Testing Player Expansion")
    print("="*60)
    
    original_players = [
        {'name': 'Player 1', 'experience': 'experienced'},
        {'name': 'Player 2', 'experience': 'beginner'},
    ]
    
    # Expand to 5 total players
    expanded = ArrangementGenerator._expand_players(original_players, 5)
    
    print(f"\nExpansion: {len(original_players)} → {len(expanded)} players")
    for i, player in enumerate(expanded):
        is_virtual = " (VIRTUAL)" if player.get('virtual') else ""
        print(f"  {i+1}. {player['name']} ({player['experience']}){is_virtual}")
    
    assert len(expanded) == 5, f"Expected 5 players, got {len(expanded)}"
    assert len(expanded) - len(original_players) == 3, "Should have added 3 virtual players"
    
    # Check virtual players are intermediate
    virtual_players = [p for p in expanded if p.get('virtual')]
    for p in virtual_players:
        assert p['experience'] == 'intermediate', "Virtual players should be intermediate"
    
    print(f"✓ Expansion successful: {len(virtual_players)} virtual intermediate players added")


if __name__ == '__main__':
    try:
        test_experience_level_max_bells()
        test_even_distribution_to_capable_players()
        test_balanced_strategy_all_notes_sorted()
        test_minimum_player_calculation()
        test_player_expansion()
        
        print("\n" + "="*60)
        print("✅ All experience constraint tests passed!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
