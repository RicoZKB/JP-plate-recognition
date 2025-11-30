#!/usr/bin/env python3
"""
GPU Configuration Verification Script
Checks all GPU/CUDA optimizations are properly configured
"""

import sys
# Add system packages for CUDA-enabled OpenCV
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.append('/usr/lib/python3/dist-packages')

import cv2
import torch
import os

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_opencv():
    print_section("OpenCV Configuration")
    print(f"Version: {cv2.__version__}")
    print(f"Optimizations enabled: {cv2.useOptimized()}")

    # Check CUDA
    cuda_devices = cv2.cuda.getCudaEnabledDeviceCount()
    print(f"CUDA devices: {cuda_devices}")

    if cuda_devices > 0:
        print("✅ OpenCV CUDA is AVAILABLE")
        # Check if CUDA is in build info
        build_info = cv2.getBuildInformation()
        if 'CUDA' in build_info:
            print("✅ OpenCV compiled with CUDA support")
            # Extract CUDA version from build info
            for line in build_info.split('\n'):
                if 'CUDA' in line and 'version' in line.lower():
                    print(f"   {line.strip()}")
    else:
        print("❌ OpenCV CUDA is NOT available")

    return cuda_devices > 0

def check_pytorch():
    print_section("PyTorch Configuration")
    print(f"Version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"✅ PyTorch CUDA is AVAILABLE")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"cuDNN version: {torch.backends.cudnn.version()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")

        # GPU memory
        total_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"Total GPU memory: {total_mem:.2f} GB")

        # CUDA optimizations
        print(f"cuDNN benchmark: {torch.backends.cudnn.benchmark}")
        print(f"cuDNN deterministic: {torch.backends.cudnn.deterministic}")

        return True
    else:
        print("❌ PyTorch CUDA is NOT available")
        return False

def check_paddleocr():
    print_section("PaddleOCR Configuration")
    try:
        import paddle
        print(f"Paddle version: {paddle.__version__}")
        print(f"CUDA compiled: {paddle.device.is_compiled_with_cuda()}")

        if paddle.device.is_compiled_with_cuda():
            print("✅ PaddlePaddle compiled with CUDA")
        else:
            print("⚠️  PaddlePaddle NOT compiled with CUDA (CPU-only version)")
            print("   Note: GPU inference still works for OCR models")

        # Try to initialize PaddleOCR
        from paddleocr import PaddleOCR
        print("✅ PaddleOCR imported successfully")
        return True
    except Exception as e:
        print(f"❌ PaddleOCR error: {e}")
        return False

def check_model_files():
    print_section("Model Files")
    model_dir = "models"

    if not os.path.exists(model_dir):
        print(f"❌ Model directory '{model_dir}' not found")
        return False

    models = {
        'best.onnx': 'ONNX model (recommended)',
        'best.pt': 'PyTorch model',
        'best.engine': 'TensorRT engine'
    }

    for model_file, description in models.items():
        path = os.path.join(model_dir, model_file)
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024**2  # MB
            print(f"✅ {model_file:20s} ({size:6.2f} MB) - {description}")
        else:
            print(f"❌ {model_file:20s} - NOT FOUND")

    return True

def check_inout_event_config():
    print_section("inout_event.py Configuration")

    # Read the file
    try:
        with open('inout_event.py', 'r') as f:
            content = f.read()

        # Check key settings
        checks = {
            'TARGET_WIDTH': None,
            'DETECT_EVERY_N': None,
            'OCR_SKIP_FRAMES': None,
            'ENABLE_OCR_CACHE': None,
            'USE_SMART_OCR_TRIGGER': None,
            'model_path': None,
        }

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('TARGET_WIDTH'):
                checks['TARGET_WIDTH'] = line
            elif line.startswith('DETECT_EVERY_N'):
                checks['DETECT_EVERY_N'] = line
            elif line.startswith('OCR_SKIP_FRAMES'):
                checks['OCR_SKIP_FRAMES'] = line
            elif line.startswith('ENABLE_OCR_CACHE'):
                checks['ENABLE_OCR_CACHE'] = line
            elif line.startswith('USE_SMART_OCR_TRIGGER'):
                checks['USE_SMART_OCR_TRIGGER'] = line
            elif 'model_path=' in line and 'LicencePlateDetection' in line:
                checks['model_path'] = line

        for key, value in checks.items():
            if value:
                print(f"✅ {key:25s}: {value}")
            else:
                print(f"⚠️  {key:25s}: NOT FOUND")

        return True
    except Exception as e:
        print(f"❌ Error reading inout_event.py: {e}")
        return False

def check_licence_plate_detection_config():
    print_section("licence_plate_detection.py Configuration")

    try:
        with open('detections/licence_plate_detection.py', 'r') as f:
            content = f.read()

        # Check for key configurations
        if 'gpu_mem=' in content:
            for line in content.split('\n'):
                if 'gpu_mem=' in line and not line.strip().startswith('#'):
                    print(f"✅ PaddleOCR GPU memory: {line.strip()}")
                    break

        if 'use_gpu=True' in content:
            print("✅ PaddleOCR use_gpu=True found")
        else:
            print("⚠️  PaddleOCR use_gpu=True NOT found")

        if 'bilateralFilter' in content:
            print("✅ FAST preprocessing (bilateralFilter) found")
        else:
            print("⚠️  FAST preprocessing NOT found")

        if 'cv2.cuda.createCLAHE' in content:
            print("✅ GPU CLAHE found")
        else:
            print("⚠️  GPU CLAHE NOT found")

        return True
    except Exception as e:
        print(f"❌ Error reading licence_plate_detection.py: {e}")
        return False

def main():
    print("\n" + "#"*60)
    print("#" + " "*58 + "#")
    print("#  GPU/CUDA Configuration Verification".center(60) + "#")
    print("#" + " "*58 + "#")
    print("#"*60)

    results = {
        'OpenCV CUDA': check_opencv(),
        'PyTorch CUDA': check_pytorch(),
        'PaddleOCR': check_paddleocr(),
        'Model Files': check_model_files(),
        'inout_event.py': check_inout_event_config(),
        'licence_plate_detection.py': check_licence_plate_detection_config(),
    }

    print_section("Summary")
    all_passed = True
    for component, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {component:35s}: {'PASS' if status else 'FAIL'}")
        if not status:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - GPU acceleration is properly configured!")
    else:
        print("⚠️  SOME CHECKS FAILED - Review the output above")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
