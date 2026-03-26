"""
Pydantic models for API request/response validation.

These schemas define the contract between frontend and backend.
Every field has constraints that match real quantum computing limits.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================
# REQUEST MODELS
# ============================================================

class GateStep(BaseModel):
    """A single gate operation in a quantum circuit."""
    gate: str = Field(..., description="Gate name: H, X, Y, Z, CNOT, Rx, etc.")
    target: Optional[int] = Field(None, ge=0, description="Target qubit index")
    control: Optional[int] = Field(None, ge=0, description="Control qubit (2-qubit gates)")
    controls: Optional[List[int]] = Field(None, description="Multiple controls (Toffoli)")
    angle: Optional[float] = Field(None, description="Rotation angle in radians")
    params: Optional[List[float]] = Field(None, description="[theta, phi, lambda] for U3")

    @field_validator('gate')
    @classmethod
    def validate_gate_name(cls, v):
        valid = {
            'I', 'H', 'X', 'Y', 'Z', 'S', 'Sdg', 'T', 'Tdg', 'SX',
            'Rx', 'Ry', 'Rz', 'P', 'U3',
            'CNOT', 'CX', 'CZ', 'SWAP', 'TOFFOLI', 'CCX',
            'MEASURE',
        }
        if v not in valid:
            raise ValueError(f"Unknown gate '{v}'. Valid: {sorted(valid)}")
        return v


class NoiseConfig(BaseModel):
    """Noise model configuration."""
    channel: str = Field(..., description="depolarising, amplitude_damping, phase_damping, bit_flip, phase_flip")
    probability: float = Field(..., ge=0.0, le=1.0)
    gates: List[str] = Field(default_factory=lambda: ['H', 'X', 'CNOT'],
                             description="Which gates to apply noise after")

    @field_validator('channel')
    @classmethod
    def validate_channel(cls, v):
        valid = {'depolarising', 'depolarizing', 'amplitude_damping',
                 'phase_damping', 'bit_flip', 'phase_flip'}
        if v not in valid:
            raise ValueError(f"Unknown noise channel '{v}'")
        return v


class SimulationRequest(BaseModel):
    """Full simulation request from the frontend."""
    n_qubits: int = Field(..., ge=1, le=32, description="Number of qubits (1-32)")
    steps: List[GateStep] = Field(..., min_length=1, max_length=500)
    noise: Optional[NoiseConfig] = None
    shots: Optional[int] = Field(None, ge=1, le=100000, description="Sampling shots")
    save_intermediate: bool = Field(True, description="Save state after each gate")

    @field_validator('steps')
    @classmethod
    def validate_qubit_indices(cls, steps, info):
        n = info.data.get('n_qubits', 1)
        for i, step in enumerate(steps):
            if step.target is not None and step.target >= n:
                raise ValueError(
                    f"Step {i}: target qubit {step.target} >= n_qubits ({n})")
            if step.control is not None and step.control >= n:
                raise ValueError(
                    f"Step {i}: control qubit {step.control} >= n_qubits ({n})")
            if step.controls:
                for c in step.controls:
                    if c >= n:
                        raise ValueError(
                            f"Step {i}: control qubit {c} >= n_qubits ({n})")
        return steps


# ============================================================
# RESPONSE MODELS
# ============================================================

class SnapshotResponse(BaseModel):
    """State snapshot after a single gate."""
    step_index: int
    gate_label: str
    probabilities: List[float]
    state_real: List[float]
    state_imag: List[float]


class BlochVectorResponse(BaseModel):
    """Bloch vector for a single qubit."""
    qubit: int
    x: float
    y: float
    z: float


class SimulationResponse(BaseModel):
    """Complete simulation result."""
    probabilities: List[float]
    labels: List[str]
    state_real: List[float]
    state_imag: List[float]
    bloch_vectors: List[BlochVectorResponse]
    snapshots: List[SnapshotResponse]
    measurement_result: Optional[str] = None
    counts: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HardwareResponse(BaseModel):
    """System hardware capabilities."""
    gpu: Dict[str, Any]
    cpu: Dict[str, Any]
    cuquantum: bool
    methods: List[str]


class PresetCircuit(BaseModel):
    """A named preset circuit."""
    name: str
    description: str
    n_qubits: int
    steps: List[GateStep]
    category: str


# ============================================================
# NATURAL LANGUAGE (LLM) MODELS
# ============================================================

class NaturalLanguageRequest(BaseModel):
    """Natural language prompt for circuit generation."""
    prompt: str = Field(..., min_length=1, max_length=2000,
                        description="User's natural language request")
    session_id: Optional[str] = Field(None, description="Session ID for multi-turn conversation")


class NaturalLanguageResponse(BaseModel):
    """Response from LLM circuit generation."""
    circuit: Optional[Dict[str, Any]] = Field(None, description="Generated circuit or None")
    explanation: str = Field(..., description="LLM explanation text")
    simulation: Optional[SimulationResponse] = Field(None,
        description="Auto-simulation result if circuit was generated")
    error: Optional[str] = Field(None, description="Error message if generation failed")
