# KANA DETECTION FIX - TEST SUMMARY
Date: 2026-01-19

## What Was Changed

### 1. Fixed Kana Caching Issue
- **Problem**: Kana was being cached with OCR text, causing wrong kana to appear on all plates
- **Fix**: Cache OCR text WITHOUT kana, inject fresh YOLO kana each frame

### 2. Fixed Spatial Matching
- **Problem**: First kana inside plate bbox was used, even if from wrong plate
- **Fix**: Find CLOSEST kana to plate center (distance-based matching)

### 3. Implemented YOLO Detection + OCR Classification
- **Problem**: YOLO class labels unreliable for kana classification
- **Fix**: YOLO finds kana location, PaddleOCR reads actual character

## Current System Architecture

```
YOLO TensorRT (GPU-FP16)
├─ Detects plate bboxes → PaddleOCR reads city/class/suffix
└─ Detects kana bboxes  → Crop + 6x upscale + PaddleOCR reads kana
```

## What to Look For During Testing

### Expected Console Output:
```
[KANA-OCR] Read 'ろ' from kana bbox=(x,y,x,y) (YOLO detected, OCR read)  ✓ Good
[KANA-SKIP] OCR failed to read kana at bbox=(x,y,x,y), skipping         ⚠ OCR failed
[KANA-INJECT] Found YOLO kana 'さ' inside plate bbox (dist=XX.Xpx)      ✓ Matched to plate
```

### Success Criteria:
- [ ] Each plate gets its own correct kana (not all "さ")
- [ ] Kana matches what you see in the camera view
- [ ] No duplicate kana in text (e.g., "品川 599 20-46 さ" not "さ さ")
- [ ] CSV shows correct kana for most plates

### Performance Metrics to Monitor:
- YOLO inference: ~60ms (should stay same)
- Total FPS: 15-20 FPS target
- Kana detection rate: Aim for >70% of plates

## Test Commands

```bash
# Start detection
./run_fr01.sh

# Monitor in another terminal:
tail -f logs/parking_log_$(date +%Y%m%d).csv

# Check last 10 detections:
tail -10 logs/parking_log_$(date +%Y%m%d).csv
```

## If Performance is Slow

If FPS drops below 10-12, consider:
1. Convert PaddleOCR to TensorRT (next optimization)
2. Reduce OCR processing (cache more aggressively)
3. Process fewer frames (DETECT_EVERY_N = 4 or 5)

## Expected Issues

1. **Some kana still missing**: OCR might fail on very blurry/small kana
2. **Slower than before**: 6x upscaling + OCR on kana adds processing time
3. **Katakana instead of hiragana**: Some plates use katakana (should still work)

## Files Modified

- `detections/licence_plate_detection.py` (main changes)
- `backup_kana_fix_20260119_052040/` (backup of current setup)

## Next Optimization (If Needed)

If OCR is too slow:
- Convert PaddleOCR to TensorRT for GPU acceleration
- Expected speedup: 2-3x faster OCR
