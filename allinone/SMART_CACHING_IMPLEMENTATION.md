# Smart OCR Caching Implementation (Option 3)

**Date:** January 15, 2026
**Status:** ✅ **IMPLEMENTED & TESTED**

---

## Summary

Implemented smart OCR caching to improve FPS from 0.6 → 3-5 by reducing unnecessary OCR operations on stable license plates.

## How It Works

### Caching Strategy

When a license plate is detected:

1. **Check cache first**: Look for cached OCR result from a similar bounding box location
2. **Cache hit**: If found within threshold distance and not too old, reuse the cached text
3. **Cache miss**: Run OCR, store result in cache for future frames

### Cache Parameters

```python
LicencePlateDetection(
    model_path="models/best_optimized.engine",
    verbose=False,
    debug_ocr=False,
    enable_ocr_cache=True,        # Enable smart caching
    cache_threshold=50,            # pixels: bbox must be within 50px to hit cache
    cache_max_age=3                # frames: re-run OCR every 3 frames
)
```

**Tunable Parameters:**
- `cache_threshold` (default: 50px): Maximum distance between bboxes for cache hit
- `cache_max_age` (default: 3 frames): Force OCR refresh after this many frames

### Cache Logic

**When cache is used:**
- Plate detected at similar position as previous detection
- Position difference < 50 pixels (center point distance)
- Cache age < 3 frames

**When OCR runs:**
- First time seeing a plate at this position
- Plate moved > 50 pixels
- Cache entry is 3+ frames old
- New vehicle enters frame

### Example Scenario

```
Frame 1: Plate detected at (100, 200, 300, 280)
         → Run OCR → "品川 589 ろ 20-46"
         → Store in cache with age=0

Frame 2: Same plate at (102, 201, 301, 281)
         → Distance from cache: 2px
         → CACHE HIT! Use "品川 589 ろ 20-46"
         → Age cache (age=1)

Frame 3: Same plate at (103, 200, 302, 280)
         → Distance from cache: 3px
         → CACHE HIT! Use "品川 589 ろ 20-46"
         → Age cache (age=2)

Frame 4: Same plate at (105, 202, 304, 282)
         → Distance from cache: 5px
         → Cache age=3 (max age reached)
         → Run OCR → Update cache with fresh result

Frame 5: New plate at (400, 150, 500, 230)
         → Distance from cache: 300px (too far)
         → CACHE MISS! Run OCR for new plate
```

---

## Implementation Details

### Files Modified

**detections/licence_plate_detection.py:**

1. **Added cache attributes to __init__:**
   - `enable_ocr_cache`: Toggle caching on/off
   - `cache_threshold`: Distance threshold for cache hits
   - `cache_max_age`: Maximum cache age in frames
   - `ocr_cache`: Dictionary storing cached results
   - `frame_count`: Track current frame number

2. **Added cache methods:**
   - `_bbox_distance()`: Calculate distance between two bboxes
   - `_find_cached_ocr()`: Search cache for matching bbox
   - `_update_ocr_cache()`: Store new OCR result
   - `_age_ocr_cache()`: Increment age and clean stale entries

3. **Modified detect_frame():**
   - Check cache before running OCR
   - Use cached text if hit
   - Update cache after OCR completes
   - Age cache at start of each frame

### Cache Data Structure

```python
ocr_cache = {
    (center_x, center_y): {
        'text': "品川 589 ろ 20-46",
        'age': 2,  # frames since last OCR
        'bbox': (100, 200, 300, 280)
    }
}
```

---

## Expected Performance

### Before Caching (Baseline)
- YOLO TensorRT: ~48ms
- CPU PaddleOCR: ~1500ms
- **Total: ~1548ms (0.6 FPS)**

### After Caching (Expected)
- YOLO TensorRT: ~48ms
- OCR (20-30% of frames): ~450ms average
- **Total: ~300-500ms (3-5 FPS)**

**Improvement: 5-8x faster**

### Cache Hit Rate Expectations

**Typical driving scenario:**
- Vehicle in view: 5-10 seconds
- At 30 FPS camera: 150-300 frames per vehicle
- With 3-frame cache: 67% cache hit rate
- With stable vehicle: Up to 80% cache hit rate

---

## Impact on Data Quality

### CSV Logging
✅ **No data loss** - Every frame with a detection is still logged to CSV
✅ **Same fields** - timestamp, object_id, vehicle_type, direction, city, engine_size, kana, four-digit
✅ **Cached text** - Frames between OCR runs use cached text (more consistent)

### OCR Accuracy
✅ **More consistent** - Reduces OCR "jitter" (same plate reading differently each frame)
✅ **Periodic refresh** - OCR re-runs every 3 frames to catch corrections
⚠️ **Sticky errors** - If OCR was wrong on first frame, error persists for 3 frames

### Terminal Output
✅ **Shows cache status** - Detections marked with `[CACHED]` tag when cache is used
✅ **Same format** - All plate fields still displayed

---

## Testing

### Verification Test

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
source ../myenv/bin/activate
python3 -c "
from detections.licence_plate_detection import LicencePlateDetection

det = LicencePlateDetection(
    'models/best_optimized.engine',
    enable_ocr_cache=True,
    cache_threshold=50,
    cache_max_age=3
)

# Test cache operations
bbox1 = (100, 100, 200, 150)
bbox2 = (102, 101, 201, 151)  # Close to bbox1
det._update_ocr_cache(bbox1, '品川 589')
cached_text, hit = det._find_cached_ocr(bbox2)
assert hit and cached_text == '品川 589'
print('✅ Cache working!')
"
```

**Result:** ✅ All tests passed

---

## Disabling Cache

If caching causes issues, it can be disabled:

### Option 1: Disable in Code

Edit `fr01.py` line ~460:

```python
lp_det = LicencePlateDetection(
    model_path="models/best_optimized.engine",
    verbose=using_camera,
    debug_ocr=False,
    enable_ocr_cache=False  # Disable caching
)
```

### Option 2: Restore Backup

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
cp backup_before_smart_caching/licence_plate_detection.py detections/
```

---

## Configuration Options

### Conservative (More Accurate, Slower)

```python
enable_ocr_cache=True,
cache_threshold=30,   # Stricter position match
cache_max_age=2       # Refresh more often
```
Expected: ~2-3 FPS

### Balanced (Default)

```python
enable_ocr_cache=True,
cache_threshold=50,   # Moderate position tolerance
cache_max_age=3       # Reasonable refresh rate
```
Expected: ~3-5 FPS

### Aggressive (Faster, Less Accurate)

```python
enable_ocr_cache=True,
cache_threshold=100,  # Looser position match
cache_max_age=5       # Less frequent refresh
```
Expected: ~5-8 FPS

---

## Next Steps

1. **Test with real camera** when available
2. **Monitor cache hit rate** and adjust parameters if needed
3. **Check CSV quality** to ensure text consistency is acceptable
4. **Tune parameters** based on actual vehicle speed and camera angle

---

## Backup Location

All files before changes:
```
/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording/backup_before_smart_caching/
├── fr01.py
├── licence_plate_detection.py
├── run_fr01.sh
└── README.md
```

To restore: See "Disabling Cache" section above.
