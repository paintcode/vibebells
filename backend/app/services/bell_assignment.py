import logging
from app.services.music_parser import MusicParser

logger = logging.getLogger(__name__)

class BellAssignmentAlgorithm:
    """Implements the bell assignment algorithm with multi-bell support"""
    
    @staticmethod
    def assign_bells(notes, players, strategy='experienced_first', priority_notes=None, config=None, note_timings=None, note_frequencies=None):
        """
        Assign bells to players based on strategy, supporting multiple bells per player.
        
        Args:
            notes: List of unique note names (e.g., ['C4', 'D4', 'E4'])
            players: List of player dicts with 'name' and 'experience'
            strategy: Assignment strategy ('experienced_first', 'balanced', 'min_transitions')
            priority_notes: Optional list of notes to prioritize (e.g., melody notes)
            config: Optional config dict with MAX_BELLS_PER_PLAYER, MIN_SWAP_GAP_MS,
                    TEMPO_BPM, TICKS_PER_BEAT, MUSIC_FORMAT
            note_timings: Optional list of full note dicts with timing info (for swap cost optimization)
            note_frequencies: Optional dict mapping notes to frequency counts (for assignment ordering)
        
        Returns:
            Dict mapping player names to assignment dicts with 'bells', 'left_hand', 'right_hand'
            
        Raises:
            ValueError: If validation fails
        """
        
        if not players:
            raise ValueError("At least one player is required")
        
        if not notes:
            raise ValueError("At least one note is required")
        
        if len(players) < 1:
            raise ValueError("Invalid player count")
        
        max_bells = config.get('MAX_BELLS_PER_PLAYER', 8) if config else 8
        
        # Get experience-level-based max bells configuration
        max_bells_per_player = config.get('MAX_BELLS_PER_EXPERIENCE', {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }) if config else {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }

        # Build timing config for swap-gap feasibility checks
        timing_config = None
        if config and note_timings:
            timing_config = {
                'min_gap_ms': config.get('MIN_SWAP_GAP_MS', {
                    'experienced': 500,
                    'intermediate': 1000,
                    'beginner': 2000,
                }),
                'tempo_bpm': config.get('TEMPO_BPM', 120),
                'ticks_per_beat': config.get('TICKS_PER_BEAT', 480),
                'fmt': config.get('MUSIC_FORMAT', 'midi'),
            }
        
        # Initialize assignments with hand tracking
        assignments = {}
        for player in players:
            assignments[player['name']] = {
                'bells': [],
                'left_hand': [],
                'right_hand': []
            }
        
        player_bell_counts = {player['name']: 0 for player in players}
        
        # Sort players by experience
        experience_order = {'experienced': 0, 'intermediate': 1, 'beginner': 2}
        sorted_players = sorted(players, key=lambda p: experience_order.get(p.get('experience', 'beginner'), 2))
        
        if strategy == 'experienced_first':
            assignments = BellAssignmentAlgorithm._assign_experienced_first(
                notes, sorted_players, assignments, player_bell_counts, priority_notes, max_bells_per_player, note_frequencies,
                note_timings=note_timings, timing_config=timing_config
            )
        elif strategy == 'balanced':
            assignments = BellAssignmentAlgorithm._assign_balanced(
                notes, sorted_players, assignments, player_bell_counts, priority_notes, max_bells_per_player, note_frequencies,
                note_timings=note_timings, timing_config=timing_config
            )
        elif strategy == 'min_transitions':
            assignments = BellAssignmentAlgorithm._assign_min_transitions(
                notes, sorted_players, assignments, player_bell_counts, priority_notes, max_bells_per_player, note_timings, note_frequencies,
                timing_config=timing_config
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Virtual player fallback: any note not assigned to any player gets its own virtual player.
        # This can happen when swap gap constraints prevent assignment to all existing players.
        assigned_bells = {b for p_data in assignments.values() for b in p_data['bells']}
        unassigned = [n for n in notes if n not in assigned_bells]
        if unassigned:
            logger.warning(f"Adding virtual players for {len(unassigned)} notes that couldn't meet swap gap constraints")
            vp_idx = sum(1 for p in sorted_players if p.get('virtual')) + 1
            for note in unassigned:
                # Reuse an existing virtual player that still has capacity (≤1 bell so far)
                vp = next(
                    (p for p in sorted_players
                     if p.get('virtual') and len(assignments[p['name']]['bells']) < 2),
                    None
                )
                if vp is None:
                    vname = f'Virtual Player {vp_idx}'
                    while vname in assignments:
                        vp_idx += 1
                        vname = f'Virtual Player {vp_idx}'
                    vp_idx += 1
                    vp = {'name': vname, 'experience': 'intermediate', 'virtual': True}
                    sorted_players.append(vp)
                    player_bell_counts[vname] = 0
                    assignments[vname] = {'bells': [], 'left_hand': [], 'right_hand': []}
                assignments[vp['name']]['bells'].append(note)
                player_bell_counts[vp['name']] += 1

        # Assign bells to specific hands
        assignments = BellAssignmentAlgorithm._assign_hands(assignments)
        
        return assignments
    
    @staticmethod
    def _check_swap_gap_for_hand(existing_hand_names, new_bell_name, note_timings, timing_config, experience):
        """Return True if adding new_bell_name to a hand is timing-feasible.

        Checks every swap between new_bell_name and any bell already on the hand has a
        gap (end of prev note → start of next) >= the min_gap_ms for this experience level.
        Returns True if timing data is unavailable.
        """
        if not timing_config or not note_timings or not existing_hand_names:
            return True

        gap_map = timing_config.get('min_gap_ms', {})
        min_gap = gap_map.get(experience, 1000) if isinstance(gap_map, dict) else int(gap_map)
        if min_gap <= 0:
            return True

        existing_pitches = set()
        for bn in existing_hand_names:
            try:
                existing_pitches.add(MusicParser.note_name_to_pitch(bn))
            except (ValueError, KeyError):
                pass

        try:
            new_pitch = MusicParser.note_name_to_pitch(new_bell_name)
        except (ValueError, KeyError):
            return True

        fmt = timing_config.get('fmt', 'midi')
        tpb = max(timing_config.get('ticks_per_beat', 480), 1)
        bpm = max(timing_config.get('tempo_bpm', 120), 1)

        def to_ms(t):
            return t / tpb * (60000.0 / bpm) if fmt == 'midi' else t * (60000.0 / bpm)

        # Build or reuse a cached per-pitch event map to avoid O(N^2) rescanning.
        pitch_events = timing_config.get('_pitch_events_ms')
        if pitch_events is None:
            pitch_events = {}
            for n in note_timings:
                p = n.get('pitch')
                if p is None:
                    continue
                t_raw = n.get('time', n.get('offset', 0))
                d_raw = n.get('duration', 0)
                start_ms = to_ms(t_raw)
                end_ms = start_ms + to_ms(d_raw)
                pitch_events.setdefault(p, []).append((start_ms, end_ms, p))
            timing_config['_pitch_events_ms'] = pitch_events

        if not pitch_events:
            return True

        hand_events = []
        for p in existing_pitches:
            hand_events.extend(pitch_events.get(p, ()))
        new_events = list(pitch_events.get(new_pitch, ()))

        if not new_events:
            return True  # New bell never played; safe to assign

        all_events = sorted(hand_events + new_events, key=lambda e: e[0])
        for i in range(1, len(all_events)):
            prev, curr = all_events[i - 1], all_events[i]
            if prev[2] != curr[2] and curr[0] - prev[1] < min_gap:
                return False

        return True

    @staticmethod
    def _try_extra_bell(assignment, bell_name, note_timings, timing_config, experience):
        """Try to add bell_name as an extra bell to a player, trying both hands.

        Tries the less-loaded hand first for balance. If that hand's swap gap is too
        tight, tries the other hand. If both fail, returns False without modifying
        the assignment. On success, updates assignment['bells'] and records the chosen
        hand in assignment['_hand_map'].
        """
        hand_map = assignment.get('_hand_map', {})
        left_bells, right_bells = [], []
        for idx, b in enumerate(assignment['bells']):
            hand = hand_map.get(b, 'left' if idx % 2 == 0 else 'right')
            (left_bells if hand == 'left' else right_bells).append(b)

        # Try less-loaded hand first for balance
        if len(left_bells) <= len(right_bells):
            hand_order = [('left', left_bells), ('right', right_bells)]
        else:
            hand_order = [('right', right_bells), ('left', left_bells)]

        for target_hand, hand_bells in hand_order:
            if BellAssignmentAlgorithm._check_swap_gap_for_hand(
                    hand_bells, bell_name, note_timings, timing_config, experience):
                assignment['bells'].append(bell_name)
                assignment.setdefault('_hand_map', {})[bell_name] = target_hand
                return True

        return False

    @staticmethod
    def _assign_experienced_first(notes, players, assignments, counts, priority_notes=None, max_bells_per_player=None, note_frequencies=None, note_timings=None, timing_config=None):
        """Assign bells ensuring every player gets at least 2, then extras to experienced/intermediate players.
        
        Experience-level constraints:
        - Beginner: max 2 bells (1 per hand, hard limit)
        - Intermediate: max 3 bells
        - Experienced: max 5 bells
        
        Sorts non-priority notes by frequency (descending) so most-played bells are assigned first.
        Least-played bells remain for extra bell slots.
        """
        
        if max_bells_per_player is None:
            max_bells_per_player = {'experienced': 5, 'intermediate': 3, 'beginner': 2}
        
        priority_notes = priority_notes or []
        all_notes = list(notes)
        assigned_notes = set()
        
        # Sort non-priority notes by frequency (most frequent first)
        # This ensures frequent bells are assigned early, leaving rare bells for extras
        non_priority_notes = [n for n in all_notes if n not in priority_notes]
        if note_frequencies:
            non_priority_notes.sort(key=lambda n: note_frequencies.get(n, 0), reverse=True)
            logger.debug(f"Sorted {len(non_priority_notes)} non-priority notes by frequency (descending)")
        
        # Phase 1: Ensure every player gets at least 2 bells
        for _ in range(2):  # Two rounds to give each player 2 bells
            for player in players:
                if counts[player['name']] < 2 and all_notes:
                    # Prefer priority notes, then remaining (sorted by frequency, most frequent first)
                    note = None
                    for n in priority_notes:
                        if n not in assigned_notes:
                            note = n
                            break
                    if not note:
                        for n in non_priority_notes:
                            if n not in assigned_notes:
                                note = n
                                break
                    
                    if note:
                        assignments[player['name']]['bells'].append(note)
                        counts[player['name']] += 1
                        assigned_notes.add(note)
        
        # Phase 2: Assign remaining priority notes to experienced/intermediate players
        for note in priority_notes:
            if note not in assigned_notes:
                for player in players:
                    experience = player.get('experience', 'beginner')
                    max_for_exp = max_bells_per_player.get(experience, 2)
                    if counts[player['name']] < max_for_exp:
                        if BellAssignmentAlgorithm._try_extra_bell(
                                assignments[player['name']], note, note_timings, timing_config, experience):
                            counts[player['name']] += 1
                            assigned_notes.add(note)
                            break
        
        # Phase 3: Assign remaining notes (sorted by frequency - least frequent last)
        # Distribute to experienced AND intermediate players only (round-robin among them)
        capable_players = [p for p in players if p.get('experience', 'beginner') in ['experienced', 'intermediate']]
        
        for note in non_priority_notes:
            if note not in assigned_notes:
                for player in capable_players:
                    experience = player.get('experience', 'beginner')
                    max_for_exp = max_bells_per_player.get(experience, 2)
                    if counts[player['name']] < max_for_exp:
                        if BellAssignmentAlgorithm._try_extra_bell(
                                assignments[player['name']], note, note_timings, timing_config, experience):
                            counts[player['name']] += 1
                            assigned_notes.add(note)
                            break
        
        unassigned_count = len(all_notes) - len(assigned_notes)
        if unassigned_count > 0:
            logger.warning(f"Could not assign {unassigned_count} notes due to player capacity limits")
        
        return assignments
    
    @staticmethod
    def _assign_balanced(notes, players, assignments, counts, priority_notes=None, max_bells_per_player=None, note_frequencies=None, note_timings=None, timing_config=None):
        """Distribute notes evenly: ensure each player gets 2 bells first, then distribute extras.
        
        Experience-level constraints:
        - Beginner: max 2 bells (1 per hand, hard limit)
        - Intermediate: max 3 bells
        - Experienced: max 5 bells
        
        **NEW: Sort ALL notes by frequency (including melody) so most-played notes are distributed first.
        This provides more balanced difficulty distribution across players.**
        """
        
        if max_bells_per_player is None:
            max_bells_per_player = {'experienced': 5, 'intermediate': 3, 'beginner': 2}
        
        priority_notes = priority_notes or []
        non_priority = [n for n in notes if n not in priority_notes]
        
        # Sort ALL notes by frequency (most frequent first) - including melody/priority notes
        all_notes = list(priority_notes) + non_priority
        if note_frequencies:
            all_notes.sort(key=lambda n: note_frequencies.get(n, 0), reverse=True)
            logger.debug(f"Sorted ALL {len(all_notes)} notes by frequency (descending)")
        
        # Phase 1: Ensure every player gets at least 2 bells using round-robin
        note_idx = 0
        for _ in range(2):  # Two rounds to give each player 2 bells
            for player in players:
                if counts[player['name']] < 2 and note_idx < len(all_notes):
                    assignments[player['name']]['bells'].append(all_notes[note_idx])
                    counts[player['name']] += 1
                    note_idx += 1
        
        # Phase 2: Distribute remaining notes round-robin to experienced/intermediate players
        # Beginners stay at 2 bells, others can get up to their max
        capable_players = [p for p in players if p.get('experience', 'beginner') in ['experienced', 'intermediate']]

        if capable_players:
            cap_start = 0  # round-robin start index
            while note_idx < len(all_notes):
                note = all_notes[note_idx]
                note_assigned = False
                # Try every capable player once (round-robin starting from cap_start)
                for i in range(len(capable_players)):
                    player = capable_players[(cap_start + i) % len(capable_players)]
                    experience = player.get('experience', 'beginner')
                    max_for_exp = max_bells_per_player.get(experience, 2)
                    if counts[player['name']] < max_for_exp:
                        if BellAssignmentAlgorithm._try_extra_bell(
                                assignments[player['name']], note, note_timings, timing_config, experience):
                            counts[player['name']] += 1
                            # Advance round-robin past the player that accepted
                            cap_start = (cap_start + i + 1) % len(capable_players)
                            note_assigned = True
                            break
                if not note_assigned:
                    logger.debug(f"Balanced strategy: note {note!r} could not be assigned to any capable player (swap gap or capacity); will use virtual player fallback")
                # Always advance to the next note; unassigned notes go to virtual fallback
                note_idx += 1
        
        if note_idx < len(all_notes):
            logger.warning(f"Balanced strategy: Could not assign {len(all_notes) - note_idx} notes due to capacity")
        
        return assignments
    
    @staticmethod
    def _assign_min_transitions(notes, players, assignments, counts, priority_notes=None, max_bells_per_player=None, note_timings=None, note_frequencies=None, timing_config=None):
        """Assign notes with swap cost optimization: minimize hand swaps.
        
        Experience-level constraints:
        - Beginner: max 2 bells (1 per hand, hard limit)
        - Intermediate: max 3 bells
        - Experienced: max 5 bells
        
        Sorts non-priority notes by frequency (descending) so most-played bells are assigned first.
        Least-played bells remain for extra bell slots.
        If note_timings provided, uses SwapCostCalculator to prefer bells that require fewer hand swaps.
        """
        
        if max_bells_per_player is None:
            max_bells_per_player = {'experienced': 5, 'intermediate': 3, 'beginner': 2}
        
        from app.services.swap_cost_calculator import SwapCostCalculator
        
        priority_notes = priority_notes or []
        non_priority = [n for n in notes if n not in priority_notes]
        
        # Sort non-priority notes by frequency (most frequent first)
        # This ensures frequent bells are assigned early, leaving rare bells for extras
        if note_frequencies:
            non_priority.sort(key=lambda n: note_frequencies.get(n, 0), reverse=True)
            logger.debug(f"Sorted {len(non_priority)} non-priority notes by frequency (descending)")
        
        all_notes = list(priority_notes) + non_priority
        
        # Phase 1: Ensure every player gets at least 2 bells
        for _ in range(2):  # Two rounds to give each player 2 bells
            for note in all_notes:
                if all([counts[p['name']] >= 2 for p in players]):
                    # All players have 2 bells, move to phase 2
                    break
                
                # Find player with fewest bells
                min_player = min(players, key=lambda p: counts[p['name']])
                if counts[min_player['name']] < 2:
                    if note not in [b for p_data in assignments.values() for b in p_data['bells']]:
                        assignments[min_player['name']]['bells'].append(note)
                        counts[min_player['name']] += 1
        
        # Phase 2: Assign remaining notes with swap cost optimization (if timings available)
        remaining_notes = [n for n in all_notes if n not in [b for p_data in assignments.values() for b in p_data['bells']]]
        
        if note_timings and len(remaining_notes) > 0:
            for note in remaining_notes:
                best_player = None
                best_score = float('inf')

                # Find player with lowest swap cost whose hand can accept this bell
                for player in players:
                    experience = player.get('experience', 'beginner')
                    max_for_exp = max_bells_per_player.get(experience, 2)
                    if counts[player['name']] >= max_for_exp:
                        continue
                    # Check feasibility (both hands) without committing yet
                    hand_map = assignments[player['name']].get('_hand_map', {})
                    left_b = [b for i, b in enumerate(assignments[player['name']]['bells'])
                               if hand_map.get(b, 'left' if i % 2 == 0 else 'right') == 'left']
                    right_b = [b for i, b in enumerate(assignments[player['name']]['bells'])
                                if hand_map.get(b, 'left' if i % 2 == 0 else 'right') == 'right']
                    feasible = any(
                        BellAssignmentAlgorithm._check_swap_gap_for_hand(
                            hb, note, note_timings, timing_config, experience)
                        for hb in [left_b, right_b]
                    )
                    if not feasible:
                        continue
                    note_pitch = MusicParser.note_name_to_pitch(note)
                    score = SwapCostCalculator.score_bell_for_player(
                        assignments[player['name']], note_pitch, note_timings,
                        weights={'swap': 0.5, 'frequency': 0.3, 'isolation': 0.2}
                    )
                    if score < best_score:
                        best_score = score
                        best_player = player

                if best_player:
                    experience = best_player.get('experience', 'beginner')
                    if BellAssignmentAlgorithm._try_extra_bell(
                            assignments[best_player['name']], note, note_timings, timing_config, experience):
                        counts[best_player['name']] += 1
        else:
            # Fallback: least-loaded player that can accept the bell on either hand
            for note in remaining_notes:
                for player in sorted(players, key=lambda p: counts[p['name']]):
                    experience = player.get('experience', 'beginner')
                    max_for_exp = max_bells_per_player.get(experience, 2)
                    if counts[player['name']] < max_for_exp:
                        if BellAssignmentAlgorithm._try_extra_bell(
                                assignments[player['name']], note, note_timings, timing_config, experience):
                            counts[player['name']] += 1
                            break

        return assignments
    
    @staticmethod
    def _assign_hands(assignments):
        """Finalise hand assignments.

        Bells assigned during Phase 2/3 have their hand recorded in '_hand_map'.
        Phase 1 bells (first 2 per player) fall back to the index-parity rule.
        Clears '_hand_map' from the assignment before returning.
        """
        for player_name, player_data in assignments.items():
            hand_map = player_data.pop('_hand_map', {})
            player_data['left_hand'] = []
            player_data['right_hand'] = []
            for idx, bell in enumerate(player_data['bells']):
                target = hand_map.get(bell, 'left' if idx % 2 == 0 else 'right')
                player_data[f'{target}_hand'].append(bell)

        return assignments

