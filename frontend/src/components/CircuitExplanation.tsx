import type { GateStep, Snapshot } from '../types/quantum';
import { getGateEducation } from '../data/gateEducation';
import { GATE_PALETTE } from '../types/quantum';

interface Props {
  steps: GateStep[];
  nQubits: number;
  snapshots: Snapshot[];
  currentStep: number;
}

function gateColor(name: string): string {
  return GATE_PALETTE.find(g => g.name === name)?.color || '#c8ad7f';
}

function gateLabel(name: string): string {
  return GATE_PALETTE.find(g => g.name === name)?.label || name;
}

function topProbabilities(probs: number[], nQubits: number, max: number): string {
  const labels = Array.from({ length: probs.length }, (_, i) =>
    `|${i.toString(2).padStart(nQubits, '0')}>`
  );
  const entries = probs
    .map((p, i) => ({ p, label: labels[i] }))
    .filter(e => e.p > 0.005)
    .sort((a, b) => b.p - a.p)
    .slice(0, max);

  return entries.map(e => `${e.label} = ${(e.p * 100).toFixed(1)}%`).join(', ');
}

function describeStep(step: GateStep, nQubits: number): string {
  const edu = getGateEducation(step.gate);
  const label = gateLabel(step.gate);
  const target = step.target !== undefined ? `q${step.target}` : '';
  const control = step.control !== undefined ? `q${step.control}` : '';
  const controls = step.controls ? step.controls.map(c => `q${c}`).join(', ') : '';

  let action = `Apply ${label} to ${target}`;
  if (step.control !== undefined) {
    action = `Apply ${label} with control ${control} and target ${target}`;
  } else if (step.controls) {
    action = `Apply ${label} with controls ${controls} and target ${target}`;
  }

  if (step.angle !== undefined) {
    const deg = ((step.angle * 180) / Math.PI).toFixed(0);
    action += ` (${deg} degrees)`;
  }

  const explanation = edu ? ` — ${edu.plainEnglish}` : '';
  return `${action}${explanation}`;
}

export default function CircuitExplanation({ steps, nQubits, snapshots, currentStep }: Props) {
  if (steps.length === 0) return null;

  return (
    <div className="flex flex-col gap-1.5">
      <h3 className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>
        What's Happening
      </h3>

      <div className="flex flex-col gap-1">
        {steps.map((step, i) => {
          const isCurrent = i + 1 === currentStep; // snapshots[0] is init, so step i corresponds to snapshot i+1
          const color = gateColor(step.gate);
          // snapshot index: init is 0, so gate i maps to snapshot i+1
          const snapIndex = i + 1;
          const snap = snapIndex < snapshots.length ? snapshots[snapIndex] : null;

          return (
            <div
              key={i}
              className="flex gap-2 rounded px-2.5 py-1.5 text-xs transition-all"
              style={{
                background: isCurrent ? `${color}15` : 'transparent',
                borderLeft: `3px solid ${isCurrent ? color : 'var(--border)'}`,
                opacity: i + 1 > currentStep ? 0.4 : 1,
              }}
            >
              <span className="shrink-0 font-bold" style={{ color, minWidth: '16px' }}>
                {i + 1}
              </span>
              <div className="flex flex-col gap-0.5">
                <span style={{ color: 'var(--text-primary)' }}>
                  {describeStep(step, nQubits)}
                </span>
                {snap && i + 1 <= currentStep && (
                  <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                    After: {topProbabilities(snap.probabilities, nQubits, 4)}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
