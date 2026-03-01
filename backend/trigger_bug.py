"""Create scenario that actually triggers the duplicate bell bug."""
import sys
sys.path.insert(0, r'C:\src\vibebells\backend')

from app.services.bell_assignment import BellAssignmentAlgorithm


def trigger_duplicate_bug():
    """
    Force the bug by creating scenario where:
    1. We need 3 pairs (9 notes - 3*2 = 3 extras)
    2. Only 1 unique pair can be selected initially (due to used_bells check)
    3. Second pass will add 2 more pairs without checking used_bells
    
    Strategy: Make C4-D4 the best pair, but also have C4-E4 and D4-F4 as pairs
    """
    players = [
        {'name': 'Exp1', 'experience': 'experienced'},
        {'name': 'Exp2', 'experience': 'experienced'},
        {'name': 'Exp3', 'experience': 'experienced'},
    ]
    
    # 9 notes: 6 guaranteed + 3 extras -> pair_count_needed = 3
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5']
    
    pitch_map = {'C4': 60, 'D4': 62, 'E4': 64, 'F4': 65, 'G4': 67, 
                 'A4': 69, 'B4': 71, 'C5': 72, 'D5': 74}
    
    # Create pairs with overlapping bells:
    # C4-D4: 10 transitions (worst)
    # C4-E4: 5 transitions
    # D4-F4: 5 transitions
    # G4-A4: 3 transitions
    # B4-C5: 2 transitions
    # D5 alone
    
    note_timings = []
    
    # C4-D4 alternate 10 times (10 transitions)
    for i in range(10):
        note_timings.append({'pitch': 60, 'time': i * 200, 'duration': 50})
        note_timings.append({'pitch': 62, 'time': i * 200 + 100, 'duration': 50})
    
    # C4-E4 alternate 5 times (5 transitions)
    for i in range(5):
        note_timings.append({'pitch': 60, 'time': 5000 + i * 200, 'duration': 50})
        note_timings.append({'pitch': 64, 'time': 5000 + i * 200 + 100, 'duration': 50})
    
    # D4-F4 alternate 5 times (5 transitions)
    for i in range(5):
        note_timings.append({'pitch': 62, 'time': 10000 + i * 200, 'duration': 50})
        note_timings.append({'pitch': 65, 'time': 10000 + i * 200 + 100, 'duration': 50})
    
    # G4-A4 alternate 3 times (3 transitions)
    for i in range(3):
        note_timings.append({'pitch': 67, 'time': 15000 + i * 200, 'duration': 50})
        note_timings.append({'pitch': 69, 'time': 15000 + i * 200 + 100, 'duration': 50})
    
    # B4-C5 alternate 2 times (2 transitions) - BEST pair
    for i in range(2):
        note_timings.append({'pitch': 71, 'time': 20000 + i * 200, 'duration': 50})
        note_timings.append({'pitch': 72, 'time': 20000 + i * 200 + 100, 'duration': 50})
    
    # D5 alone
    note_timings.append({'pitch': 74, 'time': 25000, 'duration': 50})
    
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {'experienced': 5, 'intermediate': 3, 'beginner': 2},
        'MIN_SWAP_GAP_MS': {'experienced': 50, 'intermediate': 100, 'beginner': 200},
        'TEMPO_BPM': 120,
        'TICKS_PER_BEAT': 480,
        'MUSIC_FORMAT': 'midi',
    }
    
    print("Attempting to trigger duplicate bell bug...")
    print(f"Notes: {notes}")
    print(f"Pair count needed: {len(notes) - len(players) * 2} = 3")
    print("\nExpected pair ranking (by transitions, then -avg_gap):")
    print("  1. B4-C5: 2 transitions")
    print("  2. G4-A4: 3 transitions")
    print("  3. C4-E4: 5 transitions (but C4 used if C4-D4 or C4-E4 selected)")
    print("  4. D4-F4: 5 transitions (but D4 used if C4-D4 or D4-F4 selected)")
    print("  5. C4-D4: 10 transitions")
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='min_transitions', config=config, note_timings=note_timings
    )
    
    # Check results
    all_bells = []
    for player_name, data in assignment.items():
        bells = data['bells']
        all_bells.extend(bells)
        print(f"\n{player_name}: {bells}")
    
    duplicates = [b for b in set(all_bells) if all_bells.count(b) > 1]
    
    if duplicates:
        print(f"\n❌ BUG CONFIRMED: Duplicate bells: {duplicates}")
        return False
    
    print(f"\n✓ No duplicates (total {len(all_bells)} bells)")
    return True


if __name__ == '__main__':
    trigger_duplicate_bug()
