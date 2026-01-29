import React, { useState } from 'react';
import './ArrangementDisplay.css';

function ArrangementDisplay({ arrangements }) {
  const [selectedArrangement, setSelectedArrangement] = useState(0);

  if (!arrangements || arrangements.length === 0) {
    return <p>No arrangements generated</p>;
  }

  const current = arrangements[selectedArrangement];

  const getScoreColor = (score) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  return (
    <div className="arrangement-display">
      <div className="arrangement-info">
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
        {current.assignments && Object.entries(current.assignments).map(([playerName, bells]) => (
          <div key={playerName} className="player-assignment">
            <h3>{playerName}</h3>
            <div className="bells-count">{bells.length}/2 bells</div>
            <div className="bells-list">
              {bells.length > 0 ? (
                bells.map((bell, idx) => (
                  <span key={idx} className="bell-badge">{bell}</span>
                ))
              ) : (
                <span className="no-bells">No bells assigned</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="arrangement-actions">
        <button className="export-btn">Download as PDF</button>
        <button className="export-btn">Download Player Parts</button>
      </div>
    </div>
  );
}

export default ArrangementDisplay;

