"""
Test file generator for MIDI/MusicXML files
"""

def create_test_midi():
    """Create a simple test MIDI file"""
    import midi
    
    # Create pattern
    pattern = midi.Pattern()
    
    # Create a track
    track = midi.Track()
    pattern.append(track)
    
    # Add some notes (C major scale)
    pitches = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 to C5
    
    for pitch in pitches:
        # Note on
        on = midi.NoteOnEvent(tick=100, velocity=100, pitch=pitch)
        track.append(on)
        
        # Note off
        off = midi.NoteOffEvent(tick=100, pitch=pitch)
        track.append(off)
    
    # End of track
    eot = midi.EndOfTrackEvent(tick=0)
    track.append(eot)
    
    return pattern

if __name__ == '__main__':
    pattern = create_test_midi()
    midi.write_midifile('test_song.mid', pattern)
    print("Created test_song.mid")
