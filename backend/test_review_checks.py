"""Comprehensive checks for code review: duplications, unassigned notes, experience caps."""
import sys
sys.path.insert(0, r'C:\src\vibebells\backend')

from app.services.bell_assignment import BellAssignmentAlgorithm


def check_for_duplicates_and_unassigned():
    """Test all strategies for note duplication and unassigned notes."""
    players = [
        {'name': 'Exp1', 'experience': 'experienced'},
        {'name': 'Int1', 'experience': 'intermediate'},
        {'name': 'Beg1', 'experience': 'beginner'},
    ]
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
    
    note_timings = [
        {'pitch': 60, 'time': 0, 'duration': 100},
        {'pitch': 62, 'time': 200, 'duration': 100},
        {'pitch': 64, 'time': 400, 'duration': 100},
        {'pitch': 65, 'time': 600, 'duration': 100},
        {'pitch': 67, 'time': 800, 'duration': 100},
        {'pitch': 69, 'time': 1000, 'duration': 100},
        {'pitch': 71, 'time': 1200, 'duration': 100},
        {'pitch': 72, 'time': 1400, 'duration': 100},
    ]
    
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2,
        },
        'MIN_SWAP_GAP_MS': {
            'experienced': 500,
            'intermediate': 1000,
            'beginner': 2000,
        },
        'TEMPO_BPM': 120,
        'TICKS_PER_BEAT': 480,
        'MUSIC_FORMAT': 'midi',
    }
    
    strategies = ['experienced_first', 'balanced', 'min_transitions', 'fatigue_snake', 'activity_snake']
    
    for strategy in strategies:
        print(f"\nTesting {strategy}...")
        assignment = BellAssignmentAlgorithm.assign_bells(
            notes, players, strategy=strategy, config=config, note_timings=note_timings
        )
        
        # Check for duplicates
        all_assigned_bells = []
        for player_name, data in assignment.items():
            all_assigned_bells.extend(data['bells'])
        
        if len(all_assigned_bells) != len(set(all_assigned_bells)):
            from collections import Counter
            counts = Counter(all_assigned_bells)
            duplicates = [note for note, count in counts.items() if count > 1]
            print(f"  ❌ DUPLICATE BELLS FOUND: {duplicates}")
            print(f"  Assignment: {assignment}")
            return False
        
        # Check for unassigned notes
        assigned_set = set(all_assigned_bells)
        unassigned = set(notes) - assigned_set
        if unassigned:
            print(f"  ❌ UNASSIGNED NOTES: {unassigned}")
            print(f"  Assignment: {assignment}")
            return False
        
        # Check experience caps
        for player_name, data in assignment.items():
            player = next(p for p in players if p['name'] == player_name)
            exp = player['experience']
            max_allowed = config['MAX_BELLS_PER_EXPERIENCE'][exp]
            actual_count = len(data['bells'])
            if actual_count > max_allowed:
                print(f"  ❌ EXPERIENCE CAP VIOLATED: {player_name} ({exp}) has {actual_count} bells, max is {max_allowed}")
                print(f"  Assignment: {assignment}")
                return False
        
        print(f"  ✓ {strategy} passed all checks")
    
    print("\n✅ All strategies passed: no duplicates, no unassigned notes, experience caps respected")
    return True


def check_min_transitions_pair_logic():
    """Test that pair selection doesn't create invalid state."""
    players = [
        {'name': 'Exp1', 'experience': 'experienced'},
        {'name': 'Exp2', 'experience': 'experienced'},
    ]
    # 6 notes, 4 players * 2 = 4 guaranteed, 2 extras, should select 1 pair
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4']
    
    note_timings = [
        {'pitch': 60, 'time': 0, 'duration': 100},
        {'pitch': 62, 'time': 150, 'duration': 100},
        {'pitch': 64, 'time': 300, 'duration': 100},
        {'pitch': 65, 'time': 450, 'duration': 100},
        {'pitch': 67, 'time': 600, 'duration': 100},
        {'pitch': 69, 'time': 750, 'duration': 100},
    ]
    
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {'experienced': 5, 'intermediate': 3, 'beginner': 2},
        'MIN_SWAP_GAP_MS': {'experienced': 500, 'intermediate': 1000, 'beginner': 2000},
        'TEMPO_BPM': 120,
        'TICKS_PER_BEAT': 480,
        'MUSIC_FORMAT': 'midi',
    }
    
    print("\nTesting min_transitions pair logic...")
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='min_transitions', config=config, note_timings=note_timings
    )
    
    # Verify all notes assigned
    all_assigned = []
    for data in assignment.values():
        all_assigned.extend(data['bells'])
    
    if set(all_assigned) != set(notes):
        print(f"  ❌ Not all notes assigned: {set(notes) - set(all_assigned)}")
        return False
    
    if len(all_assigned) != len(set(all_assigned)):
        print(f"  ❌ Duplicate bells in assignment")
        return False
    
    print(f"  ✓ min_transitions pair logic test passed")
    return True


def check_snake_with_single_player():
    """Test snake strategies handle single-player edge case."""
    players = [{'name': 'Solo', 'experience': 'experienced'}]
    notes = ['C4', 'D4', 'E4', 'F4', 'G4']
    
    note_timings = [
        {'pitch': 60, 'time': 0, 'duration': 100},
        {'pitch': 62, 'time': 100, 'duration': 100},
        {'pitch': 64, 'time': 200, 'duration': 100},
        {'pitch': 65, 'time': 300, 'duration': 100},
        {'pitch': 67, 'time': 400, 'duration': 100},
    ]
    
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {'experienced': 5, 'intermediate': 3, 'beginner': 2},
        'MIN_SWAP_GAP_MS': {'experienced': 500, 'intermediate': 1000, 'beginner': 2000},
        'TEMPO_BPM': 120,
        'TICKS_PER_BEAT': 480,
        'MUSIC_FORMAT': 'midi',
    }
    
    for strategy in ['fatigue_snake', 'activity_snake']:
        print(f"\nTesting {strategy} with single player...")
        assignment = BellAssignmentAlgorithm.assign_bells(
            notes, players, strategy=strategy, config=config, note_timings=note_timings
        )
        
        solo_bells = assignment['Solo']['bells']
        if len(solo_bells) != len(notes):
            print(f"  ❌ {strategy}: Expected {len(notes)} bells, got {len(solo_bells)}")
            return False
        
        if set(solo_bells) != set(notes):
            print(f"  ❌ {strategy}: Not all notes assigned")
            return False
        
        print(f"  ✓ {strategy} single player test passed")
    
    return True


if __name__ == '__main__':
    all_passed = True
    
    all_passed &= check_for_duplicates_and_unassigned()
    all_passed &= check_min_transitions_pair_logic()
    all_passed &= check_snake_with_single_player()
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL REVIEW CHECKS PASSED")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME REVIEW CHECKS FAILED")
        print("="*60)
        sys.exit(1)
