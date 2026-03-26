"""
/simulate/natural endpoint — natural language → circuit → simulation.

Receives a text prompt, calls Claude to generate a circuit,
validates it, runs it through the quantum engine, and returns
both the explanation and simulation results.
"""
import uuid
import logging
import traceback
from fastapi import APIRouter, HTTPException

from server.models.schemas import (
    NaturalLanguageRequest, NaturalLanguageResponse,
    SimulationResponse, SnapshotResponse, BlochVectorResponse,
)
from server.services.llm_service import generate_circuit
from quantum_engine.engine import get_engine
from quantum_engine.bloch import all_bloch_vectors

logger = logging.getLogger(__name__)
router = APIRouter()

# Session storage for multi-turn conversations
_sessions: dict[str, list[dict]] = {}
MAX_SESSIONS = 200
MAX_HISTORY_PER_SESSION = 20


def _get_or_create_session(session_id: str | None) -> tuple[str, list[dict]]:
    """Get existing session or create a new one."""
    if session_id and session_id in _sessions:
        return session_id, _sessions[session_id]

    new_id = session_id or str(uuid.uuid4())
    _sessions[new_id] = []

    # Evict oldest sessions if too many
    while len(_sessions) > MAX_SESSIONS:
        oldest = next(iter(_sessions))
        del _sessions[oldest]

    return new_id, _sessions[new_id]


def _simulate_circuit(circuit: dict) -> SimulationResponse | None:
    """Run generated circuit through quantum engine."""
    try:
        engine = get_engine()
        n_qubits = circuit["n_qubits"]
        steps = circuit["steps"]

        # Clean up steps — remove None values for engine compatibility
        clean_steps = []
        for step in steps:
            clean = {k: v for k, v in step.items() if v is not None}
            clean_steps.append(clean)

        result = engine.simulate(
            n_qubits=n_qubits,
            steps=clean_steps,
            save_intermediate=True,
        )

        bloch = all_bloch_vectors(result.final_state, n_qubits)
        bloch_responses = [
            BlochVectorResponse(qubit=i, **bv)
            for i, bv in enumerate(bloch)
        ]

        snapshot_responses = [
            SnapshotResponse(
                step_index=snap.step_index,
                gate_label=snap.gate_label,
                probabilities=snap.probabilities.tolist(),
                state_real=snap.state.real.tolist(),
                state_imag=snap.state.imag.tolist(),
            )
            for snap in result.snapshots
        ]

        return SimulationResponse(
            probabilities=result.probabilities.tolist(),
            labels=result.labels,
            state_real=result.final_state.real.tolist(),
            state_imag=result.final_state.imag.tolist(),
            bloch_vectors=bloch_responses,
            snapshots=snapshot_responses,
            measurement_result=result.measurement_result,
            counts=result.metadata.get('counts'),
            metadata=result.metadata,
        )

    except Exception as e:
        logger.error("Simulation of generated circuit failed: %s\n%s",
                     e, traceback.format_exc())
        return None


@router.post("/simulate/natural", response_model=NaturalLanguageResponse)
async def natural_language_simulate(request: NaturalLanguageRequest):
    """Generate a quantum circuit from natural language and simulate it."""

    session_id, history = _get_or_create_session(request.session_id)

    # Call LLM
    user_message = {"role": "user", "content": request.prompt}
    llm_result = generate_circuit(
        messages=[user_message],
        session_history=history if history else None,
    )

    # Auto-simulate if circuit was generated
    simulation = None
    if llm_result["circuit"]:
        simulation = _simulate_circuit(llm_result["circuit"])
        if not simulation:
            llm_result["error"] = "Circuit generated but simulation failed"

    # Update session history
    history.append(user_message)
    history.append({
        "role": "assistant",
        "content": llm_result["raw_response"],
    })

    # Trim history to prevent context overflow
    while len(history) > MAX_HISTORY_PER_SESSION:
        history.pop(0)

    response = NaturalLanguageResponse(
        circuit=llm_result["circuit"],
        explanation=llm_result["explanation"],
        simulation=simulation,
        error=llm_result["error"],
    )
    # Attach session_id in metadata-like fashion via header
    # (or we include it in the response model — simpler)
    response_dict = response.model_dump()
    response_dict["session_id"] = session_id
    return response_dict
