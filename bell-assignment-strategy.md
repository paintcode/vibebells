## Bell Assignment Strategy

Here's a draft algorithm that prioritizes assigning melody notes to more experienced players while ensuring no one rings more than two bells at once.

---

### Step-by-Step Algorithm for Bell Distribution

1. **Input Data**:
   - **MIDI File**: Extract data from the file to determine notes used in the song.
   - **Number of Players**: Total players available. If this parameter is not provided, try to arrange for a number of players equal to the number of unique notes divided by 2.
   - **Available Bells**: The range of bells (e.g., bells C4 through G5). If this parameter is not provided, assume all needed bells are available.

---

2. **Identify Parts**:
   - **Determine Melody**: Extract the melody notes. List the notes in the melody (e.g., C4, D4, E4).
   - **Determine Harmony**: Identify harmony chords and their constituent notes.

---

3. **Count Unique Notes**:
   - Create a unique list of melody and harmony notes.
   - Count how many times each note appears.

---

4. **Prioritize Players**:
   - **Experience Levels**: Rank players based on experience (e.g., experienced players, intermediate players, and beginners).

---

5. **Assign Melody Notes**:
   - Iterate through the melody notes:
     - **Experienced Players**: Assign melody notes to the first available experienced player who has the fewest current assignments, ensuring they don't exceed two bells.
     - **Intermediate/Beginner Players**: If no experienced player is available, assign to the next best available player, still ensuring the "two bells" rule is followed.

---

6. **Assign Harmony Notes**:
   - For each unique harmony note:
     - **Next Available**: Assign to the next available player with fewer than two bells.
     - This should not conflict with existing melody assignments.

---

7. **Conflict Resolution**:
   - If multiple players are assigned the same bell for the same note:
     - Adjust the assignments by checking if moving one player's bell to another available note will solve the conflict without exceeding the two-bell limit.
   - Assign based on a “first available” principle while prioritizing more experienced players.

---

8. **Sustainability Check**:
   - Review all assignments to ensure:
     - Each bell rings at sufficient intervals for the piece.
     - No player is overloaded with more than two bells at once.
   - Adjust based on player feedback, performance difficulties, or transitions during practice.

---

### Example Distribution

#### Players and their Experience Levels:
- **Player 1**: Experienced
- **Player 2**: Intermediate
- **Player 3**: Beginner

#### Musical Parts:
- **Melody**: C4, D4, E4
- **Chords**: C (C4, E4, G4), G (G4, B4, D5)

#### Example Assignments:
- **Player 1 (Experienced)**: C4 (melody), E4 (harmony)
- **Player 2 (Intermediate)**: D4 (melody), G4 (chord)
- **Player 3 (Beginner)**: B4 (harmony), D5 (harmony)

---

By following this revised strategy, you can ensure that melody notes are primarily assigned to more experienced players while still providing opportunities for beginners. This will boost the confidence and skill of all players involved.