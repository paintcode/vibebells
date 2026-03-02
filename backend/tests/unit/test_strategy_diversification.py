"""Tests for new strategy diversification behavior."""

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


def test_min_transitions_assigns_same_hand_pairs_to_experienced_first():
    """Pair-first min_transitions should create at least one same-hand bell pair on experienced players."""
    players = [
        {'name': 'Exp 1', 'experience': 'experienced'},
        {'name': 'Exp 2', 'experience': 'experienced'},
        {'name': 'Beg 1', 'experience': 'beginner'},
    ]
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
    note_timings = [
        {'pitch': 60, 'time': 0, 'duration': 100},
        {'pitch': 64, 'time': 220, 'duration': 100},
        {'pitch': 60, 'time': 440, 'duration': 100},
        {'pitch': 64, 'time': 660, 'duration': 100},
        {'pitch': 62, 'time': 880, 'duration': 100},
        {'pitch': 65, 'time': 1100, 'duration': 100},
        {'pitch': 62, 'time': 1320, 'duration': 100},
        {'pitch': 65, 'time': 1540, 'duration': 100},
        {'pitch': 67, 'time': 3000, 'duration': 100},
        {'pitch': 69, 'time': 3500, 'duration': 100},
        {'pitch': 71, 'time': 4000, 'duration': 100},
        {'pitch': 72, 'time': 4500, 'duration': 100},
    ]

    assignment = BellAssignmentAlgorithm.assign_bells(
        notes,
        players,
        strategy='min_transitions',
        config=_base_config(),
        note_timings=note_timings,
    )

    exp_players_with_same_hand_pair = 0
    for name in ('Exp 1', 'Exp 2'):
        pdata = assignment[name]
        if len(pdata.get('left_hand', [])) >= 2 or len(pdata.get('right_hand', [])) >= 2:
            exp_players_with_same_hand_pair += 1

    assert exp_players_with_same_hand_pair >= 1


def test_min_transitions_does_not_assign_same_hand_pair_to_beginner():
    """Beginners (capacity=2) must never receive a same-hand pair in min_transitions."""
    players = [
        {'name': 'Exp 1', 'experience': 'experienced'},
        {'name': 'Beg 1', 'experience': 'beginner'},
    ]
    notes = ['C4', 'D4', 'E4', 'F4']
    note_timings = [
        {'pitch': 60, 'time': 0, 'duration': 100},
        {'pitch': 62, 'time': 220, 'duration': 100},
        {'pitch': 60, 'time': 440, 'duration': 100},
        {'pitch': 62, 'time': 660, 'duration': 100},
        {'pitch': 64, 'time': 3000, 'duration': 100},
        {'pitch': 65, 'time': 3500, 'duration': 100},
        {'pitch': 64, 'time': 4000, 'duration': 100},
        {'pitch': 65, 'time': 4500, 'duration': 100},
    ]

    assignment = BellAssignmentAlgorithm.assign_bells(
        notes,
        players,
        strategy='min_transitions',
        config=_base_config(),
        note_timings=note_timings,
    )

    beg_data = assignment.get('Beg 1', {})
    left = beg_data.get('left_hand', [])
    right = beg_data.get('right_hand', [])
    assert len(left) <= 1, f"Beginner should not have >1 bell on left hand, got {left}"
    assert len(right) <= 1, f"Beginner should not have >1 bell on right hand, got {right}"


def test_snake_strategies_produce_different_assignments():
    """fatigue_snake and activity_snake should diverge when weight and active-time rankings differ."""
    players = [
        {'name': 'P1', 'experience': 'experienced'},
        {'name': 'P2', 'experience': 'experienced'},
    ]
    notes = ['C3', 'C6', 'D4', 'E4']
    note_timings = [
        {'pitch': 48, 'time': 0, 'duration': 200},    # C3 (heavy, shorter)
        {'pitch': 84, 'time': 300, 'duration': 1000}, # C6 (light, longer)
        {'pitch': 62, 'time': 1500, 'duration': 300},
        {'pitch': 64, 'time': 1900, 'duration': 300},
    ]
    config = _base_config()

    fatigue = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='fatigue_snake', config=config, note_timings=note_timings
    )
    activity = BellAssignmentAlgorithm.assign_bells(
        notes, players, strategy='activity_snake', config=config, note_timings=note_timings
    )

    fatigue_assigned = {b for p in fatigue.values() for b in p.get('bells', [])}
    activity_assigned = {b for p in activity.values() for b in p.get('bells', [])}
    assert fatigue_assigned == set(notes)
    assert activity_assigned == set(notes)
    assert fatigue != activity
