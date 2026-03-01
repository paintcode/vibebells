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

const SAMPLE_BREAKDOWN_NO_FAIL = {
  hard_fail: false,
  hard_fail_reasons: [],
  weights: { playability: 50, bell_fairness: 30, fatigue_fairness: 20 },
  components: {
    playability: { earned: 45, max: 50 },
    bell_fairness: { earned: 28, max: 30 },
    fatigue_fairness: { earned: 18, max: 20 },
  },
  penalties: {
    hand_load_pressure_events: 2,
    players_over_five_swaps: ['Player 2'],
    bell_fairness_spread: 1,
  },
  final_score: 91,
};

const SAMPLE_BREAKDOWN_HARD_FAIL = {
  hard_fail: true,
  hard_fail_reasons: ['Dropped notes: 1', 'Impossible swaps: 2'],
  weights: { playability: 50, bell_fairness: 30, fatigue_fairness: 20 },
  components: {
    playability: { earned: 0, max: 50 },
    bell_fairness: { earned: 0, max: 30 },
    fatigue_fairness: { earned: 0, max: 20 },
  },
  penalties: {},
  final_score: 0,
};

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

describe('ArrangementDisplay – score breakdown panel', () => {
  it('renders score details panel when quality_breakdown is present', () => {
    const arrangements = [makeArrangement({ quality_breakdown: SAMPLE_BREAKDOWN_NO_FAIL })];
    render(<ArrangementDisplay arrangements={arrangements} players={[]} />);
    expect(screen.getByTestId('score-details')).toBeInTheDocument();
  });

  it('does not render score details panel when quality_breakdown is absent', () => {
    const arrangements = [makeArrangement()];
    render(<ArrangementDisplay arrangements={arrangements} players={[]} />);
    expect(screen.queryByTestId('score-details')).not.toBeInTheDocument();
  });

  it('shows component earned/max values for playability, bell fairness and fatigue fairness', () => {
    const arrangements = [makeArrangement({ quality_breakdown: SAMPLE_BREAKDOWN_NO_FAIL })];
    render(<ArrangementDisplay arrangements={arrangements} players={[]} />);

    expect(screen.getByTestId('score-details-playability-value')).toHaveTextContent('45/50');
    expect(screen.getByTestId('score-details-bell-fairness-value')).toHaveTextContent('28/30');
    expect(screen.getByTestId('score-details-fatigue-fairness-value')).toHaveTextContent('18/20');
  });

  it('shows the penalties section (not hard-fail) when hard_fail is false', () => {
    const arrangements = [makeArrangement({ quality_breakdown: SAMPLE_BREAKDOWN_NO_FAIL })];
    render(<ArrangementDisplay arrangements={arrangements} players={[]} />);

    expect(screen.getByTestId('score-penalties')).toBeInTheDocument();
    expect(screen.queryByTestId('score-hard-fail')).not.toBeInTheDocument();

    expect(screen.getByTestId('score-penalties-pressure-events')).toHaveTextContent('Pressure events: 2');
    expect(screen.getByTestId('score-penalties-over-swap-players')).toHaveTextContent('Player 2');
    expect(screen.getByTestId('score-penalties-bell-spread')).toHaveTextContent('Bell spread: 1');
  });

  it('shows the hard-fail section (not penalties) when hard_fail is true', () => {
    const arrangements = [makeArrangement({ quality_score: 0, quality_breakdown: SAMPLE_BREAKDOWN_HARD_FAIL })];
    render(<ArrangementDisplay arrangements={arrangements} players={[]} />);

    expect(screen.getByTestId('score-hard-fail')).toBeInTheDocument();
    expect(screen.queryByTestId('score-penalties')).not.toBeInTheDocument();

    expect(screen.getByTestId('score-hard-fail-reasons')).toHaveTextContent('Dropped notes: 1');
    expect(screen.getByTestId('score-hard-fail-reasons')).toHaveTextContent('Impossible swaps: 2');
  });

  it('resets to first arrangement when arrangements list shrinks', () => {
    const { rerender } = render(
      <ArrangementDisplay
        arrangements={[
          makeArrangement({ description: 'First' }),
          makeArrangement({ description: 'Second' }),
          makeArrangement({ description: 'Third' }),
        ]}
        players={[]}
      />
    );

    // Select the third arrangement
    const tabs = screen.getAllByRole('button', { name: /arrangement/i });
    fireEvent.click(tabs[2]);
    expect(screen.getByText('Third')).toBeInTheDocument();

    // Re-render with only one arrangement (simulating regeneration)
    rerender(
      <ArrangementDisplay
        arrangements={[makeArrangement({ description: 'Only' })]}
        players={[]}
      />
    );

    // Should fall back to the first (and only) arrangement without crashing
    expect(screen.getByText('Only')).toBeInTheDocument();
  });
});
