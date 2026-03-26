import { useState, useEffect, useCallback, useMemo } from 'react';
import CircuitBuilder from './components/CircuitBuilder';
import Histogram from './components/Histogram';
import StateTable from './components/StateTable';
import BlochSphere from './components/BlochSphere';
import TimelinePlayer from './components/TimelinePlayer';
import OnboardingModal from './components/OnboardingModal';
import CircuitExplanation from './components/CircuitExplanation';
import HelpBubble from './components/HelpBubble';
import ChatPanel from './components/ChatPanel';
import { simulate, getHardware, getPresets, healthCheck } from './api/client';
import type { GateStep, SimulationResponse, HardwareInfo, PresetCircuit, NoiseConfig, BlochVector } from './types/quantum';

type ActiveTab = 'circuit' | 'chat';
import { useLearning } from './contexts/LearningContext';
import { useUndoRedo } from './hooks/useUndoRedo';

function computeBlochFromSnapshot(stateReal: number[], stateImag: number[], nQubits: number): BlochVector[] {
  // Quick client-side Bloch vector from snapshot state (partial trace)
  const size = stateReal.length;
  const vectors: BlochVector[] = [];

  for (let qubit = 0; qubit < nQubits; qubit++) {
    const bit = nQubits - 1 - qubit;
    // Compute reduced density matrix elements
    let rho00 = 0, rho01r = 0, rho01i = 0, rho10r = 0, rho10i = 0, rho11 = 0;

    for (let i = 0; i < size; i++) {
      const bi = (i >> bit) & 1;
      const re_i = stateReal[i];
      const im_i = stateImag[i];

      for (let j = 0; j < size; j++) {
        const bj = (j >> bit) & 1;
        // Check other bits match
        const mask = ~(1 << bit) & ((1 << nQubits) - 1);
        if ((i & mask) !== (j & mask)) continue;

        const re_j = stateReal[j];
        const im_j = stateImag[j];
        // ψ_i * conj(ψ_j)
        const prodR = re_i * re_j + im_i * im_j;
        const prodI = im_i * re_j - re_i * im_j;

        if (bi === 0 && bj === 0) rho00 += prodR;
        if (bi === 0 && bj === 1) { rho01r += prodR; rho01i += prodI; }
        if (bi === 1 && bj === 0) { rho10r += prodR; rho10i += prodI; }
        if (bi === 1 && bj === 1) rho11 += prodR;
      }
    }

    vectors.push({
      qubit,
      x: 2 * rho01r,
      y: 2 * rho10i,
      z: rho00 - rho11,
    });
  }
  return vectors;
}

function App() {
  const [nQubits, setNQubits] = useState(2);
  const stepsUndo = useUndoRedo<GateStep[]>([
    { gate: 'H', target: 0 },
    { gate: 'CNOT', control: 0, target: 1 },
  ]);
  const steps = stepsUndo.current;
  const setSteps = stepsUndo.set;
  const [shots, setShots] = useState<number>(0);
  const [noise, setNoise] = useState<NoiseConfig | null>(null);

  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [presets, setPresets] = useState<PresetCircuit[]>([]);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [autoRun, setAutoRun] = useState(true);

  const [showState, setShowState] = useState(true);
  const [showBloch, setShowBloch] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>('circuit');

  // Learning mode
  const { learningMode, toggleLearningMode } = useLearning();

  const handleOnboardingComplete = useCallback(() => {
    setNQubits(1);
    stepsUndo.reset([]);
    setResult(null);
    setTimelineStep(-1);
  }, [stepsUndo]);

  // Chat / LLM callbacks
  const handleCircuitGenerated = useCallback((nq: number, newSteps: GateStep[]) => {
    setNQubits(nq);
    stepsUndo.reset(newSteps);
    setTimelineStep(-1);
    setActiveTab('circuit');
  }, [stepsUndo]);

  const handleChatSimulationResult = useCallback((res: SimulationResponse) => {
    setResult(res);
    setTimelineStep(res.snapshots.length - 1);
  }, []);

  // Timeline state
  const [timelineStep, setTimelineStep] = useState(-1); // -1 = show final result

  useEffect(() => {
    (async () => {
      const ok = await healthCheck();
      setConnected(ok);
      if (ok) {
        const [hw, pr] = await Promise.all([getHardware(), getPresets()]);
        setHardware(hw);
        setPresets(pr);
      }
    })();
  }, []);

  // Clear results when circuit is emptied
  useEffect(() => {
    if (steps.length === 0) {
      setResult(null);
      setTimelineStep(-1);
    }
  }, [steps]);

  const runSimulation = useCallback(async () => {
    if (!connected || steps.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const res = await simulate({
        n_qubits: nQubits,
        steps,
        noise: noise || undefined,
        shots: shots > 0 ? shots : undefined,
        save_intermediate: true,
      });
      setResult(res);
      setTimelineStep(res.snapshots.length - 1); // show final by default
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Simulation failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [connected, nQubits, steps, noise, shots]);

  useEffect(() => {
    if (!autoRun || !connected) return;
    const timer = setTimeout(runSimulation, 300);
    return () => clearTimeout(timer);
  }, [autoRun, connected, runSimulation]);

  const loadPreset = (preset: PresetCircuit) => {
    setNQubits(preset.n_qubits);
    stepsUndo.reset(preset.steps);
    setTimelineStep(-1);
  };

  const presetsByCategory = presets.reduce<Record<string, PresetCircuit[]>>((acc, p) => {
    (acc[p.category] = acc[p.category] || []).push(p);
    return acc;
  }, {});

  // Compute display data based on timeline step
  const displayData = useMemo(() => {
    if (!result) return null;

    const snapshots = result.snapshots;
    const step = timelineStep >= 0 && timelineStep < snapshots.length
      ? timelineStep
      : snapshots.length - 1;
    const snap = snapshots[step];

    if (!snap) return null;

    // Compute Bloch vectors from snapshot state (for intermediate steps)
    const isFinal = step === snapshots.length - 1;
    // For small qubit counts, compute Bloch vectors client-side
    const blochVectors = isFinal
      ? result.bloch_vectors
      : nQubits <= 8
        ? computeBlochFromSnapshot(snap.state_real, snap.state_imag, nQubits)
        : result.bloch_vectors; // fallback to final for large

    return {
      probabilities: snap.probabilities,
      labels: result.labels,
      stateReal: snap.state_real,
      stateImag: snap.state_imag,
      blochVectors,
      isFinal,
      stepIndex: step,
    };
  }, [result, timelineStep, nQubits]);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      {/* Onboarding */}
      <OnboardingModal onComplete={handleOnboardingComplete} />

      {/* Header */}
      <header
        className="flex items-center justify-between px-6 py-3"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-secondary)' }}
      >
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--accent)' }}>
            QuantumLens
          </h1>
          <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
            v0.1
          </span>
        </div>
        <div className="flex items-center gap-4">
          {/* AI Chat toggle */}
          <button
            onClick={() => setShowChat(prev => !prev)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-all cursor-pointer"
            style={{
              background: showChat ? 'var(--accent)' : 'var(--bg-tertiary)',
              color: showChat ? '#1a1a1a' : 'var(--text-secondary)',
              border: `1px solid ${showChat ? 'var(--accent)' : 'var(--border)'}`,
            }}
            title="Ask AI to generate quantum circuits from natural language"
          >
            <span style={{ fontSize: '12px' }}>&#x1F9E0;</span>
            AI Chat
          </button>

          {/* Learning mode toggle */}
          <button
            onClick={toggleLearningMode}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-all cursor-pointer"
            style={{
              background: learningMode ? 'var(--accent)' : 'var(--bg-tertiary)',
              color: learningMode ? '#1a1a1a' : 'var(--text-secondary)',
              border: `1px solid ${learningMode ? 'var(--accent)' : 'var(--border)'}`,
            }}
            title={learningMode ? 'Learning mode ON — showing educational hints' : 'Learning mode OFF'}
          >
            <span style={{ fontSize: '12px' }}>&#x1F393;</span>
            Learn
          </button>

          <div className="flex items-center gap-2 text-xs">
            <div
              className="w-2 h-2 rounded-full"
              style={{ background: connected ? 'var(--success)' : connected === false ? 'var(--danger)' : 'var(--warning)' }}
            />
            <span style={{ color: 'var(--text-secondary)' }}>
              {connected ? 'Connected' : connected === false ? 'Disconnected' : 'Connecting...'}
            </span>
          </div>
          {hardware && (
            <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
              {hardware.gpu.available
                ? `GPU: ${hardware.gpu.name} (${hardware.gpu.vram_gb}GB)`
                : `CPU: ${hardware.cpu.threads} threads, ${hardware.cpu.ram_gb.toFixed(0)}GB RAM`}
            </span>
          )}
        </div>
      </header>

      <div className="flex-1 flex" style={{ minHeight: 0 }}>
        {/* Left sidebar */}
        <aside
          className="w-64 shrink-0 overflow-y-auto p-4 flex flex-col gap-4"
          style={{ borderRight: '1px solid var(--border)', background: 'var(--bg-secondary)' }}
        >
          <div>
            <h2 className="text-xs font-bold mb-2 uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
              Presets
            </h2>
            {Object.entries(presetsByCategory).map(([category, circuits]) => (
              <div key={category} className="mb-3">
                <div className="text-xs mb-1 font-bold" style={{ color: 'var(--accent)' }}>{category}</div>
                {circuits.map((preset, i) => (
                  <button
                    key={i}
                    onClick={() => loadPreset(preset)}
                    className="w-full text-left px-2 py-1.5 rounded text-xs mb-0.5 hover:opacity-80 transition-opacity"
                    style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                    title={preset.description}
                  >
                    <div className="font-bold">{preset.name}</div>
                    <div className="mt-0.5 line-clamp-2" style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                      {preset.description}
                    </div>
                  </button>
                ))}
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-2">
            <h2 className="text-xs font-bold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
              Controls
            </h2>

            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input type="checkbox" checked={autoRun} onChange={e => setAutoRun(e.target.checked)} className="accent-amber-300" />
              <span style={{ color: 'var(--text-secondary)' }}>Auto-simulate</span>
            </label>

            <div className="flex items-center gap-2">
              <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Shots:</label>
              <input
                type="number" value={shots}
                onChange={e => setShots(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-20 px-2 py-1 rounded text-xs"
                style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
                min={0} max={100000}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Noise:</label>
              <select
                value={noise?.channel || ''}
                onChange={e => {
                  if (e.target.value) setNoise({ channel: e.target.value, probability: 0.01, gates: ['H', 'X', 'CNOT'] });
                  else setNoise(null);
                }}
                className="px-2 py-1 rounded text-xs"
                style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
              >
                <option value="">None</option>
                <option value="depolarising">Depolarising</option>
                <option value="amplitude_damping">Amplitude Damping</option>
                <option value="phase_damping">Phase Damping</option>
                <option value="bit_flip">Bit Flip</option>
                <option value="phase_flip">Phase Flip</option>
              </select>
              {noise && (
                <div className="flex items-center gap-2">
                  <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>p:</label>
                  <input type="range" min={0} max={0.5} step={0.001} value={noise.probability}
                    onChange={e => setNoise({ ...noise, probability: parseFloat(e.target.value) })} className="flex-1" />
                  <span className="text-xs w-12 text-right" style={{ color: 'var(--accent)' }}>
                    {(noise.probability * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>

            <button
              onClick={runSimulation}
              disabled={loading || !connected}
              className="px-4 py-2 rounded text-sm font-bold transition-all w-full"
              style={{ background: loading ? 'var(--bg-tertiary)' : 'var(--accent)', color: '#1a1a1a', opacity: loading || !connected ? 0.5 : 1 }}
            >
              {loading ? 'Simulating...' : 'Simulate'}
            </button>

            <div className="flex flex-col gap-1 mt-2">
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input type="checkbox" checked={showState} onChange={e => setShowState(e.target.checked)} className="accent-amber-300" />
                <span style={{ color: 'var(--text-secondary)' }}>State vector</span>
              </label>
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input type="checkbox" checked={showBloch} onChange={e => setShowBloch(e.target.checked)} className="accent-amber-300" />
                <span style={{ color: 'var(--text-secondary)' }}>Bloch sphere</span>
              </label>
            </div>
          </div>

          {result?.metadata && (
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              <div>Device: {String(result.metadata.device)}</div>
              <div>Precision: {String(result.metadata.precision)}</div>
              <div>Time: {String(result.metadata.simulation_time_ms)}ms</div>
              <div>Gates: {String(result.metadata.n_gates)}</div>
            </div>
          )}
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
          {error && (
            <div className="px-4 py-2 rounded text-sm"
              style={{ background: '#ef444422', border: '1px solid #ef444444', color: 'var(--danger)' }}>
              {error}
            </div>
          )}

          {connected === false && (
            <div className="px-4 py-3 rounded text-sm text-center"
              style={{ background: '#eab30822', border: '1px solid #eab30844', color: 'var(--warning)' }}>
              Backend not connected. Start the server:
              <code className="ml-2 px-2 py-0.5 rounded text-xs" style={{ background: 'var(--bg-tertiary)' }}>
                cd e:/quantu2 && source .venv/Scripts/activate && uvicorn server.app:app --reload
              </code>
            </div>
          )}

          {/* Circuit builder */}
          <section className="rounded-lg p-4" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-3">
              <h2 className="text-sm font-bold" style={{ color: 'var(--text-secondary)' }}>Circuit Builder</h2>
              {learningMode && (
                <HelpBubble title="Circuit Builder">
                  Build your quantum circuit here. Select a gate from the palette above, then click on a qubit wire to place it.
                  For two-qubit gates like CNOT, click the control qubit first, then the target. Click on an existing gate to remove it.
                </HelpBubble>
              )}
            </div>
            <CircuitBuilder
              nQubits={nQubits}
              steps={steps}
              snapshots={result?.snapshots}
              onStepsChange={setSteps}
              onNQubitsChange={setNQubits}
              onUndo={stepsUndo.undo}
              onRedo={stepsUndo.redo}
              canUndo={stepsUndo.canUndo}
              canRedo={stepsUndo.canRedo}
            />
          </section>

          {loading && (
            <div className="text-center py-4 text-sm" style={{ color: 'var(--accent)' }}>
              Simulating {nQubits} qubits, {steps.length} gates...
            </div>
          )}

          {/* Results */}
          {result && !loading && displayData && (
            <>
              {/* TIMELINE PLAYER */}
              {result.snapshots.length > 1 && (
                <section className="rounded-lg p-4" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                  <TimelinePlayer
                    snapshots={result.snapshots}
                    labels={result.labels}
                    currentStep={timelineStep >= 0 ? timelineStep : result.snapshots.length - 1}
                    onStepChange={setTimelineStep}
                  />
                </section>
              )}

              {/* Circuit explanation — learning mode */}
              {learningMode && steps.length > 0 && (
                <section className="rounded-lg p-4" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                  <CircuitExplanation
                    steps={steps}
                    nQubits={nQubits}
                    snapshots={result.snapshots}
                    currentStep={timelineStep >= 0 ? timelineStep : result.snapshots.length - 1}
                  />
                </section>
              )}

              {/* Probability histogram — shows current step */}
              <section className="rounded-lg p-4" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                <Histogram
                  probabilities={displayData.probabilities}
                  labels={displayData.labels}
                  counts={displayData.isFinal ? (result.counts || undefined) : undefined}
                  shots={displayData.isFinal && shots > 0 ? shots : undefined}
                />
              </section>

              {/* Bloch + State */}
              <div className={`grid gap-4 ${showBloch && showState ? 'grid-cols-2' : 'grid-cols-1'}`}>
                {showBloch && displayData.blochVectors.length > 0 && (
                  <section className="rounded-lg p-4" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                    <BlochSphere vectors={displayData.blochVectors} />
                  </section>
                )}

                {showState && (
                  <section className="rounded-lg p-4" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                    <StateTable
                      probabilities={displayData.probabilities}
                      labels={displayData.labels}
                      stateReal={displayData.stateReal}
                      stateImag={displayData.stateImag}
                    />
                  </section>
                )}
              </div>

              {result.measurement_result && (
                <div className="px-4 py-2 rounded text-sm text-center"
                  style={{ background: '#22c55e22', border: '1px solid #22c55e44', color: 'var(--success)' }}>
                  Measurement result: <span className="font-bold">|{result.measurement_result}⟩</span>
                </div>
              )}
            </>
          )}
        </main>

        {/* AI Chat Panel — right sidebar */}
        {showChat && (
          <aside
            className="w-80 shrink-0 overflow-hidden flex flex-col"
            style={{ borderLeft: '1px solid var(--border)', background: 'var(--bg-secondary)' }}
          >
            <ChatPanel
              onCircuitGenerated={handleCircuitGenerated}
              onSimulationResult={handleChatSimulationResult}
            />
          </aside>
        )}
      </div>
    </div>
  );
}

export default App;
