"""Test for duplicate bell bug in min_transitions second pair selection."""
import sys
sys.path.insert(0, r'C:\src\vibebells\backend')

from app.services.bell_assignment import BellAssignmentAlgorithm


def test_min_transitions_duplicate_bug():
    """
    Test case where pair_count_needed > unique pairs from first pass.
    The second pass (lines 543-550) doesn't check used_bells, potentially
    allowing duplicate bell assignments.
    """
    # Create scenario where we need many pairs but have limited unique pairs
    players = [
        {'name': 'Exp1', 'experience': 'experienced'},
        {'name': 'Exp2', 'experience': 'experienced'},
        {'name': 'Exp3', 'experience': 'experienced'},
    ]
    
    # 12 notes, 6 guaranteed (3*2), 6 extras
    # pair_count_needed = 6, but we might select fewer unique pairs in first pass
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5']
    
    # Create timings where C4-D4 pair has very low cost (will be selected)
    note_timings = []
    pitch_map = {
        'C4': 60, 'D4': 62, 'E4': 64, 'F4': 65, 'G4': 67, 'A4': 69,
        'B4': 71, 'C5': 72, 'D5': 74, 'E5': 76, 'F5': 77, 'G5': 79
    }
    
    # C4 and D4 alternate frequently (low cost pair)
    for i in range(10):
        note_timings.append({'pitch': 60, 'time': i * 1000, 'duration': 200})
        note_timings.append({'pitch': 62, 'time': i * 1000 + 500, 'duration': 200})
    
    # Other notes spread out
    time_offset = 20000
    for note in ['E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5']:
        note_timings.append({'pitch': pitch_map[note], 'time': time_offset, 'duration': 200})
        time_offset += 5000
    
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {'experienced': 5, 'intermediate': 3, 'beginner': 2},
        'MIN_SWAP_GAP_MS': {'experienced': 500, 'intermediate': 1000, 'beginner': 2000},
        'TEMPO_BPM': 120,
        'TICKS_PER_BEAT': 480,
        'MUSIC_FORMAT': 'midi',
    }
    
    print("Testing min_transitions for duplicate bell bug...")
    print(f"Notes: {len(notes)}, Players: {len(players)}, Pair count needed: {len(notes) - len(players)*2}")
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='min_transitions', config=config, note_timings=note_timings
    )
    
    # Check for duplicates
    all_bells = []
    for player_name, data in assignment.items():
        bells = data['bells']
        all_bells.extend(bells)
        print(f"{player_name}: {bells}")
    
    duplicates = [b for b in set(all_bells) if all_bells.count(b) > 1]
    
    if duplicates:
        print(f"\n❌ BUG FOUND: Duplicate bells detected: {duplicates}")
        return False
    
    if len(all_bells) != len(set(all_bells)):
        print(f"\n❌ BUG FOUND: Duplicate count mismatch")
        return False
    
    print(f"\n✓ No duplicates found (tested with {len(all_bells)} bells)")
    return True


if __name__ == '__main__':
    if not test_min_transitions_duplicate_bug():
        sys.exit(1)
