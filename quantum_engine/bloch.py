"""
Bloch sphere computation from multi-qubit state vectors.

For each qubit, we compute the reduced density matrix by tracing out
all other qubits, then extract the Bloch vector (x, y, z) from:

    ρ = (I + x·σ_x + y·σ_y + z·σ_z) / 2

    x = 2·Re(ρ₀₁)  = Tr(ρ·σ_x)
    y = 2·Im(ρ₁₀)  = Tr(ρ·σ_y)   [note: Im(ρ₁₀), not Im(ρ₀₁)]
    z = ρ₀₀ - ρ₁₁   = Tr(ρ·σ_z)
"""
import numpy as np
from typing import List, Dict


def reduced_density_matrix(state: np.ndarray, qubit: int,
                           n_qubits: int) -> np.ndarray:
    """
    Compute the 2x2 reduced density matrix for a single qubit
    by tracing out all other qubits from the pure state |ψ⟩.

    For a pure state, ρ = |ψ⟩⟨ψ|, and the reduced density matrix is:
        ρ_qubit = Tr_{other qubits}(|ψ⟩⟨ψ|)

    We compute this efficiently without building the full 2^n × 2^n
    density matrix.
    """
    state = np.asarray(state)
    size = len(state)
    bit = n_qubits - 1 - qubit

    rho = np.zeros((2, 2), dtype=np.complex128)

    for i in range(size):
        for j in range(size):
            # Which row/col of the reduced matrix does this contribute to?
            bi = (i >> bit) & 1
            bj = (j >> bit) & 1

            # Check if all OTHER bits match between i and j
            mask = ~(1 << bit) & ((1 << n_qubits) - 1)
            if (i & mask) == (j & mask):
                rho[bi, bj] += state[i] * np.conj(state[j])

    return rho


def reduced_density_matrix_fast(state: np.ndarray, qubit: int,
                                n_qubits: int) -> np.ndarray:
    """
    Vectorised computation of the reduced density matrix.
    Reshapes the state vector to isolate the target qubit dimension,
    then contracts over all other dimensions.

    This is O(2^n) instead of the O(4^n) naive approach.
    """
    state = np.asarray(state, dtype=np.complex128)
    n = n_qubits

    # Reshape state into tensor with n indices, each of dimension 2
    # Index order: qubit 0 (MSB) ... qubit n-1 (LSB)
    tensor = state.reshape([2] * n)

    # Move target qubit axis to position 0
    tensor = np.moveaxis(tensor, qubit, 0)

    # Reshape: (2, 2^{n-1})
    tensor = tensor.reshape(2, -1)

    # ρ_{bi, bj} = Σ_k  tensor[bi, k] * conj(tensor[bj, k])
    rho = tensor @ tensor.conj().T

    return rho


def bloch_vector(state: np.ndarray, qubit: int,
                 n_qubits: int) -> Dict[str, float]:
    """
    Compute the Bloch vector (x, y, z) for a single qubit.

    Returns dict with keys 'x', 'y', 'z'.
    For a pure single-qubit state, the vector lies on the Bloch sphere
    surface (|r| = 1). For a mixed/entangled qubit, |r| < 1.
    """
    rho = reduced_density_matrix_fast(state, qubit, n_qubits)

    x = 2.0 * rho[0, 1].real
    y = 2.0 * rho[1, 0].imag  # = -2·Im(ρ₀₁) = 2·Im(ρ₁₀)
    z = (rho[0, 0] - rho[1, 1]).real

    return {'x': float(x), 'y': float(y), 'z': float(z)}


def all_bloch_vectors(state: np.ndarray,
                      n_qubits: int) -> List[Dict[str, float]]:
    """
    Compute Bloch vectors for all qubits in the state.
    """
    return [bloch_vector(state, q, n_qubits) for q in range(n_qubits)]
