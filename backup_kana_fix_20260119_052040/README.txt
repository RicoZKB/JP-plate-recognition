BACKUP: Kana Detection Fix
Created: 2026-01-19 05:20:40
===============================================

This backup contains the modified files for the kana character detection fix.

FILES BACKED UP:
- fr01.py                        (main detection script)
- licence_plate_detection.py     (YOLO detection + OCR with kana injection)
- run_fr01.sh                    (startup script)
- rebuild_tensorrt_optimized.py  (TensorRT rebuild script)

CHANGES MADE:
1. Added ROMAJI_TO_HIRAGANA mapping (41 kana characters)
2. Modified detect_frame() to capture all YOLO classes including kana (ro, wa, nu, etc.)
3. Added kana injection system to combine YOLO kana detections with OCR text

KEY IMPROVEMENTS:
- YOLO now detects kana classes: "ro", "wa", "nu" → converts to hiragana: ろ, わ, ぬ
- Kana bounding boxes are matched to plate bounding boxes
- YOLO kana is injected into OCR text for complete plate recognition

EXPECTED BEHAVIOR:
- Console output: [KANA-YOLO] Detected ro → ろ at bbox=(x,y,x,y)
- Console output: [KANA-INJECT] Found YOLO kana 'ろ' inside plate bbox
- Console output: LP DET: bbox=(x,y,x,y) text='品川 589 20-46 ろ' +YOLO-KANA
- CSV kana column should be populated with hiragana characters

TO RESTORE FROM BACKUP:
cp backup_kana_fix_20260119_052040/fr01.py .
cp backup_kana_fix_20260119_052040/licence_plate_detection.py detections/
cp backup_kana_fix_20260119_052040/run_fr01.sh .
cp backup_kana_fix_20260119_052040/rebuild_tensorrt_optimized.py .

NOTES:
- Model trained at 840x840 but engine built at 640x640
- Consider rebuilding engine at 840x840 for better accuracy
- PaddleOCR .predict() error was noted (should use .ocr() method)
