"""
Hardware detection and simulation strategy selection.

Detects GPU availability, VRAM, cuQuantum, CPU threads, RAM.
Selects optimal simulation method/device/precision for a given circuit.
"""
import os
import sys
import logging

# Auto-configure CUDA DLL paths for pip-installed nvidia packages (Windows)
def _setup_cuda_paths():
    """Find nvidia CUDA DLLs installed via pip and add them to PATH."""
    try:
        import site
        for sp in site.getsitepackages():
            nvrtc_bin = os.path.join(sp, "nvidia", "cuda_nvrtc", "bin")
            if os.path.isdir(nvrtc_bin):
                os.environ.setdefault("CUDA_PATH", os.path.dirname(nvrtc_bin))
                if nvrtc_bin not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = nvrtc_bin + os.pathsep + os.environ["PATH"]
                return
    except Exception:
        pass

_setup_cuda_paths()
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Device(Enum):
    CPU = "cpu"
    GPU = "gpu"


class Method(Enum):
    STATEVECTOR = "statevector"
    DENSITY_MATRIX = "density_matrix"
    TENSOR_NETWORK = "tensor_network"
    KRAUS_STATEVECTOR = "kraus_statevector"


class Precision(Enum):
    FP32 = "fp32"
    FP64 = "fp64"


@dataclass
class HardwareInfo:
    has_gpu: bool = False
    gpu_name: str = ""
    gpu_vram_gb: float = 0.0
    has_cuquantum: bool = False
    cpu_threads: int = 1
    ram_gb: float = 16.0


def detect_hardware() -> HardwareInfo:
    """Probe system for GPU, cuQuantum, CPU, and RAM capabilities."""
    info = HardwareInfo()
    info.cpu_threads = os.cpu_count() or 1

    try:
        import psutil
        info.ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        info.ram_gb = 16.0

    try:
        import cupy as cp
        props = cp.cuda.runtime.getDeviceProperties(0)
        info.has_gpu = True
        name = props['name']
        info.gpu_name = name.decode() if isinstance(name, bytes) else name
        info.gpu_vram_gb = props['totalGlobalMem'] / (1024 ** 3)
        logger.info("GPU detected: %s (%.1f GB)", info.gpu_name, info.gpu_vram_gb)
    except Exception as e:
        logger.info("No GPU available: %s", e)

    try:
        from cuquantum import custatevec  # noqa: F401
        info.has_cuquantum = True
        logger.info("cuQuantum available")
    except ImportError:
        logger.info("cuQuantum not available")

    return info


@dataclass
class SimulationStrategy:
    method: Method
    device: Device
    precision: Precision
    estimated_memory_gb: float
    estimated_time_sec: float


def select_strategy(
    n_qubits: int,
    circuit_depth: int = 10,
    noise: bool = False,
    hardware: HardwareInfo = None,
) -> SimulationStrategy:
    """
    Select optimal simulation strategy for the given parameters.

    Priority order:
    1. GPU state vector (fastest for small-medium circuits)
    2. CPU state vector (large circuits that don't fit GPU)
    3. Tensor network (very large circuits, placeholder)

    For noise: prefer density matrix when it fits, else Kraus approximation.
    """
    if hardware is None:
        hardware = detect_hardware()

    gpu_vram = hardware.gpu_vram_gb * 0.85 if hardware.has_gpu else 0
    cpu_ram = hardware.ram_gb * 0.75

    sv_fp64 = (2 ** n_qubits * 16) / (1024 ** 3)
    sv_fp32 = (2 ** n_qubits * 8) / (1024 ** 3)
    dm_fp64 = (2 ** (2 * n_qubits) * 16) / (1024 ** 3)
    dm_fp32 = (2 ** (2 * n_qubits) * 8) / (1024 ** 3)

    # Rough FLOPS estimates for time prediction
    gpu_flops = 10e12
    cpu_flops = 0.5e12

    def _est_time(mem_gb, flops):
        ops = 2 ** n_qubits * circuit_depth * 8
        return ops / flops

    # --- Noise path: density matrix preferred ---
    if noise:
        if hardware.has_gpu and dm_fp64 < gpu_vram:
            return SimulationStrategy(
                Method.DENSITY_MATRIX, Device.GPU, Precision.FP64,
                dm_fp64, _est_time(dm_fp64, gpu_flops))
        if hardware.has_gpu and dm_fp32 < gpu_vram:
            return SimulationStrategy(
                Method.DENSITY_MATRIX, Device.GPU, Precision.FP32,
                dm_fp32, _est_time(dm_fp32, gpu_flops))
        if dm_fp64 < cpu_ram:
            return SimulationStrategy(
                Method.DENSITY_MATRIX, Device.CPU, Precision.FP64,
                dm_fp64, _est_time(dm_fp64, cpu_flops))
        # Fall back to Kraus approximation with state vector
        if hardware.has_gpu and sv_fp64 < gpu_vram:
            return SimulationStrategy(
                Method.KRAUS_STATEVECTOR, Device.GPU, Precision.FP64,
                sv_fp64 * 2, _est_time(sv_fp64, gpu_flops))
        return SimulationStrategy(
            Method.KRAUS_STATEVECTOR, Device.CPU, Precision.FP64,
            sv_fp64 * 2, _est_time(sv_fp64, cpu_flops))

    # --- Pure state path ---
    if hardware.has_gpu and sv_fp64 < gpu_vram:
        return SimulationStrategy(
            Method.STATEVECTOR, Device.GPU, Precision.FP64,
            sv_fp64, _est_time(sv_fp64, gpu_flops))
    if hardware.has_gpu and sv_fp32 < gpu_vram:
        return SimulationStrategy(
            Method.STATEVECTOR, Device.GPU, Precision.FP32,
            sv_fp32, _est_time(sv_fp32, gpu_flops))
    if sv_fp64 < cpu_ram:
        return SimulationStrategy(
            Method.STATEVECTOR, Device.CPU, Precision.FP64,
            sv_fp64, _est_time(sv_fp64, cpu_flops))
    if sv_fp32 < cpu_ram:
        return SimulationStrategy(
            Method.STATEVECTOR, Device.CPU, Precision.FP32,
            sv_fp32, _est_time(sv_fp32, cpu_flops))
    if n_qubits <= 60:
        tn_mem = n_qubits * circuit_depth * 0.001
        return SimulationStrategy(
            Method.TENSOR_NETWORK,
            Device.GPU if hardware.has_gpu else Device.CPU,
            Precision.FP64, tn_mem, circuit_depth * 0.1)

    raise ValueError(
        f"Cannot simulate {n_qubits} qubits with "
        f"{hardware.gpu_vram_gb:.1f}GB GPU and {hardware.ram_gb:.1f}GB RAM"
    )
