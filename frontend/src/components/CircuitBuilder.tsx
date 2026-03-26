import { useState, useRef, useEffect, useCallback } from 'react';
import type { GateStep, GateInfo, Snapshot } from '../types/quantum';
import { GATE_PALETTE } from '../types/quantum';
import GateTooltip from './GateTooltip';

interface Props {
  nQubits: number;
  steps: GateStep[];
  snapshots?: Snapshot[];
  onStepsChange: (steps: GateStep[]) => void;
  onNQubitsChange: (n: number) => void;
  onUndo?: () => void;
  onRedo?: () => void;
  canUndo?: boolean;
  canRedo?: boolean;
}

// Layout
const WIRE_SPACING = 44;
const COL_WIDTH = 56;
const LABEL_WIDTH = 44;
const GATE_SIZE = 32;
const PADDING_TOP = 12;
const PADDING_RIGHT = 24;
const STATE_COL_WIDTH = 40;
const DRAG_THRESHOLD = 5;

// --- Helpers (module-level for stability) ---

function parseAngle(s: string): number {
  const cleaned = s.trim().replace(/pi/gi, 'π');
  if (cleaned.includes('π')) {
    const parts = cleaned.split('π');
    const before = parts[0].replace(/[*/\s]/g, '') || '1';
    const after = parts[1]?.replace(/[/\s]/g, '') || '';
    let num = before === '-' ? -1 : parseFloat(before) || 1;
    if (after) num /= parseFloat(after);
    return num * Math.PI;
  }
  return parseFloat(cleaned) || 0;
}

function gateColor(name: string): string {
  return GATE_PALETTE.find(g => g.name === name)?.color || '#c8ad7f';
}

function gateLabel(name: string): string {
  return GATE_PALETTE.find(g => g.name === name)?.label || name;
}

function stepLabel(step: GateStep): string {
  const lbl = gateLabel(step.gate);
  if (step.angle != null) {
    const deg = ((step.angle * 180) / Math.PI).toFixed(0);
    return `${lbl}(${deg}°)`;
  }
  return lbl;
}

function getStepQubits(step: GateStep): number[] {
  const qs: number[] = [];
  if (step.controls) qs.push(...step.controls);
  if (step.control !== undefined) qs.push(step.control);
  if (step.target !== undefined) qs.push(step.target);
  return qs;
}

function qubitProb1(probs: number[], qubit: number, nQubits: number): number {
  let p = 0;
  const bit = nQubits - 1 - qubit;
  for (let i = 0; i < probs.length; i++) {
    if ((i >> bit) & 1) p += probs[i];
  }
  return p;
}

// --- Types ---

interface DragInfo {
  gate: GateInfo;
  fromIndex: number | null; // null = from palette
}

interface DropZone {
  wire: number;
  insertAt: number;
}

interface DragStart {
  x: number;
  y: number;
  gate: GateInfo;
  fromIndex: number | null;
  started: boolean;
}

// --- Component ---

export default function CircuitBuilder({
  nQubits, steps, snapshots, onStepsChange, onNQubitsChange,
  onUndo, onRedo, canUndo, canRedo,
}: Props) {
  // Click-based placement state
  const [selectedGate, setSelectedGate] = useState<GateInfo | null>(null);
  const [pendingControl, setPendingControl] = useState<number | null>(null);
  const [pendingControls, setPendingControls] = useState<number[]>([]);
  const [angleInput, setAngleInput] = useState('π/2');

  // Drag state
  const [dragging, setDragging] = useState<DragInfo | null>(null);
  const [ghostPos, setGhostPos] = useState<{ x: number; y: number } | null>(null);
  const [dropZone, setDropZone] = useState<DropZone | null>(null);

  const svgContainerRef = useRef<HTMLDivElement>(null);
  const dragStartRef = useRef<DragStart | null>(null);
  const justDraggedRef = useRef(false);

  // SVG coordinates
  const wireY = (q: number) => PADDING_TOP + q * WIRE_SPACING + WIRE_SPACING / 2;
  const colX = (i: number) => LABEL_WIDTH + i * COL_WIDTH + COL_WIDTH / 2;

  const hasInlineState = !!(snapshots && snapshots.length > 0 && steps.length > 0);
  const svgWidth = LABEL_WIDTH + Math.max(steps.length, 1) * COL_WIDTH
    + (hasInlineState ? STATE_COL_WIDTH : 0) + PADDING_RIGHT;
  const svgHeight = PADDING_TOP + nQubits * WIRE_SPACING + 4;
  const stateColX = LABEL_WIDTH + steps.length * COL_WIDTH + STATE_COL_WIDTH / 2;

  // Drop zone computation
  const computeDropZone = useCallback((clientX: number, clientY: number): DropZone | null => {
    if (!svgContainerRef.current) return null;
    const rect = svgContainerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;

    if (x < LABEL_WIDTH - 10 || y < 0 || y > svgHeight) return null;

    const wire = Math.round((y - PADDING_TOP - WIRE_SPACING / 2) / WIRE_SPACING);
    const insertAt = Math.round((x - LABEL_WIDTH) / COL_WIDTH);

    return {
      wire: Math.max(0, Math.min(nQubits - 1, wire)),
      insertAt: Math.max(0, Math.min(steps.length, insertAt)),
    };
  }, [nQubits, steps.length, svgHeight]);

  // Ref for mutable state accessed by document listeners
  const stateRef = useRef({ dragging, dropZone, steps, angleInput, onStepsChange, computeDropZone });
  stateRef.current = { dragging, dropZone, steps, angleInput, onStepsChange, computeDropZone };

  // --- Drag system (document-level listeners, added once) ---
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const ds = dragStartRef.current;
      if (!ds) return;

      // Check threshold
      if (!ds.started) {
        const dx = e.clientX - ds.x;
        const dy = e.clientY - ds.y;
        if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) {
          ds.started = true;
          setDragging({ gate: ds.gate, fromIndex: ds.fromIndex });
          setSelectedGate(null);
          setPendingControl(null);
          setPendingControls([]);
        }
      }

      if (ds.started) {
        setGhostPos({ x: e.clientX, y: e.clientY });
        setDropZone(stateRef.current.computeDropZone(e.clientX, e.clientY));
      }
    };

    const handleMouseUp = () => {
      const ds = dragStartRef.current;
      if (!ds) return;

      const { dragging: d, dropZone: dz, steps: s, angleInput: a, onStepsChange: onChange } = stateRef.current;

      if (!ds.started) {
        // Click (not drag)
        if (ds.fromIndex === null) {
          // Palette click → select gate
          setSelectedGate(ds.gate);
          setPendingControl(null);
          setPendingControls([]);
        }
        // Circuit gate click → handled by SVG onClick
      } else if (d && dz) {
        // Successful drop
        justDraggedRef.current = true;
        setTimeout(() => { justDraggedRef.current = false; }, 50);

        const newSteps = [...s];

        if (d.gate.qubits === 1) {
          const step: GateStep = { gate: d.gate.name, target: dz.wire };
          if (d.gate.parametric) step.angle = parseAngle(a);

          if (d.fromIndex !== null) {
            // Reorder: remove old, insert at new position
            newSteps.splice(d.fromIndex, 1);
            const adj = d.fromIndex < dz.insertAt ? dz.insertAt - 1 : dz.insertAt;
            newSteps.splice(adj, 0, step);
          } else {
            // New gate from palette
            newSteps.splice(dz.insertAt, 0, step);
          }
          onChange(newSteps);
        } else if (d.fromIndex !== null) {
          // Reorder multi-qubit gate (keep qubit assignments, move column)
          const [gate] = newSteps.splice(d.fromIndex, 1);
          const adj = d.fromIndex < dz.insertAt ? dz.insertAt - 1 : dz.insertAt;
          newSteps.splice(adj, 0, gate);
          onChange(newSteps);
        } else {
          // New multi-qubit gate from palette → fall back to click flow
          setSelectedGate(d.gate);
          setPendingControl(null);
          setPendingControls([]);
        }
      }

      // Clean up
      dragStartRef.current = null;
      setDragging(null);
      setGhostPos(null);
      setDropZone(null);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  // Keyboard: undo/redo
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          onRedo?.();
        } else {
          onUndo?.();
        }
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        onRedo?.();
      }
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onUndo, onRedo]);

  // --- Start drag ---
  const handleDragStart = useCallback((
    e: React.MouseEvent, gate: GateInfo, fromIndex: number | null
  ) => {
    if (e.button !== 0) return;
    dragStartRef.current = { x: e.clientX, y: e.clientY, gate, fromIndex, started: false };
  }, []);

  // --- Click-based gate placement ---
  const addGate = (targetQubit: number) => {
    if (!selectedGate) return;
    const gate = selectedGate;

    if (gate.qubits === 3) {
      if (pendingControls.length < 2) {
        setPendingControls([...pendingControls, targetQubit]);
        return;
      }
      onStepsChange([...steps, { gate: gate.name, controls: pendingControls, target: targetQubit }]);
      setPendingControls([]);
      setSelectedGate(null);
      return;
    }

    if (gate.qubits === 2) {
      if (pendingControl === null) {
        setPendingControl(targetQubit);
        return;
      }
      onStepsChange([...steps, { gate: gate.name, control: pendingControl, target: targetQubit }]);
      setPendingControl(null);
      setSelectedGate(null);
      return;
    }

    const step: GateStep = { gate: gate.name, target: targetQubit };
    if (gate.parametric) step.angle = parseAngle(angleInput);
    onStepsChange([...steps, step]);
  };

  const removeStep = (index: number) => {
    if (justDraggedRef.current) return;
    onStepsChange(steps.filter((_, i) => i !== index));
  };

  const clearCircuit = () => {
    onStepsChange([]);
    setSelectedGate(null);
    setPendingControl(null);
    setPendingControls([]);
  };

  // Final snapshot probabilities for inline state
  const finalProbs = snapshots && snapshots.length > 0
    ? snapshots[snapshots.length - 1].probabilities
    : null;

  return (
    <div className="flex flex-col gap-3">
      {/* Toolbar */}
      <div className="flex items-center gap-3">
        <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>Qubits</label>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onNQubitsChange(Math.max(1, nQubits - 1))}
            className="w-7 h-7 rounded text-sm font-bold"
            style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}
          >−</button>
          <span className="w-8 text-center text-lg font-bold" style={{ color: 'var(--accent)' }}>
            {nQubits}
          </span>
          <button
            onClick={() => onNQubitsChange(Math.min(32, nQubits + 1))}
            className="w-7 h-7 rounded text-sm font-bold"
            style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}
          >+</button>
        </div>

        {/* Undo / Redo */}
        {(onUndo || onRedo) && (
          <div className="flex items-center gap-1 ml-2">
            <button
              onClick={onUndo}
              disabled={!canUndo}
              className="w-7 h-7 rounded text-sm"
              style={{
                background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
                opacity: canUndo ? 1 : 0.3,
              }}
              title="Undo (Ctrl+Z)"
            >↩</button>
            <button
              onClick={onRedo}
              disabled={!canRedo}
              className="w-7 h-7 rounded text-sm"
              style={{
                background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
                opacity: canRedo ? 1 : 0.3,
              }}
              title="Redo (Ctrl+Shift+Z)"
            >↪</button>
          </div>
        )}

        <button
          onClick={clearCircuit}
          className="ml-auto px-3 py-1 rounded text-xs"
          style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)', color: 'var(--danger)' }}
        >Clear</button>
      </div>

      {/* Gate palette — drag or click */}
      <div className="flex flex-wrap gap-1">
        {GATE_PALETTE.filter(g => g.qubits <= nQubits).map((gate) => (
          <GateTooltip key={gate.name} gate={gate}>
            <button
              onMouseDown={(e) => handleDragStart(e, gate, null)}
              className="px-2 py-1 rounded text-xs font-bold transition-all select-none"
              style={{
                background: selectedGate?.name === gate.name ? gate.color : 'var(--bg-tertiary)',
                border: `1px solid ${selectedGate?.name === gate.name ? gate.color : 'var(--border)'}`,
                color: selectedGate?.name === gate.name ? '#fff' : gate.color,
                cursor: 'grab',
              }}
            >
              {gate.label}
            </button>
          </GateTooltip>
        ))}
      </div>

      {/* Angle input */}
      {(selectedGate?.parametric || dragging?.gate.parametric) && (
        <div className="flex items-center gap-2">
          <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Angle:</label>
          <input
            value={angleInput}
            onChange={(e) => setAngleInput(e.target.value)}
            className="px-2 py-1 rounded text-xs w-24"
            style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
            placeholder="π/2"
          />
          <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            = {(parseAngle(angleInput) * 180 / Math.PI).toFixed(1)}°
          </span>
        </div>
      )}

      {/* Status prompt */}
      {selectedGate && !dragging && (
        <div className="text-xs px-2 py-1 rounded" style={{ background: 'var(--bg-tertiary)', color: 'var(--accent)' }}>
          {selectedGate.qubits === 1 && `Drag or click a qubit wire to place ${selectedGate.label}`}
          {selectedGate.qubits === 2 && pendingControl === null && `Click CONTROL qubit for ${selectedGate.label}`}
          {selectedGate.qubits === 2 && pendingControl !== null && `Click TARGET qubit for ${selectedGate.label} (control: q${pendingControl})`}
          {selectedGate.qubits === 3 && pendingControls.length === 0 && `Click FIRST control for ${selectedGate.label}`}
          {selectedGate.qubits === 3 && pendingControls.length === 1 && `Click SECOND control for ${selectedGate.label}`}
          {selectedGate.qubits === 3 && pendingControls.length === 2 && `Click TARGET qubit for ${selectedGate.label}`}
        </div>
      )}

      {dragging && (
        <div className="text-xs px-2 py-1 rounded" style={{ background: 'var(--bg-tertiary)', color: 'var(--accent)' }}>
          {dragging.fromIndex !== null
            ? `Drag ${dragging.gate.label} to a new position`
            : dragging.gate.qubits === 1
              ? `Drop ${dragging.gate.label} on a qubit wire`
              : `Drop to select ${dragging.gate.label}, then click control → target`}
        </div>
      )}

      {/* ========== CIRCUIT DIAGRAM ========== */}
      <div
        ref={svgContainerRef}
        className="rounded-lg overflow-x-auto"
        style={{
          background: 'var(--bg-primary)',
          border: `2px solid ${dropZone ? 'var(--accent)' : 'var(--border)'}`,
          transition: 'border-color 0.15s',
        }}
      >
        <svg
          width={svgWidth}
          height={svgHeight}
          style={{ display: 'block', minWidth: '100%' }}
        >
          {/* Drop zone highlights */}
          {dropZone && dragging && (
            <>
              {/* Wire highlight */}
              <rect
                x={0} y={wireY(dropZone.wire) - WIRE_SPACING / 2}
                width={svgWidth} height={WIRE_SPACING}
                fill={gateColor(dragging.gate.name)} opacity={0.08}
              />
              {/* Column insertion line */}
              <line
                x1={LABEL_WIDTH + dropZone.insertAt * COL_WIDTH}
                y1={wireY(0) - WIRE_SPACING / 2}
                x2={LABEL_WIDTH + dropZone.insertAt * COL_WIDTH}
                y2={wireY(nQubits - 1) + WIRE_SPACING / 2}
                stroke={gateColor(dragging.gate.name)}
                strokeWidth={2} strokeDasharray="4 4" opacity={0.5}
              />
              {/* Ghost gate at drop point */}
              <rect
                x={LABEL_WIDTH + dropZone.insertAt * COL_WIDTH - GATE_SIZE / 2}
                y={wireY(dropZone.wire) - GATE_SIZE / 2}
                width={GATE_SIZE} height={GATE_SIZE} rx={4}
                fill={gateColor(dragging.gate.name)} opacity={0.3}
              />
              <text
                x={LABEL_WIDTH + dropZone.insertAt * COL_WIDTH}
                y={wireY(dropZone.wire) + 1}
                textAnchor="middle" dominantBaseline="middle"
                fill="#fff" fontSize={10} fontFamily="monospace" fontWeight="bold"
                opacity={0.5}
              >
                {dragging.gate.label}
              </text>
            </>
          )}

          {/* Qubit labels + wires */}
          {Array.from({ length: nQubits }, (_, q) => {
            const y = wireY(q);
            return (
              <g key={`wire-${q}`}>
                <text
                  x={LABEL_WIDTH - 6} y={y + 1}
                  textAnchor="end" fill="#908880"
                  fontSize={11} fontFamily="monospace" fontWeight="bold"
                >
                  q{q}
                </text>
                <line
                  x1={LABEL_WIDTH} y1={y}
                  x2={svgWidth - 4} y2={y}
                  stroke="#2c2c2c" strokeWidth={1.5}
                />
                {/* Clickable zone */}
                {selectedGate && !dragging && (
                  <rect
                    x={LABEL_WIDTH} y={y - WIRE_SPACING / 2}
                    width={svgWidth - LABEL_WIDTH} height={WIRE_SPACING}
                    fill="transparent" style={{ cursor: 'pointer' }}
                    onClick={() => addGate(q)}
                  />
                )}
              </g>
            );
          })}

          {/* Gate columns */}
          {steps.map((step, i) => {
            const cx = colX(i);
            const color = gateColor(step.gate);
            const allQubits = getStepQubits(step);
            const controlQubits = [...(step.controls || [])];
            if (step.control != null) controlQubits.push(step.control);
            const isDragged = dragging?.fromIndex === i;

            return (
              <g
                key={`step-${i}`}
                style={{ cursor: 'grab', opacity: isDragged ? 0.25 : 1 }}
                onMouseDown={(e) => {
                  const gate = GATE_PALETTE.find(g => g.name === step.gate);
                  if (gate) handleDragStart(e, gate, i);
                }}
                onClick={() => removeStep(i)}
              >
                {/* Connection line */}
                {allQubits.length > 1 && (() => {
                  const minQ = Math.min(...allQubits);
                  const maxQ = Math.max(...allQubits);
                  return (
                    <line x1={cx} y1={wireY(minQ)} x2={cx} y2={wireY(maxQ)}
                      stroke={color} strokeWidth={2} />
                  );
                })()}

                {/* Control dots */}
                {controlQubits.map((cq, ci) => (
                  <circle key={`ctrl-${ci}`} cx={cx} cy={wireY(cq)} r={5} fill={color} />
                ))}

                {/* Target gate box */}
                {step.target !== undefined && (
                  <>
                    <rect
                      x={cx - GATE_SIZE / 2} y={wireY(step.target) - GATE_SIZE / 2}
                      width={GATE_SIZE} height={GATE_SIZE} rx={4} fill={color}
                    />
                    <text
                      x={cx} y={wireY(step.target) + 1}
                      textAnchor="middle" dominantBaseline="middle"
                      fill="#fff" fontSize={step.angle != null ? 8 : 10}
                      fontFamily="monospace" fontWeight="bold"
                    >
                      {stepLabel(step)}
                    </text>
                  </>
                )}
              </g>
            );
          })}

          {/* "Add gate here" indicator */}
          {selectedGate && !dragging && (
            <line
              x1={colX(steps.length)} y1={wireY(0) - 10}
              x2={colX(steps.length)} y2={wireY(nQubits - 1) + 10}
              stroke="var(--accent)" strokeWidth={1}
              strokeDasharray="4 4" opacity={0.4}
            />
          )}

          {/* ===== Inline state display ===== */}
          {hasInlineState && finalProbs && (
            <g>
              {/* Separator */}
              <line
                x1={LABEL_WIDTH + steps.length * COL_WIDTH + 6}
                y1={wireY(0) - WIRE_SPACING / 2 + 4}
                x2={LABEL_WIDTH + steps.length * COL_WIDTH + 6}
                y2={wireY(nQubits - 1) + WIRE_SPACING / 2 - 4}
                stroke="var(--border)" strokeWidth={1}
              />

              {/* Per-qubit probability bars */}
              {Array.from({ length: nQubits }, (_, q) => {
                const p1 = qubitProb1(finalProbs, q, nQubits);
                const y = wireY(q);
                const barW = 26;
                const barH = 14;
                const bx = stateColX - barW / 2;
                return (
                  <g key={`state-${q}`}>
                    <rect x={bx} y={y - barH / 2} width={barW} height={barH}
                      rx={2} fill="#1c1c1c" stroke="var(--border)" strokeWidth={0.5} />
                    <rect x={bx} y={y - barH / 2} width={barW * p1} height={barH}
                      rx={2} fill="var(--accent)" opacity={0.7} />
                    <text x={stateColX} y={y + 1}
                      textAnchor="middle" dominantBaseline="middle"
                      fill="var(--text-primary)" fontSize={8}
                      fontFamily="monospace" fontWeight="bold"
                    >
                      {(p1 * 100).toFixed(0)}%
                    </text>
                  </g>
                );
              })}
            </g>
          )}
        </svg>
      </div>

      {/* Step list */}
      {steps.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {steps.map((step, i) => (
            <span
              key={i}
              className="px-2 py-0.5 rounded text-xs cursor-pointer hover:line-through"
              style={{
                background: gateColor(step.gate) + '22',
                color: gateColor(step.gate),
                border: `1px solid ${gateColor(step.gate)}44`,
              }}
              onClick={() => removeStep(i)}
              title="Click to remove"
            >
              {stepLabel(step)}
              {step.control != null && ` c${step.control}`}
              {step.controls && ` c${step.controls.join(',')}`}
              {step.target != null && ` → q${step.target}`}
            </span>
          ))}
        </div>
      )}

      {/* Floating ghost during drag */}
      {dragging && ghostPos && (
        <div
          style={{
            position: 'fixed',
            left: ghostPos.x - GATE_SIZE / 2,
            top: ghostPos.y - GATE_SIZE / 2,
            width: GATE_SIZE,
            height: GATE_SIZE,
            borderRadius: 4,
            background: gateColor(dragging.gate.name),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 10,
            fontFamily: 'monospace',
            fontWeight: 'bold',
            pointerEvents: 'none',
            zIndex: 100,
            opacity: 0.85,
            boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
          }}
        >
          {dragging.gate.label}
        </div>
      )}
    </div>
  );
}
