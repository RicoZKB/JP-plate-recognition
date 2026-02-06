#!/usr/bin/env python3
"""
Test script to verify TensorRT setup for license plate detection
Checks all dependencies and models before running the full pipeline
"""

import sys
import os

def check_imports():
    """Check if all required packages are installed"""
    print("\n" + "="*60)
    print("Checking Python Dependencies")
    print("="*60)

    checks = []

    # TensorRT
    try:
        import tensorrt as trt
        checks.append(("TensorRT", True, trt.__version__))
    except ImportError as e:
        checks.append(("TensorRT", False, str(e)))

    # PyCUDA
    try:
        import pycuda.driver as cuda
        import pycuda.autoinit
        checks.append(("PyCUDA", True, "OK"))
    except ImportError as e:
        checks.append(("PyCUDA", False, str(e)))

    # OpenCV
    try:
        import cv2
        checks.append(("OpenCV", True, cv2.__version__))
        # Check CUDA support
        try:
            cuda_count = cv2.cuda.getCudaEnabledDeviceCount()
            if cuda_count > 0:
                checks.append(("OpenCV CUDA", True, f"{cuda_count} GPU(s)"))
            else:
                checks.append(("OpenCV CUDA", False, "No CUDA devices"))
        except:
            checks.append(("OpenCV CUDA", False, "Not available"))
    except ImportError as e:
        checks.append(("OpenCV", False, str(e)))

    # NumPy
    try:
        import numpy as np
        checks.append(("NumPy", True, np.__version__))
    except ImportError as e:
        checks.append(("NumPy", False, str(e)))

    # Print results
    all_pass = True
    for name, passed, info in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {name:20s} : {info}")
        if not passed:
            all_pass = False

    return all_pass

def check_models():
    """Check if TensorRT models exist"""
    print("\n" + "="*60)
    print("Checking TensorRT Models")
    print("="*60)

    models = [
        ("YOLO TensorRT (FP32)", "models/best.engine"),
        ("YOLO TensorRT (FP16)", "models/best_fp16.engine"),
        ("OCR TensorRT (FP16)", "models/paddleocr_onnx/rec_japan_fp16.engine"),
        ("Japanese Dictionary", "models/paddleocr_onnx/japan_dict.txt"),
    ]

    found_yolo = False
    all_critical = True

    for name, path in models:
        exists = os.path.exists(path)
        if exists:
            size = os.path.getsize(path)
            size_mb = size / (1024 * 1024)
            print(f"✅ {name:30s} : {path} ({size_mb:.1f} MB)")
            if "YOLO" in name:
                found_yolo = True
        else:
            print(f"❌ {name:30s} : {path} (NOT FOUND)")
            if "YOLO" in name and not found_yolo:
                all_critical = False
            elif "OCR" in name or "Dictionary" in name:
                all_critical = False

    return all_critical and found_yolo

def check_gpu():
    """Check GPU availability"""
    print("\n" + "="*60)
    print("Checking GPU Status")
    print("="*60)

    try:
        import pycuda.driver as cuda
        import pycuda.autoinit

        device = cuda.Device(0)
        attrs = device.get_attributes()

        print(f"✅ Device Name        : {device.name()}")
        print(f"✅ Compute Capability : {device.compute_capability()}")
        print(f"✅ Total Memory       : {device.total_memory() / (1024**3):.2f} GB")
        print(f"✅ Multiprocessors    : {attrs[cuda.device_attribute.MULTIPROCESSOR_COUNT]}")

        return True
    except Exception as e:
        print(f"❌ GPU check failed: {e}")
        return False

def test_detector():
    """Test detector initialization"""
    print("\n" + "="*60)
    print("Testing Detector Initialization")
    print("="*60)

    try:
        from detections.licence_plate_detection import LicencePlateDetection

        # Find YOLO model
        yolo_model = None
        for path in ["models/best.engine", "models/best_fp16.engine"]:
            if os.path.exists(path):
                yolo_model = path
                break

        if not yolo_model:
            print("❌ No YOLO TensorRT engine found")
            return False

        print(f"[INFO] Using YOLO model: {yolo_model}")

        detector = LicencePlateDetection(
            model_path=yolo_model,
            ocr_engine_path="models/paddleocr_onnx/rec_japan_fp16.engine",
            verbose=True
        )

        print("\n✅ Detector initialized successfully!")

        # Test with dummy frame
        import numpy as np
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        print("\n[INFO] Testing detection on dummy frame...")
        bboxes, texts = detector.detect_frame(dummy_frame)

        print(f"✅ Detection test passed! Found {len(bboxes)} plates (expected 0 on blank frame)")

        return True

    except Exception as e:
        print(f"❌ Detector initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("TensorRT License Plate Detection Setup Verification")
    print("="*60)

    results = []

    # Check imports
    results.append(("Dependencies", check_imports()))

    # Check GPU
    results.append(("GPU", check_gpu()))

    # Check models
    results.append(("Models", check_models()))

    # Test detector
    results.append(("Detector", test_detector()))

    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    all_pass = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8s} : {name}")
        if not passed:
            all_pass = False

    print("\n" + "="*60)
    if all_pass:
        print("✅ All checks passed! System is ready.")
        print("\nRun the detection pipeline with:")
        print("  ./run_tensorrt_fr01.sh")
        print("or:")
        print("  python3 fr01.py")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
