BACKUP: Performance Fix Session
Date: 2026-01-19 07:18:22
Status: Ready for modifications

BACKED UP FILES:
================

Main Scripts:
- fr01.py (main detection script)
- run_fr01.sh (startup script)

Detection Module:
- detections/__init__.py
- detections/licence_plate_detection.py (main detector)
- detections/I02.py
- detections/I03.py
- detections/l01.py

Documentation:
- PREPROCESSING_POSTPROCESSING_FIXES.md
- PERFORMANCE_FIX_20260119.md
- TEST_SUMMARY.md

CHANGES IN THESE FILES:
=======================

1. fr01.py:
   - Added numpy warning suppression (line 14-16)
   - Disabled YOLO kana retry system (line 785-795, 803-833)
   - Disabled frame preprocessing (line 684-685)
   - Added validate_plate_data() function (line 196-270)
   - Added katakana to VALID_PLATE_KANA (line 95-101)
   - Fixed retry_kana_ocr() bug (.predict → .ocr) (line 312-326)

2. detections/licence_plate_detection.py:
   - Added task='detect' to YOLO model (line 40)
   - Disabled YOLO kana detection (line 179-182)
   - Removed kana injection from cached OCR (line 204-212)
   - Removed kana injection from fresh OCR (line 318-328)
   - Simplified OCR preprocessing (line 228-243)

3. run_fr01.sh:
   - No changes in this backup

RESTORE INSTRUCTIONS:
=====================

To restore these files:

cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
cp backup_performance_fix_20260119_071822/fr01.py ./
cp backup_performance_fix_20260119_071822/detections/licence_plate_detection.py detections/

NOTE:
=====
User requested backup before next round of modifications.
System is currently working with:
- YOLO kana detection: DISABLED
- Retry OCR: DISABLED
- OCR preprocessing: SIMPLIFIED (fast mode)
- Frame preprocessing: DISABLED
