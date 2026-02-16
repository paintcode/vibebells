# Vibebells Backend Test Suite

## Overview

Comprehensive test suite for the Vibebells backend, organized into unit tests, integration tests, and manual verification scripts.

## Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest configuration
│   ├── README.md                # This file
│   ├── unit/                    # Unit tests (isolated, fast)
│   │   ├── __init__.py
│   │   ├── test_services.py     # SwapCounter, ExportFormatter (24 tests)
│   │   ├── test_swap_cost.py    # SwapCostCalculator (7 tests)
│   │   └── test_experience_constraints.py  # Experience constraints (5 tests)
│   └── integration/             # Integration tests (end-to-end workflows)
│       ├── __init__.py
│       ├── test_comprehensive_algorithm.py  # Complete algorithm tests (8 tests)
│       ├── test_complete_system.py          # Full system test
│       ├── test_frequency_assignment.py     # Frequency-based assignment
│       ├── test_multibelle.py               # Multi-bell functionality
│       ├── test_player_expansion.py         # Player expansion logic
│       ├── test_sample_music.py             # Real music file test
│       └── test_swap_optimization.py        # Hand swap optimization
└── manual_tests/                # Manual verification scripts (deprecated)
    ├── test_comprehensive_final.py          # Replaced by test_comprehensive_algorithm.py
    └── test_fixed_balanced_strategy.py      # Replaced by test_comprehensive_algorithm.py
```

## Running Tests

**Prerequisites:**
1. You must be in the `backend/` directory (not the project root)
2. You must activate the virtual environment **OR** use the venv python directly

### All Tests

```bash
cd backend

# Option 1: Activate venv first, then use pytest
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pytest tests/ -v

# Option 2: Use venv python directly (no activation needed)
python -m pytest tests/ -v                    # If venv is active
./venv/Scripts/python.exe -m pytest tests/ -v # Windows without venv activation
./venv/bin/python -m pytest tests/ -v         # macOS/Linux without venv activation
```

### Unit Tests Only

```bash
cd backend
python -m pytest tests/unit/ -v
```

### Integration Tests Only

```bash
cd backend
python -m pytest tests/integration/ -v
```

### Specific Test File

```bash
cd backend
python -m pytest tests/unit/test_services.py -v
```

### Specific Test Function

```bash
cd backend
python -m pytest tests/unit/test_services.py::TestSwapCounter::test_three_unique_pitches_simple -v
```

### Using unittest (alternative)

```bash
cd backend
python -m unittest discover -s tests/unit -v
python -m unittest discover -s tests/integration -v
```

## Test Categories

### Unit Tests (77 tests)

**Purpose**: Test individual functions and classes in isolation

**test_file_handler.py** (15 tests) - NEW!
- FileHandler: File validation, saving, and cleanup
  - File type detection (.mid, .midi, .xml, .musicxml)
  - Invalid extension rejection
  - UUID filename generation
  - File save operations and error handling
  - File deletion (existing and nonexistent files)

**test_midi_parser.py** (12 tests) - NEW!
- MIDIParser: MIDI file parsing and error handling
  - Valid MIDI file parsing with tempo and notes
  - Empty MIDI files (no notes)
  - Corrupted/malformed MIDI files
  - Missing tempo (default 120 BPM)
  - Note On without matching Note Off
  - Pitch to note name conversion (C4, A4, sharps, octaves)
  - Required fields validation

**test_musicxml_parser.py** (14 tests) - NEW!
- MusicXMLParser: MusicXML file parsing and error handling
  - Valid MusicXML files with notes and tempo
  - MusicXML files with chords (extracts individual notes)
  - Empty MusicXML files (no notes)
  - Corrupted/malformed XML files
  - Invalid XML structure
  - Missing tempo (default 120 BPM)
  - Pitch to note name conversion
  - Chord information structure validation

**test_services.py** (24 tests)
- SwapCounter: Greedy algorithm for bell swap counting
  - Edge cases: empty lists, single notes, single bell repeated
  - Basic scenarios: 2 bells (no swaps), alternating bells
  - Complex scenarios: 3+ bells, optimal bell dropping, repeating patterns
- ExportFormatter: CSV export formatting
  - Structure: metadata section, players section, bells section
  - Bell assignments: left/right hand, sorting, empty hands
  - Swap counts: included when available, estimated when missing
  - Data quality: CSV parseability, special characters

**test_swap_cost.py** (7 tests)
- SwapCostCalculator: Frequency-based swap cost calculation
  - Basic frequency calculation
  - Hand assignment cost
  - Swap frequency penalties
  - Complex scenarios with multiple players

**test_experience_constraints.py** (5 tests)
- Experience level constraints (beginner=2, intermediate=3, experienced=5 bells)
- Player expansion when capacity insufficient
- Mixed experience level handling

### Integration Tests (15 tests)

**Purpose**: Test complete workflows with multiple components

- **test_comprehensive_algorithm.py** (8 tests) - NEW! Replaces manual tests
  - Experience-level constraints enforcement (2 tests)
  - Player expansion logic (2 tests)
  - Balanced strategy behavior (2 tests)
  - Cross-strategy validation (2 tests)
- **test_complete_system.py**: Full end-to-end system test with real music
- **test_frequency_assignment.py**: Frequency-based bell assignment optimization
- **test_multibelle.py**: Multi-bell assignment with conflict resolution
- **test_player_expansion.py**: Player expansion when insufficient capacity
- **test_sample_music.py**: Real sample music file processing
- **test_swap_optimization.py**: Hand swap optimization (min_transitions strategy)

### Manual Tests (deprecated)

**Purpose**: Interactive verification and debugging tools (replaced by automated tests)

- **test_comprehensive_final.py**: ~~Manual verification script~~ → Use `test_comprehensive_algorithm.py`
- **test_fixed_balanced_strategy.py**: ~~Edge case debugging~~ → Use `test_comprehensive_algorithm.py`

These manual tests are no longer needed as their scenarios are now covered by automated tests.

## Test Coverage

### Core Services
- ✅ **FileHandler: Comprehensive (15 tests) - NEW!**
- ✅ **MIDIParser: Comprehensive (12 tests) - NEW!**
- ✅ **MusicXMLParser: Comprehensive (14 tests) - NEW!**
- ✅ SwapCounter: Comprehensive (24 tests)
- ✅ ExportFormatter: Comprehensive (12 tests in test_services.py)
- ✅ SwapCostCalculator: Good coverage (7 tests)
- ✅ Experience constraints: Comprehensive (13 tests total)
  - Unit tests: 5 tests in test_experience_constraints.py
  - Integration tests: 8 tests in test_comprehensive_algorithm.py
- ✅ Bell assignment strategies: Comprehensive (15 integration tests)

### File Parsing (NEW - Phase 1 Complete)
- ✅ File extension validation
- ✅ UUID filename generation
- ✅ Corrupted/malformed file handling
- ✅ Empty file detection
- ✅ Missing metadata (tempo defaults)
- ✅ MIDI Note On without Note Off
- ✅ MusicXML chord extraction
- ✅ Invalid XML structure detection

### Key Algorithms Tested
- ✅ Greedy lookahead for bell swaps
- ✅ Frequency-based bell assignment
- ✅ Experience-level constraint enforcement (all strategies)
- ✅ Player expansion logic (when capacity insufficient)
- ✅ Conflict resolution
- ✅ CSV export formatting
- ✅ Balanced strategy edge cases (all-beginner scenario)
- ✅ Cross-strategy validation (all respect constraints)

### Areas Without Automated Tests
- ⚠️ MIDI parsing (music21 wrapper)
- ⚠️ MusicXML parsing
- ⚠️ Melody/harmony extraction
- ⚠️ File upload handling
- ⚠️ Flask API endpoints (covered by E2E tests in desktop/e2e)

## Test Maintenance

### Adding New Tests

1. **Unit test** for new service function:
   ```bash
   # Add to appropriate file in tests/unit/
   vim tests/unit/test_myservice.py
   ```

2. **Integration test** for new workflow:
   ```bash
   # Add to tests/integration/
   vim tests/integration/test_my_workflow.py
   ```

3. Run tests to verify:
   ```bash
   pytest tests/ -v
   ```

### Test Naming Conventions

- File names: `test_*.py`
- Test functions: `def test_description()`
- Test classes: `class TestClassName(unittest.TestCase)`

### Code Changes Requiring Test Updates

| Change | Update These Tests |
|--------|-------------------|
| SwapCounter algorithm | `tests/unit/test_services.py` (TestSwapCounter) |
| CSV export format | `tests/unit/test_services.py` (TestExportFormatter) |
| Swap cost calculation | `tests/unit/test_swap_cost.py` |
| Experience constraints | `tests/unit/test_experience_constraints.py` |
| Bell assignment strategy | `tests/integration/test_*_assignment.py` |
| Player expansion | `tests/integration/test_player_expansion.py` |

## Running Manual Tests

Manual tests are scripts that print output for visual verification:

```bash
cd backend
python manual_tests/test_comprehensive_final.py
python manual_tests/test_fixed_balanced_strategy.py
```

These are useful for:
- Debugging specific edge cases
- Visual verification of algorithm behavior
- Interactive testing during development

## Test Dependencies

- **pytest**: Recommended test runner (`pip install pytest`)
- **unittest**: Python standard library (no installation needed)

All tests work with both pytest and unittest.

## Test Philosophy

1. **Unit tests** should be fast, isolated, and test one thing
2. **Integration tests** can be slower, test workflows, use real data
3. **Manual tests** are for debugging and development, not CI/CD
4. **Mock sparingly**: Use real components when possible for integration tests
5. **Test edge cases**: Empty inputs, single items, boundary conditions
6. **Test happy path**: Ensure common workflows work correctly

## Continuous Integration

To run tests in CI/CD pipeline:

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v --tb=short
```

Exit code 0 = all tests passed
Exit code 1 = one or more tests failed

## Debugging Test Failures

1. Run specific failing test:
   ```bash
   pytest tests/unit/test_services.py::TestSwapCounter::test_optimal_greedy_choice -v
   ```

2. Add print statements or use pdb:
   ```python
   import pdb; pdb.set_trace()
   ```

3. Run with more verbose output:
   ```bash
   pytest tests/ -vv -s  # -s shows print statements
   ```

4. Use unittest for detailed tracebacks:
   ```bash
   python -m unittest tests.unit.test_services.TestSwapCounter.test_optimal_greedy_choice
   ```

## Historical Context

Tests were originally in `backend/` root directory. Organized into `tests/` structure in v1.0.1 to follow Python best practices and improve maintainability.

**Previous structure** (deprecated):
- `test_*.py` files scattered in backend/ root
- Harder to distinguish unit vs integration vs manual tests
- Inconsistent import paths

**Current structure** (v1.0.1+):
- Organized `tests/unit/` and `tests/integration/` directories
- Clear separation of test types
- Consistent import paths via `conftest.py`
- Manual tests in separate `manual_tests/` directory

## Contact

For questions about tests or to report test failures, see:
- Main README: `../../README.md`
- GitHub Issues: https://github.com/paintcode/vibebells/issues
