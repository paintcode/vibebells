"""
Unit tests for SimulationBuilder.

Style: plain pytest functions (no classes, no fixtures).
"""

import logging
from app.services.simulation_builder import SimulationBuilder

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_music_data(notes=None, tempo=120, ticks_per_beat=480, fmt='midi'):
    """Build a minimal music_data dict for testing."""
    if notes is None:
        notes = []
    pitches = list({n['pitch'] for n in notes})
    return {
        'notes': notes,
        'unique_notes': pitches,
        'note_count': len(notes),
        'total_note_events': len(notes),
        'melody_pitches': pitches[:1] if pitches else [],
        'harmony_pitches': pitches[1:] if len(pitches) > 1 else [],
        'frequencies': {},
        'format': fmt,
        'tempo': tempo,
        'ticks_per_beat': ticks_per_beat,
    }


def _make_arrangement(player_data):
    """Build an arrangement dict from {name: (bells, left_hand, right_hand)} tuples."""
    arrangement = {}
    for name, (bells, left, right) in player_data.items():
        arrangement[name] = {
            'bells': bells,
            'left_hand': left,
            'right_hand': right,
        }
    return arrangement


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_ticks_to_ms_conversion():
    """480 ticks at 120 BPM should be 500 ms (one quarter note)."""
    # 480 ticks / 480 ticks_per_beat = 1 beat; 60000 / 120 bpm = 500 ms/beat
    notes = [
        {'pitch': 60, 'velocity': 80, 'time': 0, 'duration': 480},
    ]
    music_data = _make_music_data(notes=notes, tempo=120, ticks_per_beat=480)
    arrangement = _make_arrangement({'Player 1': (['C4'], ['C4'], [])})
    result = SimulationBuilder.build(music_data, arrangement)

    ring_events = [e for p in result['players'] for e in p['events'] if e['type'] == 'ring']
    assert len(ring_events) == 1
    assert ring_events[0]['duration_ms'] == 500


def test_get_bell_data_exact_pitch():
    """C4 (pitch 60) returns exact Malmark values."""
    diam, wt, cpx = SimulationBuilder._get_bell_data(60)
    assert diam == 6.75
    assert wt == 40.0
    assert 10.0 <= cpx <= 50.0


def test_get_bell_data_chromatic_interpolation():
    """C#4 (pitch 61) interpolates between C4 (60) and D4 (62)."""
    diam_c4, wt_c4, _ = SimulationBuilder._get_bell_data(60)
    diam_d4, wt_d4, _ = SimulationBuilder._get_bell_data(62)
    diam_cs, wt_cs, _ = SimulationBuilder._get_bell_data(61)

    # C#4 should be exactly midway
    assert abs(diam_cs - (diam_c4 + diam_d4) / 2) < 0.01
    assert abs(wt_cs - (wt_c4 + wt_d4) / 2) < 0.1


def test_get_bell_data_out_of_range_low():
    """Pitch below table minimum clamps to G2 (pitch 43)."""
    diam_g2, wt_g2, cpx_g2 = SimulationBuilder._get_bell_data(43)
    diam_low, wt_low, cpx_low = SimulationBuilder._get_bell_data(1)
    assert diam_low == diam_g2
    assert wt_low == wt_g2


def test_get_bell_data_out_of_range_high():
    """Pitch above table maximum clamps to C8 (pitch 108)."""
    diam_c8, wt_c8, _ = SimulationBuilder._get_bell_data(108)
    diam_high, wt_high, _ = SimulationBuilder._get_bell_data(127)
    assert diam_high == diam_c8
    assert wt_high == wt_c8


def test_build_simple_two_player():
    """Build simulation with a 2-player arrangement returns correct player count."""
    notes = [
        {'pitch': 60, 'velocity': 80, 'time': 0,   'duration': 480},
        {'pitch': 64, 'velocity': 80, 'time': 480,  'duration': 480},
    ]
    music_data = _make_music_data(notes=notes)
    arrangement = _make_arrangement({
        'Player 1': (['C4'], ['C4'], []),
        'Player 2': (['E4'], ['E4'], []),
    })
    result = SimulationBuilder.build(music_data, arrangement)
    assert len(result['players']) == 2
    assert result['tempo_bpm'] == 120
    assert result['format'] == 'midi'


def test_ring_event_has_duration_ms():
    """Ring events include a duration_ms field matching the note duration."""
    notes = [
        {'pitch': 67, 'velocity': 90, 'time': 0, 'duration': 960},
    ]
    music_data = _make_music_data(notes=notes, tempo=120, ticks_per_beat=480)
    arrangement = _make_arrangement({'P1': (['G4'], ['G4'], [])})
    result = SimulationBuilder.build(music_data, arrangement)
    rings = [e for p in result['players'] for e in p['events'] if e['type'] == 'ring']
    assert rings[0]['duration_ms'] == 1000  # 960 ticks / 480 * 500ms/beat


def test_put_down_has_gap_ms():
    """A swap generates a put_down event with a gap_ms field."""
    # Player has C4 (left) and E4 (left) — play C4 then E4 => swap
    notes = [
        {'pitch': 60, 'velocity': 80, 'time': 0,    'duration': 480},
        {'pitch': 64, 'velocity': 80, 'time': 1920,  'duration': 480},
    ]
    music_data = _make_music_data(notes=notes)
    arrangement = _make_arrangement({'P1': (['C4', 'E4'], ['C4', 'E4'], [])})
    result = SimulationBuilder.build(music_data, arrangement)
    put_downs = [e for p in result['players'] for e in p['events'] if e['type'] == 'put_down']
    assert len(put_downs) >= 1
    assert 'gap_ms' in put_downs[0]


def test_tight_swap_detection():
    """gap_ms < threshold => tight=True."""
    # C4 at t=0 dur=480, E4 at t=490 ticks; gap = 490 - 480 = 10 ticks = ~10ms
    notes = [
        {'pitch': 60, 'velocity': 80, 'time': 0,   'duration': 480},
        {'pitch': 64, 'velocity': 80, 'time': 490,  'duration': 480},
    ]
    music_data = _make_music_data(notes=notes, tempo=120, ticks_per_beat=480)
    arrangement = _make_arrangement({'P1': (['C4', 'E4'], ['C4', 'E4'], [])})
    result = SimulationBuilder.build(music_data, arrangement, tight_swap_threshold_ms=1000)
    put_downs = [e for p in result['players'] for e in p['events'] if e['type'] == 'put_down']
    assert any(e['tight'] is True for e in put_downs)


def test_not_tight_when_gap_sufficient():
    """gap_ms >= threshold => tight=False."""
    # Large gap between notes: 0 and 5000 ticks at 120bpm = 5208ms gap
    notes = [
        {'pitch': 60, 'velocity': 80, 'time': 0,    'duration': 480},
        {'pitch': 64, 'velocity': 80, 'time': 5000,  'duration': 480},
    ]
    music_data = _make_music_data(notes=notes, tempo=120, ticks_per_beat=480)
    arrangement = _make_arrangement({'P1': (['C4', 'E4'], ['C4', 'E4'], [])})
    result = SimulationBuilder.build(music_data, arrangement, tight_swap_threshold_ms=500)
    put_downs = [e for p in result['players'] for e in p['events'] if e['type'] == 'put_down']
    assert all(e['tight'] is False for e in put_downs)


def test_custom_threshold():
    """Passing threshold=500 changes which swaps are tight vs threshold=2000."""
    notes = [
        {'pitch': 60, 'velocity': 80, 'time': 0,    'duration': 480},
        {'pitch': 64, 'velocity': 80, 'time': 720,   'duration': 480},
    ]
    # gap_ms = (720 - 480) / 480 * 500 = 250ms
    music_data = _make_music_data(notes=notes, tempo=120, ticks_per_beat=480)
    arrangement = _make_arrangement({'P1': (['C4', 'E4'], ['C4', 'E4'], [])})

    result_tight = SimulationBuilder.build(music_data, arrangement, tight_swap_threshold_ms=500)
    result_not = SimulationBuilder.build(music_data, arrangement, tight_swap_threshold_ms=100)

    pd_tight = [e for p in result_tight['players'] for e in p['events'] if e['type'] == 'put_down']
    pd_not   = [e for p in result_not['players']   for e in p['events'] if e['type'] == 'put_down']

    assert any(e['tight'] is True  for e in pd_tight)
    assert any(e['tight'] is False for e in pd_not)


def test_fatigue_score_nonzero():
    """A player ringing a heavy bass bell has a non-zero fatigue_score."""
    # G2 (pitch 43) weighs 228 oz
    notes = [
        {'pitch': 43, 'velocity': 80, 'time': 0, 'duration': 480},
    ]
    music_data = _make_music_data(notes=notes)
    arrangement = _make_arrangement({'Bass': (['G2'], ['G2'], [])})
    result = SimulationBuilder.build(music_data, arrangement)
    player = result['players'][0]
    assert player['fatigue_score'] > 0


def test_events_sorted_by_time():
    """Events for a player are in chronological order by time_ms."""
    notes = [
        {'pitch': 60, 'velocity': 80, 'time': 960,  'duration': 480},
        {'pitch': 60, 'velocity': 80, 'time': 0,    'duration': 480},
        {'pitch': 60, 'velocity': 80, 'time': 1920,  'duration': 480},
    ]
    music_data = _make_music_data(notes=notes)
    arrangement = _make_arrangement({'P1': (['C4'], ['C4'], [])})
    result = SimulationBuilder.build(music_data, arrangement)
    events = result['players'][0]['events']
    times = [e['time_ms'] for e in events]
    assert times == sorted(times)


def test_invalid_bell_name_logs_warning(caplog):
    """An unrecognisable bell name logs a warning and is silently skipped."""
    notes = [
        {'pitch': 60, 'velocity': 80, 'time': 0, 'duration': 480},
    ]
    music_data = _make_music_data(notes=notes)
    arrangement = _make_arrangement({'Player 1': (['C4', 'NOT_A_BELL'], ['C4'], ['NOT_A_BELL'])})

    with caplog.at_level(logging.WARNING, logger='app.services.simulation_builder'):
        result = SimulationBuilder.build(music_data, arrangement)

    # The valid bell is still present; the invalid one is absent
    player = result['players'][0]
    bell_names = [b['name'] for b in player['bells']]
    assert 'C4' in bell_names
    assert 'NOT_A_BELL' not in bell_names

    # A warning mentioning both the player name and the bad bell was emitted for each
    # affected code path: right hand, bells list, and metadata construction (3 total).
    assert len(caplog.records) == 3
    assert any('right hand' in r.message for r in caplog.records)
    assert any('bells list' in r.message for r in caplog.records)
    assert any('metadata' in r.message for r in caplog.records)
    assert all('NOT_A_BELL' in r.message and 'Player 1' in r.message for r in caplog.records)
