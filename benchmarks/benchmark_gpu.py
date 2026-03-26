"""
QuantumLens GPU vs CPU Benchmark.

Tests state vector simulation at various qubit counts and circuit depths.
Validates correctness (GPU results must match CPU results).
Reports speedup factors.
"""
import os
import sys
import time
import numpy as np

# Ensure CuPy can find CUDA DLLs
_venv = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_nvrtc_bin = os.path.join(_venv, ".venv", "Lib", "site-packages", "nvidia", "cuda_nvrtc", "bin")
if os.path.isdir(_nvrtc_bin):
    os.environ.setdefault("CUDA_PATH", os.path.dirname(_nvrtc_bin))
    os.environ["PATH"] = _nvrtc_bin + os.pathsep + os.environ.get("PATH", "")

from quantum_engine.statevector import StateVectorSimulator
from quantum_engine.config import Device, Precision, detect_hardware


def generate_random_circuit(n_qubits: int, depth: int) -> list:
    """Generate a random circuit with H and CNOT gates."""
    steps = []
    for _ in range(depth):
        # Random H gate
        steps.append({'gate': 'H', 'target': int(np.random.randint(n_qubits))})
        # Random CNOT if multi-qubit
        if n_qubits > 1:
            c, t = np.random.choice(n_qubits, 2, replace=False)
            steps.append({'gate': 'CNOT', 'control': int(c), 'target': int(t)})
    return steps


def benchmark_single(n_qubits: int, depth: int, warmup: bool = True):
    """Run a single benchmark comparing GPU vs CPU."""
    steps = generate_random_circuit(n_qubits, depth)
    n_gates = len(steps)

    # GPU warm-up (first CuPy call has kernel compilation overhead)
    if warmup:
        try:
            sim = StateVectorSimulator(2, Device.GPU, Precision.FP64)
            sim.run_circuit([{'gate': 'H', 'target': 0}], save_intermediate=False)
            sim.cleanup()
        except Exception:
            pass

    # GPU benchmark
    gpu_time = None
    gpu_probs = None
    try:
        t0 = time.perf_counter()
        sim_gpu = StateVectorSimulator(n_qubits, Device.GPU, Precision.FP64)
        res_gpu = sim_gpu.run_circuit(steps, save_intermediate=False)
        gpu_time = time.perf_counter() - t0
        gpu_probs = res_gpu.probabilities
        sim_gpu.cleanup()
    except Exception as e:
        print(f"  GPU failed: {e}")

    # CPU benchmark
    t0 = time.perf_counter()
    sim_cpu = StateVectorSimulator(n_qubits, Device.CPU, Precision.FP64)
    res_cpu = sim_cpu.run_circuit(steps, save_intermediate=False)
    cpu_time = time.perf_counter() - t0
    cpu_probs = res_cpu.probabilities

    # Validate correctness
    correct = True
    if gpu_probs is not None:
        correct = np.allclose(gpu_probs, cpu_probs, atol=1e-8)

    # Calculate speedup
    speedup = None
    if gpu_time is not None and gpu_time > 0:
        speedup = cpu_time / gpu_time

    return {
        'n_qubits': n_qubits,
        'depth': depth,
        'n_gates': n_gates,
        'cpu_time': cpu_time,
        'gpu_time': gpu_time,
        'speedup': speedup,
        'correct': correct,
        'prob_sum_cpu': float(np.sum(cpu_probs)),
        'prob_sum_gpu': float(np.sum(gpu_probs)) if gpu_probs is not None else None,
    }


def main():
    hw = detect_hardware()
    print("=" * 60)
    print("QuantumLens GPU Benchmark")
    print("=" * 60)
    print(f"GPU: {hw.gpu_name} ({hw.gpu_vram_gb:.1f} GB VRAM)")
    print(f"CPU: {hw.cpu_threads} threads, {hw.ram_gb:.1f} GB RAM")
    print(f"cuQuantum: {hw.has_cuquantum}")
    print()

    # Warm up GPU
    print("Warming up GPU (kernel compilation)...")
    try:
        sim = StateVectorSimulator(5, Device.GPU, Precision.FP64)
        steps = generate_random_circuit(5, 20)
        sim.run_circuit(steps, save_intermediate=False)
        sim.cleanup()
        print("GPU warm-up complete.")
    except Exception as e:
        print(f"GPU warm-up failed: {e}")
    print()

    # Benchmark matrix
    configs = [
        # (qubits, depth)
        (10, 50),
        (12, 50),
        (14, 50),
        (16, 50),
        (18, 50),
        (20, 50),
        (20, 200),
        (22, 50),
        (23, 50),
        (24, 50),
        (25, 50),
    ]

    print(f"{'Qubits':>6} {'Depth':>6} {'Gates':>6} {'CPU (s)':>10} {'GPU (s)':>10} {'Speedup':>10} {'Correct':>8} {'P(sum)':>8}")
    print("-" * 72)

    results = []
    for n_qubits, depth in configs:
        # Check if we can fit in memory
        mem_gb = (2 ** n_qubits * 16) / (1024 ** 3)
        if mem_gb > hw.ram_gb * 0.75:
            print(f"{n_qubits:>6} {'SKIP':>6} - state vector too large ({mem_gb:.1f} GB)")
            continue

        r = benchmark_single(n_qubits, depth, warmup=False)
        results.append(r)

        speedup_str = f"{r['speedup']:.2f}x" if r['speedup'] is not None else "N/A"
        gpu_str = f"{r['gpu_time']:.4f}" if r['gpu_time'] is not None else "N/A"
        correct_str = "OK" if r['correct'] else "FAIL"
        psum = f"{r['prob_sum_cpu']:.6f}"

        print(f"{r['n_qubits']:>6} {r['depth']:>6} {r['n_gates']:>6} {r['cpu_time']:>10.4f} {gpu_str:>10} {speedup_str:>10} {correct_str:>8} {psum:>8}")

    print()
    print("=" * 60)
    print("Summary:")

    # Find crossover point
    crossover = None
    for r in results:
        if r['speedup'] is not None and r['speedup'] > 1.0:
            crossover = r['n_qubits']
            break

    if crossover:
        print(f"  GPU becomes faster at {crossover}+ qubits")
    else:
        print("  GPU did not outperform CPU in this benchmark")

    # All correct?
    all_correct = all(r['correct'] for r in results)
    print(f"  All results match CPU/GPU: {'YES' if all_correct else 'NO'}")

    # Peak speedup
    speedups = [r['speedup'] for r in results if r['speedup'] is not None]
    if speedups:
        print(f"  Peak GPU speedup: {max(speedups):.2f}x at {results[[r['speedup'] for r in results].index(max(speedups))]['n_qubits']} qubits")

    print()


if __name__ == "__main__":
    main()
