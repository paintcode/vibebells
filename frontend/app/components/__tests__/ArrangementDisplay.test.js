import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ArrangementDisplay from '../ArrangementDisplay';

// Mock CSS imports
jest.mock('../ArrangementDisplay.css', () => ({}));

// Mock electron utilities (not in Electron context during tests)
jest.mock('../../lib/electron', () => ({
  isElectron: () => false,
  onMenuExportCSV: () => () => {},
}));

// Mock SimulationPlayer to keep tests focused on ArrangementDisplay logic
jest.mock('../SimulationPlayer', () =>
  function MockSimulationPlayer({ onClose }) {
    return (
      <div data-testid="simulation-player">
        <button onClick={onClose}>Close</button>
      </div>
    );
  }
);

/** Minimal valid arrangement factory */
function makeArrangement(overrides = {}) {
  return {
    strategy: 'balanced',
    description: 'Balanced',
    quality_score: 75,
    assignments: { 'Player 1': { bells: ['C4'], left_hand: ['C4'], right_hand: [] } },
    validation: { valid: true, issues: [], warnings: [] },
    swaps: {},
    simulation: null,
    ...overrides,
  };
}

const SIMULATION_DATA = {
  bpm: 120,
  players: [{ name: 'Player 1', events: [] }],
};

describe('ArrangementDisplay – simulation unavailable banner', () => {
  it('shows unavailable banner when simulation is open but arrangement has no simulation data', () => {
    const arrangements = [
      makeArrangement({ simulation: SIMULATION_DATA }),
      makeArrangement({ simulation: null }),
    ];

    render(<ArrangementDisplay arrangements={arrangements} players={[]} />);

    // Open the simulation on arrangement 0 (has simulation data)
    const simulateBtn = screen.getByRole('button', { name: /simulate/i });
    fireEvent.click(simulateBtn);
    expect(screen.getByTestId('simulation-player')).toBeInTheDocument();

    // Switch to arrangement 1 (no simulation data)
    const tabs = screen.getAllByRole('button', { name: /arrangement/i });
    fireEvent.click(tabs[1]);

    // The simulation player should be gone and the unavailable banner should appear
    expect(screen.queryByTestId('simulation-player')).not.toBeInTheDocument();
    expect(
      screen.getByText('Simulation is not available for this arrangement.')
    ).toBeInTheDocument();
  });

  it('hides the banner after the user dismisses it', () => {
    const arrangements = [
      makeArrangement({ simulation: SIMULATION_DATA }),
      makeArrangement({ simulation: null }),
    ];

    render(<ArrangementDisplay arrangements={arrangements} players={[]} />);

    // Open simulation, then switch to arrangement without data
    fireEvent.click(screen.getByRole('button', { name: /simulate/i }));
    const tabs = screen.getAllByRole('button', { name: /arrangement/i });
    fireEvent.click(tabs[1]);

    // Dismiss the banner
    const dismissBtn = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissBtn);

    expect(
      screen.queryByText('Simulation is not available for this arrangement.')
    ).not.toBeInTheDocument();
  });

  it('resumes showing the simulation player when switching back to an arrangement with data', () => {
    const arrangements = [
      makeArrangement({ simulation: SIMULATION_DATA }),
      makeArrangement({ simulation: null }),
    ];

    render(<ArrangementDisplay arrangements={arrangements} players={[]} />);

    const tabs = screen.getAllByRole('button', { name: /arrangement/i });

    // Open simulation on arrangement 0
    fireEvent.click(screen.getByRole('button', { name: /simulate/i }));
    expect(screen.getByTestId('simulation-player')).toBeInTheDocument();

    // Switch to arrangement 1 (no simulation) → banner appears
    fireEvent.click(tabs[1]);
    expect(
      screen.getByText('Simulation is not available for this arrangement.')
    ).toBeInTheDocument();

    // Switch back to arrangement 0 → simulation player resumes
    fireEvent.click(tabs[0]);
    expect(screen.getByTestId('simulation-player')).toBeInTheDocument();
    expect(
      screen.queryByText('Simulation is not available for this arrangement.')
    ).not.toBeInTheDocument();
  });
});
