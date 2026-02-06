#!/usr/bin/env python3
"""
Test EasyOCR on Japanese license plates - Compare with PaddleOCR
"""

import cv2
import sys
import numpy as np

def test_easyocr_on_plate(image_path):
    """Test EasyOCR on a plate image."""
    print("\n" + "=" * 80)
    print(f"Testing EasyOCR on: {image_path}")
    print("=" * 80)

    try:
        # Import EasyOCR
        import easyocr
        print("[INFO] EasyOCR imported successfully")

        # Load image
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not load image: {image_path}")
            return False

        print(f"[INFO] Image size: {img.shape[1]}x{img.shape[0]}")

        # Initialize EasyOCR for Japanese
        print("\n[1/3] Initializing EasyOCR (Japanese)...")
        print("  (This may download models on first run, please wait...)")
        reader = easyocr.Reader(['ja'], gpu=True, verbose=False)
        print("  ✓ EasyOCR initialized")

        # Test on original image
        print("\n[2/3] Running OCR on original image...")
        results = reader.readtext(img)

        print("\nOCR Results:")
        print("-" * 80)

        if not results:
            print("  (No text detected)")
            return False

        all_text = []
        has_hiragana = False

        for i, (bbox, text, conf) in enumerate(results, 1):
            print(f"  [{i}] Text: '{text}'  (confidence: {conf:.2f})")

            # Analyze characters
            has_hira = any('\u3040' <= ch <= '\u309F' for ch in text)
            has_kata = any('\u30A0' <= ch <= '\u30FF' for ch in text)
            has_kanji = any('\u4E00' <= ch <= '\u9FFF' for ch in text)
            has_digit = any(ch.isdigit() for ch in text)

            char_types = []
            if has_hira:
                char_types.append("Hiragana ✓")
                has_hiragana = True
            if has_kata: char_types.append("Katakana")
            if has_kanji: char_types.append("Kanji")
            if has_digit: char_types.append("Digits")

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

            all_text.append(text)

        # Print combined
        combined = " ".join(all_text)
        print(f"\n  COMBINED: '{combined}'")

        if has_hiragana:
            print("  ✅ HIRAGANA DETECTED!")
        else:
            print("  ❌ NO HIRAGANA DETECTED")

        return has_hiragana

    except ImportError as e:
        print(f"❌ EasyOCR not available: {e}")
        print("\nTo install EasyOCR:")
        print("  source ../myenv/bin/activate")
        print("  pip install easyocr")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_paddleocr_on_plate(image_path):
    """Test PaddleOCR for comparison."""
    print("\n" + "=" * 80)
    print(f"Testing PaddleOCR on: {image_path} (for comparison)")
    print("=" * 80)

    try:
        from paddleocr import PaddleOCR

        img = cv2.imread(image_path)
        if img is None:
            return False

        print("[INFO] Initializing PaddleOCR...")
        ocr = PaddleOCR(use_angle_cls=True, lang='japan', use_gpu=True, show_log=False)

        print("[INFO] Running OCR...")
        result = ocr.ocr(img, cls=False)

        has_hiragana = False
        all_text = []

        if result and result[0]:
            for item in result[0]:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    if isinstance(item[1], (list, tuple)):
                        text = str(item[1][0])
                        all_text.append(text)
                        if any('\u3040' <= ch <= '\u309F' for ch in text):
                            has_hiragana = True

        combined = " ".join(all_text)
        print(f"\n  COMBINED: '{combined}'")

        if has_hiragana:
            print("  ✅ HIRAGANA DETECTED")
        else:
            print("  ❌ NO HIRAGANA DETECTED")

        return has_hiragana

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test routine."""
    print("\n" + "=" * 80)
    print("EasyOCR vs PaddleOCR - Hiragana Detection Test")
    print("=" * 80)

    if len(sys.argv) < 2:
        print("\nUsage: python3 test_easyocr.py <plate_image.jpg>")
        print("\nExample:")
        print("  python3 test_easyocr.py retry_queue/plate_05_20260119_065843.jpg")
        return 1

    image_path = sys.argv[1]

    # Test EasyOCR
    easy_result = test_easyocr_on_plate(image_path)

    # Test PaddleOCR
    paddle_result = test_paddleocr_on_plate(image_path)

    # Summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(f"  EasyOCR hiragana detection:    {'✅ YES' if easy_result else '❌ NO'}")
    print(f"  PaddleOCR hiragana detection:  {'✅ YES' if paddle_result else '❌ NO'}")

    if easy_result and not paddle_result:
        print("\n✅ EasyOCR is BETTER for hiragana detection!")
        print("   Recommendation: Switch to EasyOCR for license plate recognition")
    elif easy_result and paddle_result:
        print("\n✓ Both OCR engines detected hiragana")
    elif not easy_result and not paddle_result:
        print("\n❌ Neither OCR engine detected hiragana")
        print("   The plate may not contain hiragana, or it's too small/unclear")
    else:
        print("\n✓ PaddleOCR is working for this plate")

    print("=" * 80)

    return 0 if easy_result else 1

if __name__ == "__main__":
    sys.exit(main())
