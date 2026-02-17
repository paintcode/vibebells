"""
Unit tests for MIDIParser service
Tests MIDI file parsing, error handling, and edge cases
"""

import os
import tempfile
import mido
from app.services.midi_parser import MIDIParser


def _create_valid_midi_file():
    """Helper to create a valid MIDI file for testing"""
    # Create simple MIDI file with 3 notes
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Add tempo
    track.append(mido.MetaMessage('set_tempo', tempo=500000))  # 120 BPM
    
    # Add notes: C4, E4, G4 (C major chord)
    track.append(mido.Message('note_on', note=60, velocity=64, time=0))
    track.append(mido.Message('note_off', note=60, velocity=0, time=480))
    track.append(mido.Message('note_on', note=64, velocity=64, time=0))
    track.append(mido.Message('note_off', note=64, velocity=0, time=480))
    track.append(mido.Message('note_on', note=67, velocity=64, time=0))
    track.append(mido.Message('note_off', note=67, velocity=0, time=480))
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mid') as tmp:
        tmp_path = tmp.name
    mid.save(tmp_path)
    return tmp_path


def _create_empty_midi_file():
    """Helper to create MIDI file with no notes"""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Only tempo, no notes
    track.append(mido.MetaMessage('set_tempo', tempo=500000))
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mid') as tmp:
        tmp_path = tmp.name
    mid.save(tmp_path)
    return tmp_path


def _create_midi_without_tempo():
    """Helper to create MIDI file without tempo information"""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Add notes but no tempo
    track.append(mido.Message('note_on', note=60, velocity=64, time=0))
    track.append(mido.Message('note_off', note=60, velocity=0, time=480))
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mid') as tmp:
        tmp_path = tmp.name
    mid.save(tmp_path)
    return tmp_path


def _create_midi_note_on_without_off():
    """Helper to create MIDI file with note_on but no matching note_off"""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Add note_on without note_off
    track.append(mido.Message('note_on', note=60, velocity=64, time=0))
    track.append(mido.Message('note_on', note=64, velocity=64, time=480))
    # Missing note_off events
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mid') as tmp:
        tmp_path = tmp.name
    mid.save(tmp_path)
    return tmp_path


def test_parse_valid_midi_file():
    """Should successfully parse valid MIDI file"""
    midi_file = _create_valid_midi_file()
    
    try:
        result = MIDIParser.parse(midi_file)
        
        # Verify structure
        assert 'notes' in result
        assert 'unique_notes' in result
        assert 'note_count' in result
        assert 'tempo' in result
        assert 'format' in result
        
        # Verify content
        assert result['format'] == 'midi'
        assert result['note_count'] == 3
        assert len(result['notes']) == 3
        assert len(result['unique_notes']) == 3
        assert 60 in result['unique_notes']  # C4
        assert 64 in result['unique_notes']  # E4
        assert 67 in result['unique_notes']  # G4
        
        # Verify tempo
        assert result['tempo'] == 120  # 120 BPM
        
    finally:
        os.unlink(midi_file)


def test_parse_empty_midi_file():
    """Should raise error for MIDI file with no notes"""
    midi_file = _create_empty_midi_file()
    
    try:
        try:
            MIDIParser.parse(midi_file)
            assert False, "Should have raised exception"
        except Exception as e:
            assert "No notes found" in str(e)
    finally:
        os.unlink(midi_file)


def test_parse_corrupted_midi_file():
    """Should raise error for corrupted MIDI file"""
    # Create invalid MIDI file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.mid') as tmp:
        tmp.write('This is not a valid MIDI file')
        tmp_path = tmp.name
    
    try:
        try:
            MIDIParser.parse(tmp_path)
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Failed to parse MIDI file" in str(e)
    finally:
        os.unlink(tmp_path)


def test_parse_nonexistent_file():
    """Should raise error for nonexistent file"""
    try:
        MIDIParser.parse('/nonexistent/path/file.mid')
        assert False, "Should have raised exception"
    except Exception:
        pass  # Expected


def test_parse_midi_without_tempo():
    """Should use default tempo (120 BPM) when tempo not specified"""
    midi_file = _create_midi_without_tempo()
    
    try:
        result = MIDIParser.parse(midi_file)
        
        # Should use default tempo
        assert result['tempo'] == 120
        assert len(result['notes']) == 1
        
    finally:
        os.unlink(midi_file)


def test_parse_midi_note_on_without_off():
    """Should handle note_on events without matching note_off"""
    midi_file = _create_midi_note_on_without_off()
    
    try:
        result = MIDIParser.parse(midi_file)
        
        # Should create notes with default duration
        assert len(result['notes']) == 2
        
        # All notes should have duration >= 1
        for note in result['notes']:
            assert note['duration'] >= 1
        
    finally:
        os.unlink(midi_file)


def test_pitch_to_note_name_middle_c():
    """Should convert MIDI pitch 60 to C4"""
    result = MIDIParser.pitch_to_note_name(60)
    assert result == 'C4'


def test_pitch_to_note_name_a440():
    """Should convert MIDI pitch 69 to A4 (440Hz)"""
    result = MIDIParser.pitch_to_note_name(69)
    assert result == 'A4'


def test_pitch_to_note_name_sharp():
    """Should handle sharp notes"""
    result = MIDIParser.pitch_to_note_name(61)
    assert result == 'C#4'


def test_pitch_to_note_name_low_octave():
    """Should handle low octaves correctly"""
    result = MIDIParser.pitch_to_note_name(24)
    assert result == 'C1'


def test_pitch_to_note_name_high_octave():
    """Should handle high octaves correctly"""
    result = MIDIParser.pitch_to_note_name(96)
    assert result == 'C7'


def test_parse_notes_have_required_fields():
    """Should include all required fields in parsed notes"""
    midi_file = _create_valid_midi_file()
    
    try:
        result = MIDIParser.parse(midi_file)
        
        for note in result['notes']:
            assert 'pitch' in note
            assert 'velocity' in note
            assert 'time' in note
            assert 'offset' in note
            assert 'duration' in note
            
            # Verify types
            assert isinstance(note['pitch'], int)
            assert isinstance(note['velocity'], int)
            assert isinstance(note['duration'], int)
            
    finally:
        os.unlink(midi_file)
