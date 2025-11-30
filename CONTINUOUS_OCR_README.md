# Continuous OCR ALPR System

**Fast real-time license plate detection with continuous OCR display**

---

## Overview

This is a simplified ALPR system focused on **continuous OCR extraction** - similar to what you see in Roboflow and YouTube demonstrations where OCR text updates constantly as the car moves.

### Key Features

✅ **Continuous OCR** - Runs OCR on every detected plate (no caching delays)
✅ **Single Direction Mode** - Simple configuration: "IN" or "OUT"
✅ **No Gate Logic** - Pure detection and display, no complex tracking
✅ **Real-time Display** - Shows OCR text above detected plates
✅ **Fast & Lightweight** - Optimized for Jetson TX1
✅ **Color-coded Boxes** - Green for new detections

---

## Quick Start

### Run with CSI Camera:
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_continuous.sh
```

### Run with Video File:
Edit `continuous_ocr.py`:
```python
USE_CAMERA = False
VIDEO_PATH = "input_videos/Trim03.mp4"
```

Then run:
```bash
./run_continuous.sh
```

---

## Configuration

Edit `continuous_ocr.py` to customize settings:

### Direction Mode:
```python
DIRECTION = "IN"   # Change to "OUT" if needed
```

### Video Source:
```python
USE_CAMERA = True              # True = CSI camera, False = video file
VIDEO_PATH = "input_videos/Trim03.mp4"
```

### Model Selection:
```python
MODEL_PATH = "models/best.onnx"  # ONNX for best performance
# MODEL_PATH = "models/best.pt"  # PyTorch (slower)
```

### Performance Settings:
```python
TARGET_WIDTH = 480              # Frame width (lower = faster)
RUN_OCR_EVERY_N_FRAMES = 1      # 1 = every frame (continuous)
                                # 2 = every other frame (faster)
SHOW_FPS = True                 # Display FPS counter
```

### Display Settings:
```python
BOX_COLOR = (0, 255, 0)         # Green boxes
TEXT_COLOR = (255, 255, 255)    # White text
FONT_SCALE = 0.6
FONT_THICKNESS = 2
```

---

## How It Works

### Continuous OCR Flow:

```
┌─────────────┐
│   Camera    │
│  or Video   │
└──────┬──────┘
       │
┌──────▼──────┐
│    YOLO     │ Every frame
│ Detection   │
└──────┬──────┘
       │
┌──────▼──────┐
│  PaddleOCR  │ Continuous
│   (GPU)     │ extraction
└──────┬──────┘
       │
┌──────▼──────┐
│   Display   │ Real-time
│  with Text  │ updates
└─────────────┘
```

### Differences from Other Systems:

| Feature | Continuous OCR | Simple ALPR | Full Gate System |
|---------|---------------|-------------|------------------|
| **OCR Frequency** | Every frame | Every frame | Cached/throttled |
| **Caching** | Disabled | Enabled | Smart caching |
| **Gate Logic** | No | No | Yes |
| **Tracking** | No | No | Yes |
| **CSV Logging** | No | No | Yes |
| **Complexity** | Low | Low | High |
| **Use Case** | Demos, testing | Testing | Production |

---

## Performance

### Expected FPS:
- **Continuous OCR (every frame)**: 2-4 FPS
- **Every 2nd frame**: 4-6 FPS
- **Every 3rd frame**: 6-8 FPS

### Optimization Tips:

1. **Adjust OCR frequency:**
   ```python
   RUN_OCR_EVERY_N_FRAMES = 2  # Run OCR every 2 frames instead of every frame
   ```

2. **Reduce frame size:**
   ```python
   TARGET_WIDTH = 320  # Smaller = faster (but less accurate)
   ```

3. **Use ONNX model:**
   ```python
   MODEL_PATH = "models/best.onnx"  # 35% faster than PyTorch
   ```

---

## Display Format

### On Screen:

- **Green bounding boxes** around detected plates
- **OCR text** displayed above each plate
- **FPS counter** in top-left corner
- **Direction mode** shown with FPS

### Example Display:
```
FPS: 3.2 | Direction: IN

┌─────────────────────┐
│ 愛媛501わ67         │ ← OCR text
└─────────────────────┘
[Green box around plate]
```

---

## Troubleshooting

### Low FPS:
- Increase `RUN_OCR_EVERY_N_FRAMES` to 2 or 3
- Reduce `TARGET_WIDTH` to 320
- Verify GPU is being used (check terminal output)

### No OCR Text Showing:
- Check if plates are detected (green boxes should appear)
- Try with a test video first: `USE_CAMERA = False`
- Check terminal for errors

### Camera Won't Open:
- The script includes automatic LD_PRELOAD workaround
- If issues persist, verify camera: `ls /dev/video*`
- Check GStreamer: `gst-launch-1.0 --version`

### OCR Accuracy Issues:
- Ensure plates are large enough in frame
- Improve lighting conditions
- Try adjusting camera focus
- Use slower OCR frequency for better accuracy

---

## Comparison with Reference Images

Your reference images show:

**Image 1 (Front plate):**
- Red bounding box
- OCR text: `愛媛501わ67`
- Confidence: `@0.787`

**Image 2 (Rear plate):**
- Green bounding box
- OCR text: `福岡500い-64`
- Confidence: `@0.583`

This system replicates that behavior:
- ✅ Bounding boxes around plates
- ✅ OCR text displayed above box
- ✅ Confidence scores available (optional display)
- ✅ Real-time continuous updates

---

## Files

**Main Script:**
- `continuous_ocr.py` - Main continuous OCR implementation

**Run Script:**
- `run_continuous.sh` - Launch script with environment setup

**Shared Components:**
- `detections/licence_plate_detection.py` - YOLO + PaddleOCR detector
- `models/best.onnx` - YOLO model (ONNX format, recommended)
- `myenv/` - Virtual environment

---

## Advanced: Adjust OCR Behavior

### Force Fresh OCR (No Caching):
The system already disables caching by default:
```python
# In continuous_ocr.py (already set):
lp_detector.cache_timeout = 0.0  # Cache disabled
```

### Enable Position-based Caching:
If you want to cache stationary plates:
```python
lp_detector.cache_timeout = 2.0  # Cache for 2 seconds
```

### Adjust Cache Position Tolerance:
```python
lp_detector.position_tolerance = 20  # pixels (default)
```

---

## When to Use This System

### ✅ Use Continuous OCR When:
- Demonstrating ALPR capabilities
- Testing OCR accuracy with moving vehicles
- Need constant OCR updates (like Roboflow demos)
- Prototyping or development
- Recording demo videos

### ❌ Don't Use Continuous OCR When:
- Need parking lot management (use Full Gate System)
- Want best performance (use Simple ALPR with caching)
- Need IN/OUT tracking (use Full Gate System)
- Production deployment (use Full Gate System)

---

## System Requirements

- **Hardware:** Jetson TX1 (4GB)
- **OS:** JetPack 4.6 (R32.6.1)
- **Python:** 3.8.2
- **CUDA:** 10.2
- **Camera:** CSI camera (IMX219) or video file

---

## Credits

- **YOLO Detection:** Ultralytics YOLOv7
- **OCR Engine:** PaddleOCR (GPU-accelerated)
- **Platform:** NVIDIA Jetson TX1

---

**Last Updated:** November 26, 2025
**Status:** ✅ Ready to Use
**Performance:** 2-4 FPS (continuous OCR on every frame)
