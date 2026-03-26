"""
Tests for Bloch sphere computation.

Validates reduced density matrix and Bloch vector extraction
against known quantum states with analytically known Bloch vectors.
"""
import numpy as np
import pytest
from quantum_engine.bloch import (
    reduced_density_matrix,
    reduced_density_matrix_fast,
    bloch_vector,
    all_bloch_vectors,
)


def approx(a, b, eps=1e-6):
    return abs(a - b) < eps


# ============================================================
# REDUCED DENSITY MATRIX
# ============================================================

class TestReducedDensityMatrix:
    def test_single_qubit_zero(self):
        """ρ of |0⟩ = [[1,0],[0,0]]."""
        state = np.array([1, 0], dtype=np.complex128)
        rho = reduced_density_matrix_fast(state, 0, 1)
        np.testing.assert_allclose(rho, [[1, 0], [0, 0]], atol=1e-12)

    def test_single_qubit_one(self):
        """ρ of |1⟩ = [[0,0],[0,1]]."""
        state = np.array([0, 1], dtype=np.complex128)
        rho = reduced_density_matrix_fast(state, 0, 1)
        np.testing.assert_allclose(rho, [[0, 0], [0, 1]], atol=1e-12)

    def test_single_qubit_plus(self):
        """|+⟩ = (|0⟩+|1⟩)/√2 → ρ = [[0.5, 0.5],[0.5, 0.5]]."""
        state = np.array([1, 1], dtype=np.complex128) / np.sqrt(2)
        rho = reduced_density_matrix_fast(state, 0, 1)
        np.testing.assert_allclose(
            rho, [[0.5, 0.5], [0.5, 0.5]], atol=1e-12)

    def test_bell_state_partial_trace(self):
        """
        |Φ+⟩ = (|00⟩+|11⟩)/√2.
        Tracing out either qubit gives maximally mixed state I/2.
        """
        state = np.zeros(4, dtype=np.complex128)
        state[0b00] = 1 / np.sqrt(2)
        state[0b11] = 1 / np.sqrt(2)

        rho0 = reduced_density_matrix_fast(state, 0, 2)
        np.testing.assert_allclose(
            rho0, [[0.5, 0], [0, 0.5]], atol=1e-12)

        rho1 = reduced_density_matrix_fast(state, 1, 2)
        np.testing.assert_allclose(
            rho1, [[0.5, 0], [0, 0.5]], atol=1e-12)

    def test_product_state(self):
        """|0⟩⊗|1⟩ = |01⟩. Qubit 0 → |0⟩, qubit 1 → |1⟩."""
        state = np.zeros(4, dtype=np.complex128)
        state[0b01] = 1.0

        rho0 = reduced_density_matrix_fast(state, 0, 2)
        np.testing.assert_allclose(rho0, [[1, 0], [0, 0]], atol=1e-12)

        rho1 = reduced_density_matrix_fast(state, 1, 2)
        np.testing.assert_allclose(rho1, [[0, 0], [0, 1]], atol=1e-12)

    def test_fast_matches_naive(self):
        """Fast and naive implementations must agree."""
        np.random.seed(42)
        state = np.random.randn(8) + 1j * np.random.randn(8)
        state /= np.linalg.norm(state)

        for q in range(3):
            rho_naive = reduced_density_matrix(state, q, 3)
            rho_fast = reduced_density_matrix_fast(state, q, 3)
            np.testing.assert_allclose(rho_naive, rho_fast, atol=1e-12)

    def test_density_matrix_is_positive_semidefinite(self):
        np.random.seed(123)
        state = np.random.randn(16) + 1j * np.random.randn(16)
        state /= np.linalg.norm(state)

        for q in range(4):
            rho = reduced_density_matrix_fast(state, q, 4)
            eigenvalues = np.linalg.eigvalsh(rho)
            assert np.all(eigenvalues >= -1e-12)

    def test_density_matrix_trace_is_one(self):
        np.random.seed(77)
        state = np.random.randn(8) + 1j * np.random.randn(8)
        state /= np.linalg.norm(state)

        for q in range(3):
            rho = reduced_density_matrix_fast(state, q, 3)
            assert approx(np.trace(rho).real, 1.0)


# ============================================================
# BLOCH VECTORS
# ============================================================

class TestBlochVector:
    def test_zero_state(self):
        """|0⟩ is at north pole (0, 0, 1)."""
        state = np.array([1, 0], dtype=np.complex128)
        bv = bloch_vector(state, 0, 1)
        assert approx(bv['x'], 0.0)
        assert approx(bv['y'], 0.0)
        assert approx(bv['z'], 1.0)

    def test_one_state(self):
        """|1⟩ is at south pole (0, 0, -1)."""
        state = np.array([0, 1], dtype=np.complex128)
        bv = bloch_vector(state, 0, 1)
        assert approx(bv['x'], 0.0)
        assert approx(bv['y'], 0.0)
        assert approx(bv['z'], -1.0)

    def test_plus_state(self):
        """|+⟩ = (|0⟩+|1⟩)/√2 → (1, 0, 0)."""
        state = np.array([1, 1], dtype=np.complex128) / np.sqrt(2)
        bv = bloch_vector(state, 0, 1)
        assert approx(bv['x'], 1.0)
        assert approx(bv['y'], 0.0)
        assert approx(bv['z'], 0.0)

    def test_minus_state(self):
        """|−⟩ = (|0⟩−|1⟩)/√2 → (-1, 0, 0)."""
        state = np.array([1, -1], dtype=np.complex128) / np.sqrt(2)
        bv = bloch_vector(state, 0, 1)
        assert approx(bv['x'], -1.0)
        assert approx(bv['y'], 0.0)
        assert approx(bv['z'], 0.0)

    def test_plus_i_state(self):
        """|+i⟩ = (|0⟩+i|1⟩)/√2 → (0, 1, 0)."""
        state = np.array([1, 1j], dtype=np.complex128) / np.sqrt(2)
        bv = bloch_vector(state, 0, 1)
        assert approx(bv['x'], 0.0)
        assert approx(bv['y'], 1.0)
        assert approx(bv['z'], 0.0)

    def test_minus_i_state(self):
        """|−i⟩ = (|0⟩−i|1⟩)/√2 → (0, -1, 0)."""
        state = np.array([1, -1j], dtype=np.complex128) / np.sqrt(2)
        bv = bloch_vector(state, 0, 1)
        assert approx(bv['x'], 0.0)
        assert approx(bv['y'], -1.0)
        assert approx(bv['z'], 0.0)

    def test_entangled_qubit_is_inside_sphere(self):
        """Entangled qubit: |r| < 1 (maximally entangled → |r| = 0)."""
        state = np.zeros(4, dtype=np.complex128)
        state[0b00] = 1 / np.sqrt(2)
        state[0b11] = 1 / np.sqrt(2)

        bv = bloch_vector(state, 0, 2)
        r = np.sqrt(bv['x']**2 + bv['y']**2 + bv['z']**2)
        assert r < 0.01  # should be ~0 for maximally entangled

    def test_product_state_pure_bloch(self):
        """Product state: each qubit should be on the surface (|r|=1)."""
        # |0⟩⊗|+⟩
        state = np.zeros(4, dtype=np.complex128)
        state[0b00] = 1 / np.sqrt(2)
        state[0b01] = 1 / np.sqrt(2)

        bv0 = bloch_vector(state, 0, 2)
        r0 = np.sqrt(bv0['x']**2 + bv0['y']**2 + bv0['z']**2)
        assert approx(r0, 1.0)

        bv1 = bloch_vector(state, 1, 2)
        r1 = np.sqrt(bv1['x']**2 + bv1['y']**2 + bv1['z']**2)
        assert approx(r1, 1.0)


class TestAllBlochVectors:
    def test_returns_correct_count(self):
        state = np.zeros(8, dtype=np.complex128)
        state[0] = 1.0
        result = all_bloch_vectors(state, 3)
        assert len(result) == 3

    def test_all_zero_state(self):
        """All qubits at |0⟩ → all at north pole."""
        state = np.zeros(4, dtype=np.complex128)
        state[0] = 1.0
        result = all_bloch_vectors(state, 2)
        for bv in result:
            assert approx(bv['z'], 1.0)
            assert approx(bv['x'], 0.0)
            assert approx(bv['y'], 0.0)
