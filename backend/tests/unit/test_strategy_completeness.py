"""Tests for strategy completeness: no duplicates, no unassigned notes, edge cases."""

from app.services.bell_assignment import BellAssignmentAlgorithm


def _base_config():
    return {
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


def test_all_strategies_no_duplicates_or_unassigned_notes():
    """All strategies must assign every note exactly once and respect experience caps.

    Uses tight note timings (200 ticks apart at 120 BPM ≈ 208 ms gaps) so that
    swap-gap constraints are active — any unassigned note would fall through to a
    virtual player, making the total assigned count still equal to len(notes).
    """
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
    config = _base_config()
    exp_cap = config['MAX_BELLS_PER_EXPERIENCE']

    for strategy in ['experienced_first', 'balanced', 'min_transitions', 'fatigue_snake', 'activity_snake']:
        assignment = BellAssignmentAlgorithm.assign_bells(
            notes, players, strategy=strategy, config=config, note_timings=note_timings
        )

        all_bells = [b for data in assignment.values() for b in data['bells']]

        # No duplicate assignments
        assert len(all_bells) == len(set(all_bells)), \
            f"{strategy}: duplicate bell(s) found: {[b for b in set(all_bells) if all_bells.count(b) > 1]}"

        # All notes assigned (possibly to virtual players, but never dropped)
        assert set(all_bells) == set(notes), \
            f"{strategy}: unassigned notes: {set(notes) - set(all_bells)}"

        # Experience caps respected for non-virtual players
        for player in players:
            count = len(assignment[player['name']]['bells'])
            cap = exp_cap[player['experience']]
            assert count <= cap, \
                f"{strategy}: {player['name']} ({player['experience']}) has {count} bells, max {cap}"


def test_snake_strategies_with_single_player():
    """Snake strategies should assign all notes to the sole player.

    Notes are spaced 1000 ticks apart (≈1042 ms at 120 BPM / 480 TPB), well above the
    500 ms experienced swap-gap minimum, so every note fits on the single player.
    """
    players = [{'name': 'Solo', 'experience': 'experienced'}]
    notes = ['C4', 'D4', 'E4', 'F4', 'G4']
    note_timings = [
        {'pitch': 60, 'time': 0,    'duration': 100},
        {'pitch': 62, 'time': 1000, 'duration': 100},
        {'pitch': 64, 'time': 2000, 'duration': 100},
        {'pitch': 65, 'time': 3000, 'duration': 100},
        {'pitch': 67, 'time': 4000, 'duration': 100},
    ]
    config = _base_config()

    for strategy in ['fatigue_snake', 'activity_snake']:
        assignment = BellAssignmentAlgorithm.assign_bells(
            notes, players, strategy=strategy, config=config, note_timings=note_timings
        )

        solo_bells = assignment['Solo']['bells']
        assert set(solo_bells) == set(notes), \
            f"{strategy}: single player should have all notes; missing {set(notes) - set(solo_bells)}"
        assert len(solo_bells) == len(set(solo_bells)), \
            f"{strategy}: single player has duplicate bells"


def test_min_transitions_no_duplicate_bells_regression():
    """Regression: pair selection second pass must not reuse bells already in a pair.

    12 notes for 3 experienced players → pair_count_needed = 6.
    C4 and D4 alternate frequently (low swap cost, will be selected in first pass).
    Without the used_bells guard on the second pass, (C4, E4) or (D4, F4) could be
    selected alongside (C4, D4), causing C4 or D4 to appear in two pairs.
    """
    players = [
        {'name': 'Exp1', 'experience': 'experienced'},
        {'name': 'Exp2', 'experience': 'experienced'},
        {'name': 'Exp3', 'experience': 'experienced'},
    ]
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5']

    # C4 (60) and D4 (62) alternate 10× → lowest swap cost pair
    note_timings = []
    for i in range(10):
        note_timings.append({'pitch': 60, 'time': i * 1000, 'duration': 200})
        note_timings.append({'pitch': 62, 'time': i * 1000 + 500, 'duration': 200})
    # Remaining notes spaced well apart
    time_offset = 20000
    for name, pitch in [('E4', 64), ('F4', 65), ('G4', 67), ('A4', 69),
                         ('B4', 71), ('C5', 72), ('D5', 74), ('E5', 76), ('F5', 77), ('G5', 79)]:
        note_timings.append({'pitch': pitch, 'time': time_offset, 'duration': 200})
        time_offset += 5000

    config = _base_config()
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='min_transitions', config=config, note_timings=note_timings
    )

    all_bells = [b for data in assignment.values() for b in data['bells']]
    duplicates = [b for b in set(all_bells) if all_bells.count(b) > 1]
    assert not duplicates, f"Duplicate bells from overlapping pairs: {duplicates}"
    assert set(all_bells) == set(notes), \
        f"Unassigned notes: {set(notes) - set(all_bells)}"
