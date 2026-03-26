import { useState, useEffect } from 'react';
import { useLearning } from '../contexts/LearningContext';

interface Props {
  onComplete: () => void;
}

const STEPS = [
  {
    title: 'Welcome to QuantumLens',
    content: (
      <>
        <p style={{ marginBottom: '12px' }}>
          This tool lets you build and simulate <strong>quantum circuits</strong> — the building blocks of quantum computing.
        </p>
        <p>
          No physics degree needed. Let's walk through the basics in 60 seconds.
        </p>
      </>
    ),
  },
  {
    title: 'What is a Qubit?',
    content: (
      <>
        <p style={{ marginBottom: '12px' }}>
          A <strong>qubit</strong> is the quantum version of a bit. A regular bit is either 0 or 1.
          A qubit can be in a combination of both — this is called <strong>superposition</strong>.
        </p>
        <div
          style={{
            display: 'flex', justifyContent: 'center', gap: '32px',
            padding: '16px 0', margin: '8px 0',
          }}
        >
          {/* Classical bit */}
          <div style={{ textAlign: 'center' }}>
            <svg width="60" height="60" viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="25" fill="none" stroke="#2c2c2c" strokeWidth="2" />
              <circle cx="30" cy="10" r="6" fill="#c8ad7f" />
              <text x="30" y="56" textAnchor="middle" fill="#908880" fontSize="10">Classical</text>
            </svg>
            <div style={{ color: 'var(--text-secondary)', fontSize: '10px', marginTop: '4px' }}>
              Definitely |0{'>'}
            </div>
          </div>
          {/* Quantum qubit */}
          <div style={{ textAlign: 'center' }}>
            <svg width="60" height="60" viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="25" fill="none" stroke="#2c2c2c" strokeWidth="2" />
              <line x1="30" y1="30" x2="55" y2="30" stroke="#c8ad7f" strokeWidth="2" />
              <circle cx="55" cy="30" r="4" fill="#c8ad7f" />
              <text x="30" y="56" textAnchor="middle" fill="#908880" fontSize="10">Quantum</text>
            </svg>
            <div style={{ color: 'var(--text-secondary)', fontSize: '10px', marginTop: '4px' }}>
              Superposition!
            </div>
          </div>
        </div>
      </>
    ),
  },
  {
    title: 'Superposition & the H Gate',
    content: (
      <>
        <p style={{ marginBottom: '12px' }}>
          The <strong>Hadamard (H)</strong> gate puts a qubit into equal superposition —
          a 50/50 chance of measuring 0 or 1.
        </p>
        <div
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            gap: '16px', padding: '12px', margin: '8px 0',
            background: 'var(--bg-tertiary)', borderRadius: '8px',
          }}
        >
          {/* Before */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Before</div>
            <div style={{ display: 'flex', gap: '4px', height: '48px', alignItems: 'flex-end' }}>
              <div style={{ width: '24px', background: 'var(--accent)', height: '48px', borderRadius: '3px 3px 0 0' }} />
              <div style={{ width: '24px', background: 'var(--border)', height: '2px', borderRadius: '3px 3px 0 0' }} />
            </div>
            <div style={{ display: 'flex', gap: '4px', fontSize: '9px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              <span style={{ width: '24px', textAlign: 'center' }}>|0{'>'}</span>
              <span style={{ width: '24px', textAlign: 'center' }}>|1{'>'}</span>
            </div>
          </div>

          {/* Arrow */}
          <div style={{ color: 'var(--accent)', fontSize: '18px', padding: '0 4px' }}>
            <div style={{
              background: 'var(--accent)', color: '#1a1a1a', padding: '2px 8px',
              borderRadius: '4px', fontSize: '11px', fontWeight: 'bold',
            }}>
              H
            </div>
          </div>

          {/* After */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>After</div>
            <div style={{ display: 'flex', gap: '4px', height: '48px', alignItems: 'flex-end' }}>
              <div style={{ width: '24px', background: 'var(--accent)', height: '24px', borderRadius: '3px 3px 0 0' }} />
              <div style={{ width: '24px', background: 'var(--accent)', height: '24px', borderRadius: '3px 3px 0 0' }} />
            </div>
            <div style={{ display: 'flex', gap: '4px', fontSize: '9px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              <span style={{ width: '24px', textAlign: 'center' }}>|0{'>'}</span>
              <span style={{ width: '24px', textAlign: 'center' }}>|1{'>'}</span>
            </div>
          </div>
        </div>
        <p style={{ fontSize: '11px', color: 'var(--text-secondary)', textAlign: 'center' }}>
          100% |0{'>'} becomes 50% |0{'>'} + 50% |1{'>'}
        </p>
      </>
    ),
  },
  {
    title: 'Try It Yourself!',
    content: (
      <>
        <p style={{ marginBottom: '12px' }}>
          Your circuit is ready with 1 qubit. Here's what to do:
        </p>
        <ol style={{ paddingLeft: '20px', margin: '0 0 12px 0', lineHeight: '1.8' }}>
          <li>Click the <strong style={{ color: '#c8ad7f' }}>H</strong> gate button in the palette</li>
          <li>Click on the <strong>q0 wire</strong> in the circuit diagram</li>
          <li>Watch the histogram change to 50/50!</li>
          <li>Check the <strong>Bloch sphere</strong> — the arrow moves sideways</li>
        </ol>
        <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
          Hover over any gate for a plain-English explanation. Look for the <strong style={{ color: 'var(--accent)' }}>?</strong> icons next to each panel for more help.
          You can toggle Learning Mode on/off in the header anytime.
        </p>
      </>
    ),
  },
];

export default function OnboardingModal({ onComplete }: Props) {
  const { hasSeenOnboarding, markOnboardingComplete } = useLearning();
  const [step, setStep] = useState(0);
  const [visible, setVisible] = useState(!hasSeenOnboarding);

  useEffect(() => {
    if (!visible) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowRight' || e.key === 'Enter') advance();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  });

  if (!visible) return null;

  const isLast = step === STEPS.length - 1;
  const current = STEPS[step];

  function close() {
    setVisible(false);
    markOnboardingComplete();
    onComplete();
  }

  function advance() {
    if (isLast) {
      close();
    } else {
      setStep(s => s + 1);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)' }}
    >
      <div
        className="rounded-xl p-6 flex flex-col gap-4"
        style={{
          maxWidth: '460px',
          width: '90%',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          boxShadow: '0 16px 48px rgba(0,0,0,0.5)',
        }}
      >
        {/* Title */}
        <h2 className="text-lg font-bold" style={{ color: 'var(--accent)' }}>
          {current.title}
        </h2>

        {/* Content */}
        <div className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
          {current.content}
        </div>

        {/* Footer: dots + buttons */}
        <div className="flex items-center justify-between pt-2" style={{ borderTop: '1px solid var(--border)' }}>
          {/* Step dots */}
          <div className="flex gap-1.5">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className="rounded-full transition-all"
                style={{
                  width: i === step ? '16px' : '6px',
                  height: '6px',
                  background: i === step ? 'var(--accent)' : i < step ? 'var(--accent)' : 'var(--border)',
                  opacity: i === step ? 1 : i < step ? 0.5 : 0.3,
                }}
              />
            ))}
          </div>

          <div className="flex gap-2">
            {!isLast && (
              <button
                onClick={close}
                className="px-3 py-1.5 rounded text-xs"
                style={{ color: 'var(--text-secondary)', background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}
              >
                Skip tour
              </button>
            )}
            <button
              onClick={advance}
              className="px-4 py-1.5 rounded text-xs font-bold"
              style={{ background: 'var(--accent)', color: '#1a1a1a' }}
            >
              {isLast ? "Got it, let's go!" : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
