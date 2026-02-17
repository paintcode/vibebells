"""
Unit tests for FileHandler service
Tests file validation, saving, and cleanup operations
"""

import os
import tempfile
from unittest.mock import Mock
from app.services.file_handler import FileHandler


def test_get_file_type_midi_extension():
    """Should recognize .mid extension as MIDI"""
    result = FileHandler.get_file_type('song.mid')
    assert result == 'midi'

def test_get_file_type_midi_uppercase():
    """Should recognize .MIDI extension (case insensitive)"""
    result = FileHandler.get_file_type('SONG.MIDI')
    assert result == 'midi'

def test_get_file_type_musicxml_extension():
    """Should recognize .xml extension as MusicXML"""
    result = FileHandler.get_file_type('score.xml')
    assert result == 'musicxml'

def test_get_file_type_musicxml_long_extension():
    """Should recognize .musicxml extension"""
    result = FileHandler.get_file_type('score.musicxml')
    assert result == 'musicxml'

def test_get_file_type_no_extension():
    """Should raise error for file without extension"""
    try:
        FileHandler.get_file_type('filename_without_extension')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "File has no extension" in str(e)

def test_get_file_type_unknown_extension():
    """Should raise error for unsupported file type"""
    try:
        FileHandler.get_file_type('document.pdf')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown file type" in str(e)

def test_save_file_valid_midi():
    """Should save valid MIDI file with UUID prefix"""
    # Create mock file
    mock_file = Mock()
    mock_file.filename = 'test_song.mid'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the save method
        saved_path = None
        def save_mock(path):
            nonlocal saved_path
            saved_path = path
            # Create actual file
            with open(path, 'w') as f:
                f.write('mock midi data')
        
        mock_file.save = save_mock
        
        # Save file
        result_path = FileHandler.save_file(mock_file, tmpdir)
        
        # Verify UUID prefix in filename
        filename = os.path.basename(result_path)
        assert 'test_song.mid' in filename
        assert len(filename) > len('test_song.mid')  # Has UUID prefix
        
        # Verify file exists
        assert os.path.exists(result_path)

def test_save_file_invalid_extension():
    """Should reject file with invalid extension"""
    mock_file = Mock()
    mock_file.filename = 'document.txt'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            FileHandler.save_file(mock_file, tmpdir)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "File type not allowed" in str(e)

def test_save_file_no_extension():
    """Should reject file without extension"""
    mock_file = Mock()
    mock_file.filename = 'noextension'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            FileHandler.save_file(mock_file, tmpdir)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "File has no extension" in str(e)

def test_save_file_no_file_provided():
    """Should raise error when no file provided"""
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            FileHandler.save_file(None, tmpdir)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No file provided" in str(e)

def test_save_file_empty_filename():
    """Should raise error when filename is empty"""
    mock_file = Mock()
    mock_file.filename = ''
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            FileHandler.save_file(mock_file, tmpdir)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No file provided" in str(e)

def test_save_file_write_error():
    """Should handle file write errors gracefully"""
    mock_file = Mock()
    mock_file.filename = 'test.mid'
    mock_file.save = Mock(side_effect=IOError("Disk full"))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            FileHandler.save_file(mock_file, tmpdir)
            assert False, "Should have raised Exception"
        except Exception as e:
            assert "Failed to save file" in str(e)

def test_delete_file_existing():
    """Should delete existing file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.mid') as tmp:
        tmp.write('test data')
        tmp_path = tmp.name
    
    # Verify file exists
    assert os.path.exists(tmp_path)
    
    # Delete file
    result = FileHandler.delete_file(tmp_path)
    
    # Verify deletion
    assert result is True
    assert not os.path.exists(tmp_path)

def test_delete_file_nonexistent():
    """Should handle nonexistent file gracefully (returns None, no exception)"""
    result = FileHandler.delete_file('/nonexistent/path/file.mid')
    # Returns None (no return statement when file doesn't exist)
    assert result is None or result is False

def test_allowed_extensions_includes_all_formats():
    """Should support all documented file formats"""
    expected = {'mid', 'midi', 'musicxml', 'xml'}
    assert FileHandler.ALLOWED_EXTENSIONS == expected
