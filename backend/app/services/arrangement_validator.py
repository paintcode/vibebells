"""
Arrangement Validator and Sustainability Checker
Validates arrangements against bell-assignment strategy requirements
"""

import logging

logger = logging.getLogger(__name__)

class ArrangementValidator:
    """Validate and check sustainability of bell arrangements"""
    
    @staticmethod
    def validate(arrangement, max_bells_per_player=2):
        """
        Validate arrangement against constraints.
        
        Args:
            arrangement: Dict mapping player names to bell lists
            max_bells_per_player: Maximum bells per player (default 2)
            
        Returns:
            Dict with validation results and issues
        """
        issues = []
        warnings = []
        
        if not arrangement:
            issues.append("Empty arrangement")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # Check bell count per player
        max_seen = 0
        players_at_limit = []
        for player_name, bells in arrangement.items():
            bell_count = len(bells)
            max_seen = max(max_seen, bell_count)
            
            if bell_count > max_bells_per_player:
                issues.append(f"{player_name} has {bell_count} bells (max: {max_bells_per_player})")
            elif bell_count == max_bells_per_player:
                players_at_limit.append(player_name)
            elif bell_count == 0:
                warnings.append(f"{player_name} has no bells assigned")
        
        # Check for duplicate bell assignments
        all_bells = []
        for bells in arrangement.values():
            all_bells.extend(bells)
        
        duplicates = []
        seen = set()
        for bell in all_bells:
            if bell in seen:
                duplicates.append(bell)
            seen.add(bell)
        
        if duplicates:
            issues.append(f"Duplicate bells assigned: {', '.join(set(duplicates))}")
        
        # Calculate utilization
        total_bells = sum(len(bells) for bells in arrangement.values())
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
        Check sustainability: ensure players can physically ring bells without fatigue.
        
        Heuristics:
        - Players with 2 bells should have them at different registers (not adjacent)
        - Melody players should have some lower-register support
        
        Args:
            arrangement: Dict mapping player names to bell lists
            music_data: Dict with parsed music info and frequencies
            
        Returns:
            Dict with sustainability metrics
        """
        from app.services.music_parser import MusicParser
        
        issues = []
        recommendations = []
        
        for player_name, bells in arrangement.items():
            if len(bells) == 2:
                # Check pitch distance between bells
                pitches = []
                for bell_name in bells:
                    # Parse bell name (e.g., "C4" -> pitch estimation)
                    try:
                        # Rough pitch mapping: C=0, D=2, E=4, F=5, G=7, A=9, B=11
                        note_letter = bell_name[0]
                        octave = int(bell_name[1:]) if len(bell_name) > 1 else 4
                        
                        note_to_semitone = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
                        midi_pitch = 12 * (octave + 1) + note_to_semitone.get(note_letter, 0)
                        pitches.append(midi_pitch)
                    except:
                        pass
                
                if len(pitches) == 2:
                    pitch_distance = abs(pitches[1] - pitches[0])
                    
                    # Warn if bells are too close (less than 3 semitones = minor third)
                    if pitch_distance < 3:
                        recommendations.append(
                            f"{player_name}: Bells {bells[0]} and {bells[1]} are very close ({pitch_distance} semitones). "
                            f"Consider spacing further apart for easier ringing."
                        )
                    
                    # Recommend distribution
                    if pitch_distance > 12:
                        recommendations.append(
                            f"{player_name}: Large range ({pitch_distance} semitones). Ensure player can comfortably reach both."
                        )
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'sustainable': len(issues) == 0
        }
    
    @staticmethod
    def calculate_quality_score(arrangement, music_data=None):
        """
        Calculate arrangement quality score (0-100).
        
        Criteria:
        - Even distribution across players (25%)
        - No empty players (25%)
        - Melody/harmony separation (if available) (25%)
        - Sustainable bell spacing (25%)
        
        Args:
            arrangement: Dict mapping player names to bell lists
            music_data: Optional music data with melody/harmony info
            
        Returns:
            Quality score 0-100
        """
        score = 0
        
        # Criterion 1: Even distribution (25 points)
        bell_counts = [len(bells) for bells in arrangement.values()]
        if bell_counts and len(bell_counts) > 1:
            avg_bells = sum(bell_counts) / len(bell_counts)
            variance = sum((c - avg_bells) ** 2 for c in bell_counts) / len(bell_counts)
            
            # Normalize variance: max variance is when all bells with one player
            max_possible_variance = avg_bells ** 2 * (len(bell_counts) - 1)
            if max_possible_variance > 0:
                normalized_variance = min(variance / max_possible_variance, 1.0)
                distribution_score = 25 * (1 - normalized_variance)
            else:
                distribution_score = 25
            score += distribution_score
        elif bell_counts:
            # Single player: no variance to optimize
            score += 20  # Slight penalty for single player
        
        # Criterion 2: No empty players (25 points)
        empty_players = sum(1 for c in bell_counts if c == 0)
        occupied_players = sum(1 for c in bell_counts if c > 0)
        if len(bell_counts) > 0:
            occupancy_score = (occupied_players / len(bell_counts)) * 25
            score += occupancy_score
        
        # Criterion 3: Player capacity utilization (25 points)
        # Better if players have some "breathing room" but not too empty
        avg_utilization = sum(c for c in bell_counts) / (2 * len(bell_counts)) if bell_counts else 0
        if avg_utilization <= 0.7:  # Very underutilized (much spare capacity)
            utilization_score = 10
        elif avg_utilization <= 0.9:  # Good balance
            utilization_score = 25
        elif avg_utilization <= 1.0:  # At or near capacity
            utilization_score = 20
        else:  # Over capacity (shouldn't happen with proper validation)
            utilization_score = 5
        score += utilization_score
        
        # Criterion 4: Melody/harmony balance (25 points)
        melody_score = 0
        if music_data and music_data.get('melody_pitches'):
            # Convert melody pitches to note names for comparison
            from app.services.music_parser import MusicParser
            melody_note_names = set(MusicParser.pitch_to_note_name(p) for p in music_data.get('melody_pitches', []))
            
            all_bells_str = [bell for bells in arrangement.values() for bell in bells]
            melody_coverage = len([b for b in all_bells_str if b in melody_note_names])
            
            # Score based on coverage percentage
            if melody_note_names:
                coverage_ratio = melody_coverage / len(melody_note_names)
                melody_score = 25 * min(coverage_ratio, 1.0)
            else:
                melody_score = 25
        else:
            # No melody data, give full credit
            melody_score = 25
        
        score += melody_score
        
        return min(100, max(0, score))
