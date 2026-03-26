"""
GPU-accelerated state vector quantum simulator.

The state vector |ψ⟩ is a complex array of 2^n amplitudes.
Gates are applied via vectorised index manipulation — no full
matrix exponentiation, no Kronecker products. This is the key
to scaling: O(2^n) per gate, not O(4^n).

Supports: CuPy (GPU), NumPy (CPU). cuQuantum path planned.
"""
import numpy as np
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .config import Device, Precision
from . import gates as gate_lib

logger = logging.getLogger(__name__)


def _get_xp(device: Device):
    if device == Device.GPU:
        import cupy as cp
        return cp
    return np


def _dtype(precision: Precision):
    return np.complex64 if precision == Precision.FP32 else np.complex128


@dataclass
class SimulationSnapshot:
    """State captured after a gate application."""
    state: np.ndarray
    step_index: int
    gate_label: str
    probabilities: Optional[np.ndarray] = None


@dataclass
class SimulationResult:
    """Complete result of a circuit simulation."""
    final_state: np.ndarray
    probabilities: np.ndarray
    labels: List[str]
    snapshots: List[SimulationSnapshot]
    measurement_result: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateVectorSimulator:
    """
    State vector quantum circuit simulator.

    Core idea: represent the quantum state as a 1D array of 2^n
    complex amplitudes. Apply gates by computing index pairs that
    correspond to the |0⟩ and |1⟩ subspaces of the target qubit,
    then multiply by the 2x2 gate matrix. Fully vectorised on GPU.
    """

    def __init__(self, n_qubits: int, device: Device = Device.CPU,
                 precision: Precision = Precision.FP64):
        self.n = n_qubits
        self.size = 1 << n_qubits
        self.device = device
        self.precision = precision
        self.xp = _get_xp(device)
        self.dtype = _dtype(precision)

        # |000...0⟩
        self.state = self.xp.zeros(self.size, dtype=self.dtype)
        self.state[0] = 1.0

        self.snapshots: List[SimulationSnapshot] = []

        mem_mb = self.size * (8 if precision == Precision.FP32 else 16) / 1e6
        logger.info(
            "StateVectorSimulator: %d qubits on %s (%s), %.1f MB",
            n_qubits, device.value, precision.value, mem_mb,
        )

    # ----------------------------------------------------------
    # Device transfer helpers
    # ----------------------------------------------------------

    def _to_numpy(self, arr):
        """Ensure array is on CPU as numpy."""
        if self.device == Device.GPU:
            import cupy as cp
            return cp.asnumpy(arr)
        return np.asarray(arr)

    def _ensure_device(self, matrix):
        """Move a gate matrix to the simulator's device."""
        if self.device == Device.GPU:
            import cupy as cp
            if not isinstance(matrix, cp.ndarray):
                return cp.asarray(matrix, dtype=self.dtype)
            return matrix.astype(self.dtype, copy=False)
        else:
            if hasattr(matrix, '__cuda_array_interface__'):
                import cupy as cp
                return cp.asnumpy(matrix).astype(self.dtype, copy=False)
            return np.asarray(matrix, dtype=self.dtype)

    def _save_snapshot(self, step_index: int, gate_label: str):
        state_np = self._to_numpy(self.state.copy())
        probs_np = np.abs(state_np) ** 2
        self.snapshots.append(SimulationSnapshot(
            state=state_np,
            step_index=step_index,
            gate_label=gate_label,
            probabilities=probs_np,
        ))

    # ===========================================================
    # GATE APPLICATION — the performance-critical core
    # ===========================================================

    def apply_single_qubit_gate(self, matrix, target: int):
        """
        Apply a 2x2 unitary to target qubit.

        Algorithm: partition all 2^n indices into pairs (i0, i1) where
        i0 has bit `target` = 0 and i1 = i0 with bit `target` flipped.
        Then: state[i0], state[i1] = M @ [state[i0], state[i1]].

        Fully vectorised — no Python loops over state elements.
        """
        xp = self.xp
        matrix = self._ensure_device(matrix)

        bit = self.n - 1 - target
        stride = 1 << bit
        num_pairs = self.size >> 1
        block_size = stride << 1

        # Build index arrays for the |0⟩ subspace
        block_idx = xp.arange(num_pairs // stride, dtype=xp.int64)
        inner_idx = xp.arange(stride, dtype=xp.int64)
        i0 = (block_idx[:, None] * block_size + inner_idx[None, :]).ravel()
        i1 = i0 + stride

        a0 = self.state[i0]
        a1 = self.state[i1]

        self.state[i0] = matrix[0, 0] * a0 + matrix[0, 1] * a1
        self.state[i1] = matrix[1, 0] * a0 + matrix[1, 1] * a1

    def apply_cnot(self, control: int, target: int):
        """CNOT: flip target qubit when control is |1⟩."""
        xp = self.xp
        c_bit = self.n - 1 - control
        t_bit = self.n - 1 - target

        indices = xp.arange(self.size, dtype=xp.int64)
        # Select indices where control=1 AND target=0
        mask = (((indices >> c_bit) & 1) == 1) & (((indices >> t_bit) & 1) == 0)
        i0 = indices[mask]
        i1 = i0 ^ (1 << t_bit)

        temp = self.state[i0].copy()
        self.state[i0] = self.state[i1]
        self.state[i1] = temp

    def apply_cz(self, control: int, target: int):
        """CZ: phase flip (-1) when both qubits are |1⟩."""
        xp = self.xp
        c_bit = self.n - 1 - control
        t_bit = self.n - 1 - target

        indices = xp.arange(self.size, dtype=xp.int64)
        mask = (((indices >> c_bit) & 1) == 1) & (((indices >> t_bit) & 1) == 1)
        self.state[indices[mask]] *= -1

    def apply_swap(self, q1: int, q2: int):
        """SWAP: exchange two qubits."""
        xp = self.xp
        b1 = self.n - 1 - q1
        b2 = self.n - 1 - q2

        indices = xp.arange(self.size, dtype=xp.int64)
        bit1 = (indices >> b1) & 1
        bit2 = (indices >> b2) & 1

        # Only swap where the two bits differ, and pick one of each pair
        diff = bit1 != bit2
        first = indices[diff & (bit1 < bit2)]
        second = first ^ (1 << b1) ^ (1 << b2)

        temp = self.state[first].copy()
        self.state[first] = self.state[second]
        self.state[second] = temp

    def apply_toffoli(self, control1: int, control2: int, target: int):
        """Toffoli (CCX): flip target when both controls are |1⟩."""
        xp = self.xp
        c1_bit = self.n - 1 - control1
        c2_bit = self.n - 1 - control2
        t_bit = self.n - 1 - target

        indices = xp.arange(self.size, dtype=xp.int64)
        mask = (
            (((indices >> c1_bit) & 1) == 1)
            & (((indices >> c2_bit) & 1) == 1)
            & (((indices >> t_bit) & 1) == 0)
        )
        i0 = indices[mask]
        i1 = i0 ^ (1 << t_bit)

        temp = self.state[i0].copy()
        self.state[i0] = self.state[i1]
        self.state[i1] = temp

    def apply_controlled_gate(self, matrix, control: int, target: int):
        """Controlled-U: apply arbitrary 2x2 gate when control is |1⟩."""
        xp = self.xp
        matrix = self._ensure_device(matrix)

        c_bit = self.n - 1 - control
        t_bit = self.n - 1 - target

        indices = xp.arange(self.size, dtype=xp.int64)
        mask = (((indices >> c_bit) & 1) == 1) & (((indices >> t_bit) & 1) == 0)
        i0 = indices[mask]
        i1 = i0 ^ (1 << t_bit)

        a0 = self.state[i0]
        a1 = self.state[i1]

        self.state[i0] = matrix[0, 0] * a0 + matrix[0, 1] * a1
        self.state[i1] = matrix[1, 0] * a0 + matrix[1, 1] * a1

    # ===========================================================
    # GATE DISPATCHER
    # ===========================================================

    def apply_gate(self, step: dict):
        """
        Apply a gate described by a step dictionary.

        Expected keys:
            gate: str — gate name (H, X, CNOT, Rx, etc.)
            target: int — target qubit index
            control: int — control qubit (for 2-qubit gates)
            controls: list[int] — multiple controls (for Toffoli)
            angle: float — rotation angle (for parametric gates)
            params: list[float] — [theta, phi, lambda] for U3
        """
        gate_name = step['gate']
        target = step.get('target')
        control = step.get('control')
        controls = step.get('controls', [])
        angle = step.get('angle')

        if gate_name in gate_lib.SINGLE_GATE_MAP:
            matrix = gate_lib.SINGLE_GATE_MAP[gate_name](
                self.device, self.precision)
            self.apply_single_qubit_gate(matrix, target)

        elif gate_name in gate_lib.PARAMETRIC_GATE_MAP:
            if angle is None:
                raise ValueError(f"Gate {gate_name} requires 'angle' parameter")
            matrix = gate_lib.PARAMETRIC_GATE_MAP[gate_name](
                angle, self.device, self.precision)
            self.apply_single_qubit_gate(matrix, target)

        elif gate_name in ('CNOT', 'CX'):
            self.apply_cnot(control, target)

        elif gate_name == 'CZ':
            self.apply_cz(control, target)

        elif gate_name == 'SWAP':
            q1 = control if control is not None else step.get('targets', [0, 1])[0]
            q2 = target if target is not None else step.get('targets', [0, 1])[1]
            self.apply_swap(q1, q2)

        elif gate_name in ('TOFFOLI', 'CCX'):
            c1 = controls[0] if controls else control
            c2 = controls[1] if len(controls) > 1 else step.get('control2')
            self.apply_toffoli(c1, c2, target)

        elif gate_name == 'U3':
            params = step.get('params', [0, 0, 0])
            matrix = gate_lib.u3(
                params[0], params[1], params[2],
                self.device, self.precision)
            self.apply_single_qubit_gate(matrix, target)

        elif gate_name == 'MEASURE':
            pass  # handled separately in run_circuit

        else:
            raise ValueError(f"Unknown gate: {gate_name}")

    # ===========================================================
    # NOISE
    # ===========================================================

    def apply_noise(self, kraus_ops, target: int):
        """
        Apply noise channel via Kraus operators (probabilistic).

        For exact noise simulation, use density matrix.
        This is the Monte Carlo (quantum trajectory) approximation:
        randomly select one Kraus operator weighted by its probability.
        """
        xp = self.xp
        probabilities = []
        saved_state = self.state.copy()

        for K in kraus_ops:
            self.state = saved_state.copy()
            self.apply_single_qubit_gate(K, target)
            prob = float(xp.sum(xp.abs(self.state) ** 2).real)
            probabilities.append(prob)

        # Normalise
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]

        # Select Kraus operator
        r = np.random.random()
        cumulative = 0.0
        selected = 0
        for i, p in enumerate(probabilities):
            cumulative += p
            if r <= cumulative:
                selected = i
                break

        # Apply selected and renormalise
        self.state = saved_state
        self.apply_single_qubit_gate(kraus_ops[selected], target)
        norm = float(xp.sqrt(xp.sum(xp.abs(self.state) ** 2)).real)
        if norm > 0:
            self.state /= norm

    # ===========================================================
    # MEASUREMENT
    # ===========================================================

    def get_probabilities(self) -> np.ndarray:
        """Probability distribution |⟨i|ψ⟩|² for all basis states."""
        probs = self.xp.abs(self.state) ** 2
        return self._to_numpy(probs)

    def measure_all(self) -> str:
        """Measure all qubits. Collapses state. Returns bitstring."""
        probs = self.get_probabilities()
        result = int(np.random.choice(self.size, p=probs))
        self.state = self.xp.zeros(self.size, dtype=self.dtype)
        self.state[result] = 1.0
        return format(result, f'0{self.n}b')

    def measure_qubit(self, qubit: int) -> int:
        """Measure single qubit. Partially collapses state."""
        xp = self.xp
        bit = self.n - 1 - qubit

        indices = xp.arange(self.size, dtype=xp.int64)
        is_zero = ((indices >> bit) & 1) == 0

        prob_0 = float(xp.sum(xp.abs(self.state[is_zero]) ** 2).real)
        result = 0 if np.random.random() < prob_0 else 1

        if result == 0:
            self.state[~is_zero] = 0
            norm_sq = prob_0
        else:
            self.state[is_zero] = 0
            norm_sq = 1.0 - prob_0

        if norm_sq > 0:
            self.state /= self.xp.sqrt(
                self.xp.array(norm_sq, dtype=self.state.real.dtype))

        return result

    def sample(self, shots: int = 1024) -> Dict[str, int]:
        """
        Sample measurement outcomes WITHOUT collapsing state.
        Returns {bitstring: count}.
        """
        probs = self.get_probabilities()
        results = np.random.choice(self.size, size=shots, p=probs)

        counts: Dict[str, int] = {}
        for r in results:
            bs = format(int(r), f'0{self.n}b')
            counts[bs] = counts.get(bs, 0) + 1

        return dict(sorted(counts.items()))

    def expectation_value(self, observable_matrix, qubit: int) -> float:
        """
        ⟨ψ|O|ψ⟩ for a single-qubit observable O on the given qubit.
        Observable must be Hermitian 2x2.
        """
        xp = self.xp
        temp_state = self.state.copy()

        # Create scratch simulator to apply O
        scratch = StateVectorSimulator(self.n, self.device, self.precision)
        scratch.state = temp_state.copy()
        scratch.apply_single_qubit_gate(observable_matrix, qubit)

        result = xp.sum(xp.conj(temp_state) * scratch.state)
        return float(result.real)

    # ===========================================================
    # CIRCUIT RUNNER
    # ===========================================================

    def run_circuit(
        self,
        steps: List[dict],
        noise_model: Optional[Dict[str, tuple]] = None,
        save_intermediate: bool = True,
    ) -> SimulationResult:
        """
        Execute a full quantum circuit.

        Args:
            steps: list of gate step dicts
            noise_model: {gate_name: (channel_name, probability)}
            save_intermediate: save state snapshot after each gate

        Returns:
            SimulationResult with final state, probabilities, snapshots
        """
        # Reset to |000...0⟩
        self.state = self.xp.zeros(self.size, dtype=self.dtype)
        self.state[0] = 1.0
        self.snapshots = []

        if save_intermediate:
            self._save_snapshot(-1, 'init')

        measurement_result = None

        for i, step in enumerate(steps):
            if step['gate'] == 'MEASURE':
                measurement_result = self.measure_all()
            else:
                self.apply_gate(step)

                # Apply noise after gate if noise model specifies it
                if noise_model and step['gate'] in noise_model:
                    channel_name, param = noise_model[step['gate']]
                    target = step.get('target', 0)
                    kraus_ops = gate_lib.NOISE_CHANNEL_MAP[channel_name](
                        param, self.device, self.precision)
                    self.apply_noise(kraus_ops, target)

            if save_intermediate:
                self._save_snapshot(i, step['gate'])

        final_state = self._to_numpy(self.state.copy())
        probabilities = np.abs(final_state) ** 2
        labels = [f"|{format(i, f'0{self.n}b')}⟩" for i in range(self.size)]

        return SimulationResult(
            final_state=final_state,
            probabilities=probabilities,
            labels=labels,
            snapshots=self.snapshots,
            measurement_result=measurement_result,
            metadata={
                'n_qubits': self.n,
                'n_gates': len(steps),
                'device': self.device.value,
                'precision': self.precision.value,
            },
        )

    # ===========================================================
    # UTILITY
    # ===========================================================

    def get_labels(self) -> List[str]:
        return [f"|{format(i, f'0{self.n}b')}⟩" for i in range(self.size)]

    def cleanup(self):
        """Free GPU memory."""
        if self.device == Device.GPU:
            import cupy as cp
            del self.state
            cp.get_default_memory_pool().free_all_blocks()
