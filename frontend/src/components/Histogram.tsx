import HelpBubble from './HelpBubble';
import { useLearning } from '../contexts/LearningContext';

interface Props {
  probabilities: number[];
  labels: string[];
  counts?: Record<string, number>;
  shots?: number;
}

export default function Histogram({ probabilities, labels, counts, shots }: Props) {
  const { learningMode } = useLearning();
  const maxProb = Math.max(...probabilities, 0.001);

  // Filter to show only non-negligible states (> 0.1%)
  const significant = probabilities
    .map((p, i) => ({ prob: p, label: labels[i], index: i }))
    .filter(d => d.prob > 0.001)
    .sort((a, b) => b.prob - a.prob);

  const showAll = probabilities.length <= 32;
  const display = showAll
    ? probabilities.map((p, i) => ({ prob: p, label: labels[i], index: i }))
    : significant.slice(0, 32);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>
            Probability Distribution
          </h3>
          {learningMode && (
            <HelpBubble title="Probability Distribution">
              Each bar shows the probability of measuring that particular outcome.
              In quantum mechanics, we can only predict probabilities — the actual measurement result is random.
              Taller bars mean more likely outcomes. When you add "shots" (simulated measurements),
              you'll also see how many times each outcome actually occurred.
            </HelpBubble>
          )}
        </div>
        {!showAll && (
          <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            Showing top {display.length} of {probabilities.length} states
          </span>
        )}
      </div>

      <div className="flex items-end gap-px" style={{ height: '160px' }}>
        {display.map((d) => (
          <div
            key={d.index}
            className="flex-1 flex flex-col items-center justify-end group relative"
            style={{ minWidth: '8px', maxWidth: '40px', height: '100%' }}
          >
            {/* Tooltip */}
            <div className="absolute bottom-full mb-1 hidden group-hover:block z-10">
              <div
                className="px-2 py-1 rounded text-xs whitespace-nowrap"
                style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}
              >
                <div>{d.label}</div>
                <div style={{ color: 'var(--accent)' }}>{(d.prob * 100).toFixed(2)}%</div>
                {counts && (
                  <div style={{ color: 'var(--text-secondary)' }}>
                    {counts[d.label.replace(/[|⟩]/g, '')] || 0} / {shots}
                  </div>
                )}
              </div>
            </div>

            {/* Percentage label above bar */}
            {d.prob > 0.005 && display.length <= 16 && (
              <span
                className="text-xs font-bold mb-0.5"
                style={{ color: 'var(--accent)', fontSize: '9px' }}
              >
                {(d.prob * 100).toFixed(1)}%
              </span>
            )}

            {/* Bar */}
            <div
              className="w-full rounded-t transition-all"
              style={{
                height: `${Math.max((d.prob / maxProb) * 140, 1)}px`,
                background: d.prob > 0.01
                  ? `linear-gradient(to top, var(--accent), var(--accent-hover))`
                  : 'var(--border)',
                opacity: d.prob > 0.001 ? 1 : 0.3,
              }}
            />

            {/* Label */}
            {display.length <= 16 && (
              <span
                className="text-xs mt-1 rotate-45 origin-left whitespace-nowrap"
                style={{ color: 'var(--text-secondary)', fontSize: '9px' }}
              >
                {d.label.replace(/[|⟩]/g, '')}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Counts histogram if shots were provided */}
      {counts && (
        <div className="mt-2">
          <h3 className="text-sm font-bold mb-1" style={{ color: 'var(--text-secondary)' }}>
            Measurement Counts ({shots} shots)
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(counts)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 16)
              .map(([bitstring, count]) => (
                <div
                  key={bitstring}
                  className="px-2 py-1 rounded text-xs"
                  style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}
                >
                  <span style={{ color: 'var(--accent)' }}>|{bitstring}⟩</span>
                  <span className="ml-2" style={{ color: 'var(--text-primary)' }}>{count}</span>
                  <span className="ml-1" style={{ color: 'var(--text-secondary)' }}>
                    ({((count / (shots || 1)) * 100).toFixed(1)}%)
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
