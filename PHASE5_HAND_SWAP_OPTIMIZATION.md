# Phase 5: Hand Swap Optimization

## Overview
Enhance the `min_transitions` strategy to minimize the number of times a player needs to swap bells between their hands. When assigning extra bells (3rd, 4th, etc.) to a player, prefer bells that have lower swap costs.

## Problem Example

**Scenario**: Player has bells C4 and D4 in left and right hands respectively. Need to assign a 3rd bell.

**Option A: Assign E4**
- Timeline: C4 at beat 1, D4 at beat 2, E4 at beat 3, C4 at beat 4, D4 at beat 5
- Player needs to swap: D4 → E4, then E4 → D4 → C4
- **High swap cost**

**Option B: Assign F4**
- Timeline: C4 at beat 1, D4 at beat 2, C4 at beat 3, D4 at beat 4, F4 at beat 10 (later section)
- Player can hold C4 and D4, then only swap for F4 once
- **Low swap cost**

## Design

### 1. Swap Cost Calculation

For each bell assignment to a player, calculate:

```python
swap_cost = calculate_swap_cost(player_bells, new_bell, note_timing)
```

**Algorithm**:
1. Get all occurrences of each bell in player's collection (time values from parsed notes)
2. For the new bell, identify all its occurrences
3. Simulate hand assignments: index i goes to (i % 2 == 0) ? left : right
4. Walk through timeline and count transitions when same hand needs to switch bells
5. Return total transition count

**Example**:
```
Player has [C4, D4] → left=C4, right=D4

Note timeline with pitches:
- t=0: C4 (left hand holds)
- t=1: D4 (switch to right hand)
- t=2: C4 (switch back to left hand)
- t=3: D4 (switch to right hand)
- t=4: F4 NEW (where to assign?)

If F4 is assigned as 3rd bell (index 2):
- F4 → left hand (index 2 % 2 == 0)
- Current: left=[C4, F4], right=[D4]

Timeline analysis:
- t=0: left (C4) - no swap
- t=1: right (D4) - swap from left to right
- t=2: left (C4) - swap from right to left
- t=3: right (D4) - swap from left to right
- t=4: left (F4 occurs here) - already in left, no swap needed
- Result: 3 swaps

Alternative: Could assign F4 to right hand instead
- Right=[D4, F4], Left=[C4]
- t=0-3: same as above (3 swaps for C4/D4 alternation)
- t=4: right (F4) - already in right, no swap
- Result: still 3 swaps, but different hand dynamics
```

### 2. Enhanced Bell Assignment Strategy

Modify `_assign_min_transitions()` in `bell_assignment.py`:

**Phase 1** (unchanged): Distribute 2 bells per player
- Each player gets 1 left-hand, 1 right-hand bell
- Minimizes initial melody transitions

**Phase 2** (ENHANCED): Assign extra bells with swap cost consideration
- For each extra bell to assign:
  1. Calculate swap cost if assigned to each player
  2. Score each player: `score = swap_cost + transition_cost`
  3. Assign to player with lowest score
  4. Assign to hand with lowest swap impact

**Phase 2 Implementation**:
```python
def _assign_min_transitions_v2(notes, num_players, strategy_name):
    # Phase 1: Assign 2 bells per player (unchanged)
    arrangement = _phase1_minimum_assignment(...)
    
    # Phase 2: Assign extra bells with swap cost optimization
    assigned_pitches = collect_assigned_pitches(arrangement)
    unassigned_bells = [note for note in notes 
                        if note['pitch'] not in assigned_pitches]
    
    # Sort by swap cost (ascending) - prefer low-cost bells first
    bell_swap_costs = []
    for bell_pitch in unassigned_bells:
        cost = calculate_swap_cost(bell_pitch, notes)  # Simple cost based on frequency
        bell_swap_costs.append((bell_pitch, cost))
    
    bell_swap_costs.sort(key=lambda x: x[1])  # Lowest cost first
    
    # Assign each bell
    for bell_pitch, _ in bell_swap_costs:
        best_player = None
        best_score = float('inf')
        
        for player_name in arrangement:
            if len(arrangement[player_name]['bells']) >= MAX_BELLS:
                continue
            
            # Calculate swap cost for this bell in this player
            swap_cost = calculate_swap_cost_for_player(
                arrangement[player_name],
                bell_pitch,
                notes
            )
            
            # Consider melody transitions too
            transition_cost = check_melody_transitions(...)
            
            total_score = swap_cost + transition_cost
            
            if total_score < best_score:
                best_score = total_score
                best_player = player_name
        
        if best_player:
            assign_bell_to_player(arrangement, best_player, bell_pitch, notes)
    
    return arrangement
```

### 3. Swap Cost Calculator Functions

**New file**: `backend/app/services/swap_cost_calculator.py`

```python
class SwapCostCalculator:
    
    @staticmethod
    def calculate_swap_cost(bell_pitch, notes):
        """
        Calculate how frequently a bell is played.
        Lower frequency = lower swap cost.
        
        Returns: Count of occurrences (0 = not in notes, high = frequently played)
        """
        return sum(1 for n in notes if n['pitch'] == bell_pitch)
    
    @staticmethod
    def calculate_swap_cost_for_player(player_assignment, new_bell_pitch, notes):
        """
        Calculate swap cost if new_bell_pitch is added to player.
        
        Args:
            player_assignment: {'bells': [...], 'left_hand': [...], 'right_hand': [...]}
            new_bell_pitch: Integer MIDI pitch of new bell
            notes: All notes from music file with timing info
        
        Returns: Integer representing number of hand swaps needed
        """
        # Get sorted timeline of note occurrences for this player
        player_bells = player_assignment['bells'] + [new_bell_pitch]
        
        # Filter notes to only those played by this player
        player_notes = [n for n in notes if n['pitch'] in player_bells]
        player_notes.sort(key=lambda n: n['time'])  # Sort by time
        
        # Simulate hand assignments using index-based rule
        hand_map = {}  # pitch -> hand ('left' or 'right')
        for idx, pitch in enumerate(player_bells):
            hand_map[pitch] = 'left' if idx % 2 == 0 else 'right'
        
        # Count swaps by tracking which hand is "active"
        swaps = 0
        current_hand = None
        
        for note in player_notes:
            pitch = note['pitch']
            required_hand = hand_map[pitch]
            
            if current_hand is not None and current_hand != required_hand:
                swaps += 1
            
            current_hand = required_hand
        
        return swaps
    
    @staticmethod
    def calculate_temporal_gaps(bell_pitch, notes):
        """
        Calculate average time gap between occurrences of a bell.
        Larger gaps = better candidate for extra bells (less frequent swaps).
        
        Returns: Average gap in ticks (0 if only 1 occurrence)
        """
        bell_notes = [n for n in notes if n['pitch'] == bell_pitch]
        
        if len(bell_notes) <= 1:
            return float('inf')  # Single occurrence - best candidate
        
        times = sorted([n['time'] for n in bell_notes])
        gaps = [times[i+1] - times[i] for i in range(len(times)-1)]
        
        return sum(gaps) / len(gaps) if gaps else 0
    
    @staticmethod
    def score_bell_for_player(player_assignment, new_bell_pitch, notes, weights=None):
        """
        Comprehensive score for assigning a bell to a player.
        Lower score = better assignment.
        
        Weights:
        - swap_cost: how many hand swaps needed
        - frequency: how often the bell is played
        - isolation: how temporally separated from existing bells
        
        Returns: Float score (0-100)
        """
        if weights is None:
            weights = {'swap': 0.5, 'frequency': 0.3, 'isolation': 0.2}
        
        # Component 1: Swap cost
        swap_cost = SwapCostCalculator.calculate_swap_cost_for_player(
            player_assignment, new_bell_pitch, notes
        )
        swap_score = min(swap_cost / 10.0, 1.0)  # Normalize to 0-1
        
        # Component 2: Frequency (prefer rare bells)
        frequency = SwapCostCalculator.calculate_swap_cost(new_bell_pitch, notes)
        max_frequency = len(notes) / 10  # Heuristic
        frequency_score = frequency / max_frequency
        frequency_score = min(frequency_score, 1.0)
        
        # Component 3: Temporal isolation (prefer widely separated notes)
        gap = SwapCostCalculator.calculate_temporal_gaps(new_bell_pitch, notes)
        isolation_score = 0 if gap == float('inf') else min(1.0 / (gap / 1000), 1.0)
        
        # Weighted combination
        total_score = (
            weights['swap'] * swap_score +
            weights['frequency'] * frequency_score +
            weights['isolation'] * isolation_score
        )
        
        return total_score
```

### 4. Integration Points

**File**: `backend/app/services/bell_assignment.py`

Modify `_assign_min_transitions()`:
```python
from app.services.swap_cost_calculator import SwapCostCalculator

def _assign_min_transitions(notes, num_players, strategy_name):
    # ... existing Phase 1 code ...
    
    # Phase 2: Enhanced with swap cost
    for note_pitch in unassigned_bells:
        best_player = None
        best_score = float('inf')
        
        for player_idx, player_name in enumerate(player_names):
            if len(assignment[player_name]['bells']) >= MAX_BELLS_PER_PLAYER:
                continue
            
            # Use SwapCostCalculator
            score = SwapCostCalculator.score_bell_for_player(
                assignment[player_name],
                note_pitch,
                notes,
                weights={
                    'swap': 0.5,      # Heavy weight on swaps
                    'frequency': 0.3,
                    'isolation': 0.2
                }
            )
            
            if score < best_score:
                best_score = score
                best_player = player_name
        
        if best_player:
            _assign_bell_to_player(assignment[best_player], note_pitch, notes)
    
    return assignment
```

### 5. Testing Strategy

**File**: `backend/test_swap_cost.py`

```python
def test_swap_cost_calculation():
    """Test basic swap cost calculation"""
    # Create simple note timeline
    notes = [
        {'pitch': 60, 'time': 0},   # C4
        {'pitch': 62, 'time': 100},  # D4
        {'pitch': 60, 'time': 200},  # C4 - requires swap
        {'pitch': 62, 'time': 300},  # D4 - requires swap
        {'pitch': 64, 'time': 400},  # E4 - new bell
    ]
    
    player = {
        'bells': [60, 62],
        'left_hand': [60],
        'right_hand': [62]
    }
    
    cost = SwapCostCalculator.calculate_swap_cost_for_player(player, 64, notes)
    assert cost == 1, f"Expected 1 swap (E4 appears once after alternation), got {cost}"

def test_temporal_gaps():
    """Test temporal gap calculation"""
    notes = [
        {'pitch': 60, 'time': 0},
        {'pitch': 60, 'time': 100},
        {'pitch': 60, 'time': 500},  # Large gap
    ]
    
    gap = SwapCostCalculator.calculate_temporal_gaps(60, notes)
    assert gap == 200, f"Expected average gap of 200, got {gap}"

def test_swap_cost_vs_sample_music():
    """Integration test with actual sample music"""
    # Load sample music, generate arrangement with min_transitions
    # Verify that extra bells (3rd+) have lower swap costs than alternatives
```

### 6. Quality Score Impact

Update `arrangement_validator.py` to include hand swap metrics:

```python
def calculate_hand_swap_score(arrangement, notes):
    """
    New quality metric: hand swap efficiency.
    Penalizes arrangements with high swap costs.
    
    Returns: 0-25 points (part of 100-point quality score)
    """
    total_swaps = 0
    max_possible_swaps = 0
    
    for player_name, assignment in arrangement.items():
        player_notes = [n for n in notes if n['pitch'] in assignment['bells']]
        
        # Calculate actual swaps
        actual_swaps = SwapCostCalculator.calculate_swap_cost_for_player(
            assignment, 
            assignment['bells'][-1],  # Last bell
            notes
        )
        total_swaps += actual_swaps
        
        # Max possible is if alternating every beat
        max_possible_swaps += len(player_notes) - 1
    
    if max_possible_swaps == 0:
        return 25
    
    efficiency = 1.0 - (total_swaps / max_possible_swaps)
    return max(0, efficiency * 25)
```

Update the 4-component quality score to 5 components:
- Distribution: 20%
- Occupancy: 20%
- Utilization: 20%
- Melody: 20%
- **Hand Swaps: 20%** (NEW)

## Implementation Order

1. Create `swap_cost_calculator.py` with core calculation functions
2. Add unit tests for swap cost calculation
3. Enhance `_assign_min_transitions()` in `bell_assignment.py`
4. Update quality score calculation in `arrangement_validator.py`
5. Update frontend quality metric display (if visible)
6. Run integration tests with sample music
7. Verify all strategies still work correctly
8. Document in README

## Success Criteria

- ✅ Swap cost calculated correctly for various note patterns
- ✅ min_transitions strategy prefers low-swap-cost bells for extras
- ✅ Quality score includes hand swap efficiency metric
- ✅ Integration test shows improved swap efficiency with sample music
- ✅ All existing tests still pass (no regressions)
- ✅ Backend initializes successfully
- ✅ Frontend builds successfully

## Known Limitations

- Doesn't account for fatigue patterns (physical effort of repeated swaps)
- Assumes uniform hand capability (real players may have dominant hands)
- Doesn't predict hand conflicts that can be resolved by reordering index assignments
- Swap cost assumes fixed index-based hand assignment rule

## Future Enhancements

- Dynamic hand assignment: reorder bells to minimize swaps for specific patterns
- Left-handed/right-handed player support
- Hand strength/fatigue modeling
- Predictive hand transfer warnings in UI
