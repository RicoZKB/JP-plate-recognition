# Continuous OCR System - Implementation Memo

**Date:** November 26, 2025
**Location:** `/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording/`
**Status:** ✅ Complete and Ready

---

## 🎯 Project Goal

Create a **continuous fast OCR system** for license plate detection that:
- Updates OCR text constantly as vehicles move (like Roboflow/YouTube demos)
- Uses single direction mode only ("IN" or "OUT")
- Removes all gate and bidirectional complexity
- Displays results similar to reference images provided

---

## 📋 What Was Implemented

### New Files Created:

1. **`continuous_ocr.py`** (8.0 KB)
   - Main continuous OCR implementation
   - Single direction mode only
   - Caching disabled for true continuous updates
   - Auto-restart with LD_PRELOAD workaround

2. **`run_continuous.sh`** (562 bytes)
   - Launch script with environment setup
   - Activates myenv virtual environment
   - Exports LD_PRELOAD for GStreamer fix

3. **`CONTINUOUS_OCR_README.md`** (6.9 KB)
   - Complete user documentation
   - Configuration guide
   - Performance tuning tips
   - Troubleshooting section

4. **`CONTINUOUS_OCR_MEMO.md`** (this file)
   - Technical implementation notes
   - System architecture
   - Quick reference

---

## 🔧 Technical Architecture

### System Flow:

```
┌─────────────────────┐
│   Video Source      │
│ Camera or File      │
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │   Resize    │ TARGET_WIDTH=480
    └──────┬──────┘
           │
    ┌──────▼──────────┐
    │ YOLO Detection  │ models/best.onnx
    │   (GPU/ONNX)    │ Every frame
    └──────┬──────────┘
           │
    ┌──────▼──────────┐
    │  PaddleOCR GPU  │ Continuous
    │  (No caching)   │ Every frame
    └──────┬──────────┘
           │
    ┌──────▼──────────┐
    │  Draw Results   │ Green boxes
    │  Display Text   │ OCR above bbox
    └──────┬──────────┘
           │
    ┌──────▼──────────┐
    │  Show Window    │ Real-time
    └─────────────────┘
```

### Key Technical Decisions:

**1. Disabled Caching:**
```python
# In continuous_ocr.py:
lp_detector.cache_timeout = 0.0  # Force fresh OCR every time
```
- Ensures truly continuous updates
- No stale cached results
- OCR runs on every detected plate

**2. Direct API Usage:**
```python
# Using detect_frame instead of higher-level wrapper:
bboxes, texts, statuses = lp_detector.detect_frame(frame, ocr_filter=None)
```
- Returns: bboxes (list), texts (list), statuses (list)
- No filtering, no throttling
- Direct access to detection results

**3. Single Direction Mode:**
```python
DIRECTION = "IN"  # or "OUT"
```
- No bidirectional complexity
- No lane divider logic
- Simple changeable setting

**4. Auto-restart Mechanism:**
```python
# LD_PRELOAD auto-restart for GStreamer
if 'LD_PRELOAD' not in os.environ:
    os.environ['LD_PRELOAD'] = '/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0'
    os.execvp('python3', ['python3'] + sys.argv)
```
- Fixes GStreamer TLS memory issue
- Automatic, no manual intervention needed

---

## ⚙️ Configuration Options

### User-Configurable Settings (in `continuous_ocr.py`):

```python
# Direction
DIRECTION = "IN"  # "IN" or "OUT"

# Video Source
USE_CAMERA = True
VIDEO_PATH = "input_videos/Trim03.mp4"

# Model
MODEL_PATH = "models/best.onnx"  # Recommended

# Performance
TARGET_WIDTH = 480              # Frame resize width
RUN_OCR_EVERY_N_FRAMES = 1      # 1=continuous, 2=every other frame
SHOW_FPS = True

# Display
BOX_COLOR = (0, 255, 0)         # Green (BGR)
TEXT_COLOR = (255, 255, 255)    # White
FONT_SCALE = 0.6
FONT_THICKNESS = 2

# Camera Settings
CAMERA_CAPTURE_WIDTH = 1280
CAMERA_CAPTURE_HEIGHT = 720
CAMERA_DISPLAY_WIDTH = 480
CAMERA_DISPLAY_HEIGHT = 360
```

---

## 📊 Performance Characteristics

### Expected Performance:

| OCR Frequency | Expected FPS | Use Case |
|---------------|--------------|----------|
| Every frame (1) | 2-4 FPS | Maximum accuracy |
| Every 2 frames | 4-6 FPS | Balanced |
| Every 3 frames | 6-8 FPS | Speed priority |

### Performance Factors:

**What Affects FPS:**
- OCR frequency (RUN_OCR_EVERY_N_FRAMES)
- Frame resolution (TARGET_WIDTH)
- Number of plates in frame
- Model type (ONNX faster than PyTorch)
- GPU memory available

**Optimization Tips:**
1. Use ONNX model (35% faster)
2. Reduce TARGET_WIDTH to 320
3. Increase RUN_OCR_EVERY_N_FRAMES to 2 or 3
4. Monitor GPU usage with `jtop`

---

## 🎨 Display Format

### Visual Output:

```
╔═══════════════════════════════════════╗
║ FPS: 3.2 | Direction: IN              ║
║                                       ║
║   ┌─────────────────────────┐        ║
║   │ 愛媛501わ67              │ ← Text ║
║   └─────────────────────────┘        ║
║        [Green bounding box]           ║
║                                       ║
║   ┌─────────────────────────┐        ║
║   │ 福岡500い-64             │ ← Text ║
║   └─────────────────────────┘        ║
║        [Green bounding box]           ║
╚═══════════════════════════════════════╝
```

### Color Coding:
- **Green boxes**: All detections (continuous OCR)
- **White text**: OCR results
- **Yellow FPS**: Performance counter

---

## 🔄 Comparison with Other Systems

### System Comparison Table:

| Feature | Continuous OCR | Simple ALPR | Full Gate System |
|---------|----------------|-------------|------------------|
| **File** | continuous_ocr.py | simple_alpr.py | inout_event.py |
| **Lines of Code** | ~250 | ~200 | ~1341 |
| **OCR Caching** | Disabled | Enabled | Smart |
| **OCR Frequency** | Every frame | Configurable | Throttled |
| **Gate Logic** | None | None | Full |
| **Bidirectional** | No | No | Optional |
| **Tracking** | No | No | Yes |
| **CSV Logging** | No | No | Yes |
| **Direction Mode** | Single | None | Multiple |
| **Complexity** | Low | Low | High |
| **FPS** | 2-4 | 4-5 | 4.9 |
| **Best For** | Demos | Testing | Production |

### When to Use Each System:

**Use Continuous OCR when:**
- Recording demonstration videos
- Testing OCR accuracy with moving vehicles
- Need constant visual updates (like Roboflow)
- Prototyping new features
- Showing ALPR capabilities to clients

**Use Simple ALPR when:**
- Just need basic detection and OCR
- Don't care about direction
- Want best FPS with caching
- Quick testing and development

**Use Full Gate System when:**
- Need parking lot management
- Require IN/OUT tracking
- Want CSV data logging
- Production deployment
- Analytics and reporting needed

---

## 🚀 Quick Start Commands

### Test with Video File:
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording

# Edit continuous_ocr.py: USE_CAMERA = False
nano continuous_ocr.py  # Change USE_CAMERA to False

# Run
./run_continuous.sh
```

### Test with CSI Camera:
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording

# Edit continuous_ocr.py: USE_CAMERA = True (default)
# Run
./run_continuous.sh
```

### Change Direction:
```bash
# Edit continuous_ocr.py
nano continuous_ocr.py  # Change DIRECTION = "OUT"

# Run
./run_continuous.sh
```

### Adjust Performance:
```bash
# Edit continuous_ocr.py
nano continuous_ocr.py

# Change:
RUN_OCR_EVERY_N_FRAMES = 2  # Run OCR every 2 frames
TARGET_WIDTH = 320           # Smaller frame for speed

# Run
./run_continuous.sh
```

---

## 🛠️ Troubleshooting

### Common Issues and Solutions:

**1. Low FPS (< 2 FPS):**
```python
# Solution 1: Reduce OCR frequency
RUN_OCR_EVERY_N_FRAMES = 2  # or 3

# Solution 2: Reduce frame size
TARGET_WIDTH = 320

# Solution 3: Verify GPU usage
# Check terminal output for GPU messages
```

**2. No OCR Text Showing:**
```python
# Check if plates are detected (green boxes should appear)
# If no boxes: check model path and camera/video source
# If boxes but no text: check terminal for OCR errors
```

**3. Camera Won't Open:**
```bash
# Verify camera device
ls /dev/video*

# Check GStreamer
gst-launch-1.0 --version

# The script auto-restarts with LD_PRELOAD
# If still fails, check camera connection
```

**4. Import Errors:**
```bash
# Verify virtual environment
source ../myenv/bin/activate
pip list | grep paddle
pip list | grep ultralytics
```

**5. GStreamer Warnings:**
```bash
# The script handles this automatically with LD_PRELOAD
# If you see persistent warnings, verify:
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1
```

---

## 📁 File Structure

```
Licence-Plate-Detection-Recognition-Recording/
├── continuous_ocr.py              # Main continuous OCR script
├── run_continuous.sh              # Launch script
├── CONTINUOUS_OCR_README.md       # User documentation
├── CONTINUOUS_OCR_MEMO.md         # This file (technical notes)
│
├── simple_alpr.py                 # Alternative: Simple ALPR
├── run_simple.sh                  # Simple ALPR launcher
├── inout_event.py                 # Alternative: Full gate system
├── run_optimized.sh               # Full gate launcher
│
├── detections/
│   └── licence_plate_detection.py # Shared detector class
│
├── models/
│   ├── best.onnx                  # ONNX model (recommended)
│   ├── best.pt                    # PyTorch model
│   └── best.engine                # TensorRT (unavailable)
│
├── input_videos/
│   └── Trim03.mp4                 # Test video
│
├── logs/                          # CSV logs (gate system only)
└── myenv/                         # Shared virtual environment
```

---

## 🔍 Code Highlights

### Key Code Sections:

**1. Caching Disabled (Line 125):**
```python
lp_detector.cache_timeout = 0.0  # Force continuous OCR
```

**2. Detection Loop (Lines 152-194):**
```python
# Run detection + OCR
bboxes, texts, statuses = lp_detector.detect_frame(frame, ocr_filter=None)

# Draw detections
for idx, bbox in enumerate(bboxes):
    x1, y1, x2, y2 = bbox
    ocr_text = texts[idx] if idx < len(texts) else ''

    # Green box
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # OCR text above box
    cv2.putText(frame, ocr_text, (x1+5, y1-5), ...)
```

**3. Auto-restart (Lines 14-18):**
```python
if 'LD_PRELOAD' not in os.environ:
    os.environ['LD_PRELOAD'] = '/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0'
    os.execvp('python3', ['python3'] + sys.argv)
```

---

## 📝 Implementation Notes

### Design Decisions:

**Why Disable Caching?**
- User requested "continuous OCR like Roboflow"
- Reference images show constant updates
- Caching would delay updates for stationary plates
- Goal is real-time accuracy, not maximum FPS

**Why Single Direction Only?**
- User requested to "comment out bidirectional mode"
- Simpler configuration
- Easier to understand and modify
- Still allows "IN" or "OUT" selection

**Why No Gate Logic?**
- User requested to "comment out gate method"
- Focus on detection + OCR only
- Reduces code complexity
- Faster to load and run

**Why Use detect_frame()?**
- Direct access to detection results
- Returns clean lists: bboxes, texts, statuses
- No wrapper overhead
- Simple to understand

---

## 🔮 Future Enhancements (Optional)

### Possible Improvements:

**1. Confidence Filtering:**
```python
# Only display OCR with confidence > threshold
MIN_CONFIDENCE = 0.5
if confidence > MIN_CONFIDENCE:
    cv2.putText(frame, ocr_text, ...)
```

**2. Multi-threading:**
```python
# Run OCR in separate thread
# Could improve FPS by 20-30%
```

**3. Object Tracking:**
```python
# Add simple tracking to reduce duplicate OCR
# Track same plate across frames
```

**4. Recording:**
```python
# Save output video with annotations
out = cv2.VideoWriter('output.avi', ...)
```

**5. Statistics:**
```python
# Count total plates detected
# Average OCR confidence
# Detection rate
```

---

## ✅ Validation Checklist

- [x] Single direction mode implemented ("IN" or "OUT")
- [x] Continuous OCR on every frame
- [x] No caching delays
- [x] No gate logic
- [x] No bidirectional complexity
- [x] Green bounding boxes
- [x] OCR text displayed above boxes
- [x] Real-time FPS counter
- [x] Auto-restart with LD_PRELOAD
- [x] Works with CSI camera
- [x] Works with video files
- [x] GPU-accelerated (PaddleOCR + YOLO)
- [x] ONNX model support
- [x] Documentation complete
- [x] Launch script created
- [x] File ownership fixed

---

## 📞 Support References

### Related Documentation:
- `CONTINUOUS_OCR_README.md` - User guide
- `OPTIMIZATION_SUMMARY_20251125.md` - GPU optimization details
- `SYSTEM_RESTORE_GUIDE.md` - System switching guide
- `QUICK_SWITCH_GUIDE.txt` - Quick system comparison

### System Paths:
- **Project:** `/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording/`
- **Virtual Env:** `/home/jetson/yolo/yolov7/myenv/`
- **Models:** `models/best.onnx` (recommended)

### Key Commands:
```bash
# Run continuous OCR
./run_continuous.sh

# Check GPU usage
jtop

# List devices
ls /dev/video*

# Activate venv
source ../myenv/bin/activate
```

---

## 🎉 Summary

**What Was Achieved:**

✅ Created continuous OCR system matching reference images
✅ Single direction mode only ("IN" or "OUT")
✅ No gate logic or bidirectional complexity
✅ Disabled caching for true continuous updates
✅ Real-time display with green boxes and OCR text
✅ Auto-restart mechanism for GStreamer
✅ Complete documentation and launch scripts
✅ Performance optimized for Jetson TX1

**System is ready to use!**

```bash
./run_continuous.sh
```

---

**Last Updated:** November 26, 2025
**Author:** Claude Code Optimization Session
**Status:** ✅ Complete, Tested, and Ready
**Performance:** 2-4 FPS (continuous OCR every frame)
