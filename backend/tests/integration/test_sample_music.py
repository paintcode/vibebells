#!/usr/bin/env python3
"""Test with actual sample music file - 8 players (4 beginners)"""

import sys
import os
from app import create_app
from app.services.music_parser import MusicParser
from app.services.arrangement_generator import ArrangementGenerator

def test_sample_music_with_beginners():
    """Test multi-bell assignment with sample music and mixed experience levels"""
    app = create_app('development')
    
    with app.app_context():
        # Parse sample music
        sample_file = os.path.join(
            os.path.dirname(__file__),
            '../sample-music/O for a Thousand Tongues to Sing.mid'
        )
        
        if not os.path.exists(sample_file):
            print(f"❌ Sample file not found: {sample_file}")
            return
        
        print(f"📁 Parsing: {sample_file}")
        music_parser = MusicParser()
        music_data = music_parser.parse(sample_file)
        print(f"✓ Parsed {len(music_data['unique_notes'])} unique notes")
        print(f"✓ Total note events: {music_data['total_note_events']}")
        
        # Create players: 8 total (2 experienced, 2 intermediate, 4 beginners)
        players = [
            {'name': 'Player 1', 'experience': 'experienced'},
            {'name': 'Player 2', 'experience': 'experienced'},
            {'name': 'Player 3', 'experience': 'intermediate'},
            {'name': 'Player 4', 'experience': 'intermediate'},
            {'name': 'Player 5', 'experience': 'beginner'},
            {'name': 'Player 6', 'experience': 'beginner'},
            {'name': 'Player 7', 'experience': 'beginner'},
            {'name': 'Player 8', 'experience': 'beginner'},
        ]
        
        # Generate arrangement
        arrangement_gen = ArrangementGenerator()
        result = arrangement_gen.generate(music_data, players)
        
        # Handle new return structure with expansion info
        if isinstance(result, dict) and 'arrangements' in result:
            arrangements = result['arrangements']
            expansion_info = result.get('expansion_info')
        else:
            arrangements = result if isinstance(result, list) else [result]
            expansion_info = None
        
        if not arrangements:
            print("❌ No arrangements generated")
            return
        
        # Check the first (best) arrangement
        best = arrangements[0]
        print(f"\n✓ Generated {len(arrangements)} arrangements")
        print(f"✓ Best arrangement: {best['strategy']}")
        print(f"✓ Quality score: {best['quality_score']:.1f}/100")
        
        # Show expansion info if applicable
        if expansion_info:
            print(f"\n⚠ Player Expansion Needed:")
            print(f"  {expansion_info['message']}")
        
        # Verify all players have at least 2 bells
        print("\nBell Assignment:")
        print("-" * 50)
        
        all_have_minimum = True
        beginners_with_1_bell = []
        
        for player, data in best['assignments'].items():
            bells = data['bells']
            left = data['left_hand']
            right = data['right_hand']
            
            experience = next((p['experience'] for p in players if p['name'] == player), 'unknown')
            
            if len(bells) < 2:
                all_have_minimum = False
                if experience == 'beginner':
                    beginners_with_1_bell.append(player)
                status = "❌ BELOW MINIMUM"
            else:
                status = "✓"
            
            print(f"{status} {player:12} ({experience:12}): {len(bells)} bells (L:{len(left)} R:{len(right)})")
            if bells:
                print(f"    Bells: {', '.join(bells)}")
        
        print("-" * 50)
        total_bells = sum(len(data['bells']) for data in best['assignments'].values())
        print(f"Total bells assigned: {total_bells}/{len(music_data['unique_notes'])}")
        
        # Report issues
        if not all_have_minimum:
            print(f"\n❌ ERROR: Not all players have minimum 2 bells!")
            if beginners_with_1_bell:
                print(f"   Beginners with <2 bells: {', '.join(beginners_with_1_bell)}")
        else:
            print(f"\n✓ All players have at least 2 bells")

if __name__ == '__main__':
    test_sample_music_with_beginners()
