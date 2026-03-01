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
            "bells": ["C4", "D4", "E4"],
            "left_hand": ["C4", "E4"],
            "right_hand": ["D4"],
        }
    }
    high_swaps_notes = []
    low_swaps_notes = []
    for i in range(12):
        # 1200 ticks between starts, 120 duration => large safe gaps
        high_swaps_notes.append({"pitch": 60 if i % 2 == 0 else 64, "time": i * 1200, "duration": 120})
        low_swaps_notes.append({"pitch": 60 if i < 6 else 64, "time": i * 1200, "duration": 120})

    high_swaps_data = {
        "unique_notes": [60, 64],
        "notes": high_swaps_notes,
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }
    low_swaps_data = {
        "unique_notes": [60, 64],
        "notes": low_swaps_notes,
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }

    high_swaps_score = ArrangementValidator.calculate_quality_score(arrangement, high_swaps_data)
    low_swaps_score = ArrangementValidator.calculate_quality_score(arrangement, low_swaps_data)
    assert high_swaps_score < low_swaps_score


def test_quality_score_hard_fails_on_impossible_swaps():
    """Score should be 0 when same-hand swaps need less than Config.IMPOSSIBLE_SWAP_GAP_MS (500ms)."""
    arrangement = {
        "Player 1": {
            "bells": ["C4", "D4", "E4"],
            "left_hand": ["C4", "E4"],
            "right_hand": ["D4"],
        }
    }
    # Left-hand C4 -> E4 gap is ~250ms (< 500ms IMPOSSIBLE_SWAP_GAP_MS threshold)
    # At 120 BPM, 480 ticks/beat: C4 ends at tick 480 (500ms), E4 starts at tick 720 (750ms) → 250ms gap
    music_data = {
        "unique_notes": [60, 62, 64],
        "notes": [
            {"pitch": 60, "time": 0, "duration": 480},
            {"pitch": 62, "time": 480, "duration": 120},
            {"pitch": 64, "time": 720, "duration": 240},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }
    assert ArrangementValidator.calculate_quality_score(arrangement, music_data) == 0


def test_quality_breakdown_exposes_component_details():
    """Breakdown should include weights, component earned/max, penalties and final score."""
    arrangement = {
        "P1": {"bells": ["C4", "D4"], "left_hand": ["C4"], "right_hand": ["D4"]},
        "P2": {"bells": ["E4", "F4"], "left_hand": ["E4"], "right_hand": ["F4"]},
    }
    music_data = {
        "unique_notes": [60, 62, 64, 65],
        "notes": [
            {"pitch": 60, "time": 0, "duration": 120},
            {"pitch": 62, "time": 1200, "duration": 120},
            {"pitch": 64, "time": 2400, "duration": 120},
            {"pitch": 65, "time": 3600, "duration": 120},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }
    breakdown = ArrangementValidator.calculate_quality_breakdown(arrangement, music_data)
    assert breakdown["weights"] == {"playability": 50, "bell_fairness": 30, "fatigue_fairness": 20}
    assert "components" in breakdown and "penalties" in breakdown
    assert breakdown["components"]["playability"]["max"] == 50
    assert breakdown["components"]["bell_fairness"]["max"] == 30
    assert breakdown["components"]["fatigue_fairness"]["max"] == 20
    assert isinstance(breakdown["final_score"], (int, float))


def test_quality_breakdown_hard_fail_reasons_present():
    """Hard-fail breakdown should include a dropped-notes reason."""
    arrangement = {
        "Player 1": {"bells": ["C4"], "left_hand": ["C4"], "right_hand": []},
    }
    music_data = {
        "unique_notes": [60, 62],
        "notes": [
            {"pitch": 60, "time": 0, "duration": 120},
            {"pitch": 62, "time": 1200, "duration": 120},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }
    breakdown = ArrangementValidator.calculate_quality_breakdown(arrangement, music_data)
    assert breakdown["hard_fail"] is True
    assert any("Dropped notes" in r for r in breakdown["hard_fail_reasons"])
    assert breakdown["final_score"] == 0


def test_pressure_events_count_tight_swaps_between_thresholds():
    """Gaps between IMPOSSIBLE_SWAP_GAP_MS (500ms) and pressure_gap_ms (1000ms)
    should NOT cause a hard-fail but SHOULD count as pressure events and apply a penalty."""
    arrangement = {
        "Player 1": {
            "bells": ["C4", "E4"],
            "left_hand": ["C4", "E4"],  # both on left hand forces a same-hand swap
            "right_hand": [],
        }
    }
    # At 120 BPM, 480 ticks/beat:
    # C4 ends at tick 480 (500ms), E4 starts at tick 1200 (1250ms) → gap = 750ms
    # 750ms > 500ms (Config.IMPOSSIBLE_SWAP_GAP_MS): no hard-fail
    # 750ms < 1000ms (pressure_gap_ms):              counts as a pressure event
    music_data = {
        "unique_notes": [60, 64],
        "notes": [
            {"pitch": 60, "time": 0, "duration": 480},
            {"pitch": 64, "time": 1200, "duration": 240},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }
    breakdown = ArrangementValidator.calculate_quality_breakdown(arrangement, music_data)
    assert breakdown["hard_fail"] is False
    assert breakdown["penalties"]["hand_load_pressure_events"] == 1
    assert breakdown["penalties"]["hand_pressure_penalty"] > 0


def test_pressure_events_ignore_same_bell_repeats():
    """Fast repeats of the same bell on one hand should not count as pressure events."""
    arrangement = {
        "Player 1": {
            "bells": ["C4", "D4"],
            "left_hand": ["C4"],
            "right_hand": ["D4"],
        }
    }
    music_data = {
        "unique_notes": [60, 62],
        "notes": [
            {"pitch": 60, "time": 0, "duration": 120},
            {"pitch": 60, "time": 240, "duration": 120},
            {"pitch": 60, "time": 480, "duration": 120},
            {"pitch": 62, "time": 2000, "duration": 120},
        ],
        "format": "midi",
        "tempo": 120,
        "ticks_per_beat": 480,
    }
    breakdown = ArrangementValidator.calculate_quality_breakdown(arrangement, music_data)
    assert breakdown["hard_fail"] is False
    assert breakdown["penalties"]["hand_load_pressure_events"] == 0


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
