"""
Preset quantum circuits for the UI.

These are real, pedagogically important circuits that any physicist
would expect to see in a quantum simulator.
"""

PRESET_CIRCUITS = [
    {
        "name": "Bell State (Φ+)",
        "description": "Creates maximally entangled state (|00⟩ + |11⟩)/√2. The fundamental unit of quantum entanglement.",
        "category": "Entanglement",
        "n_qubits": 2,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "CNOT", "control": 0, "target": 1},
        ],
    },
    {
        "name": "Bell State (Ψ+)",
        "description": "Creates (|01⟩ + |10⟩)/√2. One of the four Bell states.",
        "category": "Entanglement",
        "n_qubits": 2,
        "steps": [
            {"gate": "X", "target": 1},
            {"gate": "H", "target": 0},
            {"gate": "CNOT", "control": 0, "target": 1},
        ],
    },
    {
        "name": "GHZ State (3-qubit)",
        "description": "Greenberger-Horne-Zeilinger state (|000⟩ + |111⟩)/√2. Maximally entangled 3-qubit state, key to quantum error correction.",
        "category": "Entanglement",
        "n_qubits": 3,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "CNOT", "control": 0, "target": 1},
            {"gate": "CNOT", "control": 0, "target": 2},
        ],
    },
    {
        "name": "W State (3-qubit)",
        "description": "W state (|001⟩ + |010⟩ + |100⟩)/√3. Unlike GHZ, remains entangled even if one qubit is lost.",
        "category": "Entanglement",
        "n_qubits": 3,
        "steps": [
            {"gate": "X", "target": 0},
            {"gate": "Ry", "target": 0, "angle": 1.9106332362490186},
            {"gate": "CNOT", "control": 0, "target": 1},
            {"gate": "Ry", "target": 1, "angle": 1.2309594173407747},
            {"gate": "CNOT", "control": 1, "target": 2},
        ],
    },
    {
        "name": "Quantum Teleportation",
        "description": "Teleports qubit 0 state to qubit 2 using entanglement and classical communication (measurement).",
        "category": "Algorithms",
        "n_qubits": 3,
        "steps": [
            # Prepare state to teleport
            {"gate": "Rx", "target": 0, "angle": 1.2},
            # Create Bell pair between q1, q2
            {"gate": "H", "target": 1},
            {"gate": "CNOT", "control": 1, "target": 2},
            # Bell measurement on q0, q1
            {"gate": "CNOT", "control": 0, "target": 1},
            {"gate": "H", "target": 0},
        ],
    },
    {
        "name": "Deutsch-Jozsa (Balanced)",
        "description": "Determines if a function is constant or balanced in ONE query. Exponential speedup over classical.",
        "category": "Algorithms",
        "n_qubits": 3,
        "steps": [
            {"gate": "X", "target": 2},
            {"gate": "H", "target": 0},
            {"gate": "H", "target": 1},
            {"gate": "H", "target": 2},
            {"gate": "CNOT", "control": 0, "target": 2},
            {"gate": "CNOT", "control": 1, "target": 2},
            {"gate": "H", "target": 0},
            {"gate": "H", "target": 1},
        ],
    },
    {
        "name": "Grover's Search (2-qubit)",
        "description": "Finds marked item |11⟩ in unsorted database of 4 items with O(√N) queries. One iteration suffices for N=4.",
        "category": "Algorithms",
        "n_qubits": 2,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "H", "target": 1},
            # Oracle: mark |11⟩
            {"gate": "CZ", "control": 0, "target": 1},
            # Diffusion
            {"gate": "H", "target": 0},
            {"gate": "H", "target": 1},
            {"gate": "Z", "target": 0},
            {"gate": "Z", "target": 1},
            {"gate": "CZ", "control": 0, "target": 1},
            {"gate": "H", "target": 0},
            {"gate": "H", "target": 1},
        ],
    },
    {
        "name": "Quantum Fourier Transform (3-qubit)",
        "description": "QFT — the quantum analogue of the discrete Fourier transform. Core subroutine in Shor's algorithm.",
        "category": "Algorithms",
        "n_qubits": 3,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "P", "target": 0, "angle": 0.7853981633974483},  # π/4 controlled by q2 (approx)
            {"gate": "P", "target": 0, "angle": 1.5707963267948966},  # π/2 controlled by q1 (approx)
            {"gate": "H", "target": 1},
            {"gate": "P", "target": 1, "angle": 0.7853981633974483},
            {"gate": "H", "target": 2},
            {"gate": "SWAP", "control": 0, "target": 2},
        ],
    },
    {
        "name": "Quantum Phase Estimation Setup",
        "description": "Phase estimation circuit setup — estimates eigenvalues of a unitary operator. Foundation of many quantum algorithms.",
        "category": "Algorithms",
        "n_qubits": 4,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "H", "target": 1},
            {"gate": "H", "target": 2},
            {"gate": "X", "target": 3},
            {"gate": "P", "target": 3, "angle": 0.7853981633974483},
            {"gate": "P", "target": 3, "angle": 1.5707963267948966},
            {"gate": "P", "target": 3, "angle": 3.141592653589793},
        ],
    },
    {
        "name": "Superposition (Equal)",
        "description": "Hadamard on all qubits — creates uniform superposition over all 2^n basis states.",
        "category": "Basics",
        "n_qubits": 3,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "H", "target": 1},
            {"gate": "H", "target": 2},
        ],
    },
    {
        "name": "Quantum Interference",
        "description": "HZH = X. Demonstrates constructive/destructive interference — the engine behind quantum speedups.",
        "category": "Basics",
        "n_qubits": 1,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "Z", "target": 0},
            {"gate": "H", "target": 0},
        ],
    },
    {
        "name": "Bloch Sphere Tour",
        "description": "Rotates a qubit through all 6 cardinal points of the Bloch sphere: |0⟩, |+⟩, |+i⟩, |1⟩, |−⟩, |−i⟩.",
        "category": "Basics",
        "n_qubits": 1,
        "steps": [
            {"gate": "I", "target": 0},
            {"gate": "H", "target": 0},
            {"gate": "S", "target": 0},
            {"gate": "H", "target": 0},
            {"gate": "Z", "target": 0},
            {"gate": "H", "target": 0},
            {"gate": "Sdg", "target": 0},
        ],
    },
    {
        "name": "SWAP Test",
        "description": "Tests overlap between two quantum states without tomography. Measures qubit 0 — P(0) = (1 + |⟨ψ|φ⟩|²)/2.",
        "category": "Algorithms",
        "n_qubits": 3,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "SWAP", "control": 1, "target": 2},
            {"gate": "H", "target": 0},
        ],
    },
    {
        "name": "Quantum Error Detection",
        "description": "3-qubit bit-flip repetition code. Encodes |ψ⟩ → |ψψψ⟩, detectable against single bit-flip errors.",
        "category": "Error Correction",
        "n_qubits": 3,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "CNOT", "control": 0, "target": 1},
            {"gate": "CNOT", "control": 0, "target": 2},
            # Simulate error on qubit 1
            {"gate": "X", "target": 1},
            # Syndrome extraction
            {"gate": "CNOT", "control": 0, "target": 1},
            {"gate": "CNOT", "control": 0, "target": 2},
        ],
    },
]
