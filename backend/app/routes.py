from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import os
import json
import logging
from io import BytesIO
from datetime import datetime
from app.services.file_handler import FileHandler
from app.services.music_parser import MusicParser
from app.services.arrangement_generator import ArrangementGenerator
from app.services.export_formatter import ExportFormatter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

class APIError(Exception):
    """Custom API error"""
    def __init__(self, message, code='ERR_UNKNOWN', status_code=400):
        self.message = message
        self.code = code
        self.status_code = status_code

@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@api_bp.route('/generate-arrangements', methods=['POST'])
def generate_arrangements():
    """Generate bell arrangements from music file and player config"""
    filepath = None
    try:
        # Validate file presence
        if 'file' not in request.files:
            raise APIError('No file provided', 'ERR_NO_FILE', 400)
        
        file = request.files['file']
        
        if file.filename == '':
            raise APIError('No file selected', 'ERR_NO_FILE_SELECTED', 400)
        
        # Validate players config
        if 'players' not in request.form:
            raise APIError('No player configuration provided', 'ERR_NO_PLAYERS', 400)
        
        # Parse and validate players JSON
        try:
            players = json.loads(request.form.get('players', '[]'))
        except json.JSONDecodeError:
            raise APIError('Invalid player configuration JSON', 'ERR_INVALID_JSON', 400)
        
        if not isinstance(players, list):
            raise APIError('Players must be an array', 'ERR_INVALID_PLAYERS', 400)
        
        if len(players) < current_app.config.get('MIN_PLAYERS', 1):
            raise APIError(f"Minimum {current_app.config.get('MIN_PLAYERS', 1)} player(s) required", 'ERR_TOO_FEW_PLAYERS', 400)
        
        if len(players) > current_app.config.get('MAX_PLAYERS', 20):
            raise APIError(f"Maximum {current_app.config.get('MAX_PLAYERS', 20)} players allowed", 'ERR_TOO_MANY_PLAYERS', 400)
        
        # Validate player names
        for player in players:
            if not isinstance(player, dict):
                raise APIError('Each player must be an object', 'ERR_INVALID_PLAYER_FORMAT', 400)
            if 'name' not in player or not player['name']:
                raise APIError('Each player must have a name', 'ERR_PLAYER_NO_NAME', 400)
        
        # Save uploaded file with UUID
        filepath = FileHandler.save_file(file, current_app.config['UPLOAD_FOLDER'])
        logger.info(f"File saved: {filepath}")
        
        # Parse music file
        music_parser = MusicParser()
        music_data = music_parser.parse(filepath)
        logger.info(f"Parsed music: {music_data['note_count']} unique notes")
        
        # Generate arrangements
        arrangement_gen = ArrangementGenerator()
        result = arrangement_gen.generate(music_data, players)
        
        # Handle both old (list) and new (dict) return structures
        if isinstance(result, dict) and 'arrangements' in result:
            arrangements = result['arrangements']
            logger.info(f"Generated {len(arrangements)} arrangements")
            
            response_data = {
                'success': True,
                'arrangements': arrangements,
                'note_count': music_data['note_count'],
                'melody_count': len(music_data.get('melody_pitches', [])),
                'harmony_count': len(music_data.get('harmony_pitches', [])),
                'best_arrangement': arrangements[0] if arrangements else None
            }
            
            # Add expansion info if applicable
            if result.get('expanded'):
                response_data['expansion_info'] = {
                    'expanded': True,
                    'original_player_count': result['original_player_count'],
                    'final_player_count': result['final_player_count'],
                    'minimum_required': result['minimum_players'],
                    'message': f"The song requires at least {result['minimum_players']} players. Arrangements show {result['final_player_count']} players (including {result['final_player_count'] - result['original_player_count']} virtual players)."
                }
            
            return jsonify(response_data), 200
        else:
            # Fallback for old return structure (just list)
            arrangements = result if isinstance(result, list) else [result]
            logger.info(f"Generated {len(arrangements)} arrangements")
            
            return jsonify({
                'success': True,
                'arrangements': arrangements,
                'note_count': music_data['note_count'],
                'melody_count': len(music_data.get('melody_pitches', [])),
                'harmony_count': len(music_data.get('harmony_pitches', [])),
                'best_arrangement': arrangements[0] if arrangements else None
            }), 200
    
    except ValueError as e:
        raise APIError(str(e), 'ERR_VALIDATION', 400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        # Provide context about what failed
        error_msg = str(e)
        if 'MIDI' in error_msg or 'midi' in error_msg:
            raise APIError(error_msg, 'ERR_MUSIC_PARSE', 400)
        elif 'file' in error_msg.lower():
            raise APIError(error_msg, 'ERR_FILE_SAVE', 400)
        else:
            raise APIError('Failed to generate arrangements', 'ERR_GENERATION_FAILED', 500)
    
    finally:
        # Clean up uploaded file
        if filepath:
            FileHandler.delete_file(filepath)

@api_bp.errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors"""
    return jsonify({
        'success': False,
        'error': error.message,
        'code': error.code
    }), error.status_code

@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'code': 'ERR_NOT_FOUND'
    }), 404

@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 'ERR_INTERNAL'
    }), 500

@api_bp.route('/export-csv', methods=['POST'])
def export_csv():
    """Export arrangement as CSV file"""
    try:
        # Get arrangement data from request
        data = request.get_json()
        
        if not data:
            raise APIError('No arrangement data provided', 'ERR_NO_DATA', 400)
        
        arrangement = data.get('arrangement')
        players = data.get('players', [])
        filename = data.get('filename', 'arrangement')
        strategy = data.get('strategy', 'unknown')
        swap_counts = data.get('swaps')  # May be None if not provided
        
        if not arrangement:
            raise APIError('No arrangement data provided', 'ERR_NO_DATA', 400)
        
        # Validate players have required fields
        for player in players:
            if 'name' not in player:
                raise APIError('Each player must have a name', 'ERR_PLAYER_NO_NAME', 400)
            if 'experience' not in player:
                raise APIError('Each player must have an experience level', 'ERR_PLAYER_NO_EXPERIENCE', 400)
        
        # Format arrangement as CSV (pass swap_counts if available)
        csv_content = ExportFormatter.format_to_csv(arrangement, players, filename, strategy, swap_counts)
        
        # Create response with CSV file
        csv_bytes = csv_content.encode('utf-8')
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        clean_filename = ''.join(c if c.isalnum() else '_' for c in filename.split('.')[0])
        download_name = f"arrangement_{clean_filename}_{timestamp}.csv"
        
        return send_file(
            BytesIO(csv_bytes),
            mimetype='text/csv',
            as_attachment=True,
            download_name=download_name
        )
    
    except APIError as e:
        logger.error(f"CSV export error: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in CSV export: {str(e)}", exc_info=True)
        raise APIError('Failed to export arrangement', 'ERR_EXPORT_FAILED', 500)

