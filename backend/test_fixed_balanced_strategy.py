#!/usr/bin/env python3
"""Test the fixed balanced strategy with all-beginner scenario"""

import sys
sys.path.insert(0, '.')

from app.services.bell_assignment import BellAssignmentAlgorithm

print("\nTesting Balanced Strategy - All Beginners Edge Case")
print("-" * 60)

# Edge case: all beginners with extra notes (tests the fix)
players = [
    {'name': 'Beginner 1', 'experience': 'beginner'},
    {'name': 'Beginner 2', 'experience': 'beginner'},
]

notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4']  # 6 notes, 4 capacity

config = {
    'MAX_BELLS_PER_PLAYER': 8,
    'MAX_BELLS_PER_EXPERIENCE': {
        'experienced': 5,
        'intermediate': 3,
        'beginner': 2
    }
}

note_frequencies = {
    'C4': 10, 'D4': 9, 'E4': 8, 'F4': 7, 'G4': 6, 'A4': 5
}

# This should work without IndexError (the fix ensures capable_players check)
try:
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players,
        strategy='balanced',
        config=config,
        note_frequencies=note_frequencies
    )
    
    print("PASS: No IndexError on empty capable_players")
    
    # Verify assignments
    total_assigned = sum(len(assignment[p['name']]['bells']) for p in players)
    print("Assignments:")
    for player in players:
        bells = assignment[player['name']]['bells']
        print("  %s: %d bells" % (player['name'], len(bells)))
    
    print("Total assigned: %d/%d" % (total_assigned, len(notes)))
    
    # Beginners should stay at 2 each (max)
    for player in players:
        count = len(assignment[player['name']]['bells'])
        if count != 2:
            print("ERROR: Beginner does not have 2 bells: %d" % count)
            sys.exit(1)
    
    print("PASS: All beginners have exactly 2 bells")
    print("SUCCESS: Fixed balanced strategy works correctly")
    
except IndexError as e:
    print("FAIL: IndexError occurred (fix not working)")
    print("Error: %s" % str(e))
    sys.exit(1)
except Exception as e:
    print("FAIL: Unexpected error")
    print("Error: %s" % str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
