"""
Gate definitions as numpy/cupy arrays.
Factory functions return arrays on the correct device with correct precision.

Every gate is a unitary matrix. Single-qubit gates are 2x2.
Multi-qubit gates (CNOT, CZ, SWAP, Toffoli) are handled directly
in the simulator via index manipulation — not stored as matrices.
"""
import numpy as np
from typing import List
from .config import Device, Precision


def _get_xp(device: Device):
    """Get array module: numpy for CPU, cupy for GPU."""
    if device == Device.GPU:
        import cupy as cp
        return cp
    return np


def _dtype(precision: Precision):
    """Map precision enum to numpy complex dtype."""
    return np.complex64 if precision == Precision.FP32 else np.complex128


# ============================================================
# SINGLE-QUBIT GATES
# ============================================================

def identity(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[1, 0], [0, 1]], dtype=dt)


def hadamard(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    s = 1.0 / np.sqrt(2.0)
    return xp.array([[s, s], [s, -s]], dtype=dt)


def pauli_x(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[0, 1], [1, 0]], dtype=dt)


def pauli_y(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[0, -1j], [1j, 0]], dtype=dt)


def pauli_z(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[1, 0], [0, -1]], dtype=dt)


def s_gate(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[1, 0], [0, 1j]], dtype=dt)


def s_dagger(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[1, 0], [0, -1j]], dtype=dt)


def t_gate(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=dt)


def t_dagger(device=Device.CPU, precision=Precision.FP64):
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=dt)


def sqrt_x(device=Device.CPU, precision=Precision.FP64):
    """Square root of X (sqrt(NOT)). Applying twice gives X."""
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([
        [0.5 + 0.5j, 0.5 - 0.5j],
        [0.5 - 0.5j, 0.5 + 0.5j],
    ], dtype=dt)


# ============================================================
# PARAMETRIC GATES
# ============================================================

def rx(theta: float, device=Device.CPU, precision=Precision.FP64):
    """Rotation around X axis by angle theta."""
    xp = _get_xp(device)
    dt = _dtype(precision)
    c = np.cos(theta / 2)
    s = np.sin(theta / 2)
    return xp.array([[c, -1j * s], [-1j * s, c]], dtype=dt)


def ry(theta: float, device=Device.CPU, precision=Precision.FP64):
    """Rotation around Y axis by angle theta."""
    xp = _get_xp(device)
    dt = _dtype(precision)
    c = np.cos(theta / 2)
    s = np.sin(theta / 2)
    return xp.array([[c, -s], [s, c]], dtype=dt)


def rz(theta: float, device=Device.CPU, precision=Precision.FP64):
    """Rotation around Z axis by angle theta."""
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([
        [np.exp(-1j * theta / 2), 0],
        [0, np.exp(1j * theta / 2)],
    ], dtype=dt)


def phase_gate(theta: float, device=Device.CPU, precision=Precision.FP64):
    """Phase gate P(theta) = diag(1, e^{i*theta})."""
    xp = _get_xp(device)
    dt = _dtype(precision)
    return xp.array([[1, 0], [0, np.exp(1j * theta)]], dtype=dt)


def u3(theta: float, phi: float, lam: float,
       device=Device.CPU, precision=Precision.FP64):
    """
    General single-qubit unitary U3(theta, phi, lambda).
    Any single-qubit gate can be expressed as U3 with appropriate parameters.
    """
    xp = _get_xp(device)
    dt = _dtype(precision)
    c = np.cos(theta / 2)
    s = np.sin(theta / 2)
    return xp.array([
        [c, -np.exp(1j * lam) * s],
        [np.exp(1j * phi) * s, np.exp(1j * (phi + lam)) * c],
    ], dtype=dt)


# ============================================================
# GATE REGISTRIES
# ============================================================

SINGLE_GATE_MAP = {
    'I': identity,
    'H': hadamard,
    'X': pauli_x,
    'Y': pauli_y,
    'Z': pauli_z,
    'S': s_gate,
    'Sdg': s_dagger,
    'T': t_gate,
    'Tdg': t_dagger,
    'SX': sqrt_x,
}

PARAMETRIC_GATE_MAP = {
    'Rx': rx,
    'Ry': ry,
    'Rz': rz,
    'P': phase_gate,
}

# Multi-qubit gate names (handled by simulator, not as matrices)
MULTI_QUBIT_GATES = {'CNOT', 'CX', 'CZ', 'SWAP', 'TOFFOLI', 'CCX'}


# ============================================================
# NOISE CHANNEL KRAUS OPERATORS
# ============================================================

def depolarising_kraus(p: float, device=Device.CPU,
                       precision=Precision.FP64) -> List:
    """
    Depolarising channel: with probability p, replace qubit state
    with maximally mixed state.
    Kraus operators: sqrt(1-p)*I, sqrt(p/3)*X, sqrt(p/3)*Y, sqrt(p/3)*Z
    """
    return [
        np.sqrt(1 - p) * identity(device, precision),
        np.sqrt(p / 3) * pauli_x(device, precision),
        np.sqrt(p / 3) * pauli_y(device, precision),
        np.sqrt(p / 3) * pauli_z(device, precision),
    ]


def amplitude_damping_kraus(gamma: float, device=Device.CPU,
                            precision=Precision.FP64) -> List:
    """
    Amplitude damping (T1 decay): |1> decays to |0> with probability gamma.
    Models energy relaxation in real qubits.
    """
    xp = _get_xp(device)
    dt = _dtype(precision)
    K0 = xp.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=dt)
    K1 = xp.array([[0, np.sqrt(gamma)], [0, 0]], dtype=dt)
    return [K0, K1]


def phase_damping_kraus(gamma: float, device=Device.CPU,
                        precision=Precision.FP64) -> List:
    """
    Phase damping (T2 dephasing without energy loss).
    Models loss of quantum coherence without energy exchange.
    """
    xp = _get_xp(device)
    dt = _dtype(precision)
    K0 = xp.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=dt)
    K1 = xp.array([[0, 0], [0, np.sqrt(gamma)]], dtype=dt)
    return [K0, K1]


def bit_flip_kraus(p: float, device=Device.CPU,
                   precision=Precision.FP64) -> List:
    """Bit flip channel: X applied with probability p."""
    return [
        np.sqrt(1 - p) * identity(device, precision),
        np.sqrt(p) * pauli_x(device, precision),
    ]


def phase_flip_kraus(p: float, device=Device.CPU,
                     precision=Precision.FP64) -> List:
    """Phase flip channel: Z applied with probability p."""
    return [
        np.sqrt(1 - p) * identity(device, precision),
        np.sqrt(p) * pauli_z(device, precision),
    ]


NOISE_CHANNEL_MAP = {
    'depolarising': depolarising_kraus,
    'depolarizing': depolarising_kraus,
    'amplitude_damping': amplitude_damping_kraus,
    'phase_damping': phase_damping_kraus,
    'bit_flip': bit_flip_kraus,
    'phase_flip': phase_flip_kraus,
}
