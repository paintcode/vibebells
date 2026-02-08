# Unit Tests for SwapCounter and ExportFormatter

## Test Suite Overview

**File**: `backend/test_services.py`
**Framework**: Python unittest (standard library)
**Total Tests**: 24
**Status**: ✅ All passing

## Running the Tests

```bash
cd backend
python -m unittest test_services -v
```

Output:
```
Ran 24 tests in 0.676s
OK
```

## Test Coverage

### SwapCounter Tests (13 tests)

#### Edge Cases
- ✅ `test_no_notes` - Empty note list returns 0 swaps
- ✅ `test_single_note` - Single note requires no swaps
- ✅ `test_single_bell_repeated` - Single bell played multiple times requires no swaps

#### Basic Scenarios
- ✅ `test_two_unique_pitches` - Two bells (1 per hand) = 0 swaps
- ✅ `test_alternating_two_bells` - Alternating between 2 bells = 0 swaps

#### Three Bell Scenarios
- ✅ `test_three_unique_pitches_simple` - C-D-E-D-C sequence = 2 swaps
  - Start with C and D
  - Pick up E when needed (swap 1)
  - Pick up C when needed again (swap 2)

- ✅ `test_three_unique_pitches_clustered` - C-D-E clustered = 1 swap
  - Start with C and D
  - Pick up E immediately (swap 1)

#### Advanced Scenarios
- ✅ `test_four_unique_pitches` - A-B-C-D sequence = 2 swaps
- ✅ `test_optimal_greedy_choice` - Greedy algorithm picks correct bell to drop
  - When multiple bells are held, drops the one needed furthest in future
- ✅ `test_complex_sequence` - A-B-C-A-B-C-A-B-C with 3 bells
  - Tests algorithm on repeating pattern

### ExportFormatter Tests (11 tests)

#### CSV Structure
- ✅ `test_csv_structure_has_sections` - Has Metadata, Players, and Bells sections
- ✅ `test_csv_metadata_section` - Metadata includes filename and strategy
- ✅ `test_csv_players_section` - Players section lists all players with experience
- ✅ `test_timestamp_in_metadata` - Timestamp included in generated date

#### Bell Assignments
- ✅ `test_hand_assignments_displayed` - Left and right hand bells shown correctly
- ✅ `test_empty_hands` - Players with empty hands display correctly
- ✅ `test_bell_sorting_by_pitch` - Bells sorted C4, D4, E4, F4, G4... (pitch order)
- ✅ `test_all_bells_extraction` - All unique bells included in output

#### Swap Counts
- ✅ `test_swap_counts_with_data` - CSV includes swap counts when provided
- ✅ `test_swap_counts_fallback` - CSV estimates swaps if not provided

#### Data Quality
- ✅ `test_csv_parseable` - Output is valid CSV (parseable by csv module)
- ✅ `test_special_characters_in_filename` - Handles filenames with special characters

### Integration Tests (2 tests)

- ✅ `test_calculate_swaps_for_arrangement` - Full arrangement swap calculation works
- ✅ `test_calculate_swaps_missing_music_data` - Handles missing music data gracefully

## Test Examples

### SwapCounter: C-D-E-D-C Sequence

```python
notes = [
    {'pitch': 60, 'time': 0},  # C4
    {'pitch': 62, 'time': 1},  # D4
    {'pitch': 64, 'time': 2},  # E4
    {'pitch': 62, 'time': 3},  # D4
    {'pitch': 60, 'time': 4},  # C4
]
# Expected result: 2 swaps
```

**Execution:**
1. Start: holding C4 (left), D4 (right)
2. Play C4: already holding ✓
3. Play D4: already holding ✓
4. Play E4: NOT holding
   - C4 next at position 4
   - D4 next at position 3
   - Drop C4 (position 4 > 3), pick up E4
   - **SWAP #1**
5. Play D4: already holding ✓
6. Play C4: NOT holding
   - D4 never appears again
   - Drop D4, pick up C4
   - **SWAP #2**

**Result**: 2 swaps ✓

### ExportFormatter: CSV Output

Input:
```python
arrangement = {
    'Player 1': {'left_hand': ['C4', 'D4'], 'right_hand': ['E4']},
    'Player 2': {'left_hand': ['F4'], 'right_hand': ['G4']}
}
players = [
    {'name': 'Player 1', 'experience': 'experienced'},
    {'name': 'Player 2', 'experience': 'beginner'}
]
```

Output (with swaps):
```csv
Metadata
Uploaded File,test.mid
Strategy,balanced
Generated,2026-02-08 02:30:45

Players
Player,Experience,Left Hand,Right Hand,Bell Swaps
Player 1,experienced,C4 D4,E4,2
Player 2,beginner,F4,G4,0

All Bells (sorted by pitch)
C4
D4
E4
F4
G4
```

## Key Test Insights

### SwapCounter Algorithm Verification

The tests verify the greedy lookahead algorithm works correctly:

1. **Optimal Bell Dropping**: When a swap is needed, the algorithm correctly identifies which bell to drop by looking ahead to find when each held bell is needed next.

2. **Repeated Notes**: The algorithm correctly handles repeated notes (doesn't count re-playing a held bell as a swap).

3. **Complex Patterns**: Tests verify behavior on repeating patterns (ABC-ABC-ABC) to ensure the algorithm adapts throughout the sequence.

### ExportFormatter Validation

1. **Pitch Order**: Tests verify bells are sorted correctly (C < D < E < F < G within each octave, then by octave).

2. **CSV Standards**: Tests parse output as CSV to ensure valid formatting.

3. **Graceful Degradation**: When swap counts aren't provided, the formatter falls back to an estimation algorithm.

## Running Individual Tests

```bash
# Test a specific class
python -m unittest test_services.TestSwapCounter -v

# Test a specific method
python -m unittest test_services.TestSwapCounter.test_three_unique_pitches_simple -v
```

## Test Maintenance

When modifying swap counting or export logic:

1. Run full test suite: `python -m unittest test_services -v`
2. Check that all 24 tests pass
3. Add new tests for any new edge cases discovered

## Coverage Analysis

- **SwapCounter**: Covers initialization, edge cases, basic 2-bell scenarios, 3+ bell scenarios, greedy algorithm verification, complex patterns
- **ExportFormatter**: Covers CSV structure, bell sorting, hand assignments, swap count inclusion, special characters, data parsing
- **Integration**: Covers full arrangement processing with real data structures

No external test framework dependencies required - uses Python standard library unittest module.
