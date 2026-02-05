'use client';

import React from 'react';
import './PlayerConfig.css';

export default function PlayerConfig({ players, onChange }) {
  const handlePlayerChange = (id, field, value) => {
    const updated = players.map(p =>
      p.id === id ? { ...p, [field]: value } : p
    );
    onChange(updated);
  };

  const addPlayer = () => {
    const newPlayer = {
      id: Math.max(...players.map(p => p.id), 0) + 1,
      name: `Player ${players.length + 1}`,
      experience: 'beginner',
      bells: []
    };
    onChange([...players, newPlayer]);
  };

  const removePlayer = (id) => {
    onChange(players.filter(p => p.id !== id));
  };

  return (
    <div className="player-config">
      <div className="players-list">
        {players.map(player => (
          <div key={player.id} className="player-item">
            <input
              type="text"
              value={player.name}
              onChange={(e) => handlePlayerChange(player.id, 'name', e.target.value)}
              placeholder="Player name"
              className="player-name-input"
            />
            <select
              value={player.experience}
              onChange={(e) => handlePlayerChange(player.id, 'experience', e.target.value)}
              className="player-experience-select"
            >
              <option value="experienced">Experienced</option>
              <option value="intermediate">Intermediate</option>
              <option value="beginner">Beginner</option>
            </select>
            {players.length > 1 && (
              <button
                onClick={() => removePlayer(player.id)}
                className="remove-btn"
              >
                Remove
              </button>
            )}
          </div>
        ))}
      </div>
      <button onClick={addPlayer} className="add-player-btn">
        + Add Player
      </button>
    </div>
  );
}
