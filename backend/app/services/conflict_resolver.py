"""
Conflict Resolution for Bell Assignments
Resolves duplicate assignments, balances distribution, and validates hand constraints
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
            arrangement: Dict mapping player names to assignment dicts with 'bells'
            
        Returns:
            Resolved arrangement with no duplicates
        """
        # Find duplicates
        bell_to_players = {}
        for player_name, player_data in arrangement.items():
            bells = player_data.get('bells', [])
            for bell in bells:
                if bell not in bell_to_players:
                    bell_to_players[bell] = []
                bell_to_players[bell].append(player_name)
        
        duplicates = {bell: players for bell, players in bell_to_players.items() if len(players) > 1}
        
        if not duplicates:
            return arrangement
        
        logger.warning(f"Found {len(duplicates)} duplicate bell assignments, resolving...")
        
        # Create mutable copy
        resolved = {
            player: {
                'bells': list(data.get('bells', [])),
                'left_hand': list(data.get('left_hand', [])),
                'right_hand': list(data.get('right_hand', []))
            }
            for player, data in arrangement.items()
        }
        unassigned_bells = []
        
        # For each duplicate, keep with first player and remove from others
        for bell, players in duplicates.items():
            primary_player = players[0]
            
            # Remove from other players
            for secondary_player in players[1:]:
                if bell in resolved[secondary_player]['bells']:
                    resolved[secondary_player]['bells'].remove(bell)
                    # Also remove from hand tracking
                    if bell in resolved[secondary_player]['left_hand']:
                        resolved[secondary_player]['left_hand'].remove(bell)
                    if bell in resolved[secondary_player]['right_hand']:
                        resolved[secondary_player]['right_hand'].remove(bell)
                    unassigned_bells.append(bell)
                    logger.debug(f"Removed duplicate {bell} from {secondary_player}, kept with {primary_player}")
        
        # Reassign removed bells to players with capacity
        max_bells = 8  # Default max, could be configurable
        for bell in unassigned_bells:
            assigned = False
            for player_name in resolved:
                if len(resolved[player_name]['bells']) < max_bells:
                    resolved[player_name]['bells'].append(bell)
                    # Re-assign to hand based on index
                    bell_idx = len(resolved[player_name]['bells']) - 1
                    if bell_idx % 2 == 0:
                        resolved[player_name]['left_hand'].append(bell)
                    else:
                        resolved[player_name]['right_hand'].append(bell)
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
            arrangement: Dict mapping player names to assignment dicts
            target_bells_per_player: Ideal distribution (default 2)
            
        Returns:
            More balanced arrangement
        """
        target_bells_per_player = target_bells_per_player or 2
        
        # Calculate current distribution
        player_counts = {player: len(data.get('bells', [])) for player, data in arrangement.items()}
        total_bells = sum(player_counts.values())
        
        if total_bells == 0 or len(arrangement) == 0:
            return arrangement
        
        # Create mutable copy
        balanced = {
            player: {
                'bells': list(data.get('bells', [])),
                'left_hand': list(data.get('left_hand', [])),
                'right_hand': list(data.get('right_hand', []))
            }
            for player, data in arrangement.items()
        }
        
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
            
            if balanced[source]['bells'] and len(balanced[dest]['bells']) < target_bells_per_player:
                bell = balanced[source]['bells'].pop()
                balanced[dest]['bells'].append(bell)
                
                # Update hand tracking
                if bell in balanced[source]['left_hand']:
                    balanced[source]['left_hand'].remove(bell)
                if bell in balanced[source]['right_hand']:
                    balanced[source]['right_hand'].remove(bell)
                
                # Re-assign to hand in destination
                bell_idx = len(balanced[dest]['bells']) - 1
                if bell_idx % 2 == 0:
                    balanced[dest]['left_hand'].append(bell)
                else:
                    balanced[dest]['right_hand'].append(bell)
                
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
            arrangement: Dict mapping player names to assignment dicts
            players_info: List of player dicts with 'name' and 'experience'
            
        Returns:
            Experience-optimized arrangement
        """
        
        # Build experience map
        experience_map = {p['name']: p.get('experience', 'beginner') for p in players_info}
        experience_order = {'experienced': 0, 'intermediate': 1, 'beginner': 2}
        
        # Create mutable copy
        optimized = {
            player: {
                'bells': list(data.get('bells', [])),
                'left_hand': list(data.get('left_hand', [])),
                'right_hand': list(data.get('right_hand', []))
            }
            for player, data in arrangement.items()
        }
        
        # Get experienced and beginner players
        experienced = [p for p in players_info if p.get('experience') == 'experienced']
        beginners = [p for p in players_info if p.get('experience') == 'beginner']
        
        if not experienced or not beginners:
            return optimized
        
        # Try to move bells from beginners to experienced
        # IMPORTANT: Never move bells from beginners if they have 2 or fewer bells
        changes = 0
        for beginner in beginners:
            beginner_name = beginner['name']
            bells = optimized[beginner_name]['bells']
            
            # Only move if beginner has MORE than 2 bells (protect the minimum)
            if len(bells) <= 2:
                continue
            
            # Look for experienced player with capacity
            for exp in experienced:
                exp_name = exp['name']
                if len(optimized[exp_name]['bells']) < 8:  # max_bells
                    # Move one bell from beginner to experienced
                    bell = optimized[beginner_name]['bells'].pop()
                    optimized[exp_name]['bells'].append(bell)
                    
                    # Update hand tracking in source
                    if bell in optimized[beginner_name]['left_hand']:
                        optimized[beginner_name]['left_hand'].remove(bell)
                    if bell in optimized[beginner_name]['right_hand']:
                        optimized[beginner_name]['right_hand'].remove(bell)
                    
                    # Assign to hand in destination
                    bell_idx = len(optimized[exp_name]['bells']) - 1
                    if bell_idx % 2 == 0:
                        optimized[exp_name]['left_hand'].append(bell)
                    else:
                        optimized[exp_name]['right_hand'].append(bell)
                    
                    changes += 1
                    logger.debug(f"Moved {bell} from {beginner_name} (beginner) to {exp_name} (experienced)")
                    break
        
        if changes > 0:
            logger.info(f"Optimized {changes} bell assignments for experience level (preserved minimum 2 per beginner)")
        
        return optimized

