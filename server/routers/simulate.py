"""
/simulate endpoint — the core API.

Receives a circuit, runs the quantum engine, returns full results
including state vector, probabilities, Bloch vectors, and snapshots.
"""
import time
import logging
import traceback
from fastapi import APIRouter, HTTPException

from server.models.schemas import (
    SimulationRequest, SimulationResponse,
    SnapshotResponse, BlochVectorResponse,
)
from quantum_engine.engine import get_engine
from quantum_engine.bloch import all_bloch_vectors

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest):
    """Run a quantum circuit simulation."""
    t0 = time.perf_counter()

    try:
        engine = get_engine()

        # Build noise model dict if provided
        noise_model = None
        if request.noise:
            noise_model = {}
            for gate_name in request.noise.gates:
                noise_model[gate_name] = (
                    request.noise.channel,
                    request.noise.probability,
                )

        # Convert Pydantic models to dicts for the engine
        steps = [step.model_dump(exclude_none=True) for step in request.steps]

        result = engine.simulate(
            n_qubits=request.n_qubits,
            steps=steps,
            noise_model=noise_model,
            save_intermediate=request.save_intermediate,
            shots=request.shots,
        )

        # Compute Bloch vectors from final state
        bloch = all_bloch_vectors(result.final_state, request.n_qubits)
        bloch_responses = [
            BlochVectorResponse(qubit=i, **bv)
            for i, bv in enumerate(bloch)
        ]

        # Build snapshot responses
        snapshot_responses = []
        for snap in result.snapshots:
            snapshot_responses.append(SnapshotResponse(
                step_index=snap.step_index,
                gate_label=snap.gate_label,
                probabilities=snap.probabilities.tolist(),
                state_real=snap.state.real.tolist(),
                state_imag=snap.state.imag.tolist(),
            ))

        elapsed = time.perf_counter() - t0
        metadata = result.metadata.copy()
        metadata['simulation_time_ms'] = round(elapsed * 1000, 2)

        return SimulationResponse(
            probabilities=result.probabilities.tolist(),
            labels=result.labels,
            state_real=result.final_state.real.tolist(),
            state_imag=result.final_state.imag.tolist(),
            bloch_vectors=bloch_responses,
            snapshots=snapshot_responses,
            measurement_result=result.measurement_result,
            counts=metadata.pop('counts', None),
            metadata=metadata,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error("Simulation failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Simulation error: {e}")
