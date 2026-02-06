# CSI Camera Setup Guide - Arducam IMX477 12MP

## Overview

This guide covers the complete setup for using the **Arducam IMX477 12MP CSI camera** with TensorRT-optimized license plate detection on Jetson platforms.

## Features

✅ **Automatic Process Cleanup** - Kills all stale GStreamer and camera processes
✅ **Argus Daemon Restart** - Ensures clean camera initialization
✅ **GStreamer Hardware Acceleration** - Uses nvarguscamerasrc for CSI cameras
✅ **TensorRT Optimization** - GPU-accelerated YOLO + OCR inference
✅ **Multiple Resolution Support** - From 640p to 12MP
✅ **One-Command Launch** - Everything automated in a single script

## Hardware Requirements

- **Jetson Nano/Xavier/Orin** with JetPack 4.6+
- **Arducam IMX477 12MP** CSI camera module
- **15-pin MIPI CSI ribbon cable** (included with camera)
- Properly connected CSI camera to CAM0 or CAM1 port

## Quick Start

### 1. Run the Complete Pipeline

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_csi_camera.sh
```

This single command will:
1. Kill all stale camera processes
2. Restart NVIDIA Argus daemon
3. Activate virtual environment
4. Set maximum performance mode
5. Verify TensorRT models
6. Launch license plate detection

### 2. Test Camera Only

```bash
# Test camera for 5 seconds
python3 camera_utils.py test 0 5

# List available cameras
python3 camera_utils.py list
```

### 3. Manual Cleanup (if needed)

```bash
# Kill all camera processes
./cleanup_camera.sh

# Restart Argus daemon
./restart_argus.sh
```

## Configuration

### Camera Settings

Edit `fr01.py` to configure camera:

```python
# CSI Camera settings
USE_CSI_CAMERA    = True        # Enable CSI camera
CSI_CAMERA_ID     = 0           # Sensor ID (0 for CAM0, 1 for CAM1)
CSI_RESOLUTION    = '720p'      # Resolution preset
CSI_FPS           = 30          # Frames per second
CSI_FLIP_METHOD   = 0           # Rotation (0=none, 2=180°)
```

### Supported Resolutions

| Preset | Resolution | Notes |
|--------|-----------|-------|
| `'640p'` | 640×480 | Fastest, lowest quality |
| `'720p'` | 1280×720 | **Recommended** - Best balance |
| `'1080p'` | 1920×1080 | High quality, slower |
| `'4K'` | 3840×2160 | Very high quality, much slower |
| `'12MP'` | 4032×3040 | Full resolution, very slow |

**Recommendation**: Use `'720p'` for real-time detection with good quality.

### Performance Settings

```python
TARGET_WIDTH       = 640        # Detection resolution (lower = faster)
DETECT_EVERY_N     = 1          # Process every N frames (2-3 for speedup)
MAX_INFER_WIDTH    = 640        # Max width for detection
```

## File Structure

```
Licence-Plate-Detection-Recognition-Recording/
├── camera_utils.py              # NEW: Camera utility module
├── cleanup_camera.sh            # NEW: Process cleanup script
├── restart_argus.sh             # NEW: Argus daemon restart
├── run_csi_camera.sh            # NEW: Master launch script
├── fr01.py                      # UPDATED: Main detection script
├── detections/
│   └── licence_plate_detection.py  # TensorRT detector
└── models/
    ├── best.engine              # YOLO TensorRT engine
    └── paddleocr_onnx/
        └── rec_japan_fp16.engine  # OCR TensorRT engine
```

## GStreamer Pipeline

The system uses an optimized GStreamer pipeline for CSI camera:

```
nvarguscamerasrc sensor-id=0 !
video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 !
nvvidconv flip-method=0 !
video/x-raw, format=BGRx !
videoconvert !
video/x-raw, format=BGR !
appsink
```

### Pipeline Components

- **nvarguscamerasrc**: NVIDIA Argus camera source (CSI cameras)
- **NVMM**: NVIDIA Memory Management (zero-copy GPU memory)
- **nvvidconv**: Hardware video converter
- **videoconvert**: Format converter for OpenCV
- **appsink**: OpenCV capture interface

## Troubleshooting

### Issue: Camera not detected

**Symptoms**:
```
[ERROR] Failed to open camera with GStreamer
```

**Solutions**:
1. Check physical connection
   ```bash
   ls /dev/video*
   # Should show /dev/video0 and /dev/video1
   ```

2. Verify camera is recognized
   ```bash
   v4l2-ctl --list-devices
   ```

3. Check dmesg for errors
   ```bash
   dmesg | grep -i imx477
   dmesg | grep -i argus
   ```

4. Run cleanup and restart
   ```bash
   ./cleanup_camera.sh
   ./restart_argus.sh
   ```

### Issue: Argus daemon errors

**Symptoms**:
```
nvarguscamerasrc: Cannot open camera
Argus: SCF: ERROR ...
```

**Solutions**:
1. Restart Argus daemon
   ```bash
   ./restart_argus.sh
   ```

2. Check Argus daemon status
   ```bash
   ps aux | grep nvargus-daemon
   ```

3. Manually restart if needed
   ```bash
   sudo systemctl restart nvargus-daemon
   # OR
   sudo killall nvargus-daemon
   # Daemon will auto-restart on camera access
   ```

### Issue: GStreamer processes stuck

**Symptoms**:
```
Device or resource busy
```

**Solutions**:
1. Run cleanup script
   ```bash
   ./cleanup_camera.sh
   ```

2. Manually kill processes
   ```bash
   sudo pkill -9 gst-launch
   sudo pkill -9 nvargus-daemon
   ```

3. Check for processes using camera
   ```bash
   sudo lsof /dev/video0
   ```

### Issue: Low FPS or dropped frames

**Solutions**:
1. Reduce resolution
   ```python
   CSI_RESOLUTION = '640p'  # Instead of '1080p'
   ```

2. Reduce detection frequency
   ```python
   DETECT_EVERY_N = 2  # Process every 2nd frame
   ```

3. Enable max performance mode
   ```bash
   sudo nvpmodel -m 0
   sudo jetson_clocks
   ```

4. Lower camera FPS
   ```python
   CSI_FPS = 20  # Instead of 30
   ```

### Issue: TensorRT engine loading fails

**Solutions**:
1. Check engine compatibility
   ```bash
   python3 test_tensorrt_setup.py
   ```

2. Regenerate engines for your device
   ```bash
   ./rebuild_tensorrt.py
   ```

3. Use fallback to PyTorch
   ```python
   # The system will auto-fallback if TensorRT fails
   # Check console for "Falling back to standard detector"
   ```

## Performance Optimization

### Best Settings for Real-Time Detection

```python
# In fr01.py
CSI_RESOLUTION     = '720p'     # Good balance
CSI_FPS            = 30         # Smooth video
TARGET_WIDTH       = 640        # Detection resolution
DETECT_EVERY_N     = 1          # Process all frames
```

### Expected Performance

| Resolution | FPS (Display) | FPS (Detection) | Latency |
|-----------|--------------|-----------------|---------|
| 640p | 30 | 25-30 | ~40ms |
| 720p | 30 | 20-25 | ~50ms |
| 1080p | 30 | 15-20 | ~65ms |

**Note**: Detection FPS may be lower than display FPS due to processing time.

### Power Modes

```bash
# Maximum performance (recommended)
sudo nvpmodel -m 0
sudo jetson_clocks

# Check current mode
sudo nvpmodel -q

# List available modes
sudo nvpmodel -p --verbose
```

## Camera Testing

### Quick Test (5 seconds)

```bash
python3 camera_utils.py test 0 5
```

### Test with GStreamer directly

```bash
# View camera feed
gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! \
  'video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1' ! \
  nvvidconv ! 'video/x-raw, format=BGRx' ! \
  videoconvert ! 'video/x-raw, format=BGR' ! \
  autovideosink
```

### Test with v4l2-ctl

```bash
# List camera capabilities
v4l2-ctl --list-formats-ext -d /dev/video0

# Capture a single frame
v4l2-ctl --set-fmt-video=width=1280,height=720 -d /dev/video0 --stream-mmap --stream-count=1
```

## Integration with Detection Pipeline

### How It Works

```
[1] Cleanup Script
    ↓ Kill stale processes
[2] Argus Restart
    ↓ Fresh daemon
[3] CSI Camera Init
    ↓ GStreamer pipeline
[4] OpenCV Capture
    ↓ Frame acquisition
[5] TensorRT YOLO
    ↓ Plate detection
[6] TensorRT OCR
    ↓ Text recognition
[7] CSV Logging
    ↓ Save results
```

### Pre-Run Checklist

Before each run, the script automatically:
- ✅ Kills all GStreamer processes
- ✅ Kills nvargus-daemon
- ✅ Clears device locks
- ✅ Restarts Argus daemon
- ✅ Sets LD_PRELOAD for libgomp
- ✅ Activates virtual environment
- ✅ Sets max performance mode
- ✅ Verifies TensorRT models

## Advanced Usage

### Custom GStreamer Pipeline

Edit `camera_utils.py` to customize pipeline:

```python
def get_custom_pipeline(self):
    pipeline = (
        f'nvarguscamerasrc sensor-id={self.camera_id} '
        f'tnr-mode=2 tnr-strength=0.5 '  # Temporal noise reduction
        f'ee-mode=2 ee-strength=0.5 '    # Edge enhancement
        f'! video/x-raw(memory:NVMM), '
        f'width={self.width}, height={self.height}, '
        f'format=NV12, framerate={self.fps}/1 '
        f'! nvvidconv flip-method={self.flip_method} '
        f'! video/x-raw, format=BGRx '
        f'! videoconvert ! video/x-raw, format=BGR '
        f'! appsink'
    )
    return pipeline
```

### Dual Camera Setup

For multiple cameras:

```python
# In fr01.py
CSI_CAMERA_ID = 0  # Use CAM0
# OR
CSI_CAMERA_ID = 1  # Use CAM1

# In camera_utils.py, you can open both:
cam0 = ArducamIMX477(camera_id=0, resolution='720p')
cam1 = ArducamIMX477(camera_id=1, resolution='720p')
```

### Camera Exposure Control

```bash
# Set exposure time (nanoseconds)
v4l2-ctl -d /dev/video0 -c exposure=30000000  # 30ms

# Set gain
v4l2-ctl -d /dev/video0 -c gain=100

# List all controls
v4l2-ctl -d /dev/video0 --list-ctrls
```

## References

- **Arducam IMX477**: https://www.arducam.com/product/imx477-high-quality-camera/
- **NVIDIA Argus**: https://docs.nvidia.com/jetson/l4t-multimedia/group__LibargusAPI.html
- **GStreamer**: https://gstreamer.freedesktop.org/documentation/
- **nvarguscamerasrc**: https://developer.nvidia.com/embedded/dlc/l4t-accelerated-gstreamer-guide

## Summary

The CSI camera integration provides:
- ✅ Automated setup and cleanup
- ✅ Hardware-accelerated capture via GStreamer
- ✅ TensorRT-optimized detection and OCR
- ✅ One-command launch script
- ✅ Robust error handling and fallbacks

Run with:
```bash
./run_csi_camera.sh
```

Happy detecting! 🚗📸
