import React, { useState } from 'react';
import './ArrangementDisplay.css';

function ArrangementDisplay({ arrangements }) {
  const [selectedArrangement, setSelectedArrangement] = useState(0);

  if (!arrangements || arrangements.length === 0) {
    return <p>No arrangements generated</p>;
  }

  const current = arrangements[selectedArrangement];

  return (
    <div className="arrangement-display">
      <div className="arrangement-selector">
        {arrangements.map((_, index) => (
          <button
            key={index}
            className={`arrangement-tab ${selectedArrangement === index ? 'active' : ''}`}
            onClick={() => setSelectedArrangement(index)}
          >
            Arrangement {index + 1}
          </button>
        ))}
      </div>

      <div className="arrangement-content">
        {current.assignments && Object.entries(current.assignments).map(([playerName, bells]) => (
          <div key={playerName} className="player-assignment">
            <h3>{playerName}</h3>
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
