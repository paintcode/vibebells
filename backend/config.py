import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', True)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    REQUEST_TIMEOUT = 30  # 30 second timeout
    ALLOWED_EXTENSIONS = {'mid', 'midi', 'musicxml', 'xml'}
    MIN_PLAYERS = 1
    MAX_PLAYERS = 20
    
    # Multi-bell configuration
    MAX_BELLS_PER_PLAYER = 8  # Overall practical limit
    
    # Experience-level-based maximum bells
    MAX_BELLS_PER_EXPERIENCE = {
        'experienced': 5,      # Experienced players can handle up to 5 bells
        'intermediate': 3,     # Intermediate players up to 3 bells
        'beginner': 2          # Beginners exactly 2 bells (1 per hand)
    }
    
    HAND_GAP_THRESHOLD_BEATS = 1.0  # Minimum beats between same-hand notes (configurable)
    IMPOSSIBLE_SWAP_GAP_MS = 100  # Gap (ms) below which a bell swap is physically impossible to perform

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
