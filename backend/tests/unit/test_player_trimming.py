"""Unit tests for ArrangementGenerator._trim_players."""

from app.services.arrangement_generator import ArrangementGenerator


def _make_player(name, experience='intermediate', virtual=False):
    p = {'name': name, 'experience': experience}
    if virtual:
        p['virtual'] = True
    return p


def _make_assignment(player_bells):
    """Build an assignment dict from {name: [bells]} mapping."""
    result = {}
    for name, bells in player_bells.items():
        left = bells[::2]
        right = bells[1::2]
        result[name] = {'bells': list(bells), 'left_hand': left, 'right_hand': right}
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_trim_removes_players_with_zero_bells():
    """Players with 0 bells should be removed from the assignment."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Player 2': [],
    })
    original_players = [_make_player('Player 1'), _make_player('Player 2')]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert 'Player 1' in trimmed
    assert 'Player 2' not in trimmed
    assert count == 1  # one original player was removed


def test_trim_pairs_two_sparse_players():
    """Two single-bell players should be paired: one gets 2 bells, the other is removed."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Player 2': ['E4'],
        'Player 3': ['F4'],
    })
    original_players = [
        _make_player('Player 1'),
        _make_player('Player 2'),
        _make_player('Player 3'),
    ]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert 'Player 1' in trimmed
    # Exactly one of the two sparse players remains (with 2 bells)
    sparse_remaining = [n for n in ['Player 2', 'Player 3'] if n in trimmed]
    assert len(sparse_remaining) == 1
    keeper = sparse_remaining[0]
    assert len(trimmed[keeper]['bells']) == 2
    assert count == 1  # one original player removed


def test_trim_prefers_original_over_virtual_when_sparse():
    """When one sparse slot is kept, prefer an original player over a virtual one."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Player 2': ['E4'],             # original with 1 bell
        'Virtual Player 10': ['F4'],    # virtual with 1 bell
    })
    original_players = [
        _make_player('Player 1'),
        _make_player('Player 2'),
        _make_player('Virtual Player 10', virtual=True),
    ]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert 'Player 1' in trimmed
    assert 'Player 2' in trimmed        # original sparse player kept
    assert 'Virtual Player 10' not in trimmed  # virtual sparse player removed
    assert count == 0  # no original players were removed (only virtual)


def test_trim_counts_only_original_removed():
    """trimmed_original_count should not count virtual players."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Virtual Player 2': [],  # virtual, 0 bells
        'Player 3': [],          # original, 0 bells
    })
    original_players = [
        _make_player('Player 1'),
        _make_player('Virtual Player 2', virtual=True),
        _make_player('Player 3'),
    ]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert 'Player 1' in trimmed
    assert 'Virtual Player 2' not in trimmed
    assert 'Player 3' not in trimmed
    assert count == 1  # only the original 0-bell player counts


def test_trim_no_changes_when_all_players_adequate():
    """If all players have >= 2 bells, nothing should be trimmed."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Player 2': ['E4', 'F4', 'G4'],
    })
    original_players = [_make_player('Player 1'), _make_player('Player 2')]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert set(trimmed.keys()) == {'Player 1', 'Player 2'}
    assert count == 0


def test_trim_empty_assignment():
    """An empty assignment should return empty with zero trimmed count."""
    trimmed, count = ArrangementGenerator._trim_players({}, [])
    assert trimmed == {}
    assert count == 0


def test_trim_all_zero_bells():
    """If all players have 0 bells, all should be removed."""
    assignment = _make_assignment({
        'Player 1': [],
        'Player 2': [],
    })
    original_players = [_make_player('Player 1'), _make_player('Player 2')]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert trimmed == {}
    assert count == 2


def test_trim_reassigns_bell_from_removed_sparse_player():
    """Bells from removed 1-bell players should be merged into the kept sparse player."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Player 2': ['E4'],
        'Player 3': ['F4'],
    })
    original_players = [
        _make_player('Player 1'),
        _make_player('Player 2'),
        _make_player('Player 3'),
    ]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    # All bells must be preserved — none should be dropped
    original_bells = {b for data in assignment.values() for b in data.get('bells', [])}
    trimmed_bells = {b for data in trimmed.values() for b in data.get('bells', [])}
    assert trimmed_bells == original_bells

    # The kept sparse player should now hold both spare bells
    sparse_remaining = [n for n in ['Player 2', 'Player 3'] if n in trimmed]
    assert len(sparse_remaining) == 1
    keeper = sparse_remaining[0]
    assert len(trimmed[keeper]['bells']) == 2
    assert count == 1  # one original player was removed (not dropped — its bell was merged)


def test_trim_reassigns_virtual_sparse_bell_to_original_keeper():
    """Bell from a removed virtual sparse player should be merged into the original keeper."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Player 2': ['E4'],
        'Virtual Player 10': ['F4'],
    })
    original_players = [
        _make_player('Player 1'),
        _make_player('Player 2'),
        _make_player('Virtual Player 10', virtual=True),
    ]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    # All bells must be preserved
    original_bells = {b for data in assignment.values() for b in data.get('bells', [])}
    trimmed_bells = {b for data in trimmed.values() for b in data.get('bells', [])}
    assert trimmed_bells == original_bells

    # Player 2 (original) is the keeper and should now hold both sparse bells
    assert 'Player 2' in trimmed
    assert 'Virtual Player 10' not in trimmed
    assert len(trimmed['Player 2']['bells']) == 2
    assert count == 0  # no original players were removed


def test_trim_pairs_one_pair_from_three_sparse_players():
    """Three single-bell players: one pair merges, leaving 1 player with 2 bells,
    1 removed, and 1 unpaired player still with 1 bell."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Player 2': ['E4'],
        'Player 3': ['F4'],
        'Player 4': ['G4'],
    })
    original_players = [
        _make_player('Player 1'),
        _make_player('Player 2'),
        _make_player('Player 3'),
        _make_player('Player 4'),
    ]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert 'Player 1' in trimmed

    # All bells preserved
    original_bells = {b for data in assignment.values() for b in data.get('bells', [])}
    trimmed_bells = {b for data in trimmed.values() for b in data.get('bells', [])}
    assert trimmed_bells == original_bells

    # One sparse player has 2 bells (paired), one sparse player has 1 bell (unpaired)
    sparse_names = ['Player 2', 'Player 3', 'Player 4']
    sparse_in_trimmed = [n for n in sparse_names if n in trimmed]
    assert len(sparse_in_trimmed) == 2  # one paired recipient + one unpaired

    bell_counts = sorted(len(trimmed[n]['bells']) for n in sparse_in_trimmed)
    assert bell_counts == [1, 2]  # one unpaired (1 bell), one paired (2 bells)
    assert count == 1  # one original sparse player removed (the donor)


def test_trim_pairs_two_pairs_from_four_sparse_players():
    """Four single-bell players form two pairs: 2 recipients with 2 bells each, 2 donors removed."""
    assignment = _make_assignment({
        'Player 1': ['C4', 'D4'],
        'Player 2': ['E4'],
        'Player 3': ['F4'],
        'Player 4': ['G4'],
        'Player 5': ['A4'],
    })
    original_players = [
        _make_player('Player 1'),
        _make_player('Player 2'),
        _make_player('Player 3'),
        _make_player('Player 4'),
        _make_player('Player 5'),
    ]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert 'Player 1' in trimmed

    # All bells preserved
    original_bells = {b for data in assignment.values() for b in data.get('bells', [])}
    trimmed_bells = {b for data in trimmed.values() for b in data.get('bells', [])}
    assert trimmed_bells == original_bells

    sparse_names = ['Player 2', 'Player 3', 'Player 4', 'Player 5']
    sparse_in_trimmed = [n for n in sparse_names if n in trimmed]
    assert len(sparse_in_trimmed) == 2  # two recipients remain

    for n in sparse_in_trimmed:
        assert len(trimmed[n]['bells']) == 2  # each recipient has exactly 2 bells
    assert count == 2  # two original donors removed


def test_trim_pairs_two_pairs_from_five_sparse_players():
    """Five single-bell players: two pairs formed, one unpaired player keeps 1 bell."""
    bells_map = {
        'Player 1': ['C4', 'D4'],
        'Player 2': ['E4'],
        'Player 3': ['F4'],
        'Player 4': ['G4'],
        'Player 5': ['A4'],
        'Player 6': ['B4'],
    }
    assignment = _make_assignment(bells_map)
    original_players = [_make_player(n) for n in bells_map]

    trimmed, count = ArrangementGenerator._trim_players(assignment, original_players)

    assert 'Player 1' in trimmed

    # All bells preserved
    original_bells = {b for data in assignment.values() for b in data.get('bells', [])}
    trimmed_bells = {b for data in trimmed.values() for b in data.get('bells', [])}
    assert trimmed_bells == original_bells

    sparse_names = ['Player 2', 'Player 3', 'Player 4', 'Player 5', 'Player 6']
    sparse_in_trimmed = [n for n in sparse_names if n in trimmed]
    assert len(sparse_in_trimmed) == 3  # two paired recipients + one unpaired

    bell_counts = sorted(len(trimmed[n]['bells']) for n in sparse_in_trimmed)
    assert bell_counts == [1, 2, 2]  # one unpaired, two paired
    assert count == 2  # two original donors removed
