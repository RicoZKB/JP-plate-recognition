#!/usr/bin/env python3
"""
Test script to verify TensorRT OCR integration with license plate detection.
This script tests both standard and aggressive preprocessing modes.
"""

import sys
import cv2
import numpy as np
from detections.licence_plate_detection import LicencePlateDetection

def create_test_image():
    """Create a synthetic Japanese license plate image for testing."""
    # Create white background (Japanese plates are white)
    img = np.ones((120, 330, 3), dtype=np.uint8) * 255

    # Add black border
    cv2.rectangle(img, (5, 5), (325, 115), (0, 0, 0), 2)

    # Add Japanese plate text: "山口 589 さ 20-46"
    font = cv2.FONT_HERSHEY_SIMPLEX

    # City name (山口)
    cv2.putText(img, "山口", (15, 50), font, 1.2, (0, 0, 0), 2)

    # Class number (589)
    cv2.putText(img, "589", (110, 50), font, 1.2, (0, 0, 0), 2)

    # Kana (さ) - small character
    cv2.putText(img, "さ", (210, 50), font, 0.8, (0, 0, 0), 2)

    # Suffix (20-46)
    cv2.putText(img, "20-46", (180, 95), font, 1.0, (0, 0, 0), 2)

    return img

def test_mode(detector_type, aggressive):
    """Test OCR with specified mode."""
    mode_name = f"{detector_type} - {'Aggressive' if aggressive else 'Standard'}"
    print("\n" + "=" * 80)
    print(f"Testing: {mode_name}")
    print("=" * 80)

    try:
        # Initialize detector
        use_trt = (detector_type == "TensorRT")
        detector = LicencePlateDetection(
            model_path="models/best_2026.engine",
            use_tensorrt_ocr=use_trt,
            aggressive_kana_preprocess=aggressive,
            verbose=False,
            debug_ocr=False
        )

        # Create test image
        test_img = create_test_image()

        # Save test image for reference
        cv2.imwrite(f"test_plate_{detector_type.lower()}_{'' if aggressive else 'not_'}aggressive.jpg", test_img)

        # Run detection
        print(f"\nRunning detection...")
        bboxes, texts = detector.detect_frame(test_img)

        # Display results
        print(f"  Found {len(bboxes)} plates")
        for i, (bbox, text) in enumerate(zip(bboxes, texts)):
            print(f"  Plate {i+1}:")
            print(f"    BBox: {bbox}")
            print(f"    Text: '{text}'")

        # Check if hiragana detected
        has_hiragana = False
        for text in texts:
            if any('\u3040' <= char <= '\u309F' for char in text):  # Hiragana range
                has_hiragana = True
                break

        print(f"\n  Hiragana detected: {'YES ✅' if has_hiragana else 'NO ❌'}")

        return True, has_hiragana

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, False

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("TensorRT OCR Integration Test")
    print("=" * 80)
    print("\nThis test compares:")
    print("  1. PaddleOCR (baseline)")
    print("  2. TensorRT OCR - Standard mode (fast)")
    print("  3. TensorRT OCR - Aggressive mode (hiragana-optimized)")
    print()

    results = {}

    # Test 1: PaddleOCR baseline
    success, has_kana = test_mode("PaddleOCR", aggressive=False)
    results["PaddleOCR"] = (success, has_kana)

    # Test 2: TensorRT standard
    success, has_kana = test_mode("TensorRT", aggressive=False)
    results["TensorRT Standard"] = (success, has_kana)

    # Test 3: TensorRT aggressive
    success, has_kana = test_mode("TensorRT", aggressive=True)
    results["TensorRT Aggressive"] = (success, has_kana)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for mode, (success, has_kana) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        kana_status = "Hiragana ✅" if has_kana else "No Hiragana ❌"
        print(f"  {mode:25s} : {status} | {kana_status}")

    print("\n" + "=" * 80)
    print("Expected behavior:")
    print("  - All modes should PASS (initialize without errors)")
    print("  - TensorRT Aggressive should have BEST hiragana detection")
    print("  - TensorRT Standard should be FASTER than Aggressive")
    print("=" * 80)
    print()

    # Check if all passed
    all_passed = all(success for success, _ in results.values())

    if all_passed:
        print("✅ All tests passed! TensorRT OCR integration successful.")
        return 0
    else:
        print("❌ Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
