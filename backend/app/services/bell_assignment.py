class BellAssignmentAlgorithm:
    """Implements the bell assignment algorithm from bell-assignment-strategy.md"""
    
    MAX_BELLS_PER_PLAYER = 2
    
    @staticmethod
    def assign_bells(notes, players, strategy='experienced_first', priority_notes=None):
        """
        Assign bells to players based on strategy.
        
        Args:
            notes: List of unique note names (e.g., ['C4', 'D4', 'E4'])
            players: List of player dicts with 'name' and 'experience'
            strategy: Assignment strategy ('experienced_first', 'balanced', 'min_transitions')
            priority_notes: Optional list of notes to prioritize (e.g., melody notes)
        
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
                notes, sorted_players, assignments, player_bell_counts, priority_notes
            )
        elif strategy == 'balanced':
            assignments = BellAssignmentAlgorithm._assign_balanced(
                notes, sorted_players, assignments, player_bell_counts, priority_notes
            )
        elif strategy == 'min_transitions':
            assignments = BellAssignmentAlgorithm._assign_min_transitions(
                notes, sorted_players, assignments, player_bell_counts, priority_notes
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        return assignments
    
    @staticmethod
    def _assign_experienced_first(notes, players, assignments, counts, priority_notes=None):
        """Assign priority notes to experienced players first"""
        
        priority_notes = priority_notes or []
        unassigned_notes = []
        
        # First pass: assign priority notes (melody) to experienced players
        for note in priority_notes:
            assigned = False
            for player in players:
                if counts[player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                    assignments[player['name']].append(note)
                    counts[player['name']] += 1
                    assigned = True
                    break
            if not assigned:
                unassigned_notes.append(note)
        
        # Second pass: assign remaining notes
        remaining_notes = [n for n in notes if n not in priority_notes]
        for note in remaining_notes:
            assigned = False
            for player in players:
                if counts[player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                    assignments[player['name']].append(note)
                    counts[player['name']] += 1
                    assigned = True
                    break
            
            if not assigned:
                unassigned_notes.append(note)
        
        # Validate all notes were assigned
        if unassigned_notes:
            import logging
            logging.warning(f"Could not assign {len(unassigned_notes)} notes due to player capacity limits")
        
        return assignments
    
    @staticmethod
    def _assign_balanced(notes, players, assignments, counts, priority_notes=None):
        """Distribute notes evenly across all players"""
        
        priority_notes = priority_notes or []
        unassigned_notes = []
        
        # First assign priority notes
        for idx, note in enumerate(priority_notes):
            player = players[idx % len(players)]
            if counts[player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                assignments[player['name']].append(note)
                counts[player['name']] += 1
            else:
                unassigned_notes.append(note)
        
        # Then assign remaining notes
        sorted_notes = sorted([n for n in notes if n not in priority_notes])
        for idx, note in enumerate(sorted_notes):
            player = players[(idx + len(priority_notes)) % len(players)]
            if counts[player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                assignments[player['name']].append(note)
                counts[player['name']] += 1
            else:
                unassigned_notes.append(note)
        
        if unassigned_notes:
            import logging
            logging.warning(f"Balanced strategy: Could not assign {len(unassigned_notes)} notes due to capacity")
        
        return assignments
    
    @staticmethod
    def _assign_min_transitions(notes, players, assignments, counts, priority_notes=None):
        """Assign notes to minimize transitions between players"""
        
        priority_notes = priority_notes or []
        unassigned_notes = []
        
        # First assign priority notes to minimize player switches
        for note in priority_notes:
            min_player = min(players, key=lambda p: counts[p['name']])
            if counts[min_player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                assignments[min_player['name']].append(note)
                counts[min_player['name']] += 1
            else:
                unassigned_notes.append(note)
        
        # Then assign remaining notes
        remaining_notes = [n for n in notes if n not in priority_notes]
        for note in remaining_notes:
            min_player = min(players, key=lambda p: counts[p['name']])
            if counts[min_player['name']] < BellAssignmentAlgorithm.MAX_BELLS_PER_PLAYER:
                assignments[min_player['name']].append(note)
                counts[min_player['name']] += 1
            else:
                unassigned_notes.append(note)
        
        if unassigned_notes:
            import logging
            logging.warning(f"Min transitions strategy: Could not assign {len(unassigned_notes)} notes due to capacity")
        
        return assignments


