#!/usr/bin/env python3
"""
Test Hybrid OCR integration: PaddleOCR (main) + EasyOCR (kana)
"""

import cv2
import sys
sys.path.insert(0, '/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording')

from detections import LicencePlateDetection

def test_hybrid_ocr(image_path):
    """Test Hybrid OCR on a plate image."""
    print("\n" + "=" * 80)
    print(f"Testing HYBRID OCR (PaddleOCR + EasyOCR)")
    print("=" * 80)

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not load: {image_path}")
        return False

    print(f"Image: {image_path}")
    print(f"Size: {img.shape[1]}x{img.shape[0]}")

    # Initialize detector with Hybrid OCR
    print("\n[1/2] Initializing detector with Hybrid OCR...")
    print("  - PaddleOCR: Main plate text (accurate on kanji/numbers)")
    print("  - EasyOCR: Kana region detection only (good at small hiragana)")

    detector = LicencePlateDetection(
        model_path="models/best.pt",
        use_hybrid_ocr=True,  # Enable Hybrid OCR!
        verbose=True,
        debug_ocr=True  # Enable debug to see injection
    )
    print("✓ Detector initialized")

    # Run detection
    print("\n[2/2] Running hybrid detection...")
    bboxes, texts = detector.detect_frame(img)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if not texts:
        print("  (No plates detected)")
        return False

    has_hiragana = False
    for i, (bbox, text) in enumerate(zip(bboxes, texts), 1):
        print(f"\nPlate {i}:")
        print(f"  BBox: {bbox}")
        print(f"  Text: '{text}'")

        # Analyze characters
        has_hira = any('\u3040' <= ch <= '\u309F' for ch in text)
        has_kata = any('\u30A0' <= ch <= '\u30FF' for ch in text)
        has_kanji = any('\u4E00' <= ch <= '\u9FFF' for ch in text)
        has_digit = any(ch.isdigit() for ch in text)

        char_types = []
        if has_hira:
            char_types.append("Hiragana ✅")
            has_hiragana = True
        if has_kata: char_types.append("Katakana")
        if has_kanji: char_types.append("Kanji")
        if has_digit: char_types.append("Digits")

        print(f"  Types: {', '.join(char_types) if char_types else 'Unknown'}")

        # Show individual characters
        char_list = []
        for ch in text:
            if '\u3040' <= ch <= '\u309F':
                char_list.append(f"[{ch}:HIRA]")
            elif '\u30A0' <= ch <= '\u30FF':
                char_list.append(f"[{ch}:kata]")
            elif '\u4E00' <= ch <= '\u9FFF':
                char_list.append(f"[{ch}:kanji]")
            elif ch.isdigit():
                char_list.append(f"{ch}")
            else:
                char_list.append(f"{ch}")

        print(f"  Chars: {' '.join(char_list)}")

    print("\n" + "=" * 80)
    if has_hiragana:
        print("✅ SUCCESS! Hybrid OCR detected hiragana!")
    else:
        print("❌ NO HIRAGANA DETECTED")
    print("=" * 80)

    return has_hiragana

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Test on retry queue images
        import glob
        retry_images = glob.glob("retry_queue/plate_*.jpg")

        if not retry_images:
            print("Usage: python3 test_hybrid_ocr.py <plate_image.jpg>")
            print("\nOr place test images in retry_queue/")
            sys.exit(1)

        print(f"\nFound {len(retry_images)} test images")
        print("Testing first 3 images...\n")

        results = []
        for img_path in retry_images[:3]:
            result = test_hybrid_ocr(img_path)
            results.append((img_path, result))
            print("\n")

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for img_path, has_kana in results:
            status = "✅ Hiragana" if has_kana else "❌ No kana"
            print(f"  {status}: {img_path}")
        print("=" * 80)

    else:
        test_hybrid_ocr(sys.argv[1])
