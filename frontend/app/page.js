'use client';

import React, { useState, useEffect, useRef } from 'react';
import './page.css';
import FileUpload from './components/FileUpload';
import PlayerConfig from './components/PlayerConfig';
import ArrangementDisplay from './components/ArrangementDisplay';
import { isElectron, openFileDialog, onMenuOpenFile, readFile } from './lib/electron';

export default function Home() {
  const [file, setFile] = useState(null);
  const [players, setPlayers] = useState([
    { id: 1, name: 'Player 1', experience: 'experienced', bells: [] },
    { id: 2, name: 'Player 2', experience: 'experienced', bells: [] },
    { id: 3, name: 'Player 3', experience: 'intermediate', bells: [] },
    { id: 4, name: 'Player 4', experience: 'intermediate', bells: [] },
    { id: 5, name: 'Player 5', experience: 'intermediate', bells: [] },
    { id: 6, name: 'Player 6', experience: 'intermediate', bells: [] },
    { id: 7, name: 'Player 7', experience: 'beginner', bells: [] },
    { id: 8, name: 'Player 8', experience: 'beginner', bells: [] }
  ]);
  const [arrangements, setArrangements] = useState(null);
  const [expansionInfo, setExpansionInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const arrangementsRef = useRef(null);

  // Register menu event listener for Electron
  useEffect(() => {
    if (isElectron()) {
      const cleanup = onMenuOpenFile(() => {
        handleElectronFileOpen();
      });
      // Cleanup listener on unmount
      return cleanup;
    }
  }, []);

  // Handle Electron native file dialog
  const handleElectronFileOpen = async () => {
    try {
      const filePath = await openFileDialog();
      if (filePath) {
        // Read file through IPC (secure file access)
        const result = await readFile(filePath);
        
        if (!result.success) {
          throw new Error(result.error || 'Failed to read file');
        }
        
        // Convert array back to Uint8Array and create blob
        const fileName = filePath.split(/[\\/]/).pop();
        const fileExt = fileName.split('.').pop().toLowerCase();
        
        // Determine MIME type based on extension
        let mimeType = 'audio/midi';
        if (fileExt === 'xml' || fileExt === 'musicxml') {
          mimeType = 'application/vnd.recordare.musicxml+xml';
        }
        
        const blob = new Blob([new Uint8Array(result.data)], { type: mimeType });
        const file = new File([blob], fileName, { type: mimeType });
        handleFileUpload(file);
      }
    } catch (error) {
      console.error('Error opening file from Electron dialog:', error);
      setError('Failed to open file: ' + error.message);
    }
  };

  const handleFileUpload = async (uploadedFile) => {
    setFile(uploadedFile);
    setError(null);
  };

  const handlePlayerConfigChange = (updatedPlayers) => {
    setPlayers(updatedPlayers);
    setError(null);
  };

  const generateArrangements = async () => {
    if (!file) {
      setError('Please upload a music file first');
      return;
    }

    if (players.length === 0) {
      setError('Please add at least one player');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('players', JSON.stringify(players));

      const response = await fetch('http://localhost:5000/api/generate-arrangements', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setArrangements(data.arrangements);
        // Extract and store expansion info if present
        if (data.expansion_info) {
          setExpansionInfo(data.expansion_info);
        } else {
          setExpansionInfo(null);
        }
        
        // Scroll to arrangements section after a short delay to allow rendering
        setTimeout(() => {
          arrangementsRef.current?.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
          });
        }, 100);
      } else {
        // Handle specific error codes
        const errorMessage = getErrorMessage(data.code, data.error);
        setError(errorMessage);
      }
    } catch (error) {
      console.error('Error:', error);
      setError('Network error: Unable to reach the server. Make sure the backend is running on http://localhost:5000');
    } finally {
      setLoading(false);
    }
  };

  const getErrorMessage = (code, fallback) => {
    const errorMap = {
      'ERR_NO_FILE': 'No music file provided',
      'ERR_NO_FILE_SELECTED': 'Please select a music file',
      'ERR_INVALID_JSON': 'Invalid player configuration',
      'ERR_NO_PLAYERS': 'No players configured',
      'ERR_TOO_FEW_PLAYERS': 'At least one player is required',
      'ERR_TOO_MANY_PLAYERS': 'Too many players (max 20)',
      'ERR_PLAYER_NO_NAME': 'All players must have names',
      'ERR_FILE_SAVE': 'Failed to save file',
      'ERR_MUSIC_PARSE': `Failed to parse music file: ${fallback}`,
      'ERR_VALIDATION': fallback,
      'ERR_GENERATION_FAILED': 'Failed to generate arrangements',
      'ERR_NOT_FOUND': 'API endpoint not found',
      'ERR_INTERNAL': 'Server error'
    };
    
    return errorMap[code] || fallback || 'An error occurred';
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <img src="/logo192.png" alt="Vibebells" className="header-logo" />
          <div className="header-text">
            <h1>Handbell Arrangement Generator</h1>
            <p>Upload a song and configure your players to generate bell arrangements</p>
          </div>
        </div>
      </header>

      <main className="App-main">
        <div className="container">
          {error && (
            <div className="error-message">
              <span>{error}</span>
              <button className="close-btn" onClick={() => setError(null)}>✕</button>
            </div>
          )}

          <section className="section">
            <h2>1. Upload Music File</h2>
            {isElectron() && (
              <>
                <button 
                  className="electron-file-btn"
                  onClick={handleElectronFileOpen}
                >
                  Choose File
                </button>
                <p className="file-help">Supported formats: MIDI (.mid), MusicXML (.musicxml)</p>
              </>
            )}
            {!isElectron() && <FileUpload onFileUpload={handleFileUpload} />}
            {file && <p className="file-name">Selected: {file.name}</p>}
          </section>

          <section className="section">
            <h2>2. Configure Players</h2>
            <PlayerConfig players={players} onChange={handlePlayerConfigChange} />
          </section>

          <section className="section">
            <button 
              className="generate-btn" 
              onClick={generateArrangements}
              disabled={loading || !file}
            >
              {loading ? 'Generating...' : 'Generate Arrangements'}
            </button>
          </section>

          {arrangements && (
            <section className="section" ref={arrangementsRef}>
              <h2>3. Arrangements</h2>
              <ArrangementDisplay 
                arrangements={arrangements} 
                expansionInfo={expansionInfo}
                uploadedFilename={file?.name}
                players={players}
              />
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
