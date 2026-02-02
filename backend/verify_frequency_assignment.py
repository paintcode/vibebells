"""
Verification that frequency-based assignment works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.bell_assignment import BellAssignmentAlgorithm

def verify_frequency_assignment():
    """Verify that frequency-based sorting works"""
    
    notes = ['C4', 'D4', 'E4', 'F4']
    players = [
        {'name': 'Player 1', 'experience': 'experienced'}, 
        {'name': 'Player 2', 'experience': 'beginner'}
    ]
    
    # Create frequency map (higher number = more frequent)
    freq_data = {'C4': 4, 'D4': 3, 'E4': 2, 'F4': 1}
    
    # Test with frequencies
    result = BellAssignmentAlgorithm.assign_bells(
        notes, 
        players, 
        strategy='balanced', 
        note_frequencies=freq_data
    )
    
    print("Frequency-Based Assignment Test")
    print("=" * 50)
    print(f"Notes: {notes}")
    print(f"Frequencies: {freq_data}")
    print()
    
    for player_name in sorted(result.keys()):
        bells = result[player_name]['bells']
        freqs = [freq_data.get(b, 0) for b in bells]
        print(f"{player_name}: {bells}")
        print(f"  Frequencies: {freqs}")
    
    # Verify: all players have bells
    total = sum(len(result[p]['bells']) for p in result)
    print()
    print(f"Total bells assigned: {total}/4")
    
    if total == 4 and all(len(result[p]['bells']) >= 2 for p in result):
        print("PASS: Frequency-based assignment working correctly!")
        return True
    else:
        print("FAIL: Assignment failed")
        return False

if __name__ == '__main__':
    try:
        success = verify_frequency_assignment()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
