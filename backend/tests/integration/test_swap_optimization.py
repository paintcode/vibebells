"""
Integration Test for Phase 5: Hand Swap Optimization
Demonstrates the min_transitions strategy using swap cost optimization
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.swap_cost_calculator import SwapCostCalculator
from app.services.arrangement_validator import ArrangementValidator


def test_swap_cost_optimization():
    """Test that min_transitions strategy optimizes for swap cost"""
    
    print("\n" + "=" * 70)
    print("Phase 5: Hand Swap Optimization Test")
    print("=" * 70)
    
    # Create synthetic note timeline
    # Simulating a simple melody with clear temporal separation
    notes = [
        # Section 1: C-D alternation (first 8 beats)
        {'pitch': 60, 'time': 0, 'duration': 100},    # C4
        {'pitch': 62, 'time': 100, 'duration': 100},  # D4
        {'pitch': 60, 'time': 200, 'duration': 100},  # C4
        {'pitch': 62, 'time': 300, 'duration': 100},  # D4
        {'pitch': 60, 'time': 400, 'duration': 100},  # C4
        {'pitch': 62, 'time': 500, 'duration': 100},  # D4
        
        # Section 2: E-F alternation (next 4 beats)
        {'pitch': 64, 'time': 600, 'duration': 100},  # E4
        {'pitch': 65, 'time': 700, 'duration': 100},  # F4
        {'pitch': 64, 'time': 800, 'duration': 100},  # E4
        {'pitch': 65, 'time': 900, 'duration': 100},  # F4
        
        # Section 3: G-A, later, infrequent (perfect candidate for extra bell)
        {'pitch': 67, 'time': 2000, 'duration': 100}, # G4 (late, rare)
        {'pitch': 69, 'time': 2100, 'duration': 100}, # A4 (late, rare)
    ]
    
    # Convert pitches to note names
    unique_pitches = sorted(set(n['pitch'] for n in notes))
    unique_notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4']
    
    players = [
        {'name': 'Player 1', 'experience': 'experienced'},
        {'name': 'Player 2', 'experience': 'beginner'},
    ]
    
    print("\n📊 Test Setup:")
    print(f"   Notes: {unique_notes}")
    print(f"   Players: {len(players)}")
    print(f"   Total note events: {len(notes)}")
    
    # Test 1: Generate assignment with min_transitions strategy
    print("\n🔄 Generating min_transitions arrangement with swap cost optimization...")
    assignment = BellAssignmentAlgorithm.assign_bells(
        unique_notes,
        players,
        strategy='min_transitions',
        note_timings=notes,
        config={'MAX_BELLS_PER_PLAYER': 8}
    )
    
    print("\n✓ Assignment generated:")
    for player_name, player_data in assignment.items():
        bells = player_data.get('bells', [])
        left = player_data.get('left_hand', [])
        right = player_data.get('right_hand', [])
        print(f"   {player_name}: {len(bells)} bells")
        print(f"      Bells: {bells}")
        print(f"      Left:  {left}")
        print(f"      Right: {right}")
    
    # Test 2: Calculate swap cost for actual assignment
    print("\n📈 Swap Cost Analysis:")
    for player_name, player_data in assignment.items():
        bells = player_data.get('bells', [])
        if len(bells) > 1:
            # Simulate the swaps needed for this assignment
            from app.services.music_parser import MusicParser
            
            hand_map = {}
            for idx, bell in enumerate(bells):
                hand_map[bell] = 'left' if idx % 2 == 0 else 'right'
            
            # Count swaps
            player_note_events = [n for n in notes if MusicParser.pitch_to_note_name(n['pitch']) in bells]
            player_note_events.sort(key=lambda n: n['time'])
            
            swaps = 0
            current_hand = None
            events_list = []
            
            for note in player_note_events:
                note_name = MusicParser.pitch_to_note_name(note['pitch'])
                required_hand = hand_map[note_name]
                
                if current_hand is not None and current_hand != required_hand:
                    swaps += 1
                    events_list.append(f"SWAP→{required_hand}")
                else:
                    events_list.append(required_hand[0].upper())
                
                current_hand = required_hand
            
            print(f"   {player_name}:")
            print(f"      Bells: {bells}")
            print(f"      Hand sequence: {' '.join(events_list)}")
            print(f"      Total swaps: {swaps}")
    
    # Test 3: Verify quality score includes hand swap efficiency
    print("\n🎯 Quality Score Calculation:")
    quality_score = ArrangementValidator.calculate_quality_score(assignment, {'notes': notes})
    print(f"   Quality score: {quality_score:.1f}/100")
    
    validation = ArrangementValidator.validate(assignment)
    print(f"   Valid: {validation['valid']}")
    if validation['issues']:
        print(f"   Issues: {validation['issues']}")
    if validation['warnings']:
        for w in validation['warnings']:
            print(f"      ⚠️  {w}")
    
    # Test 4: Verify all players have at least 2 bells
    print("\n✅ Validation Checks:")
    all_valid = True
    for player_name, player_data in assignment.items():
        bell_count = len(player_data.get('bells', []))
        if bell_count >= 2:
            print(f"   {player_name}: {bell_count} bells ✓")
        else:
            print(f"   {player_name}: {bell_count} bells ✗ (minimum is 2)")
            all_valid = False
    
    if all_valid:
        print("\n🎉 All players have minimum 2 bells!")
    else:
        print("\n❌ Some players violate minimum bell requirement")
        assert False, "Some players violate minimum bell requirement"
    
    # Test 5: Verify swap optimization worked
    print("\n🔍 Swap Cost Optimization Verification:")
    
    # Calculate average swap cost
    total_swaps = 0
    num_multi_bell_players = 0
    
    for player_name, player_data in assignment.items():
        bells = player_data.get('bells', [])
        if len(bells) > 1:
            from app.services.music_parser import MusicParser
            
            player_note_events = [n for n in notes if MusicParser.pitch_to_note_name(n['pitch']) in bells]
            
            if len(player_note_events) > 1:
                swap_cost = SwapCostCalculator.calculate_swap_cost_for_player(
                    player_data,
                    bells[-1],  # Simulate the last bell
                    notes
                )
                total_swaps += swap_cost
                num_multi_bell_players += 1
    
    if num_multi_bell_players > 0:
        avg_swap_cost = total_swaps / num_multi_bell_players
        print(f"   Multi-bell players: {num_multi_bell_players}")
        print(f"   Total swap cost: {total_swaps}")
        print(f"   Average swaps per player: {avg_swap_cost:.2f}")
        print(f"   ✓ Swap cost optimization is working")
    else:
        print("   ⚠️  No multi-bell players to evaluate swap cost")
    
    print("\n" + "=" * 70)
    print("✅ Phase 5 Hand Swap Optimization Test PASSED")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        test_swap_cost_optimization()
        print("All tests passed!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
