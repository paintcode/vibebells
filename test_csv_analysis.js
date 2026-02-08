// Test script to validate CSV generation and bell sorting logic

// Replicate the compareBellPitch function
const compareBellPitch = (a, b) => {
  // Simple pitch comparison (note + octave)
  const noteOrder = { 'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11 };
  
  const parseNote = (bell) => {
    const match = bell.match(/([A-G][#b]?)(\d+)/);
    if (!match) return { note: 0, octave: 4 };
    let note = noteOrder[match[1][0]] || 0;
    if (match[1].includes('#')) note += 0.5;
    if (match[1].includes('b')) note -= 0.5;
    return { note, octave: parseInt(match[2]) };
  };
  
  const noteA = parseNote(a);
  const noteB = parseNote(b);
  
  if (noteA.octave !== noteB.octave) {
    return noteA.octave - noteB.octave;
  }
  return noteA.note - noteB.note;
};

// Test cases
const testBells = [
  'C4', 'C#4', 'D4', 'Eb4', 'E4', 'F4', 'F#4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4',
  'C5', 'C3', 'G#3', 'Db4'
];

console.log('Original bells:', testBells);
const sorted = [...testBells].sort(compareBellPitch);
console.log('Sorted bells:', sorted);

// Test CSV injection
const testGenerateCSV = (arrangement, filename) => {
  let csv = 'Metadata\n';
  csv += `Uploaded File,${filename || 'unknown'}\n`;
  csv += `Strategy,${arrangement.strategy}\n`;
  csv += `Generated,${new Date().toISOString()}\n`;
  csv += '\n';
  
  csv += 'Players\n';
  csv += 'Player,Experience,Left Hand,Right Hand,Bell Swaps\n';
  
  arrangement.players.forEach(player => {
    const leftHand = player.left_hand ? player.left_hand.join(' ') : '';
    const rightHand = player.right_hand ? player.right_hand.join(' ') : '';
    const swaps = player.swaps !== undefined ? player.swaps : 0;
    csv += `${player.name},${player.experience},${leftHand},${rightHand},${swaps}\n`;
  });
  
  return csv;
};

// Test with malicious input
console.log('\n--- Testing CSV Injection ---');
const maliciousArrangement = {
  strategy: 'test',
  players: [
    {
      name: '=1+1',  // CSV injection
      experience: 'experienced',
      left_hand: ['C4'],
      right_hand: ['D4'],
      swaps: 0
    },
    {
      name: 'Player"with"quotes',
      experience: 'beginner',
      left_hand: ['E4'],
      right_hand: ['F4'],
      swaps: 0
    }
  ]
};

const csv = testGenerateCSV(maliciousArrangement, '=cmd|/c calc.exe!A1');
console.log('Generated CSV:');
console.log(csv);

// Test edge case: What if bell format is invalid?
console.log('\n--- Testing invalid bell formats ---');
const invalidBells = ['C4', 'InvalidBell', 'X99', '', 'C', '4', 'C#'];
const sortedInvalid = [...invalidBells].sort(compareBellPitch);
console.log('Invalid bells sorted:', sortedInvalid);

// Test edge case: Double sharp/flat
console.log('\n--- Testing double accidentals ---');
const doubleBells = ['C##4', 'Dbb4'];
const sortedDouble = [...doubleBells].sort(compareBellPitch);
console.log('Double accidental bells sorted:', sortedDouble);
