"""
Arrangement Validator and Sustainability Checker
Validates arrangements against bell-assignment strategy requirements
"""

import logging
import statistics

logger = logging.getLogger(__name__)

class ArrangementValidator:
    """Validate and check sustainability of bell arrangements"""
    
    @staticmethod
    def validate(arrangement, max_bells_per_player=8):
        """
        Validate arrangement against constraints.
        
        Args:
            arrangement: Dict mapping player names to assignment dicts with 'bells'
            max_bells_per_player: Maximum bells per player (default 8)
            
        Returns:
            Dict with validation results and issues
        """
        issues = []
        warnings = []
        
        if not arrangement:
            issues.append("Empty arrangement")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # Check bell count per player and hand distribution
        max_seen = 0
        players_at_limit = []
        for player_name, player_data in arrangement.items():
            bells = player_data.get('bells', [])
            left_hand = player_data.get('left_hand', [])
            right_hand = player_data.get('right_hand', [])
            
            bell_count = len(bells)
            max_seen = max(max_seen, bell_count)
            
            if bell_count > max_bells_per_player:
                issues.append(f"{player_name} has {bell_count} bells (max: {max_bells_per_player})")
            elif bell_count == max_bells_per_player:
                players_at_limit.append(player_name)
            elif bell_count == 0:
                warnings.append(f"{player_name} has no bells assigned")
            
            # Check hand balance: if player has >1 bell, should have at least 1 per hand
            if bell_count > 1:
                if len(left_hand) == 0:
                    warnings.append(f"{player_name} has no bells in left hand")
                if len(right_hand) == 0:
                    warnings.append(f"{player_name} has no bells in right hand")
        
        # Check for duplicate bell assignments
        all_bells = []
        for player_data in arrangement.values():
            all_bells.extend(player_data.get('bells', []))
        
        duplicates = []
        seen = set()
        for bell in all_bells:
            if bell in seen:
                duplicates.append(bell)
            seen.add(bell)
        
        if duplicates:
            issues.append(f"Duplicate bells assigned: {', '.join(set(duplicates))}")
        
        # Calculate utilization
        total_bells = sum(len(player_data.get('bells', [])) for player_data in arrangement.values())
        unique_bells = len(set(all_bells))
        utilization = unique_bells / total_bells if total_bells > 0 else 0
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'players_at_capacity': players_at_limit,
            'total_bells_assigned': total_bells,
            'unique_bells': unique_bells,
            'utilization': utilization,
            'max_bells_per_player_reached': max_seen
        }
    
    @staticmethod
    def sustainability_check(arrangement, music_data):
        """
        Check sustainability: ensure arrangement is practical for performance.
        
        Returns basic sustainability status. Most physical playability concerns
        are handled by bell count limits per experience level.
        
        Args:
            arrangement: Dict mapping player names to assignment dicts
            music_data: Dict with parsed music info and frequencies
            
        Returns:
            Dict with sustainability metrics
        """
        issues = []
        recommendations = []
        
        # Currently no sustainability issues to check beyond validation constraints
        # Bell count limits (2/3/5 per experience level) handle capacity concerns
        # Hand assignments ensure even distribution between hands
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'sustainable': len(issues) == 0
        }
    
    @staticmethod
    def calculate_quality_score(arrangement, music_data=None):
        """
        Calculate arrangement quality score (0-100).

        Weights:
        - Playability: 50
        - Bell-count fairness: 30
        - Fatigue fairness: 20

        Hard fail:
        - Any dropped expected note
        - Any impossible swap (same-hand bell swap gap below threshold)
        
        Args:
            arrangement: Dict mapping player names to assignment dicts
            music_data: Optional music data with melody/harmony info
            
        Returns:
            Quality score 0-100
        """
        if not arrangement:
            return 0

        dropped_count = ArrangementValidator._count_dropped_notes(arrangement, music_data)
        playability = ArrangementValidator._calculate_playability_score(arrangement, music_data)

        # Hard fail: dropped notes or impossible swaps
        if dropped_count > 0 or playability['impossible_swaps'] > 0:
            return 0

        bell_fairness_score = ArrangementValidator._calculate_bell_fairness_score(arrangement)
        fatigue_fairness_score = ArrangementValidator._calculate_fatigue_fairness_score(arrangement, music_data)

        score = playability['score'] + bell_fairness_score + fatigue_fairness_score
        return min(100, max(0, round(score, 2)))

    @staticmethod
    def _count_dropped_notes(arrangement, music_data):
        """Count expected notes in music_data that are missing from the assignment."""
        if not music_data:
            return 0

        expected = music_data.get('unique_notes')
        if not expected:
            return 0

        from app.services.music_parser import MusicParser

        expected_names = set()
        for note in expected:
            if isinstance(note, int):
                expected_names.add(MusicParser.pitch_to_note_name(note))
            else:
                expected_names.add(str(note))

        if not expected_names:
            return 0

        assigned = {
            bell
            for player_data in arrangement.values()
            for bell in player_data.get('bells', [])
        }

        return len(expected_names - assigned)

    @staticmethod
    def _calculate_bell_fairness_score(arrangement):
        """Bell fairness score (0-30): >=2 bells/player and spread <=1 are rewarded."""
        bell_counts = [len(player_data.get('bells', [])) for player_data in arrangement.values()]
        if not bell_counts:
            return 0
        players_below_two = sum(1 for c in bell_counts if c < 2)
        spread = max(bell_counts) - min(bell_counts)
        penalty_a = min(20, players_below_two * 8)
        penalty_b = 0 if spread <= 1 else min(18, (spread - 1) * 6)
        return max(0, 30 - penalty_a - penalty_b)

    @staticmethod
    def _calculate_playability_score(arrangement, music_data, min_gap_ms=1000):
        """Playability score (0-50) with impossible swap detection and swap/load penalties."""
        if not music_data or not music_data.get('notes'):
            return {'score': 50, 'impossible_swaps': 0}

        from app.services.music_parser import MusicParser

        notes = music_data.get('notes', [])
        if not notes:
            return {'score': 50, 'impossible_swaps': 0}

        def to_ms(raw):
            fmt = music_data.get('format', 'midi')
            tempo = max(music_data.get('tempo', 120), 1)
            ticks_per_beat = max(music_data.get('ticks_per_beat', 480), 1)
            if fmt == 'midi':
                return raw / ticks_per_beat * (60000.0 / tempo)
            return raw * (60000.0 / tempo)

        total_pressure_events = 0
        impossible_swaps = 0
        swap_counts = []

        for player_data in arrangement.values():
            bells = player_data.get('bells', [])
            if len(bells) < 2:
                continue

            hand_map = {}
            for bell in player_data.get('left_hand', []):
                hand_map[bell] = 'left'
            for bell in player_data.get('right_hand', []):
                hand_map[bell] = 'right'
            for idx, bell in enumerate(bells):
                if bell not in hand_map:
                    hand_map[bell] = 'left' if idx % 2 == 0 else 'right'

            player_events = []
            for n in notes:
                pitch = n.get('pitch')
                if pitch is None:
                    continue
                note_name = MusicParser.pitch_to_note_name(pitch)
                if note_name not in bells:
                    continue
                start_ms = to_ms(n.get('time', n.get('offset', 0)))
                dur_ms = to_ms(n.get('duration', 0))
                player_events.append({
                    'start_ms': start_ms,
                    'end_ms': start_ms + dur_ms,
                    'bell': note_name,
                    'hand': hand_map.get(note_name, 'left')
                })

            player_events.sort(key=lambda e: e['start_ms'])
            last_by_hand = {'left': None, 'right': None}
            player_hand_swaps = 0
            current_hand = None

            for ev in player_events:
                if current_hand is not None and ev['hand'] != current_hand:
                    player_hand_swaps += 1
                current_hand = ev['hand']

                prev = last_by_hand[ev['hand']]
                if prev is not None:
                    onset_gap = ev['start_ms'] - prev['start_ms']
                    if onset_gap < min_gap_ms:
                        total_pressure_events += 1
                    if ev['bell'] != prev['bell']:
                        swap_gap = ev['start_ms'] - prev['end_ms']
                        if swap_gap < min_gap_ms:
                            impossible_swaps += 1
                last_by_hand[ev['hand']] = ev

            swap_counts.append(player_hand_swaps)

        # Hard-fail criterion is returned for caller to gate final score.
        if impossible_swaps > 0:
            return {'score': 0, 'impossible_swaps': impossible_swaps}

        over_swap_penalty = min(24, sum(max(0, swaps - 5) * 4 for swaps in swap_counts))
        hand_pressure_penalty = min(20, total_pressure_events * 1.5)
        score = max(0, 50 - over_swap_penalty - hand_pressure_penalty)
        return {'score': score, 'impossible_swaps': 0}

    @staticmethod
    def _calculate_fatigue_fairness_score(arrangement, music_data):
        """Fatigue fairness score (0-20) using absolute workload (duration_ms * weight_oz)."""
        if not music_data or not music_data.get('notes'):
            return 20

        from app.services.music_parser import MusicParser
        from app.services.simulation_builder import SimulationBuilder

        notes = music_data.get('notes', [])
        if not notes:
            return 20

        def to_ms(raw):
            fmt = music_data.get('format', 'midi')
            tempo = max(music_data.get('tempo', 120), 1)
            ticks_per_beat = max(music_data.get('ticks_per_beat', 480), 1)
            if fmt == 'midi':
                return raw / ticks_per_beat * (60000.0 / tempo)
            return raw * (60000.0 / tempo)

        weights = {}
        fatigue_values = []

        for player_data in arrangement.values():
            bells = set(player_data.get('bells', []))
            if not bells:
                fatigue_values.append(0.0)
                continue

            fatigue = 0.0
            for n in notes:
                pitch = n.get('pitch')
                if pitch is None:
                    continue
                note_name = MusicParser.pitch_to_note_name(pitch)
                if note_name not in bells:
                    continue
                if pitch not in weights:
                    _, wt_oz, _ = SimulationBuilder._get_bell_data(pitch)
                    weights[pitch] = wt_oz
                dur_ms = to_ms(n.get('duration', 0))
                fatigue += dur_ms * weights[pitch]
            fatigue_values.append(fatigue)

        if not fatigue_values or max(fatigue_values) == 0:
            return 20

        mean_fatigue = sum(fatigue_values) / len(fatigue_values)
        if mean_fatigue <= 0:
            return 20

        std_dev = statistics.pstdev(fatigue_values)
        cv = std_dev / mean_fatigue
        score = 20 * max(0, 1 - min(cv, 1.0))

        median = statistics.median(fatigue_values)
        if median > 0:
            max_ratio = max(fatigue_values) / median
            if max_ratio > 2.0:
                score -= min(8, (max_ratio - 2.0) * 4)

        return max(0, min(20, score))


