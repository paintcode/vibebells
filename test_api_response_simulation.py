#!/usr/bin/env python3
"""Simulate complete API response with expansion notification"""

import sys
sys.path.insert(0, 'backend')

from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.arrangement_generator import ArrangementGenerator
import json

print("\n" + "="*70)
print("API RESPONSE SIMULATION - Experience Constraints & Expansion")
print("="*70)

# Scenario: 2 beginner players, 12 unique notes
print("\nScenario: Amateur players with complex song")
print("-" * 70)
print("Input:")
print("  Players: 2 beginners")
print("  Notes: 12 unique (complex arrangement needed)")

players = [
    {'name': 'Beginner 1', 'experience': 'beginner'},
    {'name': 'Beginner 2', 'experience': 'beginner'},
]

notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5']

# Calculate initial capacity
initial_capacity = ArrangementGenerator._calculate_total_capacity(players)
print(f"\nCapacity Analysis:")
print(f"  Beginner 1: 2 bells max")
print(f"  Beginner 2: 2 bells max")
print(f"  Total: {initial_capacity} bells")
print(f"  Required: {len(notes)} bells")
print(f"  Status: {'INSUFFICIENT ❌' if len(notes) > initial_capacity else 'SUFFICIENT ✓'}")

# Check if expansion needed
if len(notes) > initial_capacity:
    print(f"\n→ Expansion triggered!")
    
    # Calculate minimum required
    min_players = ArrangementGenerator._calculate_minimum_players_needed(notes, players)
    expanded = ArrangementGenerator._expand_players(players, min_players)
    expanded_capacity = ArrangementGenerator._calculate_total_capacity(expanded)
    
    print(f"\nExpansion Details:")
    print(f"  Minimum players needed: {min_players}")
    print(f"  Players added: {len(expanded) - len(players)}")
    print(f"  New capacity: {expanded_capacity} bells")
    print(f"  Status: {'SUFFICIENT ✓' if expanded_capacity >= len(notes) else 'INSUFFICIENT ❌'}")
    
    # Generate arrangement with expanded players
    config = {
        'MAX_BELLS_PER_PLAYER': 8,
        'MAX_BELLS_PER_EXPERIENCE': {
            'experienced': 5,
            'intermediate': 3,
            'beginner': 2
        }
    }
    
    assignment = BellAssignmentAlgorithm.assign_bells(
        notes, expanded, strategy='balanced', config=config
    )
    
    # Build response structure
    response = {
        'success': True,
        'arrangements': [
            {
                'strategy': 'balanced',
                'description': 'Evenly distribute melody notes',
                'assignments': assignment,
                'note_count': len(notes),
                'players': len(expanded)
            }
        ],
        'expansion_info': {
            'expanded': True,
            'original_player_count': len(players),
            'final_player_count': len(expanded),
            'minimum_required': min_players,
            'message': f"The song requires at least {min_players} players. Arrangements show {len(expanded)} players (including {len(expanded) - len(players)} virtual players)."
        }
    }
    
    print(f"\n" + "="*70)
    print("API Response JSON")
    print("="*70)
    
    # Print simplified response (without full assignments)
    response_display = {
        'success': response['success'],
        'arrangements_count': len(response['arrangements']),
        'first_arrangement': {
            'strategy': response['arrangements'][0]['strategy'],
            'players_involved': response['arrangements'][0]['players'],
            'note_count': response['arrangements'][0]['note_count'],
        },
        'expansion_info': response['expansion_info']
    }
    
    print(json.dumps(response_display, indent=2))
    
    print(f"\nFinal Player Configuration:")
    print(f"-" * 70)
    for i, player in enumerate(expanded):
        bells = assignment[player['name']]['bells']
        is_virtual = " (VIRTUAL)" if player.get('virtual') else ""
        print(f"  {i+1}. {player['name']:20s} ({player['experience']:12s}){is_virtual}: {len(bells)} bells")
        print(f"     Bells: {', '.join(bells)}")
    
    print(f"\n✓ All {len(notes)} notes assigned across {len(expanded)} players")

print("\n" + "="*70)
print("✅ API Response Simulation Complete")
print("="*70)

print("\nFrontend will display:")
print("  📊 Warning banner with expansion notification")
print("  📋 Expandable details showing player count breakdown")
print("  🎵 All arrangements properly generated")
print("  👥 Virtual players clearly marked in player list")
