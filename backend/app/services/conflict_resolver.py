"""
Conflict Resolution for Bell Assignments
Resolves duplicate assignments and improves arrangement quality
"""

import logging

logger = logging.getLogger(__name__)

class ConflictResolver:
    """Resolve conflicts in bell assignments"""
    
    @staticmethod
    def resolve_duplicates(arrangement):
        """
        Resolve duplicate bell assignments.
        
        If a bell is assigned to multiple players, reassign to player with capacity.
        
        Args:
            arrangement: Dict mapping player names to bell lists
            
        Returns:
            Resolved arrangement with no duplicates
        """
        # Find duplicates
        bell_to_players = {}
        for player_name, bells in arrangement.items():
            for bell in bells:
                if bell not in bell_to_players:
                    bell_to_players[bell] = []
                bell_to_players[bell].append(player_name)
        
        duplicates = {bell: players for bell, players in bell_to_players.items() if len(players) > 1}
        
        if not duplicates:
            return arrangement
        
        logger.warning(f"Found {len(duplicates)} duplicate bell assignments, resolving...")
        
        # Create mutable copy
        resolved = {player: list(bells) for player, bells in arrangement.items()}
        unassigned_bells = []
        
        # For each duplicate, keep with first player and remove from others
        for bell, players in duplicates.items():
            primary_player = players[0]
            
            # Remove from other players
            for secondary_player in players[1:]:
                if bell in resolved[secondary_player]:
                    resolved[secondary_player].remove(bell)
                    unassigned_bells.append(bell)
                    logger.debug(f"Removed duplicate {bell} from {secondary_player}, kept with {primary_player}")
        
        # Reassign removed bells to players with capacity
        for bell in unassigned_bells:
            assigned = False
            for player_name in resolved:
                if len(resolved[player_name]) < 2:
                    resolved[player_name].append(bell)
                    assigned = True
                    logger.debug(f"Reassigned {bell} to {player_name}")
                    break
            
            if not assigned:
                logger.warning(f"Could not reassign duplicate {bell} - all players at capacity")
        
        return resolved
    
    @staticmethod
    def balance_assignments(arrangement, target_bells_per_player=None):
        """
        Balance assignments to improve distribution.
        
        Redistributes bells to even out workload across players.
        
        Args:
            arrangement: Dict mapping player names to bell lists
            target_bells_per_player: Ideal distribution (default 2)
            
        Returns:
            More balanced arrangement
        """
        target_bells_per_player = target_bells_per_player or 2
        
        # Calculate current distribution
        player_counts = {player: len(bells) for player, bells in arrangement.items()}
        total_bells = sum(player_counts.values())
        
        if total_bells == 0 or len(arrangement) == 0:
            return arrangement
        
        # Create mutable copy
        balanced = {player: list(bells) for player, bells in arrangement.items()}
        
        # Calculate ideal distribution
        ideal_per_player = total_bells / len(arrangement)
        
        # Try to balance toward ideal
        changes = 0
        max_iterations = len(arrangement) * 2  # Scale with number of players
        
        for _ in range(max_iterations):
            # Find most loaded and least loaded players
            sorted_players = sorted(player_counts.items(), key=lambda x: x[1], reverse=True)
            
            most_loaded = sorted_players[0]
            least_loaded = sorted_players[-1]
            
            # Stop if already balanced
            if most_loaded[1] - least_loaded[1] <= 1:
                break
            
            # Move one bell from most loaded to least loaded
            source = most_loaded[0]
            dest = least_loaded[0]
            
            if balanced[source] and len(balanced[dest]) < target_bells_per_player:
                bell = balanced[source].pop()
                balanced[dest].append(bell)
                player_counts[source] -= 1
                player_counts[dest] += 1
                changes += 1
                logger.debug(f"Moved {bell} from {source} to {dest}")
        
        if changes > 0:
            logger.info(f"Balanced assignments with {changes} moves")
        
        return balanced
    
    @staticmethod
    def optimize_for_experience(arrangement, players_info):
        """
        Optimize arrangement to favor experienced players with melody notes.
        
        Moves challenging notes (melody, high-frequency) to experienced players.
        
        Args:
            arrangement: Dict mapping player names to bell lists
            players_info: List of player dicts with 'name' and 'experience'
            
        Returns:
            Experience-optimized arrangement
        """
        
        # Build experience map
        experience_map = {p['name']: p.get('experience', 'beginner') for p in players_info}
        experience_order = {'experienced': 0, 'intermediate': 1, 'beginner': 2}
        
        # Create mutable copy
        optimized = {player: list(bells) for player, bells in arrangement.items()}
        
        # Get experienced and beginner players
        experienced = [p for p in players_info if p.get('experience') == 'experienced']
        beginners = [p for p in players_info if p.get('experience') == 'beginner']
        
        if not experienced or not beginners:
            return optimized
        
        # Try to move complex notes from beginners to experienced
        changes = 0
        for beginner in beginners:
            beginner_name = beginner['name']
            if not optimized[beginner_name]:
                continue
            
            # Look for experienced player with capacity
            for exp in experienced:
                exp_name = exp['name']
                if len(optimized[exp_name]) < 2:
                    # Move one bell from beginner to experienced
                    bell = optimized[beginner_name].pop()
                    optimized[exp_name].append(bell)
                    changes += 1
                    logger.debug(f"Moved {bell} from {beginner_name} (beginner) to {exp_name} (experienced)")
                    break
        
        if changes > 0:
            logger.info(f"Optimized {changes} bell assignments for experience level")
        
        return optimized
