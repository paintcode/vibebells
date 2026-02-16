from app import create_app
import os

# Create Flask app
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Only enable debug mode in development, never in production
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, port=5000)
