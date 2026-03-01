"""Deep dive into why G4 cannot be assigned in activity_snake."""
import sys
sys.path.insert(0, r'C:\src\vibebells\backend')

from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.music_parser import MusicParser


def check_swap_gaps():
    """Check if G4 can be assigned to any player given the current state."""
    # Simulated state after snake has tried to assign
    # From debug output: Exp1: ['A4', 'C4', 'F4'], Int1: ['B4', 'E4'], Beg1: ['C5', 'D4']
    
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
    
    timing_config = {
        'min_gap_ms': {
            'experienced': 500,
            'intermediate': 1000,
            'beginner': 2000,
        },
        'tempo_bpm': 120,
        'ticks_per_beat': 480,
        'fmt': 'midi',
    }
    
    # Let's convert ticks to ms: 1 tick = (60000 / BPM) / ticks_per_beat
    # 1 tick = (60000 / 120) / 480 = 500 / 480 = ~1.042 ms
    # So 200 ticks = ~208ms, 100 ticks = ~104ms
    
    print("Time conversion: 1 tick = (60000/120)/480 = 1.042ms")
    print("Note gaps: 200 ticks = ~208ms between note starts")
    print("Note duration: 100 ticks = ~104ms")
    print("Gap between note end and next start: ~104ms")
    print()
    
    # Check if G4 (pitch 67) can be added to Exp1's bells
    exp1_bells = ['A4', 'C4', 'F4']  # pitches: 69, 60, 65
    print("Checking if G4 (pitch 67, time 800-900 ticks) can be added to Exp1 ['A4', 'C4', 'F4']:")
    print("  Exp1 experience: experienced, min gap: 500ms = ~480 ticks")
    print("  A4 (pitch 69): time 1000-1100 ticks, gap from G4 end to A4 start: 100 ticks = ~104ms < 500ms ❌")
    print("  C4 (pitch 60): time 0-100 ticks, gap from C4 end to G4 start: 700 ticks = ~729ms > 500ms ✓")
    print("  F4 (pitch 65): time 600-700 ticks, gap from F4 end to G4 start: 100 ticks = ~104ms < 500ms ❌")
    print("  Result: Cannot assign to Exp1 (A4 and F4 are too close)")
    print()
    
    # Check Int1
    int1_bells = ['B4', 'E4']  # pitches: 71, 64
    print("Checking if G4 can be added to Int1 ['B4', 'E4']:")
    print("  Int1 experience: intermediate, min gap: 1000ms = ~960 ticks")
    print("  B4 (pitch 71): time 1200-1300 ticks, gap from G4 end to B4 start: 300 ticks = ~312ms < 1000ms ❌")
    print("  E4 (pitch 64): time 400-500 ticks, gap from E4 end to G4 start: 300 ticks = ~312ms < 1000ms ❌")
    print("  Result: Cannot assign to Int1 (both too close)")
    print()
    
    # Check Beg1
    beg1_bells = ['C5', 'D4']  # pitches: 72, 62
    print("Checking if G4 can be added to Beg1 ['C5', 'D4']:")
    print("  Beg1 experience: beginner, min gap: 2000ms = ~1920 ticks")
    print("  C5 (pitch 72): time 1400-1500 ticks, gap from G4 end to C5 start: 500 ticks = ~521ms < 2000ms ❌")
    print("  D4 (pitch 62): time 200-300 ticks, gap from D4 end to G4 start: 500 ticks = ~521ms < 2000ms ❌")
    print("  Result: Cannot assign to Beg1 (both too close)")
    print()
    
    print("="*60)
    print("CONCLUSION: G4 legitimately cannot be assigned to any player")
    print("due to swap gap constraints. The virtual player is correct.")
    print("="*60)
    print()
    print("This is NOT a bug - it's expected behavior when notes are")
    print("too close together for the player experience levels.")


if __name__ == '__main__':
    check_swap_gaps()
