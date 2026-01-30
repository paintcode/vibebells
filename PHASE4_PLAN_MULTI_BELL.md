# Phase 4: Multi-Bell Assignment System Plan

## Problem Statement
Current system limits players to 2 bells max. New requirements allow players to ring multiple bells with constraints based on hand coordination and timing.

## New Requirements

### Hand Coordination Rules
1. **Physical Limit**: Each player has 2 hands, so cannot ring more than 2 notes simultaneously
2. **Initial Distribution**: Each player should start with 1 bell in each hand
3. **Extra Bells**: Unassigned bells after initial 2-bell distribution go to experienced players
4. **Same-Hand Timing**: Two bells played with the same hand must:
   - Never ring at the same time (overlap check)
   - Have at least [configurable threshold] beats gap between note offsets
5. **Hand Consistency**: Prefer to always ring a bell with the same hand

### Configuration

```python
# config.py additions
MAX_BELLS_PER_PLAYER = 8  # Practical limit for handbell ringing
HAND_GAP_THRESHOLD_BEATS = 1.0  # Minimum beats between same-hand notes (configurable)
```

## Algorithm Changes

### Phase 1: Initial Assignment (2 bells per player)
- No changes to current logic
- Each player gets 1-2 bells initially
- Bells are tracked but not assigned to specific hands yet

### Phase 2: Extra Bell Assignment
After all players have up to 2 bells:
1. Count remaining unassigned bells
2. If remaining > 0:
   - Sort players by experience (index order = experience level)
   - Assign extra bells in round-robin to most experienced players
   - Each bell gets a hand assignment (see below)

### Phase 3: Hand Assignment Strategy

For each player with bells, assign to hands:

**Initial Strategy (for 1-2 bells):**
- 1 bell: Assign to left hand (primary)
- 2 bells: One per hand (left first, then right)

**For extra bells (3+ total):**
- Bells alternate between hands: left, right, left, right...
- But respect timing constraints:
  - If a left-hand bell and another left-hand bell overlap or have <threshold gap
  - Try to move the newer bell to right hand if possible
  - If not possible, generate a warning about hand transfer

**Hand Assignment Structure:**
```python
player_assignments = {
  'Player 1': {
    'bells': ['C4', 'D4', 'E4', 'G4'],
    'left_hand': ['C4', 'E4'],           # Indices 0, 2
    'right_hand': ['D4', 'G4'],          # Indices 1, 3
    'hand_transfers': [                  # If necessary
      {'bell': 'E4', 'beat': 12, 'from': 'right', 'to': 'left'}
    ]
  }
}
```

### Phase 4: Hand Conflict Resolution

For each player, validate hand assignments:

1. **Simultaneity Check**: No two notes ring at exactly the same time
   ```python
   for note1, note2 in combinations(player_notes):
     if note1.time < note2.time + note2.duration and 
        note2.time < note1.time + note1.duration:
       # Conflict: overlapping notes
   ```

2. **Gap Check (same hand)**: Sufficient time between same-hand notes
   ```python
   for hand_notes in [left_hand_notes, right_hand_notes]:
     for note1, note2 in sorted(hand_notes, key=lambda n: n.time):
       gap = note2.time - (note1.time + note1.duration)
       if gap < threshold_beats * ticks_per_beat:
         # Conflict: insufficient gap
   ```

3. **Recovery Strategies** (in order):
   - Try to swap bells between hands within same player
   - Try to move problematic bell to different player
   - If all else fails, mark as "requires hand transfer" with warning

## Data Structure Changes

### Music Parser Output (no change needed)
```python
{
  'notes': [
    {
      'pitch': 60,              # MIDI pitch
      'velocity': 100,
      'time': 0,                # Absolute ticks from start
      'offset': 0,              # Same as time
      'duration': 480,          # In ticks
      'note_name': 'C4'
    },
    ...
  ],
  'tempo': 120,                 # BPM
  'ticks_per_beat': 480
}
```

### Arrangement Output (Multi-Bell Format)
```python
{
  'assignments': {
    'Player 1': {
      'bells': ['C4', 'D4', 'E4'],
      'left_hand': ['C4', 'E4'],
      'right_hand': ['D4'],
      'notes': [
        {'bell': 'C4', 'pitch': 60, 'time': 0, 'duration': 480},
        {'bell': 'D4', 'pitch': 62, 'time': 100, 'duration': 480},
        {'bell': 'E4', 'pitch': 64, 'time': 250, 'duration': 400}
      ]
    },
    'Player 2': {
      'bells': ['G4'],
      'left_hand': ['G4'],
      'right_hand': [],
      'notes': [...]
    }
  },
  'hand_transfers': [
    {
      'player': 'Player 1',
      'bell': 'E4',
      'beat': 12,
      'reason': 'Insufficient gap for same-hand timing'
    }
  ],
  'quality_score': 82,
  'hand_utilization': {
    'Player 1': {'left': 0.8, 'right': 0.6},
    'Player 2': {'left': 1.0, 'right': 0.0}
  }
}
```

## Implementation Steps

### Step 1: Configuration Updates
**File**: `backend/app/config.py`
```python
MAX_BELLS_PER_PLAYER = 8
HAND_GAP_THRESHOLD_BEATS = 1.0  # Configurable via env var
```

### Step 2: Bell Assignment Rewrite
**File**: `backend/app/services/bell_assignment.py`

Changes:
- Remove hardcoded `2` bells per player
- For each strategy, add logic to:
  1. First pass: Assign 2 bells to each player (existing logic)
  2. Second pass: Assign remaining bells to experienced players
  3. Third pass: Assign bells to specific hands

### Step 3: Hand Conflict Detection
**File**: `backend/app/services/conflict_resolver.py`

Add new methods:
```python
def validate_hand_constraints(assignments, music_data):
  """Check all hand assignment constraints"""
  conflicts = []
  for player, player_data in assignments.items():
    conflicts.extend(_check_hand_simultaneity(player_data, music_data))
    conflicts.extend(_check_hand_gap(player_data, music_data))
  return conflicts

def _check_hand_simultaneity(player_data, music_data):
  """Ensure no two notes on same hand ring simultaneously"""
  
def _check_hand_gap(player_data, music_data):
  """Ensure sufficient gap between same-hand notes"""
```

### Step 4: Validator Updates
**File**: `backend/app/services/arrangement_validator.py`

Updates:
- Add hand utilization metrics to quality score
- Add sustainability checks for hand constraints
- Penalty if players have unbalanced hands (e.g., 0 in one hand)

### Step 5: Generator Integration
**File**: `backend/app/services/arrangement_generator.py`

Updates:
- Pass `MAX_BELLS_PER_PLAYER` and `HAND_GAP_THRESHOLD_BEATS` to strategies
- Collect hand assignments during generation
- Run hand conflict validation before returning

### Step 6: Documentation
**File**: `bell-assignment-strategy.md`

Add sections:
- Hand assignment rules
- Multi-bell arrangement examples
- Hand transfer scenarios
- Configurable parameters

### Step 7: Frontend Updates
**File**: `frontend/src/components/ArrangementDisplay.js`

Changes:
- Display left/right hand breakdown per player
- Show bell count per player
- Highlight hand transfer warnings

## Quality Score Updates

New formula (assuming current 4-component scoring):
```
Quality = (Distribution × 0.25) + (Occupancy × 0.25) + (Utilization × 0.25) + (Melody × 0.25)

Distribution: Spread of total bells across players (std dev)
Occupancy: How many "bell slots" are filled (bells / max_possible)
Utilization: Hand utilization balance (penalty if one hand unused)
Melody: Coverage of melody notes
```

Additional metrics:
- `hand_transfer_penalty`: -5 points per required hand transfer
- `hand_balance_penalty`: -3 points if a player has 0 bells in one hand (and has >1 bell total)



## Testing Strategy

### Unit Tests
- `test_hand_simultaneity_detection()` - Overlapping notes caught
- `test_hand_gap_validation()` - Gap threshold enforced
- `test_extra_bell_assignment()` - Experienced players get extras first
- `test_hand_balance()` - Each hand gets bells fairly

### Integration Tests
- 3 players, 15 notes (5 per player average)
- 5 players, 8 notes (sparse distribution)
- 2 players, 20 notes (high per-player count)
- Edge case: more bells than notes

### Regression Tests
- All existing Phase 3 tests updated to expect new format
- Quality scores remain 0-100
- No test data changed, only assertion expectations

## Success Criteria

✅ Players can have >2 bells
✅ No two notes ever ring simultaneously in same hand
✅ Gap threshold configurable and enforced
✅ Experienced players get extra bells first
✅ Quality scores remain valid (0-100)
✅ Frontend clearly shows hand assignments
✅ All tests updated for new format
✅ No regressions in arrangement generation logic

## Open Questions

1. **Hand Transfer UI**: How should hand transfers be indicated to users?
   - Simple warning text?
   - Graphical indicator (arrow)?
   - Play/pause guidance?

2. **Max Bells Limit**: Should we enforce an absolute max (e.g., 8 bells)?
   - Current thinking: Yes, 8 is practical limit for handbell ringing

3. **Experienced Player Ranking**: How to determine experience?
   - Current: Order in player list (first = most experienced)
   - Alternative: Explicit experience level parameter

4. **Gap Threshold Default**: Is 1 beat reasonable?
   - Depends on tempo (faster songs need more physical time)
   - Consider tempo-aware dynamic threshold?

## Timeline

Estimated complexity: High (affects core algorithm)
Suggested approach: Implement incrementally, test thoroughly after each step

1. Config updates (15 min)
2. Bell assignment rewrite (2 hours)
3. Hand conflict detection (1 hour)
4. Validator updates (1 hour)
5. Generator integration (30 min)
6. Documentation (45 min)
7. Frontend updates (1 hour)
8. Testing (1.5 hours)
