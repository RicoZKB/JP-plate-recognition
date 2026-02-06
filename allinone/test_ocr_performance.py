#!/usr/bin/env python3
"""
Test OCR Performance - Option A vs Current
Measures OCR speed with GPU vs CPU PaddlePaddle
"""

import time
import sys
import cv2
import numpy as np

# Add path for imports
sys.path.insert(0, '/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording')

from detections import LicencePlateDetection

def create_fake_plate_image():
    """Create a synthetic license plate image for testing."""
    # Create white background
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255

    # Draw a fake plate region (green rectangle)
    cv2.rectangle(img, (150, 180), (490, 300), (0, 255, 0), 2)

    # Add some text to simulate plate
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "Test Plate", (170, 230), font, 1.2, (0, 0, 0), 2)
    cv2.putText(img, "123-4567", (180, 280), font, 1.0, (0, 0, 0), 2)

    return img

def test_detection_speed(num_iterations=10):
    """Test detection and OCR speed."""
    print("=" * 80)
    print("OCR Performance Test - Option A (GPU PaddlePaddle)")
    print("=" * 80)

    # Create test image
    test_img = create_fake_plate_image()

    # Initialize detector
    print("\n[1/3] Loading ONNX model and GPU PaddleOCR...")
    start_init = time.time()
    detector = LicencePlateDetection(
        model_path="models/best.onnx",
        verbose=False,
        debug_ocr=False
    )
    init_time = time.time() - start_init
    print(f"✓ Initialization time: {init_time:.2f}s")

    # Warm-up runs (models need to warm up)
    print("\n[2/3] Warming up models...")
    for i in range(3):
        _ = detector.detect_frame(test_img)
    print("✓ Warm-up complete")

    # Performance test
    print(f"\n[3/3] Running {num_iterations} detection cycles...")

    detection_times = []
    total_start = time.time()

    for i in range(num_iterations):
        iter_start = time.time()
        bboxes, texts = detector.detect_frame(test_img)
        iter_time = (time.time() - iter_start) * 1000  # Convert to ms
        detection_times.append(iter_time)

        print(f"  Iteration {i+1}/{num_iterations}: {iter_time:.1f}ms")

    total_time = time.time() - total_start

    # Calculate statistics
    avg_time = np.mean(detection_times)
    min_time = np.min(detection_times)
    max_time = np.max(detection_times)
    fps = 1000.0 / avg_time if avg_time > 0 else 0

    # Results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Average inference time: {avg_time:.1f}ms")
    print(f"Min inference time:     {min_time:.1f}ms")
    print(f"Max inference time:     {max_time:.1f}ms")
    print(f"Estimated FPS:          {fps:.1f}")
    print(f"Total test time:        {total_time:.2f}s")

    print("\n" + "=" * 80)
    print("COMPARISON WITH BASELINE (CPU PaddlePaddle)")
    print("=" * 80)
    print("Baseline (myenv CPU):   ~1500ms OCR → 0.6 FPS")
    print(f"Current (GPU):          ~{avg_time:.0f}ms total → {fps:.1f} FPS")

    if avg_time < 150:
        speedup = 1500.0 / avg_time
        print(f"\n✅ SUCCESS! {speedup:.1f}x faster than CPU version!")
        print("   Option A achieved target performance (10-15 FPS)")
    elif avg_time < 300:
        speedup = 1500.0 / avg_time
        print(f"\n⚠️  PARTIAL SUCCESS: {speedup:.1f}x faster than CPU")
        print("   Performance improved but below target")
        print("   Consider Option B (TensorRT OCR) for further improvement")
    else:
        print(f"\n❌ PERFORMANCE ISSUE: Still too slow")
        print("   Proceed to Option B (TensorRT OCR rebuild)")

    print("=" * 80)

if __name__ == "__main__":
    try:
        test_detection_speed(num_iterations=10)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
