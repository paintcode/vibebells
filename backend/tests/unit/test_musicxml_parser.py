"""
Unit tests for MusicXMLParser service
Tests MusicXML file parsing, error handling, and edge cases
"""

import os
import tempfile
from music21 import stream, note, chord, tempo, meter
from app.services.musicxml_parser import MusicXMLParser


def _create_valid_musicxml_file():
    """Helper to create a valid MusicXML file for testing"""
    # Create simple score with 3 notes
    s = stream.Score()
    part = stream.Part()
    s.append(part)
    
    # Add tempo
    part.append(tempo.MetronomeMark(number=120))
    
    # Add time signature
    part.append(meter.TimeSignature('4/4'))
    
    # Add notes: C4, E4, G4
    part.append(note.Note('C4', quarterLength=1.0))
    part.append(note.Note('E4', quarterLength=1.0))
    part.append(note.Note('G4', quarterLength=1.0))
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as tmp:
        s.write('musicxml', fp=tmp.name)
        return tmp.name


def _create_musicxml_with_chord():
    """Helper to create MusicXML file with chord"""
    s = stream.Score()
    part = stream.Part()
    s.append(part)
    
    part.append(tempo.MetronomeMark(number=120))
    part.append(meter.TimeSignature('4/4'))
    
    # Add chord (C major)
    c_major = chord.Chord(['C4', 'E4', 'G4'])
    c_major.quarterLength = 2.0
    part.append(c_major)
    
    # Add single note
    part.append(note.Note('A4', quarterLength=1.0))
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as tmp:
        s.write('musicxml', fp=tmp.name)
        return tmp.name


def _create_empty_musicxml_file():
    """Helper to create MusicXML file with no notes"""
    s = stream.Score()
    part = stream.Part()
    s.append(part)
    
    # Only metadata, no notes
    part.append(tempo.MetronomeMark(number=120))
    part.append(meter.TimeSignature('4/4'))
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as tmp:
        s.write('musicxml', fp=tmp.name)
        return tmp.name


def _create_musicxml_without_tempo():
    """Helper to create MusicXML file without tempo marking"""
    s = stream.Score()
    part = stream.Part()
    s.append(part)
    
    # No tempo, only notes
    part.append(note.Note('C4', quarterLength=1.0))
    part.append(note.Note('D4', quarterLength=1.0))
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as tmp:
        s.write('musicxml', fp=tmp.name)
        return tmp.name


def test_parse_valid_musicxml_file():
    """Should successfully parse valid MusicXML file"""
    xml_file = _create_valid_musicxml_file()
    
    try:
        result = MusicXMLParser.parse(xml_file)
        
        # Verify structure
        assert 'notes' in result
        assert 'unique_notes' in result
        assert 'note_count' in result
        assert 'tempo' in result
        assert 'format' in result
        assert 'chords' in result
        
        # Verify content
        assert result['format'] == 'musicxml'
        assert result['note_count'] == 3
        assert len(result['notes']) == 3
        assert len(result['unique_notes']) == 3
        
        # Verify tempo
        assert result['tempo'] == 120
        
    finally:
        os.unlink(xml_file)


def test_parse_musicxml_with_chord():
    """Should parse chords and extract individual notes"""
    xml_file = _create_musicxml_with_chord()
    
    try:
        result = MusicXMLParser.parse(xml_file)
        
        # Should have 4 notes (3 from chord + 1 single note)
        assert len(result['notes']) == 4
        
        # Should have chord info
        assert len(result['chords']) >= 1
        
        # Verify chord members are marked
        chord_notes = [n for n in result['notes'] if n.get('is_chord_member')]
        assert len(chord_notes) == 3
        
        # Verify single note is not marked as chord member
        single_notes = [n for n in result['notes'] if not n.get('is_chord_member')]
        assert len(single_notes) == 1
        
    finally:
        os.unlink(xml_file)


def test_parse_empty_musicxml_file():
    """Should raise error for MusicXML file with no notes"""
    xml_file = _create_empty_musicxml_file()
    
    try:
        try:
            MusicXMLParser.parse(xml_file)
            assert False, "Should have raised exception"
        except Exception as e:
            assert "No notes found" in str(e)
    finally:
        os.unlink(xml_file)


def test_parse_corrupted_musicxml_file():
    """Should raise error for corrupted MusicXML file"""
    # Create invalid XML file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as tmp:
        tmp.write('This is not valid XML <unclosed tag')
        tmp_path = tmp.name
    
    try:
        try:
            MusicXMLParser.parse(tmp_path)
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Failed to parse MusicXML file" in str(e)
    finally:
        os.unlink(tmp_path)


def test_parse_nonexistent_file():
    """Should raise error for nonexistent file"""
    try:
        MusicXMLParser.parse('/nonexistent/path/file.xml')
        assert False, "Should have raised exception"
    except Exception:
        pass  # Expected


def test_parse_musicxml_without_tempo():
    """Should use default tempo (120 BPM) when tempo not specified"""
    xml_file = _create_musicxml_without_tempo()
    
    try:
        result = MusicXMLParser.parse(xml_file)
        
        # Should use default tempo
        assert result['tempo'] == 120
        assert len(result['notes']) == 2
        
    finally:
        os.unlink(xml_file)


def test_pitch_to_note_name_middle_c():
    """Should convert MIDI pitch 60 to C4"""
    result = MusicXMLParser.pitch_to_note_name(60)
    assert result == 'C4'


def test_pitch_to_note_name_a440():
    """Should convert MIDI pitch 69 to A4 (440Hz)"""
    result = MusicXMLParser.pitch_to_note_name(69)
    assert result == 'A4'


def test_pitch_to_note_name_sharp():
    """Should handle sharp notes"""
    result = MusicXMLParser.pitch_to_note_name(61)
    assert result == 'C#4'


def test_pitch_to_note_name_low_octave():
    """Should handle low octaves correctly"""
    result = MusicXMLParser.pitch_to_note_name(24)
    assert result == 'C1'


def test_pitch_to_note_name_high_octave():
    """Should handle high octaves correctly"""
    result = MusicXMLParser.pitch_to_note_name(96)
    assert result == 'C7'


def test_parse_notes_have_required_fields():
    """Should include all required fields in parsed notes"""
    xml_file = _create_valid_musicxml_file()
    
    try:
        result = MusicXMLParser.parse(xml_file)
        
        for note_data in result['notes']:
            assert 'pitch' in note_data
            assert 'duration' in note_data
            assert 'offset' in note_data
            assert 'is_chord_member' in note_data
            
            # Verify types
            assert isinstance(note_data['pitch'], int)
            assert isinstance(note_data['duration'], (int, float))
            assert isinstance(note_data['offset'], (int, float))
            assert isinstance(note_data['is_chord_member'], bool)
            
    finally:
        os.unlink(xml_file)


def test_parse_chord_info_structure():
    """Should include correct structure in chord info"""
    xml_file = _create_musicxml_with_chord()
    
    try:
        result = MusicXMLParser.parse(xml_file)
        
        for chord_info in result['chords']:
            assert 'pitches' in chord_info
            assert 'duration' in chord_info
            assert 'offset' in chord_info
            assert 'type' in chord_info
            
            assert chord_info['type'] == 'chord'
            assert isinstance(chord_info['pitches'], list)
            assert len(chord_info['pitches']) >= 2  # Chord must have 2+ notes
            
    finally:
        os.unlink(xml_file)


def test_parse_invalid_xml_structure():
    """Should handle XML files with invalid music structure"""
    # Create XML that's valid but not valid MusicXML
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as tmp:
        tmp.write('<?xml version="1.0"?><root><invalid>structure</invalid></root>')
        tmp_path = tmp.name
    
    try:
        try:
            MusicXMLParser.parse(tmp_path)
            assert False, "Should have raised exception"
        except Exception:
            pass  # Expected
    finally:
        os.unlink(tmp_path)
