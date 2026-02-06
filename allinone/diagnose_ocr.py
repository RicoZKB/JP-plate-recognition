#!/usr/bin/env python3
"""
OCR Diagnostic Tool - Compare Different OCR Engines on Real Plates
This helps identify why hiragana detection is failing.
"""

import cv2
import sys
import numpy as np
from paddleocr import PaddleOCR

def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def test_paddleocr_on_plate(image_path):
    """Test PaddleOCR on a license plate image."""
    print_section(f"Testing PaddleOCR on: {image_path}")

    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not load image: {image_path}")
            return

        print(f"Image size: {img.shape[1]}x{img.shape[0]}")

        # Initialize PaddleOCR
        print("\n[1/4] Initializing PaddleOCR...")
        ocr = PaddleOCR(use_angle_cls=True, lang='japan', use_gpu=True, show_log=False)

        # Test 1: Original image
        print("\n[2/4] Testing on ORIGINAL image...")
        result = ocr.ocr(img, cls=False)
        print_ocr_result(result, "Original")

        # Test 2: Grayscale
        print("\n[3/4] Testing on GRAYSCALE image...")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        result = ocr.ocr(gray_bgr, cls=False)
        print_ocr_result(result, "Grayscale")

        # Test 3: Preprocessed (like in licence_plate_detection.py)
        print("\n[4/4] Testing on PREPROCESSED image (2x upscale + CLAHE)...")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        upscaled = cv2.resize(enhanced, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        prep_bgr = cv2.cvtColor(upscaled, cv2.COLOR_GRAY2BGR)
        result = ocr.ocr(prep_bgr, cls=False)
        print_ocr_result(result, "Preprocessed (2x)")

        # Test 4: Aggressive preprocessing (6x upscale)
        print("\n[5/5] Testing on AGGRESSIVE preprocessing (6x upscale + strong CLAHE)...")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        # Bilateral filter
        enhanced = cv2.bilateralFilter(enhanced, 5, 50, 50)
        # Unsharp mask
        blur = cv2.GaussianBlur(enhanced, (0, 0), 1.5)
        enhanced = cv2.addWeighted(enhanced, 2.0, blur, -1.0, 0)
        # 6x upscale
        upscaled = cv2.resize(enhanced, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
        prep_bgr = cv2.cvtColor(upscaled, cv2.COLOR_GRAY2BGR)
        result = ocr.ocr(prep_bgr, cls=False)
        print_ocr_result(result, "Aggressive (6x)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def print_ocr_result(result, mode_name):
    """Print OCR result in readable format."""
    print(f"\nOCR Result ({mode_name}):")
    print("-" * 80)

    if not result or not result[0]:
        print("  (No text detected)")
        return

    # Extract all text
    all_text = []
    if isinstance(result, list) and len(result) > 0:
        items = result[0] if isinstance(result[0], list) else result

        for item in items:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                # Format: [bbox, (text, confidence)]
                if isinstance(item[1], (list, tuple)) and len(item[1]) >= 1:
                    text = str(item[1][0])
                    conf = float(item[1][1]) if len(item[1]) >= 2 else 0.0
                    all_text.append((text, conf))
                elif isinstance(item[1], str):
                    all_text.append((item[1], 0.0))

    if not all_text:
        print("  (No text extracted)")
        return

    # Print each detected text
    for i, (text, conf) in enumerate(all_text, 1):
        print(f"  [{i}] Text: '{text}'  (confidence: {conf:.2f})")

        # Analyze characters
        has_hiragana = any('\u3040' <= ch <= '\u309F' for ch in text)
        has_katakana = any('\u30A0' <= ch <= '\u30FF' for ch in text)
        has_kanji = any('\u4E00' <= ch <= '\u9FFF' for ch in text)
        has_digit = any(ch.isdigit() for ch in text)
        has_latin = any(ch.isalpha() and ord(ch) < 128 for ch in text)

        char_types = []
        if has_hiragana: char_types.append("Hiragana ✓")
        if has_katakana: char_types.append("Katakana")
        if has_kanji: char_types.append("Kanji")
        if has_digit: char_types.append("Digits")
        if has_latin: char_types.append("Latin")

        print(f"       Types: {', '.join(char_types) if char_types else 'Unknown'}")

        # Show individual characters
        char_list = []
        for ch in text:
            if '\u3040' <= ch <= '\u309F':
                char_list.append(f"{ch}(hira)")
            elif '\u30A0' <= ch <= '\u30FF':
                char_list.append(f"{ch}(kata)")
            elif '\u4E00' <= ch <= '\u9FFF':
                char_list.append(f"{ch}(kanji)")
            elif ch.isdigit():
                char_list.append(f"{ch}(digit)")
            else:
                char_list.append(f"{ch}")
        print(f"       Chars: {' '.join(char_list)}")

    # Print combined text
    combined = " ".join(text for text, _ in all_text)
    print(f"\n  COMBINED: '{combined}'")

    # Check for hiragana
    has_any_hiragana = any('\u3040' <= ch <= '\u309F' for text, _ in all_text for ch in text)
    if has_any_hiragana:
        print("  ✅ HIRAGANA DETECTED!")
    else:
        print("  ❌ NO HIRAGANA DETECTED")

def test_on_retry_queue():
    """Test on images from retry_queue folder."""
    import glob
    import os

    print_section("Testing on Retry Queue Images")

    retry_images = glob.glob("retry_queue/plate_*.jpg")

    if not retry_images:
        print("No images found in retry_queue/")
        return

    print(f"Found {len(retry_images)} images in retry_queue/")

    # Test first 3 images
    for img_path in retry_images[:3]:
        test_paddleocr_on_plate(img_path)

def test_on_latest_csv_images():
    """Extract plate info from latest CSV and suggest test images."""
    import os
    import glob

    print_section("Checking Latest CSV Logs")

    csv_files = glob.glob("logs/parking_log_*.csv")
    if not csv_files:
        print("No CSV files found in logs/")
        return

    latest_csv = max(csv_files, key=os.path.getmtime)
    print(f"Latest CSV: {latest_csv}")

    # Read last 10 lines
    try:
        with open(latest_csv, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"\nLast 10 detections:")
        print("-" * 80)
        for line in lines[-10:]:
            parts = line.strip().split(',')
            if len(parts) >= 8:
                timestamp, obj_id, vtype, direction, city, class_num, kana, suffix = parts[:8]
                kana_status = "✓" if kana.strip() else "✗"
                print(f"  [{kana_status}] {timestamp} | {city} {class_num} {kana or '(empty)'} {suffix}")

    except Exception as e:
        print(f"Error reading CSV: {e}")

def main():
    """Main diagnostic routine."""
    print("\n" + "=" * 80)
    print("OCR DIAGNOSTIC TOOL - Hiragana Detection Analysis")
    print("=" * 80)
    print("\nThis tool helps diagnose why hiragana characters are not being detected.")
    print("It will test PaddleOCR with different preprocessing strategies.")

    # Check for test images
    if len(sys.argv) > 1:
        # User provided an image path
        image_path = sys.argv[1]
        test_paddleocr_on_plate(image_path)
    else:
        # Check CSV logs
        test_on_latest_csv_images()

        # Check retry queue
        test_on_retry_queue()

        print("\n" + "=" * 80)
        print("USAGE")
        print("=" * 80)
        print("To test on a specific plate image:")
        print("  python3 diagnose_ocr.py path/to/plate_image.jpg")
        print("\nTo save a test plate from running system:")
        print("  1. Uncomment the cv2.imwrite() line in fr01.py (around line 796)")
        print("  2. Run the system to capture a plate")
        print("  3. Test: python3 diagnose_ocr.py retry_queue/plate_XX.jpg")
        print("=" * 80)

if __name__ == "__main__":
    main()
