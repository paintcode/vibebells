'use client';

import React, { useState, useEffect, useCallback } from 'react';
import './ArrangementDisplay.css';
import { isElectron, onMenuExportCSV } from '../lib/electron';
import SimulationPlayer from './SimulationPlayer';

export default function ArrangementDisplay({ arrangements, expansionInfo, uploadedFilename, players }) {
  const [selectedArrangement, setSelectedArrangement] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [showSimulation, setShowSimulation] = useState(false);

  useEffect(() => {
    if (selectedArrangement >= arrangements.length) {
      setSelectedArrangement(0);
    }
  }, [arrangements.length, selectedArrangement]);

  if (!arrangements || arrangements.length === 0) {
    return <p>No arrangements generated</p>;
  }

  const current = arrangements[selectedArrangement] ?? arrangements[0];
  const scoreBreakdown = current?.quality_breakdown;

  const getScoreColor = (score) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  const handleExportCSV = useCallback(async () => {
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
          swaps: current.swaps || {}
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
      if (objectUrl) {
        setTimeout(() => window.URL.revokeObjectURL(objectUrl), 100);
      }
    }
  }, [current, uploadedFilename, players]);

  // Register menu event listener for Electron
  useEffect(() => {
    if (isElectron()) {
      const cleanup = onMenuExportCSV(handleExportCSV);
      return cleanup;
    }
  }, [handleExportCSV]);

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

      <div className="arrangement-info">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
          <div style={{ flex: '0 1 60%', maxWidth: '60%', minWidth: 0 }}>
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
            {scoreBreakdown && (
              <div className="score-details">
                <h4>Score details</h4>
                <div className="score-details-grid">
                  <div className="score-details-row">
                    <span>Playability</span>
                    <span>{scoreBreakdown.components?.playability?.earned ?? 0}/{scoreBreakdown.components?.playability?.max ?? 50}</span>
                  </div>
                  <div className="score-details-row">
                    <span>Bell fairness</span>
                    <span>{scoreBreakdown.components?.bell_fairness?.earned ?? 0}/{scoreBreakdown.components?.bell_fairness?.max ?? 30}</span>
                  </div>
                  <div className="score-details-row">
                    <span>Fatigue fairness</span>
                    <span>{scoreBreakdown.components?.fatigue_fairness?.earned ?? 0}/{scoreBreakdown.components?.fatigue_fairness?.max ?? 20}</span>
                  </div>
                </div>
                {scoreBreakdown.hard_fail ? (
                  <div className="score-hard-fail">
                    <strong>Hard fail:</strong> {scoreBreakdown.hard_fail_reasons?.join(', ') || 'Failed constraints'}
                  </div>
                ) : (
                  <div className="score-penalties">
                    <span>Pressure events: {scoreBreakdown.penalties?.hand_load_pressure_events ?? 0}</span>
                    <span>Over-swap players: {(scoreBreakdown.penalties?.players_over_five_swaps || []).join(', ') || 'None'}</span>
                    <span>Bell spread: {scoreBreakdown.penalties?.bell_fairness_spread ?? 0}</span>
                  </div>
                )}
              </div>
            )}
          </div>
          {current && current.assignments && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end', marginLeft: 'auto' }}>
              <button
                className="export-btn"
                onClick={() => setShowSimulation(s => !s)}
                disabled={!current.simulation}
                title={current.simulation ? 'Open practice simulation' : 'Simulation data not available'}
              >
                {showSimulation ? '⏹ Close Simulation' : '▶ Simulate'}
              </button>
              <button 
                className="export-btn" 
                onClick={handleExportCSV}
                disabled={exporting}
                title="Export arrangement as CSV spreadsheet"
              >
                {exporting ? 'Exporting...' : 'Export CSV'}
              </button>
            </div>
          )}
        </div>
      </div>

      {current.validation && (() => {
        // Check simulation data for impossible swaps (gap_ms < impossible_swap_gap_ms = physically unperformable)
        const impossibleSwapGapMs = current.simulation?.impossible_swap_gap_ms ?? 100;
        const invalidSimPlayers = current.simulation?.players?.filter(p =>
          p.events.some(e => e.type === 'put_down' && e.gap_ms < impossibleSwapGapMs)
        ).map(p => p.name) ?? [];
        const simInvalid = invalidSimPlayers.length > 0;
        const isValid = current.validation.valid && !simInvalid;
        return (
          <div className={`validation-status ${isValid ? 'valid' : 'invalid'}`}>
            {isValid ? (
              <span>✓ Valid arrangement</span>
            ) : (
              <>
                {!current.validation.valid && (
                  <span>⚠ Issues found: {current.validation.issues.join(', ')}</span>
                )}
                {simInvalid && (
                  <span>⛔ Impossible swaps: {invalidSimPlayers.join(', ')} cannot perform required bell changes in time</span>
                )}
              </>
            )}
            {current.validation.warnings.length > 0 && (
              <div className="warnings">
                {current.validation.warnings.map((warning, idx) => (
                  <p key={idx}>{warning}</p>
                ))}
              </div>
            )}
          </div>
        );
      })()}

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

      {showSimulation && !current.simulation && (
        <div className="simulation-unavailable">
          <span className="simulation-unavailable-icon">ℹ</span>
          <span>Simulation is not available for this arrangement.</span>
          <button type="button" className="simulation-unavailable-close" onClick={() => setShowSimulation(false)} aria-label="Dismiss">✕</button>
        </div>
      )}
      {showSimulation && current.simulation && (
        <SimulationPlayer
          simulationData={current.simulation}
          onClose={() => setShowSimulation(false)}
        />
      )}

      <div className="arrangement-content">
        {current.assignments && Object.entries(current.assignments).map(([playerName, playerData]) => {
          const bells = playerData.bells || [];
          const leftHand = playerData.left_hand || [];
          const rightHand = playerData.right_hand || [];
          const swapCount = current.swaps ? current.swaps[playerName] : null;
          
          return (
            <div key={playerName} className="player-assignment">
              <h3>{playerName}</h3>
              <div className="player-stats">
                <div className="bells-count">{bells.length} bells</div>
                {swapCount !== null && swapCount !== undefined && (
                  <div className="swaps-count">{swapCount} swaps</div>
                )}
              </div>
              
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

