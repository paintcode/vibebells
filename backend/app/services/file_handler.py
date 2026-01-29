import os
import uuid
from werkzeug.utils import secure_filename

class FileHandler:
    """Handle file operations"""
    
    ALLOWED_EXTENSIONS = {'mid', 'midi', 'musicxml', 'xml'}
    
    @staticmethod
    def get_file_type(filename):
        """Determine file type from extension"""
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
        if not ext:
            raise ValueError("File has no extension")
        if ext in {'mid', 'midi'}:
            return 'midi'
        elif ext in {'musicxml', 'xml'}:
            return 'musicxml'
        raise ValueError(f"Unknown file type: {ext}")
    
    @staticmethod
    def save_file(file, upload_folder):
        """Save uploaded file securely with UUID"""
        if not file or file.filename == '':
            raise ValueError('No file provided')
        
        filename = secure_filename(file.filename)
        
        # Validate extension
        if '.' not in filename:
            raise ValueError('File has no extension')
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in FileHandler.ALLOWED_EXTENSIONS:
            raise ValueError(f'File type not allowed. Supported: {", ".join(FileHandler.ALLOWED_EXTENSIONS)}')
        
        # Generate unique filename with UUID to prevent collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(upload_folder, unique_filename)
        
        try:
            file.save(filepath)
            return filepath
        except Exception as e:
            raise Exception(f"Failed to save file: {str(e)}")
    
    @staticmethod
    def delete_file(filepath):
        """Delete a file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            import logging
            logging.error(f"Error deleting file {filepath}: {e}")
            return False

