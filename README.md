<p align="center">
  <img src="frontend/src/assets/hero.png" alt="QuantumLens" width="600" />
</p>

# QuantumLens

A quantum circuit simulator you can actually learn from. Build circuits visually, watch quantum states evolve step-by-step, or just tell the AI what you want in plain English.

The problem: there are only [29 degree programs](https://epjquantumtechnology.springeropen.com/articles/10.1140/epjqt/s40507-024-00294-2) in the world that teach quantum computing, and the existing tools feel like [assembly languages](https://arxiv.org/abs/2403.02240). QuantumLens is for everyone else.

---

## What it does

**Circuit builder** with drag-and-drop. 17 gates (H, X, Y, Z, S, T, CNOT, CZ, SWAP, Toffoli, Rx, Ry, Rz, P, U3), parametric angle input, undo/redo, up to 32 qubits.

**Visualizations** that actually help you understand what's happening:
- 3D Bloch sphere (Three.js, orbit controls, multi-qubit)
- Probability histogram with percentage labels
- Full state table with amplitudes, phases, and a color wheel
- Timeline player to step through the circuit gate by gate
- Per-qubit probability bars right on the circuit wires

**AI chat** powered by Claude. Type "create a Bell state" or "show me Grover's search on 3 qubits" and it generates the circuit, explains it, and runs the simulation. Multi-turn conversations work too.

**Learning mode** with a walkthrough for first-timers, tooltips on every gate, step-by-step explanations of what each gate does to the quantum state, and help bubbles on every panel.

**GPU acceleration** via CuPy. Auto-detected, no config needed. 4-12x speedup at 18+ qubits on an RTX 4050.

**13 preset circuits** covering Bell states, GHZ, W state, teleportation, Deutsch-Jozsa, Grover's, QFT, phase estimation, error detection, and more.

---

## Quick start

You need Python 3.12+ and Node.js 18+. GPU is optional.

```bash
# clone and set up
git clone https://github.com/Azura-Whiston/Quantumlens.git
cd Quantumlens

# backend
python -m venv .venv
source .venv/Scripts/activate   # windows (git bash)
# source .venv/bin/activate     # mac/linux
pip install -r requirements.txt
pip install fastapi uvicorn pydantic anthropic

# optional: GPU support
pip install cupy-cuda12x nvidia-cuda-nvrtc-cu12 nvidia-cuda-runtime-cu12

# optional: set API key for AI chat (everything else works without it)
export ANTHROPIC_API_KEY="your-key-here"

# start server
uvicorn server.app:app --reload --port 8000
```

```bash
# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

```bash
# tests (125 total, all passing)
python -m pytest quantum_engine/tests/ server/tests/ -v
```

---

## Project structure

```
quantum_engine/        Python simulation engine
  gates.py             17 gate matrices, 5 noise channels (Kraus operators)
  statevector.py       state vector sim, NumPy (CPU) + CuPy (GPU)
  bloch.py             Bloch vectors via fast partial trace
  config.py            hardware detection, strategy selection
  engine.py            unified engine, auto strategy dispatch
  tests/               114 tests

server/                FastAPI backend
  routers/simulate.py  POST /simulate
  routers/natural.py   POST /simulate/natural (AI chat)
  routers/hardware.py  GET /hardware, /presets, /health
  services/llm_service.py   Claude API, prompt engineering, validation, caching
  services/presets.py        13 preset circuits
  models/schemas.py          Pydantic request/response models
  tests/                     11 API tests

frontend/              React 19 + TypeScript + Tailwind v4 + Vite 8
  components/
    CircuitBuilder     drag-and-drop circuit editor
    BlochSphere        3D Three.js visualization
    Histogram          probability bar chart
    StateTable         amplitude/phase table
    TimelinePlayer     step-by-step playback
    ChatPanel          AI natural language interface
    OnboardingModal    first-time walkthrough
    CircuitExplanation plain-English gate descriptions
    GateTooltip        hover cards with education content
    HelpBubble         contextual help popover

benchmarks/            GPU vs CPU benchmark scripts
```

### Stack

Python (NumPy, CuPy, SciPy, FastAPI, Pydantic) + React 19 + TypeScript + Tailwind CSS v4 + Three.js + Claude API

### Endpoints

```
POST /simulate           run a quantum circuit
POST /simulate/natural   natural language -> circuit -> simulation
GET  /hardware           system capabilities
GET  /presets            preset circuit list
GET  /health             health check
```

---

## Benchmarks

RTX 4050 (6 GB VRAM), random H+CNOT circuits:

| Qubits | CPU | GPU | Speedup |
|--------|-----|-----|---------|
| 16 | 0.08s | 0.08s | 1.0x |
| 18 | 0.50s | 0.13s | 3.9x |
| 20 | 2.10s | 0.66s | 3.2x |
| 20 (200 gates) | 11.63s | 0.96s | **12.1x** |
| 23 | 19.09s | 4.85s | 3.9x |
| 25 | 95.84s | 24.50s | 3.9x |

GPU starts winning at 16 qubits. Deep circuits benefit the most.

```bash
python benchmarks/benchmark_gpu.py   # run your own
```

### Memory usage

20 qubits = 16 MB. 25 = 512 MB. 28 = 4 GB. 30 = 16 GB. 32 = 64 GB (FP64).

---

## Limitations

This is a classical simulator, not a quantum computer. Important to understand:

- **No quantum speedup.** Grover's search here is actually *slower* than classical search, because we're simulating the quantum mechanics with regular math. The speedup only exists on real hardware.
- **Max 32 qubits.** State vector simulation needs 2^n complex numbers in memory. 32 qubits = 64 GB. Real quantum computers handle 100+ qubits natively because the physics *is* the computation.
- **Idealized noise.** We model 5 noise channels but real devices have correlated errors, crosstalk, and calibration drift that we don't capture.
- **No real hardware connection.** Results come from math, not actual quantum processors.

It's a flight simulator, not an airplane. But you can see things here that are physically impossible to observe on real quantum hardware (intermediate states, full amplitudes, phase evolution), which is exactly why it's useful for learning.

### AI chat costs

The AI chat calls the Claude API. Getting a key is free at [console.anthropic.com](https://console.anthropic.com/settings/keys), each message costs roughly $0.003-0.01 depending on conversation length. Identical prompts are cached. Everything except the chat works without a key.

---

## Research background

The design was informed by 15 papers (2020-2026). The ones that mattered most:

- LLMs get [19% accuracy on quantum coding tasks without chain-of-thought, 78% with reasoning](https://arxiv.org/abs/2510.26101). That's why we validate every AI-generated circuit before displaying it.
- [Quantum state intuition](https://arxiv.org/abs/2602.07589) is the biggest barrier for beginners, not the math. Step-by-step visualization helps more than equations.
- [Entanglement visualization](https://arxiv.org/abs/2601.07872) is still an open research problem. Nobody's fully solved it yet.
- Simulator performance [varies by 1000x](https://arxiv.org/abs/2401.09076) across 24 packages. Our vectorized NumPy/CuPy approach is competitive for the circuit sizes we target.

---

## Roadmap

**Done:**
- [x] Core simulation engine (114 tests, 17 gates, 5 noise channels)
- [x] FastAPI server (11 tests, all endpoints)
- [x] React frontend (circuit builder, Bloch sphere, histogram, state table, timeline)
- [x] AI chat integration (Claude API, multi-turn, validated circuit generation)
- [x] GPU acceleration (CuPy, 4-12x speedup)
- [x] Learning mode (onboarding, tooltips, gate explanations)
- [x] Drag-and-drop circuit builder with undo/redo

**Next up:**

User accounts and persistence — save your circuits, share them with a link, fork other people's experiments. PostgreSQL for data, Redis for caching and rate limits, MinIO for storing large state vectors. Tiered access (free/pro/team) with daily simulation limits.

Export and import — generate Qiskit, Cirq, OpenQASM 2.0/3.0, and Quil code from any circuit you build. Import circuits from QASM files. Copy-paste interop with the frameworks people already use.

Docker deployment — single `docker compose up` to run everything (API, frontend, database, Redis, GPU worker). Nginx reverse proxy with SSL. Monitoring, backups, the whole production stack.

**Later:**

Tensor network simulator — the big one. Matrix Product States let you simulate 50-100+ qubits for circuits with limited entanglement (which covers most educational and chemistry use cases). This breaks us past the 32-qubit memory wall.

Density matrix simulator — proper mixed-state simulation for noise modeling. GPU-accelerated up to ~14 qubits. Needed for realistic decoherence studies beyond what Kraus operators approximate.

Circuit optimization — gate fusion, depth compression, redundancy elimination. Right now we execute circuits as-is. An optimizer could cut gate counts by 30-50% for complex circuits.

Real quantum hardware — run circuits on IBM Quantum and AWS Braket, then compare simulation vs real hardware results side by side. See where noise actually matters, not just where we model it.

Fine-tuned quantum LLM — train a Mistral/LLaMA model on 50K+ quantum instruction pairs via QLoRA. Self-hosted inference removes the Claude API dependency and gives us a model that actually understands quantum deeply, not just pattern-matches.

Interactive lessons and challenges — guided tutorials ("Build a circuit that produces this target state"), challenge mode with scoring, and a full quantum algorithm library (Shor's, VQE, QAOA). The education platform layer.

Classroom mode — teacher creates assignments, students submit circuits, progress tracking and analytics. University site licensing.

Collaborative editing — real-time shared simulation sessions, like Google Docs for quantum circuits.

---

## Tests

125 tests covering gate unitarity, Kraus trace preservation, Bell/GHZ/Deutsch-Jozsa/Grover correctness, scaling to 20 qubits, FP32/FP64 precision, all API endpoints, noise channels, and the invariant that probabilities always sum to 1.

```bash
python -m pytest quantum_engine/tests/ server/tests/ -v --tb=short
```

---

## Contributing

Fork it, branch it, make sure all 125 tests pass, open a PR.

---

## License

AGPL-3.0. See [LICENSE](LICENSE).

You can use, modify, and distribute this freely. If you host a modified version as a service, you must open source your changes under the same license.
