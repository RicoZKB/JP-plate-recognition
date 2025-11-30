#!/bin/bash
# Optimized runner for inout_event.py with TensorRT on Jetson
# Fixes TLS error by preloading libGLdispatch before Python starts

# Activate virtual environment
source ../myenv/bin/activate

# Set LD_PRELOAD to fix TensorRT TLS error on Jetson
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0

# Run the script with all GPU/CUDA/TensorRT optimizations
echo "[INFO] Running with LD_PRELOAD=$LD_PRELOAD"
echo "[INFO] Activating GPU + CUDA + TensorRT optimizations..."

python inout_event.py "$@"
