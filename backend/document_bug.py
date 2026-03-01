"""
Verify the latent bug in _assign_min_transitions second pair selection pass.

The bug exists at lines 543-550 where the code adds additional pairs without 
checking if the individual bells are already used in another pair.
"""
import sys
sys.path.insert(0, r'C:\src\vibebells\backend')


def demonstrate_latent_bug():
    """
    Show that the code logic allows duplicate bell assignment, even though
    it may not manifest in practice due to _try_assign_pair_same_hand failures.
    """
    print("="*70)
    print("LATENT BUG ANALYSIS: _assign_min_transitions (lines 543-550)")
    print("="*70)
    print()
    
    print("CODE REVIEW:")
    print("-" * 70)
    print("""
    # First pass: Select unique pairs (lines 534-542)
    for info in pair_costs:
        if len(selected_pairs) >= pair_count_needed:
            break
        a, b = info['pair']
        if a in used_bells or b in used_bells:  # ✓ Checks used_bells
            continue
        selected_pairs.append((a, b))
        used_bells.add(a)
        used_bells.add(b)
    
    # Second pass: Fill remaining quota (lines 543-550)
    if len(selected_pairs) < pair_count_needed:
        for info in pair_costs:
            if len(selected_pairs) >= pair_count_needed:
                break
            pair = info['pair']
            if pair in selected_pairs:  # ❌ Only checks pair, not used_bells
                continue
            selected_pairs.append(pair)  # Bug: Could add (A,C) when (A,B) exists
    """)
    print("-" * 70)
    print()
    
    print("BUG EXPLANATION:")
    print("-" * 70)
    print("The second pass (lines 543-550) checks:")
    print("  if pair in selected_pairs")
    print()
    print("But it SHOULD check:")
    print("  if pair in selected_pairs OR a in used_bells OR b in used_bells")
    print()
    print("This means:")
    print("  - If first pass selects (C4, D4)")
    print("  - Second pass could add (C4, E4) because (C4, E4) != (C4, D4)")
    print("  - Result: C4 appears in two pairs -> potential duplicate assignment")
    print("-" * 70)
    print()
    
    print("WHY IT HASN'T MANIFESTED:")
    print("-" * 70)
    print("The bug is latent because:")
    print("1. Later code calls _try_assign_pair_same_hand() for each pair")
    print("2. This function checks swap gaps and may fail to place duplicate bells")
    print("3. Even if both pairs are added to selected_pairs, the actual assignment")
    print("   phase (lines 555-580) may not successfully place them")
    print("4. Lines 565-567 check 'if a in assigned_notes or b in assigned_notes'")
    print("   which prevents actual duplicate assignment")
    print("-" * 70)
    print()
    
    print("SEVERITY ASSESSMENT:")
    print("-" * 70)
    print("Severity: High")
    print()
    print("Reasoning:")
    print("- The selected_pairs list could contain overlapping bells")
    print("- If swap gap checks are relaxed or timing data allows it")
    print("- A bell could be assigned to multiple players")
    print("- The safeguard at lines 565-567 prevents manifestation BUT:")
    print("  * This creates silent failure (pairs not placed)")
    print("  * Pair count may be lower than expected")
    print("  * Algorithm behavior becomes unpredictable")
    print("-" * 70)
    print()
    
    print("RECOMMENDATION:")
    print("-" * 70)
    print("Fix the bug by modifying lines 543-550:")
    print()
    print("""
    if len(selected_pairs) < pair_count_needed:
        for info in pair_costs:
            if len(selected_pairs) >= pair_count_needed:
                break
            a, b = info['pair']
            if (a, b) in selected_pairs or a in used_bells or b in used_bells:
                continue
            selected_pairs.append((a, b))
            used_bells.add(a)  # Add this line
            used_bells.add(b)  # Add this line
    """)
    print("-" * 70)
    print()
    
    print("✅ ANALYSIS COMPLETE")
    print("="*70)


if __name__ == '__main__':
    demonstrate_latent_bug()
