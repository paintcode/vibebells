"""Debug why activity_snake is creating virtual players."""
import sys
sys.path.insert(0, r'C:\src\vibebells\backend')

from app.services.bell_assignment import BellAssignmentAlgorithm


def debug_activity_snake():
    """Debug why activity_snake creates virtual player."""
    players = [
        {'name': 'Exp1', 'experience': 'experienced'},
        {'name': 'Int1', 'experience': 'intermediate'},
        {'name': 'Beg1', 'experience': 'beginner'},
    ]
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
    
    note_timings = [
        {'pitch': 60, 'time': 0, 'duration': 100},    # C4
        {'pitch': 62, 'time': 200, 'duration': 100},  # D4
        {'pitch': 64, 'time': 400, 'duration': 100},  # E4
        {'pitch': 65, 'time': 600, 'duration': 100},  # F4
        {'pitch': 67, 'time': 800, 'duration': 100},  # G4
        {'pitch': 69, 'time': 1000, 'duration': 100}, # A4
        {'pitch': 71, 'time': 1200, 'duration': 100}, # B4
        {'pitch': 72, 'time': 1400, 'duration': 100}, # C5
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
    
    # Expected capacity: Exp1: 5, Int1: 3, Beg1: 2 = 10 total
    # We have 8 notes, so all should fit
    
    print("Testing activity_snake with debugging...")
    print(f"Total notes: {len(notes)}")
    print(f"Total capacity: 5 (exp) + 3 (int) + 2 (beg) = 10")
    print(f"Note timings (all 200 ticks apart, equal 100 tick duration):")
    for nt in note_timings:
        print(f"  Pitch {nt['pitch']}: time={nt['time']}, duration={nt['duration']}")
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='activity_snake', config=config, note_timings=note_timings
    )
    
    print("\nAssignment result:")
    for player_name, data in assignment.items():
        bells = data['bells']
        print(f"  {player_name}: {len(bells)} bells - {bells}")
    
    # Check if virtual player was created
    has_virtual = any('Virtual' in pname for pname in assignment.keys())
    if has_virtual:
        print("\n❌ Virtual player was created - there's likely a bug in activity_snake")
        print("   All 8 notes should fit in capacity of 10")
        return False
    else:
        print("\n✓ No virtual player needed - correct behavior")
        return True


if __name__ == '__main__':
    debug_activity_snake()
