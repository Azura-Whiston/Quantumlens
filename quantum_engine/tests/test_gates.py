"""
Tests for gate definitions.

Verifies that all gates are unitary (U†U = I) and have correct properties.
"""
import numpy as np
import pytest
from quantum_engine.config import Device, Precision
from quantum_engine import gates


def is_unitary(matrix, eps=1e-10):
    """Check U†U = I."""
    product = matrix.conj().T @ matrix
    identity = np.eye(matrix.shape[0], dtype=matrix.dtype)
    return np.allclose(product, identity, atol=eps)


class TestSingleGatesUnitary:
    @pytest.mark.parametrize("name", list(gates.SINGLE_GATE_MAP.keys()))
    def test_unitary(self, name):
        gate = gates.SINGLE_GATE_MAP[name]()
        assert is_unitary(gate), f"{name} is not unitary"

    @pytest.mark.parametrize("name", list(gates.SINGLE_GATE_MAP.keys()))
    def test_shape(self, name):
        gate = gates.SINGLE_GATE_MAP[name]()
        assert gate.shape == (2, 2)


class TestParametricGatesUnitary:
    @pytest.mark.parametrize("name", list(gates.PARAMETRIC_GATE_MAP.keys()))
    def test_unitary_various_angles(self, name):
        for theta in [0, np.pi/4, np.pi/2, np.pi, 2*np.pi, 1.23]:
            gate = gates.PARAMETRIC_GATE_MAP[name](theta)
            assert is_unitary(gate), f"{name}({theta}) is not unitary"


class TestU3:
    def test_unitary(self):
        for _ in range(10):
            theta, phi, lam = np.random.uniform(0, 2*np.pi, 3)
            gate = gates.u3(theta, phi, lam)
            assert is_unitary(gate)

    def test_reproduces_identity(self):
        gate = gates.u3(0, 0, 0)
        np.testing.assert_allclose(gate, np.eye(2), atol=1e-12)


class TestGateProperties:
    def test_x_squared_is_identity(self):
        x = gates.pauli_x()
        np.testing.assert_allclose(x @ x, np.eye(2), atol=1e-12)

    def test_y_squared_is_identity(self):
        y = gates.pauli_y()
        np.testing.assert_allclose(y @ y, np.eye(2), atol=1e-12)

    def test_z_squared_is_identity(self):
        z = gates.pauli_z()
        np.testing.assert_allclose(z @ z, np.eye(2), atol=1e-12)

    def test_h_squared_is_identity(self):
        h = gates.hadamard()
        np.testing.assert_allclose(h @ h, np.eye(2), atol=1e-12)

    def test_s_squared_is_z(self):
        s = gates.s_gate()
        z = gates.pauli_z()
        np.testing.assert_allclose(s @ s, z, atol=1e-12)

    def test_t_fourth_is_z(self):
        t = gates.t_gate()
        z = gates.pauli_z()
        t4 = t @ t @ t @ t
        np.testing.assert_allclose(t4, z, atol=1e-12)

    def test_pauli_anticommutation(self):
        """XY = iZ, YX = -iZ → {X,Y} = 0."""
        x, y, z = gates.pauli_x(), gates.pauli_y(), gates.pauli_z()
        xy = x @ y
        yx = y @ x
        np.testing.assert_allclose(xy, 1j * z, atol=1e-12)
        np.testing.assert_allclose(yx, -1j * z, atol=1e-12)
        np.testing.assert_allclose(xy + yx, np.zeros((2, 2)), atol=1e-12)


class TestPrecision:
    def test_fp32_gates(self):
        h = gates.hadamard(precision=Precision.FP32)
        assert h.dtype == np.complex64
        assert is_unitary(h.astype(np.complex128), eps=1e-5)

    def test_fp64_gates(self):
        h = gates.hadamard(precision=Precision.FP64)
        assert h.dtype == np.complex128


class TestNoiseChannels:
    def test_depolarising_kraus_completeness(self):
        """Sum of K†K must equal I (trace preservation)."""
        for p in [0.0, 0.01, 0.1, 0.5, 1.0]:
            ops = gates.depolarising_kraus(p)
            total = sum(K.conj().T @ K for K in ops)
            np.testing.assert_allclose(total, np.eye(2), atol=1e-10)

    def test_amplitude_damping_completeness(self):
        for gamma in [0.0, 0.01, 0.5, 1.0]:
            ops = gates.amplitude_damping_kraus(gamma)
            total = sum(K.conj().T @ K for K in ops)
            np.testing.assert_allclose(total, np.eye(2), atol=1e-10)

    def test_phase_damping_completeness(self):
        for gamma in [0.0, 0.1, 0.5, 1.0]:
            ops = gates.phase_damping_kraus(gamma)
            total = sum(K.conj().T @ K for K in ops)
            np.testing.assert_allclose(total, np.eye(2), atol=1e-10)

    def test_bit_flip_completeness(self):
        for p in [0.0, 0.1, 0.5, 1.0]:
            ops = gates.bit_flip_kraus(p)
            total = sum(K.conj().T @ K for K in ops)
            np.testing.assert_allclose(total, np.eye(2), atol=1e-10)
