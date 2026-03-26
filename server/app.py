"""
FastAPI application — QuantumLens API server.
"""
import os
import sys
import logging

# Ensure CuPy can find CUDA DLLs from pip-installed nvidia packages
_venv = os.path.dirname(os.path.dirname(sys.executable))
_nvrtc_bin = os.path.join(_venv, "Lib", "site-packages", "nvidia", "cuda_nvrtc", "bin")
if os.path.isdir(_nvrtc_bin):
    os.environ.setdefault("CUDA_PATH", os.path.dirname(_nvrtc_bin))
    os.environ["PATH"] = _nvrtc_bin + os.pathsep + os.environ.get("PATH", "")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routers import simulate, hardware, natural

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = FastAPI(
    title="QuantumLens API",
    description="GPU-accelerated quantum circuit simulation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulate.router, tags=["Simulation"])
app.include_router(hardware.router, tags=["System"])
app.include_router(natural.router, tags=["Natural Language"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "quantumlens"}
