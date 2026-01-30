#!/usr/bin/env python3
"""Quick integration test for multi-bell functionality"""

from app import create_app
from app.services.bell_assignment import BellAssignmentAlgorithm
from app.services.conflict_resolver import ConflictResolver
from app.services.arrangement_validator import ArrangementValidator

def test_multibelle_assignment():
    """Test multi-bell assignment works correctly"""
    app = create_app('development')
    
    with app.app_context():
        config = {
            'MAX_BELLS_PER_PLAYER': 8,
            'HAND_GAP_THRESHOLD_BEATS': 1.0
        }
        
        players = [
            {'name': 'Player 1', 'experience': 'experienced'},
            {'name': 'Player 2', 'experience': 'intermediate'},
            {'name': 'Player 3', 'experience': 'beginner'}
        ]
        
        notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
        melody = ['E4', 'G4', 'C5']
        
        # Test 1: Bell assignment creates proper structure
        result = BellAssignmentAlgorithm.assign_bells(
            notes, players, 
            strategy='experienced_first',
            priority_notes=melody,
            config=config
        )
        
        assert isinstance(result, dict), "Result should be dict"
        assert len(result) == 3, "Should have 3 players"
        
        total_bells = 0
        for player, data in result.items():
            assert 'bells' in data, f"{player} missing 'bells' key"
            assert 'left_hand' in data, f"{player} missing 'left_hand' key"
            assert 'right_hand' in data, f"{player} missing 'right_hand' key"
            
            bells = data['bells']
            left = data['left_hand']
            right = data['right_hand']
            
            # Verify invariant: left ∪ right = bells
            combined = set(left) | set(right)
            assert combined == set(bells), f"{player}: hand union != bells"
            
            # Verify no overlap: left ∩ right = ∅
            assert set(left) & set(right) == set(), f"{player}: hands overlap"
            
            # Verify count: |left| + |right| = |bells|
            assert len(left) + len(right) == len(bells), f"{player}: counts don't match"
            
            print(f"✓ {player}: {len(bells)} bells (L:{len(left)} R:{len(right)})")
            total_bells += len(bells)
        
        print(f"✓ Total bells assigned: {total_bells}/{len(notes)}")
        
        # Test 2: Conflict resolution maintains structure
        resolved = ConflictResolver.resolve_duplicates(result)
        for player, data in resolved.items():
            assert 'bells' in data and 'left_hand' in data and 'right_hand' in data
        print("✓ Conflict resolution maintains structure")
        
        # Test 3: Validation works with new structure
        balanced = ConflictResolver.balance_assignments(resolved)
        validation = ArrangementValidator.validate(balanced)
        assert 'valid' in validation
        assert 'issues' in validation
        assert 'warnings' in validation
        print(f"✓ Validation works: valid={validation['valid']}")
        
        # Test 4: Quality score calculation
        score = ArrangementValidator.calculate_quality_score(balanced)
        assert 0 <= score <= 100, f"Score {score} out of bounds"
        print(f"✓ Quality score: {score}/100")
        
        # Test 5: Sustainability check
        music_data = {
            'melody_pitches': [64, 67, 72],  # E4, G4, C5 in MIDI
            'unique_notes': [60, 62, 64, 65, 67, 69, 71, 72]
        }
        sustainability = ArrangementValidator.sustainability_check(balanced, music_data)
        assert 'sustainable' in sustainability
        assert 'recommendations' in sustainability
        print(f"✓ Sustainability check: {len(sustainability['recommendations'])} recommendations")
        
        print("\n" + "="*50)
        print("✅ All multi-bell tests passed!")
        print("="*50)
        
        # Show final result
        print("\nFinal Arrangement:")
        for player, data in balanced.items():
            if data['bells']:
                print(f"\n{player}:")
                print(f"  Bells: {', '.join(data['bells'])}")
                print(f"  Left:  {', '.join(data['left_hand']) if data['left_hand'] else '—'}")
                print(f"  Right: {', '.join(data['right_hand']) if data['right_hand'] else '—'}")

if __name__ == '__main__':
    test_multibelle_assignment()
