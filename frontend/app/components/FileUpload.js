'use client';

import React from 'react';
import './FileUpload.css';

export default function FileUpload({ onFileUpload }) {
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      const validTypes = ['audio/midi', 'application/vnd.recordare.musicxml', 'application/vnd.recordare.musicxml+xml', 'text/xml'];
      if (validTypes.includes(file.type) || file.name.endsWith('.mid') || file.name.endsWith('.musicxml') || file.name.endsWith('.xml')) {
        onFileUpload(file);
      } else {
        alert('Please upload a MIDI or MusicXML file');
      }
    }
  };

  return (
    <div className="file-upload">
      <input 
        type="file" 
        accept=".mid,.midi,.musicxml,.xml"
        onChange={handleFileChange}
        className="file-input-browser"
        id="file-input"
      />
      <label htmlFor="file-input" className="file-input-label">
        Choose File
      </label>
      <p className="file-help">Supported formats: MIDI (.mid), MusicXML (.musicxml)</p>
    </div>
  );
}
