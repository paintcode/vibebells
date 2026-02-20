'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import './SimulationPlayer.css';

const PLAYER_WIDTH = 180;
const CANVAS_HEIGHT = 380;
const PLAYER_PADDING = 10;

// Arm angles in radians from horizontal (positive = downward)
const ARM_IDLE_ANGLE = 0.4;
const ARM_RING_ANGLE = -0.8;
const ARM_TABLE_ANGLE = 1.2;

const SWAP_MAX_DURATION_MS = 2000;

// Stick figure geometry
const HEAD_R = 12;
const ARM_LEN = 50;
const LEG_LEN = 60;
const FIGURE_TOP = 50;
const TABLE_Y = 270;
const FATIGUE_BAR_Y = 340;
const FATIGUE_BAR_H = 18;

function lerp(a, b, t) {
  return a + (b - a) * Math.clamp(t, 0, 1);
}
Math.clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/** Pre-compute stable table x/y positions for all bells, sorted by pitch ascending. */
function computeTablePositions(bells, colX) {
  const sorted = [...bells].sort((a, b) => a.pitch - b.pitch);
  const positions = {};
  let x = colX + PLAYER_PADDING + 12;
  for (const bell of sorted) {
    const rx = bell.canvas_px * 0.35;
    positions[bell.pitch] = { x: x + rx, y: TABLE_Y + bell.canvas_px * 0.6 };
    x += rx * 2 + 6;
  }
  return positions;
}

/** Arm endpoint pointing toward (targetX, targetY) from shoulder, capped at 1.3× ARM_LEN. */
function armEndToward(cx, shoulderY, targetX, targetY) {
  const dx = targetX - cx;
  const dy = targetY - shoulderY;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const len = Math.min(ARM_LEN * 1.3, dist);
  return { x: cx + (dx / dist) * len, y: shoulderY + (dy / dist) * len };
}

/** Idle hand position for a given hand. */
function idleHandPos(cx, shoulderY, hand) {
  const sign = hand === 'left' ? -1 : 1;
  return {
    x: cx + sign * ARM_LEN * Math.cos(ARM_IDLE_ANGLE),
    y: shoulderY + ARM_LEN * Math.sin(ARM_IDLE_ANGLE),
  };
}

/**
 * Determine the full animation state for one hand at timeMs.
 * Returns { phase, flyingBell, flyingPos, heldBell, armTip, isRinging, isTight }
 * phase: 'idle' | 'ringing' | 'swap_phase1' | 'swap_phase2' | 'swap_done'
 */
function getHandAnimState(events, hand, timeMs, thresholdMs, bells, tablePosMap, cx, shoulderY) {
  const handEvents = events
    .filter(e => e.hand === hand)
    .sort((a, b) => a.time_ms - b.time_ms);

  // Collect swap pairs { putDown, pickUp }
  const swapPairs = [];
  for (let i = 0; i < handEvents.length; i++) {
    if (handEvents[i].type !== 'put_down') continue;
    const pickUp = handEvents.slice(i + 1).find(e => e.type === 'pick_up');
    if (pickUp) swapPairs.push({ putDown: handEvents[i], pickUp });
  }

  // Check if timeMs falls inside a swap window
  for (const { putDown, pickUp } of swapPairs) {
    if (timeMs < putDown.time_ms || timeMs >= pickUp.time_ms) continue;

    const gapMs = pickUp.time_ms - putDown.time_ms;
    const animDuration = Math.min(Math.max(gapMs, 0), SWAP_MAX_DURATION_MS);
    const animStart = putDown.time_ms;
    const phase1End = animStart + animDuration / 2;
    const animEnd = animStart + animDuration;

    const oldBell = bells.find(b => b.pitch === putDown.pitch) || null;
    const newBell = bells.find(b => b.pitch === pickUp.pitch) || null;
    const isTight = putDown.gap_ms < thresholdMs;
    const hp = idleHandPos(cx, shoulderY, hand);
    const oldTablePos = tablePosMap[putDown.pitch] || hp;
    const newTablePos = tablePosMap[pickUp.pitch] || hp;

    if (animDuration <= 0 || timeMs >= animEnd) {
      // Animation finished; holding new bell, waiting for ring
      return { phase: 'swap_done', flyingBell: null, flyingPos: null,
               heldBell: newBell, armTip: hp, isRinging: false, isTight: false };
    }
    if (timeMs < phase1End) {
      // Phase 1: old bell flies from hand → table
      const t = (timeMs - animStart) / (animDuration / 2);
      const flyPos = { x: lerp(hp.x, oldTablePos.x, t), y: lerp(hp.y, oldTablePos.y, t) };
      return { phase: 'swap_phase1', flyingBell: oldBell, flyingPos: flyPos,
               heldBell: null, armTip: armEndToward(cx, shoulderY, flyPos.x, flyPos.y),
               isRinging: false, isTight };
    } else {
      // Phase 2: new bell flies from table → hand
      const t = (timeMs - phase1End) / (animDuration / 2);
      const flyPos = { x: lerp(newTablePos.x, hp.x, t), y: lerp(newTablePos.y, hp.y, t) };
      return { phase: 'swap_phase2', flyingBell: newBell, flyingPos: flyPos,
               heldBell: null, armTip: armEndToward(cx, shoulderY, flyPos.x, flyPos.y),
               isRinging: false, isTight };
    }
  }

  // Compute current held bell from pick_up history
  let heldBell = bells.find(b => b.hand === hand) || null;
  for (const ev of handEvents) {
    if (ev.time_ms > timeMs) break;
    if (ev.type === 'pick_up') heldBell = bells.find(b => b.pitch === ev.pitch) || heldBell;
  }

  // Active ring?
  const ring = handEvents.find(e =>
    e.type === 'ring' && e.time_ms <= timeMs && timeMs <= e.time_ms + e.duration_ms
  );
  const sign = hand === 'left' ? -1 : 1;
  if (ring) {
    const progress = (timeMs - ring.time_ms) / Math.max(ring.duration_ms, 1);
    let angle;
    if (progress < 0.15)       angle = lerp(ARM_IDLE_ANGLE, ARM_RING_ANGLE, progress / 0.15);
    else if (progress > 0.85)  angle = lerp(ARM_RING_ANGLE, ARM_IDLE_ANGLE, (progress - 0.85) / 0.15);
    else                       angle = ARM_RING_ANGLE;
    return { phase: 'ringing', flyingBell: null, flyingPos: null, heldBell,
             armTip: { x: cx + sign * ARM_LEN * Math.cos(angle),
                       y: shoulderY + ARM_LEN * Math.sin(angle) },
             isRinging: true, isTight: false };
  }

  // Idle
  return { phase: 'idle', flyingBell: null, flyingPos: null,
           heldBell, armTip: idleHandPos(cx, shoulderY, hand), isRinging: false, isTight: false };
}

/** Draw a handbell oval at (x, y) with size canvasPx. state: 'idle'|'ringing'|'swapping'|'tight' */
function drawBell(ctx, x, y, canvasPx, state) {
  const rx = canvasPx * 0.35;
  const ry = canvasPx * 0.55;
  const fillColors = { idle: '#c0a020', ringing: '#d4af37', swapping: '#e07820', tight: '#d43020' };
  const strokeColors = { idle: '#8b7000', ringing: '#fff8dc', swapping: '#ff9933', tight: '#ff4422' };
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
  ctx.fillStyle = fillColors[state] || fillColors.idle;
  ctx.fill();
  ctx.strokeStyle = strokeColors[state] || strokeColors.idle;
  ctx.lineWidth = (state === 'ringing' || state === 'swapping' || state === 'tight') ? 2.5 : 1.5;
  ctx.stroke();
  // Handle stub
  ctx.beginPath();
  ctx.moveTo(x, y - ry);
  ctx.lineTo(x, y - ry - 8);
  ctx.strokeStyle = '#555';
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.restore();
}

/** Draw the fatigue bar for a player. */
function drawFatigueBar(ctx, colX, fatigue, maxFatigue) {
  const barW = PLAYER_WIDTH - PLAYER_PADDING * 2;
  const barX = colX + PLAYER_PADDING;
  const norm = maxFatigue > 0 ? Math.min(fatigue / maxFatigue, 1) : 0;

  // Background
  ctx.fillStyle = '#333';
  ctx.fillRect(barX, FATIGUE_BAR_Y, barW, FATIGUE_BAR_H);

  // Gradient fill
  const fillW = barW * norm;
  if (fillW > 0) {
    const grad = ctx.createLinearGradient(barX, 0, barX + barW, 0);
    grad.addColorStop(0, '#4caf50');
    grad.addColorStop(0.5, '#ffeb3b');
    grad.addColorStop(1, '#f44336');
    ctx.fillStyle = grad;
    ctx.fillRect(barX, FATIGUE_BAR_Y, fillW, FATIGUE_BAR_H);
  }

  ctx.strokeStyle = '#666';
  ctx.lineWidth = 1;
  ctx.strokeRect(barX, FATIGUE_BAR_Y, barW, FATIGUE_BAR_H);

  ctx.fillStyle = '#ddd';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('Fatigue', barX + barW / 2, FATIGUE_BAR_Y - 3);
}

/** Draw one player column. */
function drawPlayer(ctx, player, colX, timeMs, maxFatigue, thresholdMs, impossibleSwapGapMs) {
  const cx = colX + PLAYER_WIDTH / 2;
  const events = player.events;
  const headY = FIGURE_TOP + HEAD_R;
  const shoulderY = headY + HEAD_R + 10;
  const hipY = shoulderY + 70;

  // Pre-compute stable table positions for all bells
  const tablePosMap = computeTablePositions(player.bells, colX);

  // Detect any swap that is physically impossible to perform (too fast to animate).
  const hasImpossibleSwap = events.some(e => e.type === 'put_down' && e.gap_ms < impossibleSwapGapMs);

  // Get animation state for each hand
  const leftState  = getHandAnimState(events, 'left',  timeMs, thresholdMs, player.bells, tablePosMap, cx, shoulderY);
  const rightState = getHandAnimState(events, 'right', timeMs, thresholdMs, player.bells, tablePosMap, cx, shoulderY);
  const isSwapping = leftState.phase.startsWith('swap') || rightState.phase.startsWith('swap');
  const isTight    = leftState.isTight || rightState.isTight;

  // Column background highlight
  if (hasImpossibleSwap || isTight) {
    ctx.save();
    ctx.fillStyle = 'rgba(255,0,0,0.18)';
    ctx.fillRect(colX, 0, PLAYER_WIDTH, CANVAS_HEIGHT);
    ctx.strokeStyle = 'rgba(255,60,60,0.85)';
    ctx.lineWidth = 3;
    ctx.strokeRect(colX + 1, 1, PLAYER_WIDTH - 2, CANVAS_HEIGHT - 2);
    ctx.restore();
  } else if (isSwapping) {
    ctx.save();
    ctx.fillStyle = 'rgba(255,140,0,0.10)';
    ctx.fillRect(colX, 0, PLAYER_WIDTH, CANVAS_HEIGHT);
    ctx.restore();
  }

  // Completed swap count: number of put_down events that have passed
  const completedSwaps = events.filter(e => e.type === 'put_down' && e.time_ms <= timeMs).length;

  // Player name
  ctx.fillStyle = '#eee';
  ctx.font = 'bold 12px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(player.name, cx, 20);

  // "INVALID" badge for impossible swaps (always shown)
  if (hasImpossibleSwap) {
    ctx.save();
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#ff4422';
    ctx.fillText('⛔ INVALID', cx, 36);
    ctx.restore();
  }

  // Swap counter (always visible)
  ctx.save();
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillStyle = completedSwaps > 0 ? '#aaa' : '#555';
  const swapCountY = hasImpossibleSwap ? 47 : (isSwapping ? 47 : 36);
  ctx.fillText(`swaps: ${completedSwaps}`, cx, swapCountY);
  ctx.restore();

  // SWAP label (shown during active swap)
  if (isSwapping) {
    ctx.save();
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = isTight ? '#ff4422' : '#ff9933';
    ctx.fillText(isTight ? '⚠ SWAP' : 'SWAP', cx, 36);
    ctx.restore();
  }

  // Head
  ctx.beginPath();
  ctx.arc(cx, headY, HEAD_R, 0, Math.PI * 2);
  ctx.strokeStyle = '#ddd';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Body
  ctx.beginPath();
  ctx.moveTo(cx, shoulderY);
  ctx.lineTo(cx, hipY);
  ctx.strokeStyle = '#ddd';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Legs
  ctx.beginPath();
  ctx.moveTo(cx, hipY); ctx.lineTo(cx - 18, hipY + LEG_LEN);
  ctx.moveTo(cx, hipY); ctx.lineTo(cx + 18, hipY + LEG_LEN);
  ctx.strokeStyle = '#ddd';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Track which pitches are flying or held (to exclude from table render)
  const flyingPitches = new Set();
  if (leftState.flyingBell)  flyingPitches.add(leftState.flyingBell.pitch);
  if (rightState.flyingBell) flyingPitches.add(rightState.flyingBell.pitch);
  const heldPitches = new Set();
  if (leftState.heldBell)  heldPitches.add(leftState.heldBell.pitch);
  if (rightState.heldBell) heldPitches.add(rightState.heldBell.pitch);

  // Arms, held bells, flying bells
  for (const [hs, hand] of [[leftState, 'left'], [rightState, 'right']]) {
    const { phase, armTip, heldBell, flyingBell, flyingPos, isRinging, isTight: ht } = hs;
    const isSwap = phase.startsWith('swap');
    const armColor = ht ? '#ff4422' : isSwap ? '#ff9933' : '#ccc';

    // Arm line from shoulder to tip
    ctx.beginPath();
    ctx.moveTo(cx, shoulderY);
    ctx.lineTo(armTip.x, armTip.y);
    ctx.strokeStyle = armColor;
    ctx.lineWidth = isSwap ? 3 : 2;
    ctx.stroke();

    // Bell in hand (at arm tip)
    if (heldBell) {
      const state = isRinging ? 'ringing' : ht ? 'tight' : isSwap ? 'swapping' : 'idle';
      drawBell(ctx, armTip.x, armTip.y, heldBell.canvas_px, state);
    }

    // Flying bell (travels between hand and table)
    if (flyingBell && flyingPos) {
      drawBell(ctx, flyingPos.x, flyingPos.y, flyingBell.canvas_px, ht ? 'tight' : 'swapping');
      // Dashed trail from arm tip to bell (shows reach/connection)
      ctx.save();
      ctx.beginPath();
      ctx.setLineDash([4, 4]);
      ctx.moveTo(armTip.x, armTip.y);
      ctx.lineTo(flyingPos.x, flyingPos.y);
      ctx.strokeStyle = ht ? 'rgba(255,68,34,0.5)' : 'rgba(255,153,51,0.5)';
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.restore();
    }
  }

  // Table line
  ctx.beginPath();
  ctx.moveTo(colX + PLAYER_PADDING, TABLE_Y);
  ctx.lineTo(colX + PLAYER_WIDTH - PLAYER_PADDING, TABLE_Y);
  ctx.strokeStyle = '#888';
  ctx.lineWidth = 3;
  ctx.stroke();

  // Bells on table: all bells except held or mid-air
  for (const bell of player.bells) {
    if (heldPitches.has(bell.pitch) || flyingPitches.has(bell.pitch)) continue;
    const pos = tablePosMap[bell.pitch];
    if (pos) drawBell(ctx, pos.x, pos.y, bell.canvas_px, 'idle');
  }

  // Fatigue bar
  drawFatigueBar(ctx, colX, player.fatigue_score, maxFatigue);
}

export default function SimulationPlayer({ simulationData, onClose }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const audioCtxRef = useRef(null);
  const scheduledRef = useRef(new Set());
  const startWallTimeRef = useRef(null);
  const startSimTimeRef = useRef(0);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [threshold, setThreshold] = useState(simulationData?.tight_swap_threshold_ms ?? 1000);

  const players = simulationData?.players ?? [];
  const durationMs = simulationData?.duration_ms ?? 0;
  const impossibleSwapGapMs = simulationData?.impossible_swap_gap_ms ?? 100;
  const maxFatigue = Math.max(...players.map(p => p.fatigue_score), 1);

  // Draw a single frame
  const draw = useCallback((simTimeMs) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const totalW = players.length * PLAYER_WIDTH;
    canvas.width = totalW || PLAYER_WIDTH;
    canvas.height = CANVAS_HEIGHT;

    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    players.forEach((player, i) => {
      const colX = i * PLAYER_WIDTH;
      // Column separator
      if (i > 0) {
        ctx.beginPath();
        ctx.moveTo(colX, 0);
        ctx.lineTo(colX, CANVAS_HEIGHT);
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      drawPlayer(ctx, player, colX, simTimeMs, maxFatigue, threshold, impossibleSwapGapMs);
    });

    // Time indicator
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.font = '11px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(`${(simTimeMs / 1000).toFixed(2)}s / ${(durationMs / 1000).toFixed(2)}s`, canvas.width - 6, CANVAS_HEIGHT - 6);
  }, [players, maxFatigue, threshold, durationMs, impossibleSwapGapMs]);

  // Animation loop
  const tick = useCallback(() => {
    const now = performance.now();
    const elapsed = (now - startWallTimeRef.current) * speed;
    const simTime = startSimTimeRef.current + elapsed;

    if (simTime >= durationMs) {
      setCurrentTimeMs(durationMs);
      draw(durationMs);
      setIsPlaying(false);
      return;
    }

    setCurrentTimeMs(simTime);
    draw(simTime);

    // Schedule audio for upcoming events
    if (audioCtxRef.current) {
      const audioCtx = audioCtxRef.current;
      const lookahead = 0.25; // seconds
      const audioNow = audioCtx.currentTime;

      players.forEach(player => {
        player.events.forEach(ev => {
          if (ev.type !== 'ring') return;
          const evKey = `${player.name}-${ev.time_ms}-${ev.pitch}`;
          if (scheduledRef.current.has(evKey)) return;

          const evTimeFromNow = (ev.time_ms - simTime) / 1000 / speed;
          if (evTimeFromNow >= 0 && evTimeFromNow <= lookahead) {
            scheduledRef.current.add(evKey);
            const scheduleTime = audioNow + evTimeFromNow;
            const frequency = 440 * Math.pow(2, (ev.pitch - 69) / 12);
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.type = 'sine';
            osc.frequency.value = frequency;
            const vel = (ev.velocity || 80) / 127 * 0.4;
            gain.gain.setValueAtTime(vel, scheduleTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, scheduleTime + 2.0);
            osc.start(scheduleTime);
            osc.stop(scheduleTime + 2.5);
          }
        });
      });
    }

    rafRef.current = requestAnimationFrame(tick);
  }, [speed, durationMs, draw, players]);

  const handlePlay = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    startWallTimeRef.current = performance.now();
    startSimTimeRef.current = currentTimeMs >= durationMs ? 0 : currentTimeMs;
    scheduledRef.current = new Set();
    setIsPlaying(true);
    rafRef.current = requestAnimationFrame(tick);
  }, [currentTimeMs, durationMs, tick]);

  const handlePause = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    setIsPlaying(false);
  }, []);

  const handleRestart = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    scheduledRef.current = new Set();
    setCurrentTimeMs(0);
    draw(0);
    setIsPlaying(false);
  }, [draw]);

  // Draw initial frame
  useEffect(() => {
    draw(0);
  }, [draw]);

  // Restart tick when speed changes while playing
  useEffect(() => {
    if (isPlaying) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      startWallTimeRef.current = performance.now();
      startSimTimeRef.current = currentTimeMs;
      scheduledRef.current = new Set();
      rafRef.current = requestAnimationFrame(tick);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [speed]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const totalWidth = players.length * PLAYER_WIDTH;

  return (
    <div className="sim-player">
      <div className="sim-header">
        <h3 className="sim-title">🔔 Bell Practice Simulation</h3>
        <button className="sim-close-btn" onClick={onClose} title="Close simulation">✕</button>
      </div>

      <div className="sim-controls">
        <button
          className="sim-btn sim-btn-primary"
          onClick={isPlaying ? handlePause : handlePlay}
        >
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </button>
        <button className="sim-btn" onClick={handleRestart}>⏮ Restart</button>

        <label className="sim-label">
          Speed:
          <select
            className="sim-select"
            value={speed}
            onChange={e => setSpeed(parseFloat(e.target.value))}
          >
            <option value={0.5}>0.5×</option>
            <option value={1}>1×</option>
            <option value={1.5}>1.5×</option>
            <option value={2}>2×</option>
          </select>
        </label>

        <label className="sim-label">
          Tight swap &lt;
          <input
            className="sim-threshold"
            type="number"
            min={100}
            step={100}
            value={threshold}
            onChange={e => setThreshold(Number(e.target.value))}
          />
          ms
        </label>
      </div>

      <div className="sim-canvas-wrapper">
        <canvas
          ref={canvasRef}
          width={totalWidth || PLAYER_WIDTH}
          height={CANVAS_HEIGHT}
          className="sim-canvas"
        />
      </div>

      <div className="sim-legend">
        <span className="sim-legend-item"><span className="sim-legend-color" style={{ background: '#d4af37' }} /> Ringing</span>
        <span className="sim-legend-item"><span className="sim-legend-color" style={{ background: '#e07820' }} /> Swapping</span>
        <span className="sim-legend-item"><span className="sim-legend-color" style={{ background: '#d43020' }} /> Tight swap</span>
        <span className="sim-legend-item"><span className="sim-legend-color" style={{ background: '#ff4422', outline: '2px solid #ff4422' }} /> ⛔ Invalid (impossible swap)</span>
        <span className="sim-legend-item">
          <span className="sim-legend-bar" style={{ background: 'linear-gradient(to right,#4caf50,#ffeb3b,#f44336)' }} /> Fatigue
        </span>
      </div>
    </div>
  );
}
