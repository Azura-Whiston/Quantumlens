"""
LLM service — Claude API integration for natural language → quantum circuit.

Uses chain-of-thought prompting (research shows reasoning models score 78%
vs 19% for standard models on quantum tasks — QCoder benchmark).
All generated circuits are validated before returning.
"""
import os
import json
import re
import logging
import hashlib
from typing import Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Valid gates matching server/models/schemas.py GateStep validator
VALID_GATES = {
    'I', 'H', 'X', 'Y', 'Z', 'S', 'Sdg', 'T', 'Tdg', 'SX',
    'Rx', 'Ry', 'Rz', 'P', 'U3',
    'CNOT', 'CX', 'CZ', 'SWAP', 'TOFFOLI', 'CCX',
}

SYSTEM_PROMPT = """You are QuantumLens AI, an expert quantum computing assistant built into a quantum circuit simulator.

Your role:
1. Convert natural language descriptions into quantum circuits
2. Explain quantum concepts in plain, beginner-friendly language
3. Help users understand what their circuits do

When the user asks you to create or modify a circuit, you MUST respond with valid JSON in a ```json code block containing:
{
  "circuit": {
    "n_qubits": <int 1-25>,
    "steps": [
      {"gate": "<gate_name>", "target": <int>, "control": <int|null>, "angle": <float|null>}
    ]
  },
  "explanation": "<plain English explanation of what this circuit does and why each gate is used>"
}

Available gates:
- Single-qubit: I, H, X, Y, Z, S, Sdg, T, Tdg, SX
- Parametric (require "angle" in radians): Rx, Ry, Rz, P
- Two-qubit (require "control" and "target"): CNOT (or CX), CZ, SWAP
- Three-qubit (use "controls" array): TOFFOLI (or CCX)

Rules:
- All qubit indices are 0-based
- target, control indices must be < n_qubits
- For CNOT/CZ: use "control" and "target" fields
- For SWAP: use "control" and "target" (the two qubits to swap)
- For TOFFOLI: use "controls": [q0, q1] and "target": q2
- Angles are in radians. Use math: π ≈ 3.14159265
- Keep circuits minimal — don't add unnecessary gates
- Always explain your reasoning step by step

Common circuits you should know:
- Bell state (Φ+): H on q0, CNOT q0→q1. Creates maximal entanglement.
- GHZ state: H on q0, CNOT q0→q1, CNOT q0→q2. Multi-qubit entanglement.
- Superposition: H on each qubit. Equal probability of all states.
- Quantum teleportation: Bell pair + BSM + corrections
- Deutsch-Jozsa: H on all, oracle, H on all, measure
- Grover's search: H, oracle, diffusion operator, repeat
- QFT: H + controlled rotations + SWAP

When the user asks a question (not requesting a circuit), respond with just explanation text (no JSON block).

Think step by step before generating circuits. Consider what quantum state the user wants and which gates achieve it most efficiently."""

# In-memory cache for identical prompts
_response_cache: dict[str, dict] = {}
MAX_CACHE_SIZE = 100


def _cache_key(messages: list[dict]) -> str:
    """Generate cache key from conversation messages."""
    content = json.dumps(messages, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def _get_client() -> Anthropic:
    """Get Anthropic client. API key from environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Get your key at https://console.anthropic.com/settings/keys"
        )
    return Anthropic(api_key=api_key)


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON from Claude's response (from ```json blocks or raw JSON)."""
    # Try ```json code block first
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try raw JSON object
    match = re.search(r'\{[\s\S]*"circuit"[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _validate_circuit(data: dict) -> tuple[bool, str]:
    """Validate a generated circuit against our schema constraints."""
    if "circuit" not in data:
        return False, "No 'circuit' key in response"

    circuit = data["circuit"]
    n_qubits = circuit.get("n_qubits")
    if not isinstance(n_qubits, int) or n_qubits < 1 or n_qubits > 25:
        return False, f"Invalid n_qubits: {n_qubits} (must be 1-25)"

    steps = circuit.get("steps", [])
    if not steps:
        return False, "Circuit has no steps"
    if len(steps) > 500:
        return False, f"Too many steps: {len(steps)} (max 500)"

    for i, step in enumerate(steps):
        gate = step.get("gate")
        if gate not in VALID_GATES:
            return False, f"Step {i}: invalid gate '{gate}'"

        target = step.get("target")
        if target is not None and (target < 0 or target >= n_qubits):
            return False, f"Step {i}: target {target} out of range (n_qubits={n_qubits})"

        control = step.get("control")
        if control is not None and (control < 0 or control >= n_qubits):
            return False, f"Step {i}: control {control} out of range"

        controls = step.get("controls")
        if controls:
            for c in controls:
                if c < 0 or c >= n_qubits:
                    return False, f"Step {i}: control {c} out of range"

    return True, "OK"


def generate_circuit(
    messages: list[dict],
    session_history: Optional[list[dict]] = None,
) -> dict:
    """
    Call Claude API to generate a quantum circuit from conversation.

    Args:
        messages: Current conversation messages [{"role": "user"|"assistant", "content": "..."}]
        session_history: Previous messages for multi-turn context

    Returns:
        {
            "circuit": {"n_qubits": int, "steps": [...]} or None,
            "explanation": str,
            "raw_response": str,
            "error": str or None,
        }
    """
    # Build full conversation
    full_messages = []
    if session_history:
        full_messages.extend(session_history)
    full_messages.extend(messages)

    # Check cache
    cache_key = _cache_key(full_messages)
    if cache_key in _response_cache:
        logger.info("LLM cache hit")
        return _response_cache[cache_key]

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=full_messages,
        )
        raw_text = response.content[0].text
    except ValueError as e:
        # API key not set
        return {
            "circuit": None,
            "explanation": str(e),
            "raw_response": "",
            "error": str(e),
        }
    except Exception as e:
        logger.error("Claude API error: %s", e)
        return {
            "circuit": None,
            "explanation": f"Failed to reach Claude API: {e}",
            "raw_response": "",
            "error": str(e),
        }

    # Try to extract circuit JSON
    parsed = _extract_json(raw_text)
    result: dict

    if parsed and "circuit" in parsed:
        valid, msg = _validate_circuit(parsed)
        if valid:
            result = {
                "circuit": parsed["circuit"],
                "explanation": parsed.get("explanation", ""),
                "raw_response": raw_text,
                "error": None,
            }
        else:
            logger.warning("LLM generated invalid circuit: %s", msg)
            result = {
                "circuit": None,
                "explanation": f"I generated a circuit but it had an issue: {msg}. "
                               f"Here's what I was trying to do:\n\n{raw_text}",
                "raw_response": raw_text,
                "error": f"Validation failed: {msg}",
            }
    else:
        # No circuit in response — just an explanation/conversation
        result = {
            "circuit": None,
            "explanation": raw_text,
            "raw_response": raw_text,
            "error": None,
        }

    # Cache the result
    if len(_response_cache) >= MAX_CACHE_SIZE:
        # Evict oldest entry
        oldest = next(iter(_response_cache))
        del _response_cache[oldest]
    _response_cache[cache_key] = result

    return result
