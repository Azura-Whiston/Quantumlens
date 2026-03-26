import { useState, useRef, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { GateInfo } from '../types/quantum';
import { getGateEducation } from '../data/gateEducation';
import { useLearning } from '../contexts/LearningContext';

interface Props {
  gate: GateInfo;
  children: ReactNode;
}

export default function GateTooltip({ gate, children }: Props) {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { learningMode } = useLearning();
  const edu = getGateEducation(gate.name);

  const showTooltip = useCallback(() => {
    timerRef.current = setTimeout(() => setVisible(true), 200);
  }, []);

  const hideTooltip = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setVisible(false);
  }, []);

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
    >
      {children}

      {visible && (
        <div
          className="absolute z-50 rounded-lg p-3"
          style={{
            bottom: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            marginBottom: '6px',
            width: '260px',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            pointerEvents: 'none',
          }}
        >
          {/* Gate name */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-sm font-bold" style={{ color: gate.color }}>
              {gate.label}
            </span>
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              {gate.name}
            </span>
          </div>

          {/* Description */}
          <div className="text-xs mb-1.5" style={{ color: 'var(--text-primary)' }}>
            {edu ? edu.plainEnglish : gate.description}
          </div>

          {/* Bloch hint — only in learning mode */}
          {learningMode && edu && (
            <>
              <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>
                <span style={{ color: 'var(--accent)', fontSize: '10px' }}>BLOCH: </span>
                {edu.blochHint}
              </div>
              <div className="text-xs italic" style={{ color: 'var(--text-secondary)' }}>
                {edu.example}
              </div>
            </>
          )}

          {/* Click prompt */}
          <div className="text-xs mt-1.5 pt-1.5" style={{ borderTop: '1px solid var(--border)', color: 'var(--text-secondary)', fontSize: '10px' }}>
            Click to select this gate
          </div>
        </div>
      )}
    </div>
  );
}
