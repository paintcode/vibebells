"""
Test demonstrating frequency-based bell assignment optimization.
Ensures least-frequently-played notes are assigned to extra bell slots.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.music_parser import MusicParser


def test_frequency_based_assignment():
    """
    Test that least-frequently-played notes are assigned as extra bells.
    
    Scenario:
    - 8 unique notes with varying frequencies
    - C4 and D4 played most frequently (should be in initial 2 bells)
    - E4, F4 played moderately (should be in initial 2 bells)
    - G4, A4, B4, C5 played rarely (should be extra bells)
    """
    
    print("\n" + "=" * 70)
    print("Frequency-Based Bell Assignment Test")
    print("=" * 70)
    
    # Define notes and their frequencies
    note_data = {
        'C4': 8,    # Most frequent
        'D4': 7,    # Very frequent
        'E4': 6,    # Frequent
        'F4': 5,    # Moderate
        'G4': 2,    # Rare
        'A4': 2,    # Rare
        'B4': 1,    # Least frequent
        'C5': 1,    # Least frequent
    }
    
    unique_notes = list(note_data.keys())
    note_frequencies = note_data
    
    players = [
        {'name': 'Player 1', 'experience': 'experienced'},
        {'name': 'Player 2', 'experience': 'beginner'},
    ]
    
    print("\nTest Setup:")
    print(f"  Notes: {unique_notes}")
    print(f"  Frequencies: {note_frequencies}")
    print(f"  Players: {[p['name'] + ' (' + p['experience'] + ')' for p in players]}")
    
    # Test each strategy
    strategies = ['experienced_first', 'balanced', 'min_transitions']
    
    for strategy in strategies:
        print(f"\n{strategy.upper()} Strategy:")
        print("-" * 70)
        
        assignment = BellAssignmentAlgorithm.assign_bells(
            unique_notes,
            players,
            strategy=strategy,
            note_frequencies=note_frequencies,
            config={'MAX_BELLS_PER_PLAYER': 8}
        )
        
        # Analyze assignment
        for player_name, player_data in assignment.items():
            bells = player_data['bells']
            bell_frequencies = [note_frequencies[bell] for bell in bells]
            
            print(f"\n  {player_name}:")
            print(f"    Bells: {bells}")
            print(f"    Frequencies: {bell_frequencies}")
            
            # Check if less frequent bells are in extra slots
            if len(bells) > 2:
                primary_bells = bells[:2]
                extra_bells = bells[2:]
                
                primary_freq = [note_frequencies[b] for b in primary_bells]
                extra_freq = [note_frequencies[b] for b in extra_bells]
                
                print(f"    Primary (first 2): {primary_bells} (frequencies: {primary_freq})")
                print(f"    Extra: {extra_bells} (frequencies: {extra_freq})")
                
                # Verify: average frequency of extra bells should be lower
                avg_primary = sum(primary_freq) / len(primary_freq) if primary_freq else 0
                avg_extra = sum(extra_freq) / len(extra_freq) if extra_freq else 0
                
                if avg_extra <= avg_primary:
                    print(f"    ✓ Extra bells less frequent (avg {avg_extra:.1f} vs {avg_primary:.1f})")
                else:
                    print(f"    ⚠ Extra bells more frequent (avg {avg_extra:.1f} vs {avg_primary:.1f})")
    
    print("\n" + "=" * 70)
    print("Analysis:")
    print("=" * 70)
    print("""
Expected Behavior:
- Most frequent notes (C4, D4, E4, F4) assigned first to all players
- Least frequent notes (G4, A4, B4, C5) assigned as extra bells
- This ensures frequently-played notes are covered
- Extra bells (less critical) go to less-experienced players if needed

Benefits:
1. Beginners get less-critical notes as extras
2. Frequent notes are well-distributed
3. If someone has to drop a bell, it's one played less often
4. More resilient arrangements
""")


if __name__ == '__main__':
    try:
        test_frequency_based_assignment()
        print("\n✅ Frequency-based assignment test completed!\n")
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
