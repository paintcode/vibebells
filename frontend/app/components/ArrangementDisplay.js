'use client';

import React, { useState, useEffect, useCallback } from 'react';
import './ArrangementDisplay.css';
import { isElectron, saveFileDialog, onMenuExportCSV } from '../lib/electron';

export default function ArrangementDisplay({ arrangements, expansionInfo, uploadedFilename, players }) {
  const [selectedArrangement, setSelectedArrangement] = useState(0);
  const [exporting, setExporting] = useState(false);

  if (!arrangements || arrangements.length === 0) {
    return <p>No arrangements generated</p>;
  }

  const current = arrangements[selectedArrangement];

  const getScoreColor = (score) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  const handleExportCSV = async () => {
    setExporting(true);
    let objectUrl = null;
    try {
      const response = await fetch('http://localhost:5000/api/export-csv', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          arrangement: current.assignments,
          players: players || [],
          filename: uploadedFilename || 'arrangement',
          strategy: current.strategy || current.description || 'unknown',
          swaps: current.swaps || {}  // Pass calculated swap counts
        })
      });

      if (!response.ok) {
        let errorMessage = `Export failed: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (e) {
          // If response isn't JSON, use status text
        }
        throw new Error(errorMessage);
      }

      // Generate filename client-side
      const baseFilename = uploadedFilename ? uploadedFilename.replace(/\.[^/.]+$/, '') : 'arrangement';
      const strategy = (current.strategy || current.description || 'unknown').replace(/[^a-z0-9]/gi, '_').toLowerCase();
      const filename = `${baseFilename}_${strategy}.csv`;

      // Download the CSV file
      const blob = await response.blob();
      objectUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      alert('Failed to export arrangement: ' + error.message);
    } finally {
      setExporting(false);
      // Clean up object URL
      if (objectUrl) {
        window.URL.revokeObjectURL(objectUrl);
      }
    }
  };

  // Commented out conflicting client-side export logic that was previously registered with Electron menu
  // const handleExportCSV = useCallback(async () => {
  //   try {
  //     const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
  //     const defaultFilename = `arrangement_${timestamp}.csv`;
      
  //     let filepath = null;
  //     if (isElectron()) {
  //       // Use native save dialog in Electron
  //       filepath = await saveFileDialog(defaultFilename);
  //       if (!filepath) return; // User cancelled
  //     }

  //     // Generate CSV content
  //     const csvContent = generateCSV(current, uploadedFilename, players);

  //     if (isElectron() && filepath) {
  //       // In Electron, write to the selected file
  //       // For now, we'll use the browser download method
  //       // TODO: Implement native file write using Electron IPC
  //       downloadCSV(csvContent, filepath.split(/[\\/]/).pop());
  //     } else {
  //       // Browser download
  //       downloadCSV(csvContent, defaultFilename);
  //     }
  //   } catch (error) {
  //     console.error('Export failed:', error);
  //     alert('Failed to export CSV: ' + error.message);
  //   }
  // }, [current, uploadedFilename, players, selectedArrangement]);

  // Register menu event listener for Electron
  useEffect(() => {
    if (isElectron()) {
      const cleanup = onMenuExportCSV(handleExportCSV);
      // Cleanup listener on unmount
      return cleanup;
    }
  }, [handleExportCSV]);

  // Commented out client-side CSV generation logic that conflicts with server-side export endpoint
  // const generateCSV = (arrangement, filename, playersList) => {
  //   let csv = 'Metadata\n';
  //   csv += `Uploaded File,${escapeCSVField(filename || 'unknown')}\n`;
  //   csv += `Strategy,${escapeCSVField(arrangement.strategy)}\n`;
  //   csv += `Generated,${new Date().toISOString()}\n`;
  //   csv += '\n';
    
  //   csv += 'Players\n';
  //   csv += 'Player,Experience,Left Hand,Right Hand,Bell Swaps\n';
    
  //   arrangement.players.forEach(player => {
  //     const leftHand = player.left_hand ? player.left_hand.join(' ') : '';
  //     const rightHand = player.right_hand ? player.right_hand.join(' ') : '';
  //     const swaps = player.swaps !== undefined ? player.swaps : 0;
  //     csv += `${escapeCSVField(player.name)},${escapeCSVField(player.experience)},${escapeCSVField(leftHand)},${escapeCSVField(rightHand)},${swaps}\n`;
  //   });
    
  //   csv += '\n';
  //   csv += 'All Bells (sorted by pitch)\n';
    
  //   const allBells = new Set();
  //   arrangement.players.forEach(player => {
  //     if (player.left_hand) player.left_hand.forEach(bell => allBells.add(bell));
  //     if (player.right_hand) player.right_hand.forEach(bell => allBells.add(bell));
  //   });
    
  //   const sortedBells = Array.from(allBells).sort((a, b) => {
  //     return compareBellPitch(a, b);
  //   });
    
  //   sortedBells.forEach(bell => {
  //     csv += bell + '\n';
  //   });
    
  //   return csv;
  // };

  // Commented out function used for sorting bells by pitch in client-side CSV generation, which is no longer needed with server-side export
  // const compareBellPitch = (a, b) => {
  //   // Simple pitch comparison (note + octave)
  //   const noteOrder = { 'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11 };
    
  //   const parseNote = (bell) => {
  //     const match = bell.match(/([A-G][#b]?)(\d+)/);
  //     if (!match) return { note: 0, octave: 4 };
  //     let note = noteOrder[match[1][0]] || 0;
  //     if (match[1].includes('#')) note += 0.5;
  //     if (match[1].includes('b')) note -= 0.5;
  //     return { note, octave: parseInt(match[2]) };
  //   };
    
  //   const noteA = parseNote(a);
  //   const noteB = parseNote(b);
    
  //   if (noteA.octave !== noteB.octave) {
  //     return noteA.octave - noteB.octave;
  //   }
  //   return noteA.note - noteB.note;
  // };

  // Commented out client-side CSV download logic that conflicts with server-side export endpoint
  // const downloadCSV = (content, filename) => {
  //   const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  //   const link = document.createElement('a');
  //   const url = URL.createObjectURL(blob);
  //   link.setAttribute('href', url);
  //   link.setAttribute('download', filename);
  //   link.style.visibility = 'hidden';
  //   document.body.appendChild(link);
  //   link.click();
  //   document.body.removeChild(link);
  //   URL.revokeObjectURL(url);
  // };

  return (
    <div className="arrangement-display">
      {expansionInfo && expansionInfo.expanded && (
        <div className="expansion-notification">
          <div className="expansion-icon">⚠</div>
          <div className="expansion-content">
            <h4>Players Expanded</h4>
            <p>{expansionInfo.message}</p>
            <details className="expansion-details">
              <summary>Details</summary>
              <ul>
                <li><strong>Original players:</strong> {expansionInfo.original_player_count}</li>
                <li><strong>Final players:</strong> {expansionInfo.final_player_count}</li>
                <li><strong>Virtual players added:</strong> {expansionInfo.final_player_count - expansionInfo.original_player_count}</li>
                <li><strong>Minimum required:</strong> {expansionInfo.minimum_required}</li>
              </ul>
            </details>
          </div>
        </div>
      )}

      <div className="arrangement-info">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <p>
              <strong>Strategy:</strong> {current.description || current.strategy}
            </p>
            <div className="quality-score">
              <span className="score-label">Quality Score:</span>
              <div className="score-bar">
                <div 
                  className="score-fill" 
                  style={{ 
                    width: `${current.quality_score}%`,
                    backgroundColor: getScoreColor(current.quality_score)
                  }}
                />
              </div>
              <span className="score-value">{Math.round(current.quality_score)}/100</span>
            </div>
          </div>
          {current && current.assignments && (
            <button 
              className="export-btn" 
              onClick={handleExportCSV}
              disabled={exporting}
              title="Export arrangement as CSV spreadsheet"
            >
              {exporting ? 'Exporting...' : 'Export CSV'}
            </button>
          )}
        </div>
      </div>

      <div className="arrangement-selector">
        {arrangements.map((arr, index) => (
          <button
            key={index}
            className={`arrangement-tab ${selectedArrangement === index ? 'active' : ''}`}
            onClick={() => setSelectedArrangement(index)}
            title={arr.description}
          >
            <div>Arrangement {index + 1}</div>
            <small>{Math.round(arr.quality_score)}</small>
          </button>
        ))}
      </div>

      {current.validation && (
        <div className={`validation-status ${current.validation.valid ? 'valid' : 'invalid'}`}>
          {current.validation.valid ? (
            <span>✓ Valid arrangement</span>
          ) : (
            <span>⚠ Issues found: {current.validation.issues.join(', ')}</span>
          )}
          {current.validation.warnings.length > 0 && (
            <div className="warnings">
              {current.validation.warnings.map((warning, idx) => (
                <p key={idx}>{warning}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {current.sustainability && current.sustainability.recommendations.length > 0 && (
        <div className="sustainability-recommendations">
          <h4>Sustainability Recommendations:</h4>
          <ul>
            {current.sustainability.recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="arrangement-content">
        {current.assignments && Object.entries(current.assignments).map(([playerName, playerData]) => {
          const bells = playerData.bells || [];
          const leftHand = playerData.left_hand || [];
          const rightHand = playerData.right_hand || [];
          
          return (
            <div key={playerName} className="player-assignment">
              <h3>{playerName}</h3>
              <div className="bells-count">{bells.length} bells</div>
              
              {/* Overall bells list */}
              <div className="bells-list">
                {bells.length > 0 ? (
                  bells.map((bell, idx) => (
                    <span key={idx} className="bell-badge">{bell}</span>
                  ))
                ) : (
                  <span className="no-bells">No bells assigned</span>
                )}
              </div>
              
              {/* Hand breakdown */}
              {bells.length > 0 && (
                <div className="hand-assignment">
                  <div className="hand-column">
                    <h4>Left Hand</h4>
                    {leftHand.length > 0 ? (
                      <div className="hand-bells">
                        {leftHand.map((bell, idx) => (
                          <span key={idx} className="bell-badge left">{bell}</span>
                        ))}
                      </div>
                    ) : (
                      <span className="no-hand-bells">—</span>
                    )}
                  </div>
                  <div className="hand-column">
                    <h4>Right Hand</h4>
                    {rightHand.length > 0 ? (
                      <div className="hand-bells">
                        {rightHand.map((bell, idx) => (
                          <span key={idx} className="bell-badge right">{bell}</span>
                        ))}
                      </div>
                    ) : (
                      <span className="no-hand-bells">—</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

