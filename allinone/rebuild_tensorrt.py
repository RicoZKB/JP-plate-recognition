#!/usr/bin/env python3
"""
Rebuild TensorRT engine with proper metadata
"""
import sys
sys.path.append('/usr/lib/python3/dist-packages')

from ultralytics import YOLO
import torch

print("=" * 60)
print("TensorRT Engine Rebuild")
print("=" * 60)

# Load PyTorch model
print("\n[1/3] Loading PyTorch model...")
model = YOLO('models/best.pt')
print(f"  ✓ Model loaded: {model.ckpt_path}")
print(f"  ✓ Task: {model.task}")
print(f"  ✓ Model type: {type(model.model)}")

# Export to TensorRT with proper settings
print("\n[2/3] Exporting to TensorRT FP16...")
print("  This may take several minutes...")

try:
    # Export with metadata preservation
    engine_path = model.export(
        format='engine',          # TensorRT format
        half=True,                # FP16 precision
        device=0,                 # GPU 0
        workspace=4,              # 4GB workspace
        verbose=True,             # Show export details
        simplify=True,            # Simplify ONNX model
        dynamic=False,            # Static shapes for better performance
        imgsz=640,                # Input size
    )
    print(f"\n  ✓ TensorRT engine exported: {engine_path}")

    # Test the new engine
    print("\n[3/3] Testing new TensorRT engine...")
    test_model = YOLO(engine_path)
    print(f"  ✓ Engine loads successfully")
    print(f"  ✓ Task: {test_model.task}")
    print(f"  ✓ Device: {test_model.device}")

    print("\n" + "=" * 60)
    print("SUCCESS: TensorRT engine rebuilt with metadata!")
    print(f"New engine: {engine_path}")
    print("=" * 60)

except Exception as e:
    print(f"\n  ✗ Export failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
