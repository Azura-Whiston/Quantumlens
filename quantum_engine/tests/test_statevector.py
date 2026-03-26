"""
Comprehensive tests for the state vector simulator.

Tests verify mathematical correctness against known quantum mechanics results.
If these pass, the simulator is producing physically correct output.

Run: python -m pytest quantum_engine/tests/test_statevector.py -v
"""
import numpy as np
import pytest
from quantum_engine.config import Device, Precision
from quantum_engine.statevector import StateVectorSimulator


def approx(a, b, eps=1e-6):
    return abs(a - b) < eps


# ============================================================
# BASIC GATES
# ============================================================

class TestInitialState:
    def test_single_qubit_starts_at_zero(self):
        sim = StateVectorSimulator(1, Device.CPU)
        probs = sim.get_probabilities()
        assert approx(probs[0], 1.0)
        assert approx(probs[1], 0.0)

    def test_two_qubit_starts_at_zero(self):
        sim = StateVectorSimulator(2, Device.CPU)
        probs = sim.get_probabilities()
        assert approx(probs[0], 1.0)
        assert approx(sum(probs[1:]), 0.0)

    def test_state_vector_length(self):
        for n in [1, 2, 3, 5]:
            sim = StateVectorSimulator(n, Device.CPU)
            assert len(sim.state) == 2 ** n


class TestPauliGates:
    def test_x_flips_zero_to_one(self):
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[0], 0.0)
        assert approx(probs[1], 1.0)

    def test_x_squared_is_identity(self):
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        sim.apply_gate({'gate': 'X', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[0], 1.0)

    def test_y_gate(self):
        """Y|0⟩ = i|1⟩, so probability of |1⟩ should be 1."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'Y', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[1], 1.0)

    def test_z_gate_on_zero(self):
        """Z|0⟩ = |0⟩, no change in probabilities."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'Z', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[0], 1.0)

    def test_z_gate_phase_flip(self):
        """Z|+⟩ = |−⟩. After Z then H, should get |1⟩."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'Z', 'target': 0})
        sim.apply_gate({'gate': 'H', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[1], 1.0)


class TestHadamard:
    def test_creates_superposition(self):
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[0], 0.5)
        assert approx(probs[1], 0.5)

    def test_hadamard_squared_is_identity(self):
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'H', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[0], 1.0)

    def test_hadamard_on_specific_qubit(self):
        """H on qubit 1 of 3-qubit system: only qubit 1 in superposition."""
        sim = StateVectorSimulator(3, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 1})
        probs = sim.get_probabilities()
        # |000⟩ and |010⟩ should each have 0.5
        assert approx(probs[0b000], 0.5)
        assert approx(probs[0b010], 0.5)
        assert approx(sum(probs), 1.0)


class TestPhaseGates:
    def test_s_gate(self):
        """S|+⟩ should give specific phase. S² = Z."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'S', 'target': 0})
        sim.apply_gate({'gate': 'S', 'target': 0})
        sim.apply_gate({'gate': 'H', 'target': 0})
        probs = sim.get_probabilities()
        # S² = Z, and HZH|0⟩ = |1⟩
        assert approx(probs[1], 1.0)

    def test_t_gate(self):
        """T⁴ = Z. Verify T⁴·H gives same as Z·H."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        for _ in range(4):
            sim.apply_gate({'gate': 'T', 'target': 0})
        sim.apply_gate({'gate': 'H', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[1], 1.0)


# ============================================================
# PARAMETRIC GATES
# ============================================================

class TestParametricGates:
    def test_rx_pi_equals_x(self):
        """Rx(π) = -iX, same probabilities as X."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'Rx', 'target': 0, 'angle': np.pi})
        probs = sim.get_probabilities()
        assert approx(probs[1], 1.0)

    def test_ry_pi_equals_y(self):
        """Ry(π)|0⟩ = |1⟩."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'Ry', 'target': 0, 'angle': np.pi})
        probs = sim.get_probabilities()
        assert approx(probs[1], 1.0)

    def test_rz_does_not_change_probabilities(self):
        """Rz only adds phase, doesn't change measurement probabilities from |0⟩."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'Rz', 'target': 0, 'angle': np.pi / 3})
        probs = sim.get_probabilities()
        assert approx(probs[0], 1.0)

    def test_rx_pi_half_creates_superposition(self):
        """Rx(π/2)|0⟩ should give 50/50."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'Rx', 'target': 0, 'angle': np.pi / 2})
        probs = sim.get_probabilities()
        assert approx(probs[0], 0.5)
        assert approx(probs[1], 0.5)

    def test_ry_creates_specific_state(self):
        """Ry(π/3)|0⟩ = cos(π/6)|0⟩ + sin(π/6)|1⟩."""
        theta = np.pi / 3
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'Ry', 'target': 0, 'angle': theta})
        probs = sim.get_probabilities()
        assert approx(probs[0], np.cos(theta / 2) ** 2)
        assert approx(probs[1], np.sin(theta / 2) ** 2)

    def test_u3_reproduces_hadamard(self):
        """U3(π/2, 0, π) ≈ H (up to global phase)."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({
            'gate': 'U3', 'target': 0,
            'params': [np.pi / 2, 0, np.pi],
        })
        probs = sim.get_probabilities()
        assert approx(probs[0], 0.5)
        assert approx(probs[1], 0.5)


# ============================================================
# MULTI-QUBIT GATES
# ============================================================

class TestCNOT:
    def test_cnot_no_flip_when_control_zero(self):
        """CNOT with control=|0⟩ does nothing."""
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})
        probs = sim.get_probabilities()
        assert approx(probs[0b00], 1.0)

    def test_cnot_flips_when_control_one(self):
        """Set control to |1⟩, CNOT should flip target."""
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})   # |10⟩
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})  # |11⟩
        probs = sim.get_probabilities()
        assert approx(probs[0b11], 1.0)

    def test_cx_alias(self):
        """CX should work same as CNOT."""
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        sim.apply_gate({'gate': 'CX', 'control': 0, 'target': 1})
        probs = sim.get_probabilities()
        assert approx(probs[0b11], 1.0)


class TestEntanglement:
    def test_bell_state_phi_plus(self):
        """|Φ+⟩ = (|00⟩ + |11⟩)/√2."""
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})
        probs = sim.get_probabilities()
        assert approx(probs[0b00], 0.5)
        assert approx(probs[0b01], 0.0)
        assert approx(probs[0b10], 0.0)
        assert approx(probs[0b11], 0.5)

    def test_bell_state_psi_plus(self):
        """|Ψ+⟩ = (|01⟩ + |10⟩)/√2."""
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 1})   # |01⟩
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})
        probs = sim.get_probabilities()
        assert approx(probs[0b01], 0.5)
        assert approx(probs[0b10], 0.5)

    def test_ghz_3_qubit(self):
        """|GHZ⟩ = (|000⟩ + |111⟩)/√2."""
        sim = StateVectorSimulator(3, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 2})
        probs = sim.get_probabilities()
        assert approx(probs[0b000], 0.5)
        assert approx(probs[0b111], 0.5)
        assert approx(sum(probs[1:7]), 0.0)

    def test_ghz_4_qubit(self):
        sim = StateVectorSimulator(4, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        for i in range(1, 4):
            sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': i})
        probs = sim.get_probabilities()
        assert approx(probs[0b0000], 0.5)
        assert approx(probs[0b1111], 0.5)
        non_ghz = sum(probs) - probs[0] - probs[15]
        assert approx(non_ghz, 0.0)


class TestSWAP:
    def test_swap_10_to_01(self):
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})   # |10⟩
        sim.apply_gate({'gate': 'SWAP', 'control': 0, 'target': 1})
        probs = sim.get_probabilities()
        assert approx(probs[0b01], 1.0)

    def test_swap_is_symmetric(self):
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        sim.apply_gate({'gate': 'SWAP', 'control': 1, 'target': 0})
        probs = sim.get_probabilities()
        assert approx(probs[0b01], 1.0)

    def test_swap_squared_is_identity(self):
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        sim.apply_gate({'gate': 'SWAP', 'control': 0, 'target': 1})
        sim.apply_gate({'gate': 'SWAP', 'control': 0, 'target': 1})
        probs = sim.get_probabilities()
        assert approx(probs[0b10], 1.0)


class TestCZ:
    def test_cz_both_one(self):
        """CZ flips phase of |11⟩."""
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        sim.apply_gate({'gate': 'X', 'target': 1})
        sim.apply_gate({'gate': 'CZ', 'control': 0, 'target': 1})
        # Probabilities unchanged (phase flip doesn't affect |ψ|²)
        probs = sim.get_probabilities()
        assert approx(probs[0b11], 1.0)

    def test_cz_is_symmetric(self):
        """CZ is symmetric: CZ(0,1) = CZ(1,0)."""
        sim1 = StateVectorSimulator(2, Device.CPU)
        sim1.apply_gate({'gate': 'H', 'target': 0})
        sim1.apply_gate({'gate': 'H', 'target': 1})
        sim1.apply_gate({'gate': 'CZ', 'control': 0, 'target': 1})

        sim2 = StateVectorSimulator(2, Device.CPU)
        sim2.apply_gate({'gate': 'H', 'target': 0})
        sim2.apply_gate({'gate': 'H', 'target': 1})
        sim2.apply_gate({'gate': 'CZ', 'control': 1, 'target': 0})

        np.testing.assert_allclose(
            sim1.get_probabilities(), sim2.get_probabilities(), atol=1e-10)


class TestToffoli:
    def test_toffoli_both_controls_one(self):
        """CCX flips target when both controls are |1⟩."""
        sim = StateVectorSimulator(3, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        sim.apply_gate({'gate': 'X', 'target': 1})
        sim.apply_gate({
            'gate': 'TOFFOLI', 'controls': [0, 1], 'target': 2})
        probs = sim.get_probabilities()
        assert approx(probs[0b111], 1.0)

    def test_toffoli_one_control_zero(self):
        """CCX does nothing when one control is |0⟩."""
        sim = StateVectorSimulator(3, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        # control 1 is still |0⟩
        sim.apply_gate({
            'gate': 'TOFFOLI', 'controls': [0, 1], 'target': 2})
        probs = sim.get_probabilities()
        assert approx(probs[0b100], 1.0)


# ============================================================
# MEASUREMENT
# ============================================================

class TestMeasurement:
    def test_deterministic_zero(self):
        sim = StateVectorSimulator(1, Device.CPU)
        result = sim.measure_all()
        assert result == '0'

    def test_deterministic_one(self):
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        result = sim.measure_all()
        assert result == '1'

    def test_deterministic_two_qubit(self):
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})
        result = sim.measure_all()
        assert result == '10'

    def test_measurement_collapses_state(self):
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        result = sim.measure_all()
        probs = sim.get_probabilities()
        # After measurement, state should be collapsed
        if result == '0':
            assert approx(probs[0], 1.0)
        else:
            assert approx(probs[1], 1.0)

    def test_sampling_distribution(self):
        """H|0⟩ sampled many times should be roughly 50/50."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        counts = sim.sample(10000)
        ratio_0 = counts.get('0', 0) / 10000
        ratio_1 = counts.get('1', 0) / 10000
        assert abs(ratio_0 - 0.5) < 0.05
        assert abs(ratio_1 - 0.5) < 0.05

    def test_sampling_preserves_state(self):
        """sample() should NOT collapse the state."""
        sim = StateVectorSimulator(1, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        state_before = sim.state.copy()
        sim.sample(1000)
        np.testing.assert_allclose(sim.state, state_before)

    def test_bell_state_sampling(self):
        """Bell state should only produce 00 and 11."""
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})
        counts = sim.sample(5000)
        assert '01' not in counts
        assert '10' not in counts
        assert '00' in counts
        assert '11' in counts

    def test_single_qubit_measurement(self):
        """Measure qubit 0 of |10⟩ should give 1."""
        sim = StateVectorSimulator(2, Device.CPU)
        sim.apply_gate({'gate': 'X', 'target': 0})  # |10⟩
        result = sim.measure_qubit(0)
        assert result == 1


# ============================================================
# CIRCUIT RUNNER
# ============================================================

class TestCircuitRunner:
    def test_bell_circuit(self):
        sim = StateVectorSimulator(2, Device.CPU)
        result = sim.run_circuit([
            {'gate': 'H', 'target': 0},
            {'gate': 'CNOT', 'control': 0, 'target': 1},
        ])
        assert approx(result.probabilities[0], 0.5)
        assert approx(result.probabilities[3], 0.5)
        assert len(result.snapshots) == 3  # init + 2 gates
        assert result.labels[0] == '|00⟩'

    def test_circuit_with_measurement(self):
        sim = StateVectorSimulator(2, Device.CPU)
        result = sim.run_circuit([
            {'gate': 'X', 'target': 0},
            {'gate': 'MEASURE'},
        ])
        assert result.measurement_result == '10'

    def test_snapshots_track_evolution(self):
        sim = StateVectorSimulator(1, Device.CPU)
        result = sim.run_circuit([
            {'gate': 'H', 'target': 0},
            {'gate': 'Z', 'target': 0},
            {'gate': 'H', 'target': 0},
        ])
        # 4 snapshots: init, after H, after Z, after H
        assert len(result.snapshots) == 4

        # After first H: 50/50
        assert approx(result.snapshots[1].probabilities[0], 0.5)
        assert approx(result.snapshots[1].probabilities[1], 0.5)

        # After Z: still 50/50 (phase doesn't affect probs)
        assert approx(result.snapshots[2].probabilities[0], 0.5)

        # After second H: |1⟩ (HZH = X)
        assert approx(result.snapshots[3].probabilities[1], 1.0)

    def test_metadata(self):
        sim = StateVectorSimulator(3, Device.CPU)
        result = sim.run_circuit([
            {'gate': 'H', 'target': 0},
        ])
        assert result.metadata['n_qubits'] == 3
        assert result.metadata['n_gates'] == 1
        assert result.metadata['device'] == 'cpu'


# ============================================================
# NORMALIZATION AND UNITARITY
# ============================================================

class TestUnitarity:
    def test_probabilities_sum_to_one_simple(self):
        sim = StateVectorSimulator(3, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'H', 'target': 1})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 2})
        probs = sim.get_probabilities()
        assert approx(sum(probs), 1.0)

    def test_probabilities_sum_to_one_deep_circuit(self):
        """4-qubit circuit with 10 gates — probs must still sum to 1."""
        sim = StateVectorSimulator(4, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'H', 'target': 1})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 2})
        sim.apply_gate({'gate': 'T', 'target': 1})
        sim.apply_gate({'gate': 'CNOT', 'control': 1, 'target': 3})
        sim.apply_gate({'gate': 'S', 'target': 0})
        sim.apply_gate({'gate': 'H', 'target': 2})
        sim.apply_gate({'gate': 'CZ', 'control': 2, 'target': 3})
        sim.apply_gate({'gate': 'Rx', 'target': 0, 'angle': 0.7})
        sim.apply_gate({'gate': 'SWAP', 'control': 1, 'target': 2})
        probs = sim.get_probabilities()
        assert approx(sum(probs), 1.0)

    def test_state_norm_preserved(self):
        """After many gates, ||ψ||² should still be 1."""
        sim = StateVectorSimulator(3, Device.CPU)
        for _ in range(20):
            sim.apply_gate({'gate': 'H', 'target': 0})
            sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})
            sim.apply_gate({'gate': 'T', 'target': 2})
        norm_sq = np.sum(np.abs(sim.state) ** 2)
        assert approx(norm_sq, 1.0, eps=1e-10)


# ============================================================
# QUANTUM ALGORITHMS (integration-level)
# ============================================================

class TestQuantumAlgorithms:
    def test_quantum_interference(self):
        """HZH|0⟩ = X|0⟩ = |1⟩ — constructive/destructive interference."""
        sim = StateVectorSimulator(1, Device.CPU)
        result = sim.run_circuit([
            {'gate': 'H', 'target': 0},
            {'gate': 'Z', 'target': 0},
            {'gate': 'H', 'target': 0},
        ])
        assert approx(result.probabilities[1], 1.0)

    def test_deutsch_jozsa_balanced(self):
        """Deutsch-Jozsa with balanced oracle should measure |11⟩."""
        sim = StateVectorSimulator(3, Device.CPU)
        result = sim.run_circuit([
            {'gate': 'X', 'target': 2},
            {'gate': 'H', 'target': 0},
            {'gate': 'H', 'target': 1},
            {'gate': 'H', 'target': 2},
            # Oracle: balanced function (CNOT from each input to output)
            {'gate': 'CNOT', 'control': 0, 'target': 2},
            {'gate': 'CNOT', 'control': 1, 'target': 2},
            # Decode
            {'gate': 'H', 'target': 0},
            {'gate': 'H', 'target': 1},
        ])
        # For balanced oracle: qubits 0,1 should NOT be |00⟩
        # The combined prob of |00x⟩ states should be 0
        prob_00x = result.probabilities[0b000] + result.probabilities[0b001]
        assert approx(prob_00x, 0.0)

    def test_grover_2_qubit(self):
        """Grover's search for |11⟩ in 2-qubit space — 1 iteration suffices."""
        sim = StateVectorSimulator(2, Device.CPU)
        result = sim.run_circuit([
            # Superposition
            {'gate': 'H', 'target': 0},
            {'gate': 'H', 'target': 1},
            # Oracle: mark |11⟩ with CZ
            {'gate': 'CZ', 'control': 0, 'target': 1},
            # Diffusion operator
            {'gate': 'H', 'target': 0},
            {'gate': 'H', 'target': 1},
            {'gate': 'Z', 'target': 0},
            {'gate': 'Z', 'target': 1},
            {'gate': 'CZ', 'control': 0, 'target': 1},
            {'gate': 'H', 'target': 0},
            {'gate': 'H', 'target': 1},
        ])
        # |11⟩ should have highest probability (ideally 1.0 for 2 qubits)
        assert result.probabilities[0b11] > 0.9


# ============================================================
# SCALING
# ============================================================

class TestScaling:
    def test_10_qubits(self):
        sim = StateVectorSimulator(10, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 5})
        probs = sim.get_probabilities()
        assert approx(sum(probs), 1.0)

    def test_15_qubits(self):
        sim = StateVectorSimulator(15, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(sum(probs), 1.0)
        assert len(probs) == 2 ** 15

    def test_20_qubits(self):
        """20 qubits = 16 MB. Should complete in under a second."""
        sim = StateVectorSimulator(20, Device.CPU)
        sim.apply_gate({'gate': 'H', 'target': 0})
        probs = sim.get_probabilities()
        assert approx(sum(probs), 1.0)

    def test_labels_format(self):
        sim = StateVectorSimulator(3, Device.CPU)
        labels = sim.get_labels()
        assert labels[0] == '|000⟩'
        assert labels[7] == '|111⟩'
        assert len(labels) == 8


# ============================================================
# FP32 PRECISION
# ============================================================

class TestPrecision:
    def test_fp32_bell_state(self):
        sim = StateVectorSimulator(2, Device.CPU, Precision.FP32)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})
        probs = sim.get_probabilities()
        assert approx(probs[0], 0.5, eps=1e-4)
        assert approx(probs[3], 0.5, eps=1e-4)

    def test_fp32_unitarity(self):
        sim = StateVectorSimulator(4, Device.CPU, Precision.FP32)
        sim.apply_gate({'gate': 'H', 'target': 0})
        sim.apply_gate({'gate': 'CNOT', 'control': 0, 'target': 1})
        sim.apply_gate({'gate': 'T', 'target': 2})
        sim.apply_gate({'gate': 'Ry', 'target': 3, 'angle': 1.23})
        probs = sim.get_probabilities()
        assert approx(sum(probs), 1.0, eps=1e-4)
