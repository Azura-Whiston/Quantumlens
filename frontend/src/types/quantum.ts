export interface GateStep {
  gate: string;
  target?: number;
  control?: number;
  controls?: number[];
  angle?: number;
  params?: number[];
}

export interface NoiseConfig {
  channel: string;
  probability: number;
  gates: string[];
}

export interface SimulationRequest {
  n_qubits: number;
  steps: GateStep[];
  noise?: NoiseConfig;
  shots?: number;
  save_intermediate?: boolean;
}

export interface BlochVector {
  qubit: number;
  x: number;
  y: number;
  z: number;
}

export interface Snapshot {
  step_index: number;
  gate_label: string;
  probabilities: number[];
  state_real: number[];
  state_imag: number[];
}

export interface SimulationResponse {
  probabilities: number[];
  labels: string[];
  state_real: number[];
  state_imag: number[];
  bloch_vectors: BlochVector[];
  snapshots: Snapshot[];
  measurement_result?: string;
  counts?: Record<string, number>;
  metadata: Record<string, unknown>;
}

export interface HardwareInfo {
  gpu: {
    available: boolean;
    name: string;
    vram_gb: number;
    max_qubits_sv_fp64: number;
    max_qubits_sv_fp32: number;
  };
  cpu: {
    threads: number;
    ram_gb: number;
    max_qubits_sv_fp64: number;
  };
  cuquantum: boolean;
  methods: string[];
}

export interface PresetCircuit {
  name: string;
  description: string;
  n_qubits: number;
  steps: GateStep[];
  category: string;
}

// Natural Language (LLM) types
export interface NaturalLanguageRequest {
  prompt: string;
  session_id?: string;
}

export interface NaturalLanguageResponse {
  circuit: { n_qubits: number; steps: GateStep[] } | null;
  explanation: string;
  simulation: SimulationResponse | null;
  session_id: string;
  error: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  circuit?: { n_qubits: number; steps: GateStep[] } | null;
  simulation?: SimulationResponse | null;
}

export interface GateInfo {
  name: string;
  label: string;
  qubits: number; // 1 = single, 2 = two-qubit, 3 = toffoli
  parametric: boolean;
  color: string;
  description: string;
}

export const GATE_PALETTE: GateInfo[] = [
  // Single-qubit
  { name: 'H', label: 'H', qubits: 1, parametric: false, color: '#c8ad7f', description: 'Hadamard — creates superposition' },
  { name: 'X', label: 'X', qubits: 1, parametric: false, color: '#ef4444', description: 'Pauli-X — bit flip (NOT)' },
  { name: 'Y', label: 'Y', qubits: 1, parametric: false, color: '#22c55e', description: 'Pauli-Y — bit + phase flip' },
  { name: 'Z', label: 'Z', qubits: 1, parametric: false, color: '#3b82f6', description: 'Pauli-Z — phase flip' },
  { name: 'S', label: 'S', qubits: 1, parametric: false, color: '#a89bc4', description: 'S gate — π/2 phase' },
  { name: 'T', label: 'T', qubits: 1, parametric: false, color: '#ec4899', description: 'T gate — π/4 phase' },
  { name: 'Sdg', label: 'S†', qubits: 1, parametric: false, color: '#a89bc4', description: 'S-dagger — −π/2 phase' },
  { name: 'Tdg', label: 'T†', qubits: 1, parametric: false, color: '#ec4899', description: 'T-dagger — −π/4 phase' },
  { name: 'SX', label: '√X', qubits: 1, parametric: false, color: '#f97316', description: 'Square root of X' },
  // Parametric
  { name: 'Rx', label: 'Rx', qubits: 1, parametric: true, color: '#ef4444', description: 'X-axis rotation by θ' },
  { name: 'Ry', label: 'Ry', qubits: 1, parametric: true, color: '#22c55e', description: 'Y-axis rotation by θ' },
  { name: 'Rz', label: 'Rz', qubits: 1, parametric: true, color: '#3b82f6', description: 'Z-axis rotation by θ' },
  { name: 'P', label: 'P', qubits: 1, parametric: true, color: '#eab308', description: 'Phase gate P(θ)' },
  // Multi-qubit
  { name: 'CNOT', label: 'CX', qubits: 2, parametric: false, color: '#14b8a6', description: 'Controlled-NOT' },
  { name: 'CZ', label: 'CZ', qubits: 2, parametric: false, color: '#0ea5e9', description: 'Controlled-Z' },
  { name: 'SWAP', label: 'SW', qubits: 2, parametric: false, color: '#f59e0b', description: 'SWAP two qubits' },
  { name: 'TOFFOLI', label: 'CCX', qubits: 3, parametric: false, color: '#10b981', description: 'Toffoli (double-controlled NOT)' },
];
