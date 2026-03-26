"""
End-to-end API tests.
Tests every endpoint with real simulation — no mocks.
"""
import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport
from server.app import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.anyio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.anyio
async def test_hardware(client):
    r = await client.get("/hardware")
    assert r.status_code == 200
    data = r.json()
    assert "gpu" in data
    assert "cpu" in data
    assert data["cpu"]["threads"] >= 1
    assert data["cpu"]["ram_gb"] > 0


@pytest.mark.anyio
async def test_presets(client):
    r = await client.get("/presets")
    assert r.status_code == 200
    presets = r.json()
    assert len(presets) > 5
    for p in presets:
        assert "name" in p
        assert "steps" in p
        assert len(p["steps"]) > 0


@pytest.mark.anyio
async def test_simulate_bell_state(client):
    r = await client.post("/simulate", json={
        "n_qubits": 2,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "CNOT", "control": 0, "target": 1},
        ],
    })
    assert r.status_code == 200
    data = r.json()

    probs = data["probabilities"]
    assert len(probs) == 4
    assert abs(probs[0] - 0.5) < 1e-6  # |00⟩
    assert abs(probs[3] - 0.5) < 1e-6  # |11⟩
    assert abs(sum(probs) - 1.0) < 1e-6

    assert len(data["labels"]) == 4
    assert data["labels"][0] == "|00⟩"

    assert len(data["bloch_vectors"]) == 2

    # Bell state: each qubit is maximally mixed → Bloch vector at origin
    for bv in data["bloch_vectors"]:
        length = np.sqrt(bv["x"]**2 + bv["y"]**2 + bv["z"]**2)
        assert length < 0.01  # nearly zero = maximally mixed

    assert len(data["state_real"]) == 4
    assert len(data["state_imag"]) == 4
    assert len(data["snapshots"]) == 3  # init + H + CNOT


@pytest.mark.anyio
async def test_simulate_with_shots(client):
    r = await client.post("/simulate", json={
        "n_qubits": 1,
        "steps": [{"gate": "H", "target": 0}],
        "shots": 1000,
    })
    assert r.status_code == 200
    data = r.json()
    counts = data["counts"]
    assert "0" in counts or "1" in counts
    total = sum(counts.values())
    assert total == 1000


@pytest.mark.anyio
async def test_simulate_parametric(client):
    r = await client.post("/simulate", json={
        "n_qubits": 1,
        "steps": [{"gate": "Ry", "target": 0, "angle": 1.5707963267948966}],
    })
    assert r.status_code == 200
    probs = r.json()["probabilities"]
    assert abs(probs[0] - 0.5) < 1e-4
    assert abs(probs[1] - 0.5) < 1e-4


@pytest.mark.anyio
async def test_simulate_ghz(client):
    r = await client.post("/simulate", json={
        "n_qubits": 3,
        "steps": [
            {"gate": "H", "target": 0},
            {"gate": "CNOT", "control": 0, "target": 1},
            {"gate": "CNOT", "control": 0, "target": 2},
        ],
    })
    assert r.status_code == 200
    probs = r.json()["probabilities"]
    assert abs(probs[0] - 0.5) < 1e-6
    assert abs(probs[7] - 0.5) < 1e-6


@pytest.mark.anyio
async def test_simulate_with_noise(client):
    r = await client.post("/simulate", json={
        "n_qubits": 1,
        "steps": [{"gate": "H", "target": 0}],
        "noise": {
            "channel": "depolarising",
            "probability": 0.01,
            "gates": ["H"],
        },
    })
    assert r.status_code == 200
    probs = r.json()["probabilities"]
    assert abs(sum(probs) - 1.0) < 1e-6


@pytest.mark.anyio
async def test_invalid_gate(client):
    r = await client.post("/simulate", json={
        "n_qubits": 1,
        "steps": [{"gate": "FAKEGATE", "target": 0}],
    })
    assert r.status_code == 422


@pytest.mark.anyio
async def test_qubit_out_of_range(client):
    r = await client.post("/simulate", json={
        "n_qubits": 2,
        "steps": [{"gate": "H", "target": 5}],
    })
    assert r.status_code == 422


@pytest.mark.anyio
async def test_all_presets_simulate(client):
    """Every preset circuit must simulate successfully."""
    presets_r = await client.get("/presets")
    presets = presets_r.json()

    for preset in presets:
        r = await client.post("/simulate", json={
            "n_qubits": preset["n_qubits"],
            "steps": preset["steps"],
        })
        assert r.status_code == 200, f"Preset '{preset['name']}' failed: {r.text}"
        probs = r.json()["probabilities"]
        assert abs(sum(probs) - 1.0) < 1e-4, f"Preset '{preset['name']}' probs sum = {sum(probs)}"
