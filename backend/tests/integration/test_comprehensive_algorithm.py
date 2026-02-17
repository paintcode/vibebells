"""
Comprehensive tests for bell assignment algorithm

Tests converted from manual_tests/test_comprehensive_final.py
Covers experience-level constraints, player expansion, and strategy behavior.
"""

from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.arrangement_generator import ArrangementGenerator


def test_all_players_respect_max_bells():
    """Test that no player exceeds their experience-level maximum"""
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    mixed_players = [
        {'name': 'Expert', 'experience': 'experienced'},
        {'name': 'Intermediate1', 'experience': 'intermediate'},
        {'name': 'Intermediate2', 'experience': 'intermediate'},
        {'name': 'Beginner1', 'experience': 'beginner'},
        {'name': 'Beginner2', 'experience': 'beginner'},
    ]
    
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5']
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, mixed_players, strategy='experienced_first', config=config
    )
    
    # Check each player respects their max
    for player in mixed_players:
        exp = player['experience']
        count = len(assignment[player['name']]['bells'])
        max_allowed = config['MAX_BELLS_PER_EXPERIENCE'][exp]
        
        assert count <= max_allowed, \
            f"{player['name']} ({exp}) has {count} bells, max is {max_allowed}"


def test_beginners_have_minimum_bells():
    """Test that beginners get at least 2 bells (minimum)"""
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    mixed_players = [
        {'name': 'Expert', 'experience': 'experienced'},
        {'name': 'Intermediate1', 'experience': 'intermediate'},
        {'name': 'Intermediate2', 'experience': 'intermediate'},
        {'name': 'Beginner1', 'experience': 'beginner'},
        {'name': 'Beginner2', 'experience': 'beginner'},
    ]
    
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5']
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, mixed_players, strategy='experienced_first', config=config
    )
    
    # Check beginners have at least 2 bells
    for player in mixed_players:
        if player['experience'] == 'beginner':
            count = len(assignment[player['name']]['bells'])
            assert count >= 2, f"{player['name']} only has {count} bells, minimum is 2"


def test_expansion_when_capacity_insufficient():
    """Test that players are automatically expanded when needed"""
    small_team = [
        {'name': 'Beginner1', 'experience': 'beginner'},
        {'name': 'Beginner2', 'experience': 'beginner'},
    ]
    
    many_notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5']  # 10 notes
    
    # Original capacity: 2 players * 2 bells = 4 (not enough for 10 notes)
    capacity = ArrangementGenerator._calculate_total_capacity(small_team)
    assert capacity == 4
    assert len(many_notes) > capacity
    
    # Trigger expansion
    min_needed = ArrangementGenerator._calculate_minimum_players_needed(many_notes, small_team)
    expanded = ArrangementGenerator._expand_players(small_team, min_needed)
    
    # Verify expansion occurred
    assert len(expanded) > len(small_team), "Players should be expanded"
    
    # Verify new capacity is sufficient
    new_capacity = ArrangementGenerator._calculate_total_capacity(expanded)
    assert new_capacity >= len(many_notes), \
        f"New capacity {new_capacity} insufficient for {len(many_notes)} notes"


def test_no_expansion_when_capacity_sufficient():
    """Test that expansion doesn't occur when capacity is sufficient"""
    team = [
        {'name': 'Experienced1', 'experience': 'experienced'},
        {'name': 'Experienced2', 'experience': 'experienced'},
    ]
    
    few_notes = ['C4', 'D4', 'E4', 'F4', 'G4']  # 5 notes
    
    # Capacity: 2 players * 5 bells = 10 (enough for 5 notes)
    capacity = ArrangementGenerator._calculate_total_capacity(team)
    assert capacity == 10
    assert len(few_notes) <= capacity
    
    # No expansion should be needed
    min_needed = ArrangementGenerator._calculate_minimum_players_needed(few_notes, team)
    expanded = ArrangementGenerator._expand_players(team, min_needed)
    
    # Team size should remain the same
    assert len(expanded) == len(team), "No expansion should occur"


def test_balanced_strategy_distributes_evenly():
    """Test that balanced strategy distributes bells evenly"""
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    notes_freq = ['C4', 'D4', 'E4', 'F4', 'G4']
    note_frequencies = {
        'C4': 100,  # Most frequent
        'D4': 80,
        'E4': 60,
        'F4': 40,
        'G4': 5,    # Least frequent
    }
    
    test_players = [
        {'name': 'P1', 'experience': 'experienced'},
        {'name': 'P2', 'experience': 'intermediate'},
    ]
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes_freq, test_players,
        strategy='balanced',
        config=config,
        note_frequencies=note_frequencies
    )
    
    # Verify all notes assigned
    total_bells = sum(len(assignment[p['name']]['bells']) for p in test_players)
    assert total_bells == len(notes_freq), "All notes should be assigned"
    
    # Both players should have bells
    for player in test_players:
        count = len(assignment[player['name']]['bells'])
        assert count > 0, f"{player['name']} should have bells"


def test_balanced_strategy_with_all_beginners():
    """Test balanced strategy with all beginners (edge case)"""
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    players = [
        {'name': 'Beginner 1', 'experience': 'beginner'},
        {'name': 'Beginner 2', 'experience': 'beginner'},
    ]
    
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4']  # 6 notes, 4 capacity
    
    note_frequencies = {
        'C4': 10, 'D4': 9, 'E4': 8, 'F4': 7, 'G4': 6, 'A4': 5
    }
    
    # This should not raise IndexError
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players,
        strategy='balanced',
        config=config,
        note_frequencies=note_frequencies
    )
    
    # Verify assignments
    total_assigned = sum(len(assignment[p['name']]['bells']) for p in players)
    assert total_assigned <= len(notes), "Cannot assign more bells than notes"
    
    # Each beginner should have at most 2 bells
    for player in players:
        count = len(assignment[player['name']]['bells'])
        assert count <= 2, f"{player['name']} should have max 2 bells, has {count}"
        assert count >= 2, f"{player['name']} should have min 2 bells, has {count}"


def test_experienced_first_prefers_experienced_players():
    """Test that experienced_first strategy assigns more to experienced players"""
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    mixed_players = [
        {'name': 'Expert', 'experience': 'experienced'},
        {'name': 'Intermediate', 'experience': 'intermediate'},
        {'name': 'Beginner', 'experience': 'beginner'},
    ]
    
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, mixed_players, strategy='experienced_first', config=config
    )
    
    expert_bells = len(assignment['Expert']['bells'])
    intermediate_bells = len(assignment['Intermediate']['bells'])
    beginner_bells = len(assignment['Beginner']['bells'])
    
    # Experienced player should typically get the most bells
    assert expert_bells >= intermediate_bells, \
        "Expert should have at least as many bells as intermediate"
    assert expert_bells >= beginner_bells, \
        "Expert should have at least as many bells as beginner"


def test_all_strategies_respect_constraints():
    """Test that all strategies respect experience-level constraints"""
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    mixed_players = [
        {'name': 'Expert', 'experience': 'experienced'},
        {'name': 'Intermediate', 'experience': 'intermediate'},
        {'name': 'Beginner', 'experience': 'beginner'},
    ]
    
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5']
    
    strategies = ['experienced_first', 'balanced', 'min_transitions']
    
    for strategy in strategies:
        assignment = BellAssignmentAlgorithm.assign_bells(
            notes, mixed_players, strategy=strategy, config=config
        )
        
        # Check constraints for each player
        for player in mixed_players:
            exp = player['experience']
            count = len(assignment[player['name']]['bells'])
            max_allowed = config['MAX_BELLS_PER_EXPERIENCE'][exp]
            
            assert count <= max_allowed, \
                f"{strategy}: {player['name']} ({exp}) has {count} bells, max is {max_allowed}"
