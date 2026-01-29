class BellAssignmentAlgorithm:
    """Implements the bell assignment algorithm from bell-assignment-strategy.md"""
    
    MAX_BELLS_PER_PLAYER = 2
    
    @staticmethod
    def assign_bells(notes, players, strategy='experienced_first'):
        """
        Assign bells to players based on strategy.
        
        Args:
            notes: List of unique note names (e.g., ['C4', 'D4', 'E4'])
            players: List of player dicts with 'name' and 'experience'
            strategy: Assignment strategy ('experienced_first', 'balanced', 'min_transitions')
        
        Returns:
            Dict mapping player names to assigned bells
            
        Raises:
            ValueError: If validation fails
        """
        
        if not players:
            raise ValueError("At least one player is required")
        
        if not notes:
            raise ValueError("At least one note is required")
        
        if len(players) < 1:
            raise ValueError("Invalid player count")
        
        assignments = {player['name']: [] for player in players}
        player_bell_counts = {player['name']: 0 for player in players}
        
        # Sort players by experience
        experience_order = {'experienced': 0, 'intermediate': 1, 'beginner': 2}
        sorted_players = sorted(players, key=lambda p: experience_order.get(p.get('experience', 'beginner'), 2))
        
        if strategy == 'experienced_first':
            assignments = BellAssignmentAlgorithm._assign_experienced_first(
                notes, sorted_players, assignments, player_bell_counts
            )
        elif strategy == 'balanced':
            assignments = BellAssignmentAlgorithm._assign_balanced(
                notes, sorted_players, assignments, player_bell_counts
            )
        elif strategy == 'min_transitions':
            assignments = BellAssignmentAlgorithm._assign_min_transitions(
                notes, sorted_players, assignments, player_bell_counts
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        return assignments
    
    @staticmethod
    def _assign_experienced_first(notes, players, assignments, counts):
        """Assign priority notes to experienced players first"""
        
        for note in notes:
            assigned = False
            # Try to assign to experienced players with space
            for player in players:
                if counts[player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                    assignments[player['name']].append(note)
                    counts[player['name']] += 1
                    assigned = True
                    break
            
            # If all experienced players are full, still assign if possible
            if not assigned and players:
                min_player = min(players, key=lambda p: counts[p['name']])
                if counts[min_player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                    assignments[min_player['name']].append(note)
                    counts[min_player['name']] += 1
        
        return assignments
    
    @staticmethod
    def _assign_balanced(notes, players, assignments, counts):
        """Distribute notes evenly across all players"""
        
        sorted_notes = sorted(notes)
        for idx, note in enumerate(sorted_notes):
            player = players[idx % len(players)]
            if counts[player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                assignments[player['name']].append(note)
                counts[player['name']] += 1
        
        return assignments
    
    @staticmethod
    def _assign_min_transitions(notes, players, assignments, counts):
        """Assign notes to minimize transitions between players"""
        
        for note in notes:
            # Find player with fewest bells
            min_player = min(players, key=lambda p: counts[p['name']])
            if counts[min_player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                assignments[min_player['name']].append(note)
                counts[min_player['name']] += 1
        
        return assignments

