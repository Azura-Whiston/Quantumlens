import { useState, useEffect, useRef, useCallback } from 'react';
import type { Snapshot } from '../types/quantum';
import HelpBubble from './HelpBubble';
import { useLearning } from '../contexts/LearningContext';

interface Props {
  snapshots: Snapshot[];
  labels: string[];
  currentStep: number;
  onStepChange: (step: number) => void;
}

export default function TimelinePlayer({ snapshots, labels, currentStep, onStepChange }: Props) {
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // 1x, 2x, 4x
  const { learningMode } = useLearning();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const maxStep = snapshots.length - 1;
  const baseInterval = 800; // ms per step at 1x

  const stepForward = useCallback(() => {
    onStepChange(Math.min(currentStep + 1, maxStep));
  }, [currentStep, maxStep, onStepChange]);

  const stepBack = useCallback(() => {
    onStepChange(Math.max(currentStep - 1, 0));
  }, [currentStep, onStepChange]);

  // Auto-play
  useEffect(() => {
    if (!playing) {
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }

    if (currentStep >= maxStep) {
      setPlaying(false);
      return;
    }

    timerRef.current = setTimeout(() => {
      onStepChange(currentStep + 1);
    }, baseInterval / speed);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [playing, currentStep, maxStep, speed, onStepChange]);

  const togglePlay = () => {
    if (currentStep >= maxStep) {
      // Reset to start then play
      onStepChange(0);
      setPlaying(true);
    } else {
      setPlaying(!playing);
    }
  };

  const currentSnap = snapshots[currentStep];
  if (!currentSnap || snapshots.length < 2) return null;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>
            Step-Through Timeline
          </h3>
          {learningMode && (
            <HelpBubble title="Step-Through Timeline">
              Step through your circuit one gate at a time to see how each gate transforms the quantum state.
              Watch the Bloch sphere, histogram, and state table update as you advance through each step.
              Use the play button for automatic playback, or step manually with the arrow buttons.
            </HelpBubble>
          )}
        </div>
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          Gate {currentStep} / {maxStep}
          {currentSnap.gate_label !== 'init' && (
            <span style={{ color: 'var(--accent)' }}> — {currentSnap.gate_label}</span>
          )}
          {currentSnap.gate_label === 'init' && (
            <span style={{ color: 'var(--text-secondary)' }}> — initial |0...0⟩</span>
          )}
        </span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2">
        {/* Reset */}
        <button
          onClick={() => { setPlaying(false); onStepChange(0); }}
          className="w-8 h-8 rounded flex items-center justify-center text-sm"
          style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}
          title="Reset"
        >⏮</button>

        {/* Step back */}
        <button
          onClick={() => { setPlaying(false); stepBack(); }}
          className="w-8 h-8 rounded flex items-center justify-center text-sm"
          style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}
          disabled={currentStep <= 0}
          title="Step back"
        >◀</button>

        {/* Play/Pause */}
        <button
          onClick={togglePlay}
          className="w-10 h-8 rounded flex items-center justify-center text-sm font-bold"
          style={{
            background: playing ? 'var(--warning)' : 'var(--accent)',
            color: '#1a1a1a',
          }}
          title={playing ? 'Pause' : 'Play'}
        >
          {playing ? '⏸' : '▶'}
        </button>

        {/* Step forward */}
        <button
          onClick={() => { setPlaying(false); stepForward(); }}
          className="w-8 h-8 rounded flex items-center justify-center text-sm"
          style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}
          disabled={currentStep >= maxStep}
          title="Step forward"
        >▶</button>

        {/* End */}
        <button
          onClick={() => { setPlaying(false); onStepChange(maxStep); }}
          className="w-8 h-8 rounded flex items-center justify-center text-sm"
          style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}
          title="Jump to end"
        >⏭</button>

        {/* Speed selector */}
        <div className="ml-2 flex items-center gap-1">
          {[1, 2, 4].map(s => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className="px-2 py-1 rounded text-xs font-bold"
              style={{
                background: speed === s ? 'var(--accent)' : 'var(--bg-tertiary)',
                color: speed === s ? '#1a1a1a' : 'var(--text-secondary)',
                border: `1px solid ${speed === s ? 'var(--accent)' : 'var(--border)'}`,
              }}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Timeline slider */}
        <input
          type="range"
          min={0}
          max={maxStep}
          value={currentStep}
          onChange={e => { setPlaying(false); onStepChange(parseInt(e.target.value)); }}
          className="flex-1 ml-2"
          style={{ accentColor: 'var(--accent)' }}
        />
      </div>

      {/* Step markers */}
      <div className="flex gap-px" style={{ paddingLeft: '0' }}>
        {snapshots.map((snap, i) => (
          <button
            key={i}
            onClick={() => { setPlaying(false); onStepChange(i); }}
            className="flex-1 h-6 rounded-sm flex items-center justify-center text-xs transition-all"
            style={{
              background: i === currentStep
                ? 'var(--accent)'
                : i < currentStep
                  ? 'var(--accent)33'
                  : 'var(--bg-tertiary)',
              color: i === currentStep ? '#1a1a1a' : 'var(--text-secondary)',
              fontSize: '9px',
              minWidth: '24px',
            }}
            title={`Step ${i}: ${snap.gate_label}`}
          >
            {snap.gate_label === 'init' ? '|0⟩' : snap.gate_label}
          </button>
        ))}
      </div>
    </div>
  );
}
