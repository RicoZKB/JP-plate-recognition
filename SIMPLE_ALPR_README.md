# Simple ALPR - License Plate Detection & OCR

**No Gate System | No Tracking | Pure Detection & Extraction**

---

## Overview

This is a simplified ALPR (Automatic License Plate Recognition) system that focuses solely on:
1. **Detecting** license plates in video frames
2. **Cropping** the plate region
3. **Extracting** text using OCR (PaddleOCR with GPU acceleration)

All gate logic, bidirectional tracking, IN/OUT events, and parking analytics have been **removed**.

---

## Features

✅ **Simple & Clean** - No complex gate or tracking logic
✅ **GPU Accelerated** - YOLO ONNX + PaddleOCR GPU
✅ **CSI Camera Support** - Real-time processing with GStreamer
✅ **Video File Support** - Process recorded videos
✅ **OCR Caching** - Smart caching to avoid redundant OCR calls
✅ **Japanese Plates** - Optimized for Japanese license plate recognition
✅ **Real-time FPS** - Live FPS counter and statistics

---

## Quick Start

### Run with CSI Camera (Default):
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_simple.sh
```

### Run with Video File:
Edit `simple_alpr.py` and change:
```python
USE_CAMERA = False          # Set to False
VIDEO_PATH = "input_videos/Trim03.mp4"  # Your video path
```

Then run:
```bash
./run_simple.sh
```

---

## Configuration

Edit `simple_alpr.py` to customize:

### Video Source:
```python
USE_CAMERA = True          # True = CSI camera, False = video file
VIDEO_PATH = "input_videos/Trim03.mp4"  # Video file path
```

### Camera Settings:
```python
CAMERA_WIDTH = 640         # Resolution width
CAMERA_HEIGHT = 480        # Resolution height
```

### Model:
```python
MODEL_PATH = "models/best.onnx"  # ONNX for best performance
```

### Display:
```python
SHOW_FPS = True           # Show FPS counter
SAVE_OUTPUT = False       # Save output video
OUTPUT_PATH = "output_simple_alpr.avi"  # Output video path
```

---

## Controls

- **ESC** - Stop and exit
- **S** - Save current frame as JPG

---

## Visual Indicators

### Bounding Box Colors:
- **Green** - NEW detection (OCR just ran)
- **Yellow** - CACHED detection (using cached OCR result)

### On-Screen Display:
- **FPS** - Current frames per second
- **Frames** - Total frames processed
- **Detections** - Number of plates detected in current frame

---

## File Structure

```
simple_alpr.py              # Main script (NO gate system)
run_simple.sh               # Run script
detections/
  └── licence_plate_detection.py  # GPU-optimized detector with PaddleOCR
models/
  ├── best.onnx             # ONNX model (recommended)
  ├── best.pt               # PyTorch model
  └── best.engine           # TensorRT engine (if available)
```

---

## Comparison: Simple vs Full System

| Feature | Simple ALPR | Full System (inout_event.py) |
|---------|-------------|------------------------------|
| Detection | ✅ Yes | ✅ Yes |
| OCR | ✅ Yes | ✅ Yes |
| Gate System | ❌ No | ✅ Yes |
| Tracking | ❌ No | ✅ Yes |
| IN/OUT Events | ❌ No | ✅ Yes |
| CSV Logging | ❌ No | ✅ Yes |
| Parking Analytics | ❌ No | ✅ Yes |
| Complexity | 🟢 Low | 🔴 High |
| Code Lines | ~200 | ~800+ |

---

## Performance

### Expected Performance on Jetson TX1:

| Configuration | FPS | Detection Time |
|---------------|-----|----------------|
| CSI Camera + ONNX | ~4-5 FPS | ~1 second |
| Video File + ONNX | ~4 FPS | ~3 seconds |
| CSI Camera + PyTorch | ~2-3 FPS | ~1.5 seconds |

---

## Technical Details

### Detection Pipeline:
```
┌─────────────────┐
│  Video Source   │ (CSI Camera or Video File)
└────────┬────────┘
         │
┌────────▼────────┐
│ YOLO Detection  │ (ONNX Runtime)
│  License Plate  │
└────────┬────────┘
         │
┌────────▼────────┐
│  Crop Plate     │ (OpenCV)
│  Region         │
└────────┬────────┘
         │
┌────────▼────────┐
│  PaddleOCR      │ (GPU Accelerated)
│  Text Extract   │
└────────┬────────┘
         │
┌────────▼────────┐
│  Display        │ (Draw boxes + text)
└─────────────────┘
```

### GPU Optimizations:
- ✅ **YOLO**: ONNX Runtime (CPU optimized)
- ✅ **OCR**: PaddleOCR GPU (400MB memory limit)
- ✅ **Camera**: GStreamer hardware acceleration
- ✅ **OpenCV**: CUDA support for preprocessing

---

## Differences from Old Reference

Based on `old_refer.py` and `detections/P01.py`:

### What Changed:
1. ✅ **Updated to optimized detector** - Using GPU-accelerated PaddleOCR
2. ✅ **Added CSI camera support** - GStreamer pipeline
3. ✅ **Better error handling** - Graceful camera/video handling
4. ✅ **Enhanced display** - FPS, frame count, detection count
5. ✅ **OCR caching** - Built into detector for performance

### What Stayed the Same:
- ✅ **Simple flow** - Detect → Crop → Extract
- ✅ **No gate logic** - Pure ALPR functionality
- ✅ **Real-time display** - Live video window
- ✅ **Easy to understand** - ~200 lines of clean code

---

## Troubleshooting

### Camera not opening:
```bash
# Check camera connection
ls /dev/video*

# Test GStreamer pipeline
gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink
```

### Low FPS:
- Check if GPU is being used: `jtop`
- Try reducing resolution in camera settings
- Verify ONNX model is loaded (check console output)

### OCR not working:
- Verify PaddleOCR GPU initialized (check console output)
- Check GPU memory: `jtop` → GPU section
- If issues persist, OCR will automatically fall back to CPU

### Import errors:
```bash
# Activate virtual environment
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
source myenv/bin/activate

# Check packages
pip list | grep paddle
pip list | grep ultralytics
```

---

## Example Output

```
============================================================
Simple ALPR - License Plate Detection & OCR
============================================================
Model: models/best.onnx
Initializing CSI Camera...
Camera: 640x480
Resolution: 640x480 @ 30.0 FPS
Loading License Plate Detector...
[INFO] Using device: cuda:0
[INFO] ONNX model loaded: models/best.onnx
[INFO] Model will run on GPU with CUDA acceleration
[INFO] Initializing PaddleOCR with GPU acceleration...
[INFO] PaddleOCR initialized with GPU acceleration (400MB limit)
Detector loaded successfully!

============================================================
Starting detection... (Press ESC to quit)
============================================================

LP DET: bbox=(245,180,421,238) text='世田谷310 70-50'
LP DET: bbox=(245,180,421,238) text='世田谷310 70-50' [CACHED]
...
```

---

## Credits

- **Base Reference**: `old_refer.py` and `detections/P01.py`
- **GPU Optimizations**: From `OPTIMIZATION_SUMMARY_20251125.md`
- **Detection Engine**: YOLOv11 + PaddleOCR
- **Platform**: Jetson TX1 (JetPack 4.6)

---

## Status

✅ **Ready to Use**
✅ **Tested on Jetson TX1**
✅ **GPU Accelerated**
✅ **Production Ready**

**Last Updated:** November 26, 2025
