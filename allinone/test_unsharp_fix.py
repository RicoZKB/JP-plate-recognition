#!/usr/bin/env python3
"""
Test if unsharp mask fix restores hiragana detection
"""

import cv2
import sys
sys.path.insert(0, '/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording')

from detections import LicencePlateDetection

def test_plate(image_path):
    print("\n" + "=" * 80)
    print(f"Testing UPDATED detector with unsharp mask on: {image_path}")
    print("=" * 80)

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not load: {image_path}")
        return

    print(f"Image size: {img.shape[1]}x{img.shape[0]}")

    # Initialize detector with standard PaddleOCR (with unsharp mask fix)
    print("\n[1/2] Initializing detector...")
    detector = LicencePlateDetection(
        model_path="models/best_2026.engine",
        verbose=False,
        debug_ocr=False
    )
    print("✓ Detector initialized")

    # Run detection
    print("\n[2/2] Running detection...")
    bboxes, texts = detector.detect_frame(img)

    print(f"\nResults:")
    print("-" * 80)
    if not texts:
        print("  (No plates detected)")
        return

    has_hiragana = False
    for i, (bbox, text) in enumerate(zip(bboxes, texts), 1):
        print(f"  Plate {i}: '{text}'")

        # Check for hiragana
        has_hira = any('\u3040' <= ch <= '\u309F' for ch in text)
        if has_hira:
            has_hiragana = True
            print(f"    ✅ Contains hiragana!")

            # Show hiragana characters
            kana_chars = [ch for ch in text if '\u3040' <= ch <= '\u309F']
            print(f"    Hiragana found: {', '.join(kana_chars)}")

    if not has_hiragana:
        print("  ❌ NO HIRAGANA DETECTED")
    else:
        print("\n✅ SUCCESS! Hiragana detection is working!")

    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_unsharp_fix.py <plate_image.jpg>")
        sys.exit(1)

    test_plate(sys.argv[1])
