import { useState } from 'react';
import HelpBubble from './HelpBubble';
import { useLearning } from '../contexts/LearningContext';

interface Props {
  probabilities: number[];
  labels: string[];
  stateReal: number[];
  stateImag: number[];
}

export default function StateTable({ probabilities, labels, stateReal, stateImag }: Props) {
  const [showAll, setShowAll] = useState(false);
  const { learningMode } = useLearning();
  const threshold = 1e-6;

  const rows = probabilities
    .map((p, i) => ({
      index: i,
      label: labels[i],
      prob: p,
      real: stateReal[i],
      imag: stateImag[i],
      amplitude: Math.sqrt(stateReal[i] ** 2 + stateImag[i] ** 2),
      phase: Math.atan2(stateImag[i], stateReal[i]),
    }))
    .filter(r => showAll || r.prob > threshold);

  const formatComplex = (re: number, im: number) => {
    if (Math.abs(re) < 1e-10 && Math.abs(im) < 1e-10) return '0';
    const rStr = Math.abs(re) > 1e-10 ? re.toFixed(4) : '';
    const iStr = Math.abs(im) > 1e-10
      ? `${im >= 0 && rStr ? '+' : ''}${im.toFixed(4)}i`
      : '';
    return `${rStr}${iStr}` || '0';
  };

  const phaseColor = (phase: number) => {
    const hue = ((phase + Math.PI) / (2 * Math.PI)) * 360;
    return `hsl(${hue}, 70%, 60%)`;
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>
            State Vector ({rows.length} states)
          </h3>
          {learningMode && (
            <HelpBubble title="State Vector">
              The state vector shows the full mathematical description of your quantum system.
              Each row is a possible outcome. The "amplitude" is a complex number whose squared magnitude gives the probability.
              The "phase" is the angle of the complex number — it matters for interference
              even though it doesn't affect individual measurement probabilities.
            </HelpBubble>
          )}
        </div>
        <button
          onClick={() => setShowAll(!showAll)}
          className="text-xs px-2 py-1 rounded"
          style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
        >
          {showAll ? 'Non-zero only' : 'Show all'}
        </button>
      </div>

      <div className="overflow-auto rounded-lg" style={{ maxHeight: '300px', border: '1px solid var(--border)' }}>
        <table className="w-full text-xs" style={{ borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--bg-tertiary)', position: 'sticky', top: 0, zIndex: 1 }}>
              <th className="px-3 py-2 text-left" style={{ color: 'var(--text-secondary)' }}>State</th>
              <th className="px-3 py-2 text-right" style={{ color: 'var(--text-secondary)' }}>Amplitude</th>
              <th className="px-3 py-2 text-right" style={{ color: 'var(--text-secondary)' }}>Probability</th>
              <th className="px-3 py-2 text-center" style={{ color: 'var(--text-secondary)' }}>Phase</th>
              <th className="px-3 py-2 text-left" style={{ color: 'var(--text-secondary)' }}>Bar</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.index}
                className="hover:opacity-80"
                style={{ borderTop: '1px solid var(--border)', background: 'var(--bg-secondary)' }}
              >
                <td className="px-3 py-1.5 font-bold" style={{ color: 'var(--accent)' }}>
                  {r.label}
                </td>
                <td className="px-3 py-1.5 text-right font-mono" style={{ color: 'var(--text-primary)' }}>
                  {formatComplex(r.real, r.imag)}
                </td>
                <td className="px-3 py-1.5 text-right font-mono" style={{ color: 'var(--text-primary)' }}>
                  {(r.prob * 100).toFixed(2)}%
                </td>
                <td className="px-3 py-1.5 text-center">
                  {r.prob > threshold && (
                    <div className="flex items-center justify-center gap-1">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ background: phaseColor(r.phase) }}
                      />
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {(r.phase * 180 / Math.PI).toFixed(0)}°
                      </span>
                    </div>
                  )}
                </td>
                <td className="px-3 py-1.5" style={{ minWidth: '100px' }}>
                  <div
                    className="h-3 rounded"
                    style={{
                      width: `${r.prob * 100}%`,
                      background: `linear-gradient(to right, var(--accent), var(--accent-hover))`,
                      minWidth: r.prob > threshold ? '2px' : '0',
                    }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
