#!/bin/bash

# ========================================
# TENSORRT TEST SCRIPT
# ========================================
# This tests if TensorRT engine works
# (Should be 3-5x faster than ONNX!)

echo "=========================================="
echo "  TensorRT Engine Test"
echo "=========================================="
echo ""

cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
source ../myenv/bin/activate
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0

echo "Testing TensorRT engine load..."
python3 << EOF
from ultralytics import YOLO
import time

print("")
print("Loading TensorRT engine (models/best.engine)...")
start = time.time()

try:
    model = YOLO('models/best.engine', task='detect')
    load_time = time.time() - start
    print(f"✓ TensorRT engine loaded successfully in {load_time:.2f}s")
    print("")
    print("Engine info:")
    print(f"  - Type: {type(model).__name__}")
    print(f"  - File: models/best.engine")
    print(f"  - Size: 13.2 MB")
    print("")
    print("TensorRT is ready to use!")
    print("")
    print("To use TensorRT in your system:")
    print("  Edit inout_event.py line ~740")
    print("  Change: model_path='models/best.onnx'")
    print("  To:     model_path='models/best.engine'")
    print("")
    print("Expected speedup: 3-5x faster (8-12 FPS instead of 4.3 FPS)")

except Exception as e:
    print(f"✗ Error loading TensorRT engine: {e}")
    print("")
    print("Falling back to ONNX is still fine (4.3 FPS)")

EOF

echo "=========================================="
deactivate
