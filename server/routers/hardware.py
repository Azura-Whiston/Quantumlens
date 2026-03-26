"""
/hardware and /presets endpoints.
"""
from fastapi import APIRouter
from server.models.schemas import HardwareResponse, PresetCircuit
from server.services.presets import PRESET_CIRCUITS
from quantum_engine.engine import get_engine

router = APIRouter()


@router.get("/hardware", response_model=HardwareResponse)
async def get_hardware():
    """Return system hardware capabilities and simulation limits."""
    engine = get_engine()
    caps = engine.get_capabilities()
    return HardwareResponse(**caps)


@router.get("/presets", response_model=list[PresetCircuit])
async def get_presets():
    """Return all preset circuits."""
    return [PresetCircuit(**p) for p in PRESET_CIRCUITS]
