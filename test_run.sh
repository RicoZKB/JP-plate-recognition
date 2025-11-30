#!/bin/bash

# ========================================
# TEST RUN SCRIPT - License Plate Detection
# ========================================
# This script helps you test the system easily
# Created for learning and testing

echo "=========================================="
echo "  License Plate Detection - TEST MODE"
echo "=========================================="
echo ""

# Step 1: Navigate to project directory
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording

echo "[1/5] Current directory: $(pwd)"
echo ""

# Step 2: Activate virtual environment
echo "[2/5] Activating virtual environment..."
source ../myenv/bin/activate

if [ $? -eq 0 ]; then
    echo "✓ Virtual environment activated"
else
    echo "✗ Failed to activate virtual environment"
    exit 1
fi
echo ""

# Step 3: Set GPU workaround for Jetson
echo "[3/5] Setting up GPU optimizations..."
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0
echo "✓ LD_PRELOAD set for TensorRT compatibility"
echo ""

# Step 4: Display current configuration
echo "[4/5] System Configuration:"
echo "  - Python: $(python --version 2>&1)"
echo "  - Input: Video file (Trim03.mp4)"
echo "  - Mode: IN_ONLY direction"
echo "  - Model: ONNX (you can change to TensorRT)"
echo ""

# Step 5: Run the detection system
echo "[5/5] Starting license plate detection..."
echo "=========================================="
echo "Press Ctrl+C to stop the program"
echo "=========================================="
echo ""

# Run the main script
python3 inout_event.py

# Cleanup
echo ""
echo "=========================================="
echo "Program stopped."
echo "Check logs in: logs/parking_log_*.csv"
echo "=========================================="

deactivate
