// Malmark handbell specifications (MIDI pitch -> {diameterIn, weightOz})
// Source: Malmark manufacturer data. Diatonic pitches only; use getBellData() for chromatic interpolation.
export const MALMARK_DATA = {
   43: { diameterIn: 14.0,   weightOz: 228 },  // G2
   45: { diameterIn: 13.0,   weightOz: 199 },  // A2
   47: { diameterIn: 11.125, weightOz: 148 },  // B2
   48: { diameterIn: 10.875, weightOz: 140 },  // C3
   50: { diameterIn: 10.25,  weightOz: 124 },  // D3
   52: { diameterIn: 9.75,   weightOz: 104 },  // E3
   53: { diameterIn: 9.0,    weightOz: 96  },  // F3
   55: { diameterIn: 8.125,  weightOz: 60  },  // G3
   57: { diameterIn: 7.5,    weightOz: 52  },  // A3
   59: { diameterIn: 7.25,   weightOz: 48  },  // B3
   60: { diameterIn: 6.75,   weightOz: 40  },  // C4
   62: { diameterIn: 6.625,  weightOz: 40  },  // D4
   64: { diameterIn: 6.125,  weightOz: 40  },  // E4
   65: { diameterIn: 5.875,  weightOz: 41  },  // F4
   67: { diameterIn: 5.625,  weightOz: 32  },  // G4
   69: { diameterIn: 5.125,  weightOz: 28  },  // A4
   71: { diameterIn: 4.75,   weightOz: 24  },  // B4
   72: { diameterIn: 4.5,    weightOz: 24  },  // C5
   74: { diameterIn: 4.25,   weightOz: 21  },  // D5
   76: { diameterIn: 4.25,   weightOz: 19  },  // E5
   77: { diameterIn: 4.125,  weightOz: 18  },  // F5
   79: { diameterIn: 3.875,  weightOz: 17  },  // G5
   81: { diameterIn: 3.625,  weightOz: 15  },  // A5
   83: { diameterIn: 3.5,    weightOz: 14  },  // B5
   84: { diameterIn: 3.375,  weightOz: 13  },  // C6
   86: { diameterIn: 3.25,   weightOz: 13  },  // D6
   88: { diameterIn: 3.125,  weightOz: 12  },  // E6
   89: { diameterIn: 3.0,    weightOz: 10  },  // F6
   91: { diameterIn: 2.875,  weightOz: 9   },  // G6
   93: { diameterIn: 2.75,   weightOz: 9   },  // A6
   95: { diameterIn: 2.625,  weightOz: 9   },  // B6
   96: { diameterIn: 2.5,    weightOz: 8   },  // C7
   98: { diameterIn: 2.5,    weightOz: 8   },  // D7
  100: { diameterIn: 2.375,  weightOz: 8   },  // E7
  101: { diameterIn: 2.375,  weightOz: 8   },  // F7
  103: { diameterIn: 2.25,   weightOz: 8   },  // G7
  105: { diameterIn: 2.25,   weightOz: 8   },  // A7
  107: { diameterIn: 2.25,   weightOz: 8   },  // B7
  108: { diameterIn: 2.25,   weightOz: 8   },  // C8
};

// Canvas rendering range
const BELL_MAX_IN = 10.875;  // C3
const BELL_MIN_IN = 2.25;    // C8
const BELL_MAX_PX = 50;
const BELL_MIN_PX = 10;

/** Get bell data for any MIDI pitch, interpolating for chromatic notes. */
export function getBellData(pitch) {
  if (MALMARK_DATA[pitch]) {
    const { diameterIn, weightOz } = MALMARK_DATA[pitch];
    return { diameterIn, weightOz, canvasPx: diameterToCanvasPx(diameterIn) };
  }
  const keys = Object.keys(MALMARK_DATA).map(Number).sort((a, b) => a - b);
  const lower = [...keys].reverse().find(k => k <= pitch) ?? keys[0];
  const upper = keys.find(k => k >= pitch) ?? keys[keys.length - 1];
  if (lower === upper) {
    const { diameterIn, weightOz } = MALMARK_DATA[lower];
    return { diameterIn, weightOz, canvasPx: diameterToCanvasPx(diameterIn) };
  }
  const t = (pitch - lower) / (upper - lower);
  const dLo = MALMARK_DATA[lower], dHi = MALMARK_DATA[upper];
  const diameterIn = dLo.diameterIn + t * (dHi.diameterIn - dLo.diameterIn);
  const weightOz   = dLo.weightOz   + t * (dHi.weightOz   - dLo.weightOz);
  return { diameterIn, weightOz, canvasPx: diameterToCanvasPx(diameterIn) };
}

function diameterToCanvasPx(diameterIn) {
  const px = BELL_MIN_PX + (diameterIn - BELL_MIN_IN) / (BELL_MAX_IN - BELL_MIN_IN) * (BELL_MAX_PX - BELL_MIN_PX);
  return Math.max(BELL_MIN_PX, Math.min(BELL_MAX_PX, px));
}
