"""Unit tests for quality scoring penalties and no-drop assignment fallback."""

from app.services.arrangement_validator import ArrangementValidator
from app.services.bell_assignment import BellAssignmentAlgorithm


def test_quality_score_penalizes_dropped_notes():
    """Quality score should be lower when expected notes are missing from assignment."""
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
        "unique_notes": [60, 62, 64],  # C4, D4, E4
        "notes": [
            {"pitch": 60, "time": 0, "duration": 480},
            {"pitch": 62, "time": 480, "duration": 480},
            {"pitch": 64, "time": 960, "duration": 480},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }

    complete_score = ArrangementValidator.calculate_quality_score(complete, music_data)
    dropped_score = ArrangementValidator.calculate_quality_score(dropped, music_data)

    assert dropped_score < complete_score


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
