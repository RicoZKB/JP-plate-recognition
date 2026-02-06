#!/usr/bin/env python3
"""
Rebuild TensorRT Engine - Optimized for Jetson TX1
- 4GB unified memory (shared CPU/GPU)
- Maxwell GPU architecture (256 CUDA cores)
- FP16 precision for faster inference
- Optimized workspace size for limited memory
"""

from ultralytics import YOLO
import os

print("=" * 60)
print("TensorRT Engine Rebuild - Optimized for Jetson TX1")
print("=" * 60)

# Model configuration
MODEL_PT = "models/best.pt"
ENGINE_OUTPUT = "models/best_optimized.engine"

# Jetson TX1 optimized settings
IMGSZ = 640  # Input size
FP16 = True  # Use FP16 for faster inference on TX1
WORKSPACE = 2  # Limited workspace (2GB) for 4GB unified memory
BATCH = 1  # Single batch for real-time
DEVICE = 0  # GPU device

print(f"\n[1/3] Loading PyTorch model: {MODEL_PT}")
if not os.path.exists(MODEL_PT):
    print(f"[ERROR] Model not found: {MODEL_PT}")
    exit(1)

model = YOLO(MODEL_PT)
print(f"  ✓ Model loaded: {MODEL_PT}")
print(f"  ✓ Task: {model.task}")
print(f"  ✓ Classes: {len(model.names)}")
print(f"  ✓ Class names: {model.names}")

print(f"\n[2/3] Exporting to TensorRT (optimized for TX1)...")
print(f"  - Input size: {IMGSZ}x{IMGSZ}")
print(f"  - FP16 precision: {FP16}")
print(f"  - Workspace: {WORKSPACE}GB")
print(f"  - Batch size: {BATCH}")
print(f"  - Device: {DEVICE}")
print(f"  This may take 5-10 minutes...")

try:
    # Export with TX1-optimized settings
    model.export(
        format='engine',
        imgsz=IMGSZ,
        half=FP16,
        workspace=WORKSPACE,
        batch=BATCH,
        device=DEVICE,
        simplify=True,  # Simplify ONNX graph
        verbose=True
    )

    # Rename to optimized name
    default_engine = MODEL_PT.replace('.pt', '.engine')
    if os.path.exists(default_engine):
        if os.path.exists(ENGINE_OUTPUT):
            os.remove(ENGINE_OUTPUT)
        os.rename(default_engine, ENGINE_OUTPUT)
        print(f"\n  ✓ TensorRT engine created: {ENGINE_OUTPUT}")
        print(f"  ✓ Size: {os.path.getsize(ENGINE_OUTPUT) / (1024*1024):.1f} MB")

except Exception as e:
    print(f"\n[ERROR] Export failed: {e}")
    print("\nTrying with reduced workspace...")
    try:
        model.export(
            format='engine',
            imgsz=IMGSZ,
            half=FP16,
            workspace=1,  # Reduce to 1GB workspace
            batch=BATCH,
            device=DEVICE,
            simplify=True,
            verbose=True
        )
        default_engine = MODEL_PT.replace('.pt', '.engine')
        if os.path.exists(default_engine):
            if os.path.exists(ENGINE_OUTPUT):
                os.remove(ENGINE_OUTPUT)
            os.rename(default_engine, ENGINE_OUTPUT)
            print(f"\n  ✓ TensorRT engine created: {ENGINE_OUTPUT}")
            print(f"  ✓ Size: {os.path.getsize(ENGINE_OUTPUT) / (1024*1024):.1f} MB")
    except Exception as e2:
        print(f"[ERROR] Export failed with reduced workspace: {e2}")
        exit(1)

print(f"\n[3/3] Testing new TensorRT engine...")
try:
    test_model = YOLO(ENGINE_OUTPUT)
    print(f"  ✓ Engine loads successfully")
    print(f"  ✓ Task: {test_model.task}")
    print(f"  ✓ Device: {test_model.device}")

    # Test inference
    import numpy as np
    test_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    results = test_model.predict(test_img, verbose=False)
    print(f"  ✓ Inference test successful")

except Exception as e:
    print(f"[ERROR] Engine test failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("SUCCESS: TensorRT engine optimized for Jetson TX1!")
print(f"New engine: {ENGINE_OUTPUT}")
print("=" * 60)
print("\nOptimizations applied:")
print("  ✓ FP16 precision (2x faster on TX1)")
print("  ✓ Limited workspace for 4GB unified memory")
print("  ✓ Simplified ONNX graph")
print("  ✓ Single batch for real-time inference")
print("\nExpected performance:")
print("  - Inference: ~40-60ms per frame")
print("  - FPS: ~15-20 FPS")
print("=" * 60)
