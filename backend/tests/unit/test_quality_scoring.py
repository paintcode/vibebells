"""Unit tests for scoring rules and no-drop assignment fallback."""

from app.services.arrangement_validator import ArrangementValidator
from app.services.bell_assignment import BellAssignmentAlgorithm


def test_quality_score_hard_fails_on_dropped_notes():
    """Quality score should hard-fail (0) when expected notes are dropped."""
    complete = {
        "Player 1": {
            "bells": ["C4", "D4", "E4"],
            "left_hand": ["C4", "E4"],
            "right_hand": ["D4"],
        }
    }
    dropped = {
        "Player 1": {
            "bells": ["C4", "D4"],  # E4 dropped
            "left_hand": ["C4"],
            "right_hand": ["D4"],
        }
    }
    music_data = {
        "unique_notes": [60, 62, 64],
        "notes": [
            {"pitch": 60, "time": 0, "duration": 480},
            {"pitch": 62, "time": 1440, "duration": 480},
            {"pitch": 64, "time": 2880, "duration": 480},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }

    complete_score = ArrangementValidator.calculate_quality_score(complete, music_data)
    dropped_score = ArrangementValidator.calculate_quality_score(dropped, music_data)

    assert complete_score > 0
    assert dropped_score == 0


def test_quality_score_penalizes_unbalanced_bell_counts():
    """Score should be lower when players are <2 bells and spread is >=2."""
    balanced = {
        "P1": {"bells": ["C4", "D4"], "left_hand": ["C4"], "right_hand": ["D4"]},
        "P2": {"bells": ["E4", "F4"], "left_hand": ["E4"], "right_hand": ["F4"]},
    }
    unbalanced = {
        "P1": {"bells": ["C4", "D4", "E4", "F4"], "left_hand": ["C4", "E4"], "right_hand": ["D4", "F4"]},
        "P2": {"bells": [], "left_hand": [], "right_hand": []},
    }
    music_data = {
        "unique_notes": [60, 62, 64, 65],
        "notes": [
            {"pitch": 60, "time": 0, "duration": 240},
            {"pitch": 62, "time": 1200, "duration": 240},
            {"pitch": 64, "time": 2400, "duration": 240},
            {"pitch": 65, "time": 3600, "duration": 240},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }

    balanced_score = ArrangementValidator.calculate_quality_score(balanced, music_data)
    unbalanced_score = ArrangementValidator.calculate_quality_score(unbalanced, music_data)
    assert unbalanced_score < balanced_score


def test_quality_score_penalizes_players_with_over_five_swaps():
    """Playability score should drop when a player exceeds 5 swaps."""
    arrangement = {
        "Player 1": {
            "bells": ["C4", "D4"],
            "left_hand": ["C4"],
            "right_hand": ["D4"],
        }
    }
    high_swaps_notes = []
    low_swaps_notes = []
    for i in range(12):
        # 1200 ticks between starts, 120 duration => large safe gaps
        high_swaps_notes.append({"pitch": 60 if i % 2 == 0 else 62, "time": i * 1200, "duration": 120})
        low_swaps_notes.append({"pitch": 60 if i < 6 else 62, "time": i * 1200, "duration": 120})

    high_swaps_data = {
        "unique_notes": [60, 62],
        "notes": high_swaps_notes,
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }
    low_swaps_data = {
        "unique_notes": [60, 62],
        "notes": low_swaps_notes,
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }

    high_swaps_score = ArrangementValidator.calculate_quality_score(arrangement, high_swaps_data)
    low_swaps_score = ArrangementValidator.calculate_quality_score(arrangement, low_swaps_data)
    assert high_swaps_score < low_swaps_score


def test_quality_score_hard_fails_on_impossible_swaps():
    """Score should be 0 when same-hand swaps need less than 1s gap."""
    arrangement = {
        "Player 1": {
            "bells": ["C4", "D4", "E4"],
            "left_hand": ["C4", "E4"],
            "right_hand": ["D4"],
        }
    }
    # Left-hand C4 -> E4 gap is 500ms (impossible by 1s threshold)
    music_data = {
        "unique_notes": [60, 62, 64],
        "notes": [
            {"pitch": 60, "time": 0, "duration": 480},
            {"pitch": 62, "time": 480, "duration": 120},
            {"pitch": 64, "time": 960, "duration": 240},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }
    assert ArrangementValidator.calculate_quality_score(arrangement, music_data) == 0


def test_assign_bells_adds_virtual_player_when_gap_blocks_both_hands():
    """If extra bell is infeasible on both hands, algorithm should add a virtual player."""
    players = [{"name": "Player 1", "experience": "experienced"}]
    notes = ["C4", "D4", "E4"]
    # E4 overlaps tightly with both C4 and D4, so both hands should fail the gap check.
    note_timings = [
        {"pitch": 60, "time": 0, "duration": 480},   # C4
        {"pitch": 62, "time": 0, "duration": 480},   # D4
        {"pitch": 64, "time": 240, "duration": 120}, # E4 (overlaps both)
    ]
    config = {
        "MAX_BELLS_PER_PLAYER": 8,
        "MAX_BELLS_PER_EXPERIENCE": {
            "experienced": 5,
            "intermediate": 3,
            "beginner": 2,
        },
        "MIN_SWAP_GAP_MS": {
            "experienced": 1000,
            "intermediate": 1000,
            "beginner": 1000,
        },
        "TEMPO_BPM": 120,
        "TICKS_PER_BEAT": 480,
        "MUSIC_FORMAT": "midi",
    }

    assignment = BellAssignmentAlgorithm.assign_bells(
        notes,
        players,
        strategy="balanced",
        config=config,
        note_timings=note_timings,
    )

    assigned = {bell for pdata in assignment.values() for bell in pdata.get("bells", [])}
    assert set(notes).issubset(assigned)
    assert any(name.startswith("Virtual Player") for name in assignment.keys())
