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
    # Path from backend/tests/integration/ to project root sample-music/
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    project_root = os.path.dirname(backend_dir)
    sample_file = os.path.join(project_root, 'sample-music', 'O for a Thousand Tongues to Sing.mid')
    
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
            result = gen.generate(music_data, players)
        
        arrangements = result['arrangements']
        
        print(f"\nResults:")
        print(f"  Arrangements: {len(arrangements)}")
        
        # Verify we got arrangements
        assert len(arrangements) > 0, "Should generate at least one arrangement"
        assert 'quality_score' in arrangements[0], "Arrangement should have quality_score"
        assert 'strategy' in arrangements[0], "Arrangement should have strategy"
        assert 'assignments' in arrangements[0], "Arrangement should have assignments"
        
        print(f"  Best score: {arrangements[0]['quality_score']:.1f}/100")
        print(f"  Strategy: {arrangements[0]['strategy']}")
        
        # Show best arrangement
        print(f"\nBest Arrangement:")
        for player_name in sorted(arrangements[0]['assignments'].keys()):
            bells = arrangements[0]['assignments'][player_name]['bells']
            print(f"  {player_name}: {len(bells)} bells")
        
        print("\nSUCCESS: Complete system working with frequency optimization!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    try:
        test_complete_system()
        sys.exit(0)
    except Exception:
        sys.exit(1)
