"""
Unified simulation interface.

Single entry point for all simulation requests.
Automatically selects backend (state vector, density matrix, tensor network)
and device (CPU, GPU) based on circuit parameters and available hardware.
"""
import logging
import numpy as np
from typing import List, Optional, Dict, Any

from .config import (
    detect_hardware, select_strategy, HardwareInfo,
    Method, Device, Precision, SimulationStrategy,
)
from .statevector import StateVectorSimulator, SimulationResult

logger = logging.getLogger(__name__)

_hardware: Optional[HardwareInfo] = None


def get_hardware() -> HardwareInfo:
    global _hardware
    if _hardware is None:
        _hardware = detect_hardware()
    return _hardware


class QuantumEngine:
    """
    High-level quantum simulation engine.
    Wraps strategy selection and simulator dispatch.
    """

    def __init__(self):
        self.hardware = get_hardware()

    def simulate(
        self,
        n_qubits: int,
        steps: List[dict],
        noise_model: Optional[Dict[str, tuple]] = None,
        save_intermediate: bool = True,
        force_device: Optional[str] = None,
        force_method: Optional[str] = None,
        shots: Optional[int] = None,
    ) -> SimulationResult:
        """
        Run a quantum circuit simulation.

        This is the single entry point. It:
        1. Selects the optimal strategy (method + device + precision)
        2. Creates the appropriate simulator
        3. Runs the circuit
        4. Optionally samples
        5. Returns the result
        """
        strategy = select_strategy(
            n_qubits,
            circuit_depth=len(steps),
            noise=noise_model is not None,
            hardware=self.hardware,
        )

        if force_device:
            strategy.device = Device(force_device)
        if force_method:
            strategy.method = Method(force_method)

        logger.info(
            "Simulation: %d qubits, %d gates, method=%s, device=%s, "
            "precision=%s, est_mem=%.2fGB",
            n_qubits, len(steps), strategy.method.value,
            strategy.device.value, strategy.precision.value,
            strategy.estimated_memory_gb,
        )

        # Dispatch
        if strategy.method in (Method.STATEVECTOR, Method.KRAUS_STATEVECTOR):
            sim = StateVectorSimulator(
                n_qubits, strategy.device, strategy.precision)
            result = sim.run_circuit(steps, noise_model, save_intermediate)

            if shots:
                sim2 = StateVectorSimulator(
                    n_qubits, strategy.device, strategy.precision)
                non_measure = [s for s in steps if s['gate'] != 'MEASURE']
                sim2.run_circuit(non_measure, noise_model, False)
                result.metadata['counts'] = sim2.sample(shots)
                sim2.cleanup()

            sim.cleanup()
            return result

        elif strategy.method == Method.DENSITY_MATRIX:
            logger.warning(
                "Density matrix not yet implemented, "
                "falling back to Kraus state vector approximation")
            sim = StateVectorSimulator(
                n_qubits, strategy.device, strategy.precision)
            result = sim.run_circuit(steps, noise_model, save_intermediate)
            sim.cleanup()
            return result

        elif strategy.method == Method.TENSOR_NETWORK:
            raise NotImplementedError(
                f"Tensor network simulation for {n_qubits} qubits "
                f"is planned but not yet implemented. "
                f"Max state vector: ~{25 if self.hardware.has_gpu else 30} qubits."
            )

        raise ValueError(f"Unknown method: {strategy.method}")

    def get_capabilities(self) -> dict:
        """Return hardware capabilities and limits for the /hardware endpoint."""
        hw = self.hardware

        max_cpu = 0
        if hw.ram_gb > 0:
            usable = hw.ram_gb * 0.75
            if usable > 0:
                max_cpu = min(31, int(np.log2(usable * 1024**3 / 16)))

        max_gpu_64 = 0
        max_gpu_32 = 0
        if hw.has_gpu and hw.gpu_vram_gb > 0:
            usable_gpu = hw.gpu_vram_gb * 0.85
            if usable_gpu > 0:
                max_gpu_64 = int(np.log2(usable_gpu * 1024**3 / 16))
                max_gpu_32 = int(np.log2(usable_gpu * 1024**3 / 8))

        return {
            'gpu': {
                'available': hw.has_gpu,
                'name': hw.gpu_name,
                'vram_gb': round(hw.gpu_vram_gb, 1),
                'max_qubits_sv_fp64': max_gpu_64,
                'max_qubits_sv_fp32': max_gpu_32,
            },
            'cpu': {
                'threads': hw.cpu_threads,
                'ram_gb': round(hw.ram_gb, 1),
                'max_qubits_sv_fp64': max_cpu,
            },
            'cuquantum': hw.has_cuquantum,
            'methods': ['statevector', 'kraus_statevector'],
        }


_engine: Optional[QuantumEngine] = None


def get_engine() -> QuantumEngine:
    global _engine
    if _engine is None:
        _engine = QuantumEngine()
    return _engine
