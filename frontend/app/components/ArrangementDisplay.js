'use client';

import React, { useState } from 'react';
import './ArrangementDisplay.css';

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

      // Get the filename from response
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'arrangement.csv';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) filename = match[1];
      }

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

