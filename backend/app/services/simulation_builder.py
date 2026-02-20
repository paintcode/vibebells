"""
Simulation Builder - Generate player event timelines for bell arrangement animation.

Produces a serializable data structure that the frontend uses to animate
stick-figure players ringing handbells in sync with the uploaded music.
"""

import logging

logger = logging.getLogger(__name__)

# Malmark handbell data: MIDI pitch -> (diameter_in, weight_oz)
# Source: Malmark manufacturer specifications. Diatonic pitches only.
_MALMARK_DATA = {
    43: (14.0, 228),    # G2
    45: (13.0, 199),    # A2
    47: (11.125, 148),  # B2
    48: (10.875, 140),  # C3
    50: (10.25, 124),   # D3
    52: (9.75, 104),    # E3
    53: (9.0, 96),      # F3
    55: (8.125, 60),    # G3
    57: (7.5, 52),      # A3
    59: (7.25, 48),     # B3
    60: (6.75, 40),     # C4
    62: (6.625, 40),    # D4
    64: (6.125, 40),    # E4
    65: (5.875, 41),    # F4
    67: (5.625, 32),    # G4
    69: (5.125, 28),    # A4
    71: (4.75, 24),     # B4
    72: (4.5, 24),      # C5
    74: (4.25, 21),     # D5
    76: (4.25, 19),     # E5
    77: (4.125, 18),    # F5
    79: (3.875, 17),    # G5
    81: (3.625, 15),    # A5
    83: (3.5, 14),      # B5
    84: (3.375, 13),    # C6
    86: (3.25, 13),     # D6
    88: (3.125, 12),    # E6
    89: (3.0, 10),      # F6
    91: (2.875, 9),     # G6
    93: (2.75, 9),      # A6
    95: (2.625, 9),     # B6
    96: (2.5, 8),       # C7
    98: (2.5, 8),       # D7
    100: (2.375, 8),    # E7
    101: (2.375, 8),    # F7
    103: (2.25, 8),     # G7
    105: (2.25, 8),     # A7
    107: (2.25, 8),     # B7
    108: (2.25, 8),     # C8
}

_SORTED_PITCHES = sorted(_MALMARK_DATA.keys())

# Canvas size mapping: C3 (10.875") -> 50px, C8 (2.25") -> 10px
_DIAM_MAX = 10.875  # C3
_DIAM_MIN = 2.25    # C8
_PX_MAX = 50.0
_PX_MIN = 10.0


class SimulationBuilder:
    """Build simulation event timelines for bell arrangement animation."""

    @staticmethod
    def _get_bell_data(pitch):
        """Return (diameter_in, weight_oz, canvas_px) for any MIDI pitch.

        Linearly interpolates for chromatic pitches between nearest diatonic
        neighbors. Clamps to table bounds for out-of-range pitches.
        """
        if pitch in _MALMARK_DATA:
            diam, wt = _MALMARK_DATA[pitch]
        else:
            keys = _SORTED_PITCHES
            if pitch <= keys[0]:
                diam, wt = _MALMARK_DATA[keys[0]]
            elif pitch >= keys[-1]:
                diam, wt = _MALMARK_DATA[keys[-1]]
            else:
                lower = max(k for k in keys if k <= pitch)
                upper = min(k for k in keys if k >= pitch)
                t = (pitch - lower) / (upper - lower)
                dlo, wlo = _MALMARK_DATA[lower]
                dhi, whi = _MALMARK_DATA[upper]
                diam = dlo + t * (dhi - dlo)
                wt = wlo + t * (whi - wlo)

        canvas_px = _PX_MIN + (diam - _DIAM_MIN) / (_DIAM_MAX - _DIAM_MIN) * (_PX_MAX - _PX_MIN)
        canvas_px = max(_PX_MIN, min(_PX_MAX, canvas_px))

        return round(diam, 3), round(wt, 1), round(canvas_px, 1)

    @staticmethod
    def build(music_data, arrangement, tight_swap_threshold_ms=1000):
        """Build a simulation data structure for the given arrangement.

        Args:
            music_data: Parsed music dict (from MusicParser.parse).
            arrangement: Assignment dict {player_name: {'bells', 'left_hand', 'right_hand'}}.
            tight_swap_threshold_ms: Gap threshold in ms below which a swap is flagged tight.

        Returns:
            Serializable dict describing player timelines for animation.
        """
        from app.services.music_parser import MusicParser

        fmt = music_data.get('format', 'midi')
        tempo_bpm = int(music_data.get('tempo', 120))
        all_notes = music_data.get('notes', [])

        if fmt == 'midi':
            ticks_per_beat = int(music_data.get('ticks_per_beat', 480))
        else:
            # MusicXML uses quarter_length units; treat as ticks_per_beat=1 sentinel
            ticks_per_beat = 1

        def to_ms(ticks_or_ql):
            """Convert ticks (MIDI) or quarter_length (MusicXML) to ms."""
            return ticks_or_ql / ticks_per_beat * (60000.0 / tempo_bpm)

        def note_time_ms(n):
            if fmt == 'midi':
                return to_ms(n.get('time', n.get('offset', 0)))
            else:
                return to_ms(n.get('offset', 0))

        def note_dur_ms(n):
            if fmt == 'midi':
                return to_ms(n.get('duration', 1))
            else:
                return to_ms(n.get('duration', 0.5))

        # Determine total duration from last note end
        duration_ms = 0
        for n in all_notes:
            end = note_time_ms(n) + note_dur_ms(n)
            if end > duration_ms:
                duration_ms = end

        players_out = []

        for player_name, player_data in arrangement.items():
            left_hand_bells = player_data.get('left_hand', [])
            right_hand_bells = player_data.get('right_hand', [])
            all_bell_names = player_data.get('bells', list(set(left_hand_bells) | set(right_hand_bells)))

            # Build pitch->hand and pitch->name mappings
            hand_map = {}   # pitch -> 'left' or 'right'
            name_map = {}   # pitch -> note_name
            bell_pitches = set()

            for bell_name in left_hand_bells:
                try:
                    p = MusicParser.note_name_to_pitch(bell_name)
                    hand_map[p] = 'left'
                    name_map[p] = bell_name
                    bell_pitches.add(p)
                except (ValueError, KeyError):
                    logger.warning(
                        "Could not convert bell '%s' to pitch for player '%s' (left hand); skipping.",
                        bell_name, player_name,
                    )

            for bell_name in right_hand_bells:
                try:
                    p = MusicParser.note_name_to_pitch(bell_name)
                    hand_map[p] = 'right'
                    name_map[p] = bell_name
                    bell_pitches.add(p)
                except (ValueError, KeyError):
                    logger.warning(
                        "Could not convert bell '%s' to pitch for player '%s' (right hand); skipping.",
                        bell_name, player_name,
                    )

            # Handle bells listed only in 'bells' (not in hand lists)
            for bell_name in all_bell_names:
                try:
                    p = MusicParser.note_name_to_pitch(bell_name)
                    if p not in hand_map:
                        hand_map[p] = 'left'
                        name_map[p] = bell_name
                        bell_pitches.add(p)
                except (ValueError, KeyError):
                    logger.warning(
                        "Could not convert bell '%s' to pitch for player '%s' (bells list); skipping.",
                        bell_name, player_name,
                    )

            # Build bells metadata list
            bells_meta = []
            for bell_name in all_bell_names:
                try:
                    p = MusicParser.note_name_to_pitch(bell_name)
                    diam, wt, cpx = SimulationBuilder._get_bell_data(p)
                    bells_meta.append({
                        'name': bell_name,
                        'pitch': p,
                        'hand': hand_map.get(p, 'left'),
                        'diameter_in': diam,
                        'weight_oz': wt,
                        'canvas_px': cpx,
                    })
                except (ValueError, KeyError):
                    logger.warning(
                        "Could not build metadata for bell '%s' for player '%s'; skipping.",
                        bell_name, player_name,
                    )
            weight_by_pitch = {b['pitch']: b['weight_oz'] for b in bells_meta}

            # Filter and sort notes for this player
            player_notes = [n for n in all_notes if n.get('pitch') in bell_pitches]
            player_notes.sort(key=lambda n: note_time_ms(n))

            # Determine initial held bells per hand (first unique pitch seen per hand)
            holding = {'left': None, 'right': None}
            for n in player_notes:
                p = n.get('pitch')
                h = hand_map.get(p, 'left')
                if holding[h] is None:
                    holding[h] = p
                if holding['left'] is not None and holding['right'] is not None:
                    break

            # Track last ring end time per hand for put_down placement
            last_ring_end = {'left': None, 'right': None}  # (time_ms, duration_ms)

            events = []

            for n in player_notes:
                pitch = n.get('pitch')
                if pitch is None or pitch not in bell_pitches:
                    continue

                ring_time = note_time_ms(n)
                ring_dur = note_dur_ms(n)
                velocity = n.get('velocity', 80)
                hand = hand_map.get(pitch, 'left')
                bell_name = name_map.get(pitch, MusicParser.pitch_to_note_name(pitch))

                # Check if we need a swap on this hand
                if holding[hand] != pitch:
                    old_pitch = holding[hand]
                    # put_down time = end of last ring on this hand
                    if last_ring_end[hand] is not None:
                        pd_time = last_ring_end[hand]
                        gap_ms = ring_time - pd_time
                        if gap_ms < 0:
                            gap_ms = 0
                            pd_time = ring_time
                    else:
                        pd_time = ring_time
                        gap_ms = 0

                    tight = gap_ms < tight_swap_threshold_ms

                    if old_pitch is not None:
                        old_name = name_map.get(old_pitch, MusicParser.pitch_to_note_name(old_pitch))
                        events.append({
                            'type': 'put_down',
                            'bell_name': old_name,
                            'pitch': old_pitch,
                            'hand': hand,
                            'time_ms': int(round(pd_time)),
                            'gap_ms': int(round(gap_ms)),
                            'tight': tight,
                        })

                    events.append({
                        'type': 'pick_up',
                        'bell_name': bell_name,
                        'pitch': pitch,
                        'hand': hand,
                        'time_ms': int(round(ring_time)),
                    })

                    holding[hand] = pitch

                # Emit ring event
                events.append({
                    'type': 'ring',
                    'bell_name': bell_name,
                    'pitch': pitch,
                    'hand': hand,
                    'time_ms': int(round(ring_time)),
                    'duration_ms': int(round(ring_dur)),
                    'velocity': velocity,
                })

                # Update last ring end time for this hand
                last_ring_end[hand] = ring_time + ring_dur

            # Sort events by time_ms
            events.sort(key=lambda e: e['time_ms'])

            # Compute fatigue score
            fatigue_score = 0.0
            for ev in events:
                if ev['type'] == 'ring':
                    wt = weight_by_pitch.get(ev['pitch'], 0.0)
                    fatigue_score += ev['duration_ms'] * wt

            players_out.append({
                'name': player_name,
                'bells': bells_meta,
                'fatigue_score': round(fatigue_score, 2),
                'events': events,
            })

        return {
            'tempo_bpm': tempo_bpm,
            'ticks_per_beat': ticks_per_beat,
            'format': fmt,
            'duration_ms': int(round(duration_ms)),
            'tight_swap_threshold_ms': tight_swap_threshold_ms,
            'players': players_out,
        }
