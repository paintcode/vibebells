"""
Final system verification with frequency optimization.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.services.arrangement_generator import ArrangementGenerator
from app.services.music_parser import MusicParser


def test_complete_system():
    """Test complete system with frequency optimization"""
    
    # Initialize app
    app = create_app()
    
    # Parse real music
    parser = MusicParser()
    sample_file = os.path.join(os.path.dirname(__file__), '../sample-music/O for a Thousand Tongues to Sing.mid')
    
    try:
        print("Parsing MIDI file...")
        music_data = parser.parse(sample_file)
        
        # Create player configuration
        players = [
            {'name': 'Player 1 (Exp)', 'experience': 'experienced'},
            {'name': 'Player 2 (Exp)', 'experience': 'experienced'},
            {'name': 'Player 3 (Int)', 'experience': 'intermediate'},
            {'name': 'Player 4 (Int)', 'experience': 'intermediate'},
            {'name': 'Player 5 (Beg)', 'experience': 'beginner'},
            {'name': 'Player 6 (Beg)', 'experience': 'beginner'},
        ]
        
        print(f"Generating arrangements with frequency optimization...")
        print(f"  Notes: {len(music_data['unique_notes'])} unique")
        print(f"  Events: {len(music_data['notes'])} total")
        print(f"  Players: {len(players)}")
        
        with app.app_context():
            gen = ArrangementGenerator()
            arrangements = gen.generate(music_data, players)
        
        print(f"\nResults:")
        print(f"  Arrangements: {len(arrangements)}")
        print(f"  Best score: {arrangements[0]['quality_score']:.1f}/100")
        print(f"  Strategy: {arrangements[0]['strategy']}")
        
        # Show best arrangement
        print(f"\nBest Arrangement:")
        for player_name in sorted(arrangements[0]['assignments'].keys()):
            bells = arrangements[0]['assignments'][player_name]['bells']
            print(f"  {player_name}: {len(bells)} bells")
        
        print("\nSUCCESS: Complete system working with frequency optimization!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_complete_system()
    sys.exit(0 if success else 1)
