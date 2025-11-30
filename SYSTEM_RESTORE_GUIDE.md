# System Restore Guide - Switch Between Simple ALPR and Full Gate System

**Date:** November 26, 2025
**Location:** `/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording/`

---

## Overview

This guide allows you to **safely switch** between two systems:

1. **Simple ALPR** - Basic detection and OCR (no gate system)
2. **Full Gate System** - Complete IN/OUT tracking with parking analytics

Both systems are **preserved** and can be used at any time.

---

## Quick Reference

| System | Script | Run Command | Features |
|--------|--------|-------------|----------|
| **Simple ALPR** | `simple_alpr.py` | `./run_simple.sh` | Detection + OCR only |
| **Full Gate System** | `inout_event.py` | `./run_optimized.sh` | Gate + Tracking + CSV |

---

## System 1: Simple ALPR (NEW)

### Files:
- **Main Script:** `simple_alpr.py` (200 lines)
- **Run Script:** `run_simple.sh`
- **Documentation:** `SIMPLE_ALPR_README.md`

### What It Does:
✅ License plate detection
✅ OCR extraction (PaddleOCR GPU)
✅ Real-time display with FPS
❌ No gate system
❌ No tracking
❌ No IN/OUT events
❌ No CSV logging
❌ No parking analytics

### How to Run:
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_simple.sh
```

### Configuration:
Edit `simple_alpr.py`:
```python
# Line 36-37: Choose video source
USE_CAMERA = True          # True = CSI camera, False = video file
VIDEO_PATH = "input_videos/Trim03.mp4"

# Line 42: Model selection
MODEL_PATH = "models/best.onnx"  # Use ONNX for best performance

# Line 45-47: Display options
SHOW_FPS = True
SAVE_OUTPUT = False
OUTPUT_PATH = "output_simple_alpr.avi"
```

---

## System 2: Full Gate System (ORIGINAL - PRESERVED)

### Files:
- **Main Script:** `inout_event.py` (1341 lines)
- **Run Scripts:**
  - `run_optimized.sh` - **RECOMMENDED** (with all optimizations)
  - `run_camera.sh` - Alternative camera launcher
  - `run.sh` - Basic launcher
- **Documentation:**
  - `OPTIMIZATION_SUMMARY_20251125.md` - Full optimization details
  - `IMPLEMENTATION_COMPLETE.md` - Implementation guide
  - `CSV_LOGGING_GUIDE.md` - CSV logging setup
  - `INOUT_EVENT_GUIDE.md` - Gate system guide
  - `OCR_CACHE_GUIDE.md` - OCR caching details

### What It Does:
✅ License plate detection
✅ OCR extraction (PaddleOCR GPU)
✅ **Gate system** (virtual line or ROI)
✅ **Bidirectional tracking** (IN/OUT lanes)
✅ **Object tracking** (tracks cars across frames)
✅ **Event detection** (ENTER/EXIT events)
✅ **CSV logging** with timestamps
✅ **Parking analytics** (occupancy, duration)
✅ **Smart OCR caching**
✅ **Frame skipping optimization**

### How to Run:
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_optimized.sh
```

### Key Configuration:
Edit `inout_event.py`:

#### Source Selection (Lines 32-40):
```python
USE_CAMERA   = True   # CSI Camera
USE_FILE     = False  # Video file
USE_YOUTUBE  = False  # YouTube stream

INPUT_VIDEO_PATH = "input_videos/Trim03.mp4"  # If USE_FILE=True
YOUTUBE_URL = "https://www.youtube.com/watch?v=..."  # If USE_YOUTUBE=True
```

#### Direction Mode (Lines 44-52):
```python
DIRECTION_MODE = "BIDIRECTIONAL"  # Options: IN_ONLY, OUT_ONLY, BIDIRECTIONAL

# For bidirectional mode:
LANE_DIVIDER_X_RATIO = 0.50       # Center divider
LEFT_LANE_DIRECTION = "out"       # Left lane = exit
RIGHT_LANE_DIRECTION = "in"       # Right lane = entry
```

#### Gate Configuration (Lines 69-79):
```python
USE_ROI = False                   # False = use virtual gate line
ENTRY_LINE_X_RATIO = 0.55         # Gate line position (55% from left)
GATE_CAPTURE_MARGIN_PX = 80       # Capture window around gate
GATE_INSIDE_IS_RIGHT = True       # Right of line = inside

# OCR trigger zone (optimal detection area)
OCR_TRIGGER_ZONE_RATIO = 0.35     # 35% of frame width
OCR_MIN_DISTANCE_FROM_GATE = 10   # Min pixels from gate
OCR_MAX_DISTANCE_FROM_GATE = 220  # Max pixels from gate
```

#### Performance Tuning (Lines 89-98):
```python
INSIDE_PROCESS_EVERY_N = 20       # Throttle when car inside
DETECT_EVERY_N = 6                # Process every 6th frame
OCR_SKIP_FRAMES = 5               # Skip OCR for performance
ENABLE_OCR_CACHE = True           # Cache OCR results
OCR_CACHE_MIN_CONFIDENCE = 0.60   # Cache confidence threshold
OCR_CACHE_MAX_AGE_FRAMES = 300    # Cache age limit
```

#### Model Selection (Line 740):
```python
lp_det = LicencePlateDetection(
    model_path="models/best.onnx",  # ONNX (recommended)
    # model_path="models/best.pt",  # PyTorch (slower)
    # model_path="models/best.engine",  # TensorRT (if available)
    verbose=PRINT_RAW_OCR_FOUND,
    debug_ocr=PASS_OCR_DEBUG_TO_DETECT
)
```

---

## Switching Between Systems

### From Simple ALPR → Full Gate System:

1. **Stop Simple ALPR** (press ESC)
2. **Run Gate System:**
   ```bash
   ./run_optimized.sh
   ```
3. **Verify settings** in `inout_event.py` (lines 32-40 for video source)
4. **Check CSV logs** in `logs/parking_log_YYYYMMDD.csv`

### From Full Gate System → Simple ALPR:

1. **Stop Gate System** (press ESC or Ctrl+C)
2. **Run Simple ALPR:**
   ```bash
   ./run_simple.sh
   ```
3. **Verify settings** in `simple_alpr.py` (lines 36-37 for video source)

---

## Backup Status

### ✅ Both Systems Are Safe

| Component | Simple ALPR | Full Gate System | Status |
|-----------|-------------|------------------|--------|
| Main Script | `simple_alpr.py` | `inout_event.py` | ✅ Both preserved |
| Run Script | `run_simple.sh` | `run_optimized.sh` | ✅ Both preserved |
| Detector | `detections/licence_plate_detection.py` | Same | ✅ Shared (GPU optimized) |
| Models | `models/best.onnx` | Same | ✅ Shared |
| Virtual Env | `myenv/` | Same | ✅ Shared |

### 🔒 Nothing Was Deleted

The simple ALPR system was **added** as a new option. The full gate system (`inout_event.py`) remains **completely intact** and unchanged.

---

## Output Locations

### Simple ALPR:
- **Video Output:** `output_simple_alpr.avi` (if SAVE_OUTPUT=True)
- **Frame Snapshots:** `frame_YYYYMMDD_HHMMSS.jpg` (press 'S' to save)
- **No CSV logging** (not implemented)

### Full Gate System:
- **CSV Logs:** `logs/parking_log_YYYYMMDD.csv`
- **Video Output:** (optional, can be enabled in code)
- **Terminal Output:** Real-time IN/OUT events

---

## CSV Log Format (Full Gate System Only)

**Location:** `logs/parking_log_YYYYMMDD.csv`

**Format:**
```csv
timestamp,object_id,vehicle_type,direction,city,engine_size,kana,four-digit number
2025-11-25 01:23:21,01,car,in,世田谷,310,,70-50
2025-11-25 01:23:45,01,car,out,世田谷,310,,70-50
```

**Fields:**
- `timestamp` - ISO format datetime
- `object_id` - Unique tracker ID
- `vehicle_type` - "car", "truck", "motorcycle"
- `direction` - "in", "out", or "L-out"/"R-in" (bidirectional)
- `city` - Japanese city name (地域)
- `engine_size` - Classification number
- `kana` - Kana character (if present)
- `four-digit number` - License plate number

---

## Performance Comparison

| Metric | Simple ALPR | Full Gate System |
|--------|-------------|------------------|
| **FPS (Camera)** | ~4-5 FPS | ~4.9 FPS |
| **Detection Time** | ~1 second | ~1 second |
| **Code Complexity** | 🟢 Low (200 lines) | 🔴 High (1341 lines) |
| **Memory Usage** | 🟢 Lower | 🟡 Higher |
| **CPU Usage** | 🟢 Lower | 🟡 Higher |
| **GPU Usage** | Same | Same |
| **Features** | Basic | Complete |

Both systems use the same GPU optimizations and detector, so performance is similar.

---

## Troubleshooting

### Simple ALPR Issues:

**Camera not opening:**
```bash
# Test camera
ls /dev/video*
v4l2-ctl --list-devices
```

**Import errors:**
```bash
source myenv/bin/activate
pip list | grep paddle
```

### Full Gate System Issues:

**CSV not logging:**
- Check `logs/` folder exists
- Verify disk space: `df -h`
- Check permissions: `ls -la logs/`

**Gate not detecting:**
- Verify `ENTRY_LINE_X_RATIO` position
- Check `GATE_CAPTURE_MARGIN_PX` size
- Enable debug: `PRINT_EVENTS_TO_TERMINAL = True`

**Tracking issues:**
- Adjust `DETECT_EVERY_N` (lower = more detections)
- Check `MIN_EVENT_GAP_FRAMES`
- Verify gate direction: `GATE_INSIDE_IS_RIGHT`

---

## System Architecture Comparison

### Simple ALPR Pipeline:
```
┌─────────────┐
│   Camera    │
└──────┬──────┘
       │
┌──────▼──────┐
│    YOLO     │ (Detection)
└──────┬──────┘
       │
┌──────▼──────┐
│  PaddleOCR  │ (Extract)
└──────┬──────┘
       │
┌──────▼──────┐
│   Display   │
└─────────────┘
```

### Full Gate System Pipeline:
```
┌─────────────┐
│   Camera    │
└──────┬──────┘
       │
┌──────▼──────┐
│    YOLO     │ (Detection)
└──────┬──────┘
       │
┌──────▼──────┐
│   Tracker   │ (Track objects)
└──────┬──────┘
       │
┌──────▼──────┐
│Gate Monitor │ (Check gate crossing)
└──────┬──────┘
       │
┌──────▼──────┐
│  PaddleOCR  │ (Extract when triggered)
└──────┬──────┘
       │
┌──────▼──────┐
│ Event Logic │ (IN/OUT detection)
└──────┬──────┘
       │
┌──────▼──────┐
│ CSV Logger  │ (Save to file)
└──────┬──────┘
       │
┌──────▼──────┐
│   Display   │
└─────────────┘
```

---

## Recommendations

### Use Simple ALPR When:
- ✅ Just need plate detection and OCR
- ✅ Testing or debugging detection
- ✅ Don't need IN/OUT tracking
- ✅ Want simpler, cleaner output
- ✅ Prototyping or development

### Use Full Gate System When:
- ✅ Need parking lot management
- ✅ Require IN/OUT event tracking
- ✅ Need CSV logs for analytics
- ✅ Want occupancy monitoring
- ✅ Production deployment

---

## Virtual Environment Details

**Location:** `/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording/myenv/`

**Shared by both systems:**
- PaddlePaddle 2.6.2
- PaddleOCR 2.7.3
- Ultralytics 8.3.231
- OpenCV 4.8.0 (system, with CUDA)
- PyTorch 1.13.0a0+936e930

**Activation:**
```bash
source myenv/bin/activate
```

---

## Model Files

**Location:** `models/`

| File | Type | Size | Performance | Status |
|------|------|------|-------------|--------|
| `best.onnx` | ONNX | ~37MB | ⚡ Fast (recommended) | ✅ Working |
| `best.pt` | PyTorch | ~37MB | 🐌 Slower | ✅ Working |
| `best.engine` | TensorRT | ~18MB | 🚀 Fastest | ⚠️ Cannot use (Python bindings unavailable) |

**Recommendation:** Use `best.onnx` for best balance of speed and compatibility.

---

## Emergency Restore Procedures

### If Simple ALPR Breaks:

1. **Delete broken file:**
   ```bash
   rm simple_alpr.py
   rm run_simple.sh
   ```

2. **Restore from git** (if under version control):
   ```bash
   git checkout simple_alpr.py run_simple.sh
   ```

3. **Or recreate from reference:**
   ```bash
   # Files old_refer.py and detections/P01.py contain the reference code
   python old_refer.py  # Test reference version
   ```

### If Full Gate System Breaks:

1. **Check git history:**
   ```bash
   git log --oneline inout_event.py
   git diff inout_event.py
   ```

2. **Restore from git:**
   ```bash
   git checkout inout_event.py
   ```

3. **Verify configuration:**
   ```bash
   grep "USE_CAMERA" inout_event.py
   grep "MODEL_PATH" inout_event.py
   ```

---

## Testing Both Systems

### Quick Test - Simple ALPR:
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_simple.sh
# Press ESC to stop
```

### Quick Test - Full Gate System:
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_optimized.sh
# Press ESC to stop
# Check logs/parking_log_*.csv for output
```

---

## Summary

### ✅ What's Protected:

1. **Full Gate System** (`inout_event.py`) - **100% preserved, untouched**
2. **Simple ALPR** (`simple_alpr.py`) - **New addition, independent**
3. **Shared Components** - Both use same detector, models, venv
4. **Documentation** - Complete guides for both systems
5. **Run Scripts** - Separate launchers for each system

### 🔄 Easy Switching:

```bash
# Switch to Simple ALPR
./run_simple.sh

# Switch to Full Gate System
./run_optimized.sh
```

### 🛡️ Safety:

- ✅ No files were deleted
- ✅ No files were overwritten
- ✅ Both systems are independent
- ✅ Can switch at any time
- ✅ Both systems are documented
- ✅ Both systems are tested

---

## Support Files Reference

### Documentation Files:
- `OPTIMIZATION_SUMMARY_20251125.md` - GPU optimization details
- `SIMPLE_ALPR_README.md` - Simple ALPR guide
- `SYSTEM_RESTORE_GUIDE.md` - This file
- `CSV_LOGGING_GUIDE.md` - CSV logging setup
- `INOUT_EVENT_GUIDE.md` - Gate system guide
- `IMPLEMENTATION_COMPLETE.md` - Implementation status
- `OCR_CACHE_GUIDE.md` - OCR caching optimization

### Code Files:
- `inout_event.py` - Full gate system (1341 lines)
- `simple_alpr.py` - Simple ALPR (200 lines)
- `old_refer.py` - Original reference
- `detections/licence_plate_detection.py` - Shared detector
- `detections/P01.py` - Old simple detector

### Run Scripts:
- `run_simple.sh` - Simple ALPR launcher
- `run_optimized.sh` - Full gate system launcher
- `run_camera.sh` - Alternative camera launcher
- `run.sh` - Basic launcher

---

**Last Updated:** November 26, 2025
**Status:** ✅ Both systems ready and safe
**Backup:** ✅ Complete restoration guide available
