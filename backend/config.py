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
    MAX_PLAYERS = 100
    
    # Multi-bell configuration
    MAX_BELLS_PER_PLAYER = 8  # Overall practical limit
    
    # Experience-level-based maximum bells
    MAX_BELLS_PER_EXPERIENCE = {
        'experienced': 5,      # Experienced players can handle up to 5 bells
        'intermediate': 3,     # Intermediate players up to 3 bells
        'beginner': 2          # Beginners exactly 2 bells (1 per hand)
    }
    
    IMPOSSIBLE_SWAP_GAP_MS = 500  # Gap (ms) below which a bell swap is physically impossible to perform

    # Minimum gap (ms) required between consecutive notes on the same hand before an extra bell
    # may be assigned.  Reflects real-world swap speed limits per experience level.
    MIN_SWAP_GAP_MS = {
        'experienced': 500,
        'intermediate': 1000,
        'beginner': 2000,
    }

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
