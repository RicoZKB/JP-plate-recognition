# CSI Camera Setup - IMX477 12MP ArduCam

**Date:** January 15, 2026
**Camera:** IMX477 12MP ArduCam (Jetson CSI)
**Status:** ✅ Configured with GStreamer

---

## Camera Specifications

### IMX477 12MP ArduCam

| Specification | Value |
|---------------|-------|
| **Sensor** | Sony IMX477 |
| **Resolution** | 12.3 MP (4056 × 3040) |
| **Max Video** | 4K @ 60fps, 1080p @ 120fps |
| **Interface** | MIPI CSI-2 |
| **Connector** | 15-pin FFC cable |
| **Manufacturer** | ArduCam |

---

## System Configuration

### GStreamer Pipeline

The system uses optimized GStreamer pipeline for IMX477:

```python
nvarguscamerasrc sensor-id=0 !
video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 !
nvvidconv flip-method=0 !
video/x-raw, width=640, height=480, format=BGRx !
videoconvert !
video/x-raw, format=BGR !
appsink
```

### Pipeline Components

| Component | Purpose |
|-----------|---------|
| **nvarguscamerasrc** | NVIDIA Argus camera source driver |
| **sensor-id=0** | Primary CSI camera (change to 1 for second camera) |
| **1920x1080** | Capture resolution (1080p for quality) |
| **30fps** | Frame rate |
| **nvvidconv** | Hardware-accelerated video conversion |
| **flip-method=0** | No rotation (2 = rotate 180°) |
| **640x480** | Output resolution for processing |
| **BGRx → BGR** | Color format conversion for OpenCV |

### Capture Settings

**Optimized for License Plate Detection:**

- **Capture Resolution:** 1920×1080 (1080p)
  - Good quality for plate reading
  - Not too demanding on TX1 hardware
  - 60% of native 4K resolution

- **Processing Resolution:** 640×480
  - Fast inference with TensorRT
  - Sufficient detail for plates
  - Matches TARGET_WIDTH setting

- **Frame Rate:** 30 FPS
  - Smooth video capture
  - Good for moving vehicles

---

## Run Script Process

### What `run_fr01.sh` Does

**Step 1: Clean Up Processes**
```bash
# Kill any existing GStreamer processes
pkill -f "gst-launch\|nvarguscamera\|nvargus"

# Kill any Python camera processes
pkill -f "fr01.py\|fast_realtime"
```

**Step 2: Restart nvargus-daemon**
```bash
# Stop daemon
sudo systemctl stop nvargus-daemon

# Kill any remaining processes
sudo pkill -9 nvargus-daemon

# Start daemon fresh
sudo systemctl start nvargus-daemon
```

**Step 3: Verify Camera**
```bash
# Check camera device exists
ls -l /dev/video*
```

**Step 4-6: Environment & Run**
- Activate virtual environment
- Set LD_PRELOAD variables
- Run detection system

### Why This Process is Needed

**Problem:** Camera/daemon can get stuck after crashes
**Solution:** Clean restart ensures:
- ✅ No leftover processes blocking camera
- ✅ nvargus-daemon in fresh state
- ✅ GStreamer pipeline initializes properly
- ✅ Consistent behavior every run

---

## Camera Configuration

### Change Capture Resolution

Edit `fr01.py` around line 380:

```python
gst_pipeline = get_csi_camera_pipeline(
    sensor_id=0,
    capture_width=1920,    # Change this (options: 1280, 1920, 3840)
    capture_height=1080,   # Change this (options: 720, 1080, 2160)
    display_width=TARGET_WIDTH,
    display_height=int(TARGET_WIDTH * 9 / 16),
    framerate=30,          # Change FPS (options: 15, 30, 60)
    flip_method=0          # 0=normal, 2=rotate-180
)
```

### Resolution Options

| Resolution | Width × Height | Use Case | TX1 Performance |
|------------|---------------|----------|-----------------|
| **720p** | 1280 × 720 | Fast, lower quality | ~25 FPS |
| **1080p** | 1920 × 1080 | Balanced (recommended) | ~18 FPS |
| **4K** | 3840 × 2160 | Max quality, slow | ~8 FPS |

### Frame Rate Options

| FPS | Use Case | Notes |
|-----|----------|-------|
| **15** | Slow traffic, max processing time | More time per frame |
| **30** | Normal traffic (recommended) | Good balance |
| **60** | Fast traffic, smooth video | Requires 720p or lower |

### Flip Methods

| Value | Rotation | Use When |
|-------|----------|----------|
| **0** | No rotation | Camera mounted normally |
| **2** | 180° rotation | Camera mounted upside down |

---

## Troubleshooting

### Camera Not Detected

**Symptoms:**
- Error: "Could not open video source"
- No /dev/video0 device

**Solutions:**

1. **Check Physical Connection**
   ```bash
   # Check if camera is detected
   ls /dev/video*
   # Should show: /dev/video0
   ```

2. **Restart nvargus-daemon**
   ```bash
   sudo systemctl restart nvargus-daemon
   sleep 2
   systemctl status nvargus-daemon
   ```

3. **Check Camera with v4l2-ctl**
   ```bash
   v4l2-ctl --list-devices
   # Should show: vi-output camera
   ```

4. **Test with Simple Pipeline**
   ```bash
   gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink
   # Should show camera preview
   ```

### nvargus-daemon Errors

**Symptoms:**
- "SCF: Error Timeout" in logs
- "ArgusCore: Init failed"

**Solutions:**

1. **Full Restart**
   ```bash
   ./run_fr01.sh
   # Script handles full cleanup and restart
   ```

2. **Manual Restart**
   ```bash
   sudo systemctl stop nvargus-daemon
   sudo pkill -9 nvargus-daemon
   sudo rm /tmp/argus_socket
   sudo systemctl start nvargus-daemon
   ```

3. **Check Logs**
   ```bash
   sudo journalctl -u nvargus-daemon -n 50
   ```

### GStreamer Pipeline Errors

**Symptoms:**
- "Cannot find element nvarguscamerasrc"
- Pipeline fails to initialize

**Solutions:**

1. **Check GStreamer Plugins**
   ```bash
   gst-inspect-1.0 nvarguscamerasrc
   # Should show plugin details
   ```

2. **Verify CUDA Libraries**
   ```bash
   export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0:/usr/lib/aarch64-linux-gnu/libgomp.so.1
   ```

3. **Enable Debug Output**
   ```bash
   export GST_DEBUG=3
   python3 fr01.py
   ```

### Low FPS / Stuttering

**Symptoms:**
- FPS drops below 10
- Video stutters

**Solutions:**

1. **Reduce Capture Resolution**
   ```python
   # In fr01.py, change to 720p
   capture_width=1280,
   capture_height=720,
   ```

2. **Reduce Frame Rate**
   ```python
   framerate=15,  # Instead of 30
   ```

3. **Check System Load**
   ```bash
   tegrastats
   # Check CPU/GPU usage
   ```

### Camera Appears Black/Dark

**Symptoms:**
- Camera working but image is very dark
- Plates not visible

**Solutions:**

1. **Auto Exposure Takes Time**
   - Wait 5-10 seconds for camera to adjust
   - Point at bright area first

2. **Add Manual Exposure**
   ```python
   # In GStreamer pipeline, add:
   nvarguscamerasrc sensor-id=0 exposurecompensation=1.5 !
   ```

3. **Check Lighting**
   - IMX477 needs adequate lighting
   - Use external lighting for night operation

---

## Testing Camera

### Quick Camera Test

```bash
# Test 1: Simple preview (5 seconds)
gst-launch-1.0 nvarguscamerasrc num-buffers=150 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvoverlaysink

# Test 2: Save test image
gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080' ! nvjpegenc ! filesink location=test.jpg

# Test 3: OpenCV capture test
python3 -c "
import cv2
pipeline = 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 ! nvvidconv ! video/x-raw, width=640, height=480, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
print('Camera opened:', cap.isOpened())
ret, frame = cap.read()
print('Frame captured:', ret)
if ret:
    print('Frame shape:', frame.shape)
cap.release()
"
```

### Check Camera Info

```bash
# List camera devices
v4l2-ctl --list-devices

# Get camera capabilities
v4l2-ctl -d /dev/video0 --all

# Check supported formats
v4l2-ctl -d /dev/video0 --list-formats-ext
```

---

## Advanced Configuration

### Multiple Cameras

If you have two CSI cameras:

```python
# Camera 0 (default)
gst_pipeline = get_csi_camera_pipeline(sensor_id=0, ...)

# Camera 1 (second CSI port)
gst_pipeline = get_csi_camera_pipeline(sensor_id=1, ...)
```

### Custom Exposure Settings

```python
# Add to GStreamer pipeline
nvarguscamerasrc sensor-id=0
    exposurecompensation=1.0     # -2.0 to 2.0
    tnr-mode=2                   # Temporal noise reduction (1=fast, 2=quality)
    tnr-strength=0.5             # 0.0 to 1.0
    ee-mode=2                    # Edge enhancement (1=fast, 2=quality)
    ee-strength=0.5              # 0.0 to 1.0
    ! ...
```

### Focus Adjustment

IMX477 supports autofocus (if module has motor):

```bash
# Set focus position (manual)
v4l2-ctl -d /dev/video0 --set-ctrl=focus_absolute=300

# Enable autofocus
v4l2-ctl -d /dev/video0 --set-ctrl=focus_auto=1
```

---

## Performance Optimization

### Recommended Settings for TX1

**For Maximum FPS (20+ FPS):**
```python
capture_width=1280,      # 720p
capture_height=720,
display_width=640,
display_height=360,
framerate=30,
```

**For Maximum Quality (12-15 FPS):**
```python
capture_width=1920,      # 1080p
capture_height=1080,
display_width=640,
display_height=480,
framerate=30,
```

**For 4K Quality (8-10 FPS):**
```python
capture_width=3840,      # 4K
capture_height=2160,
display_width=640,
display_height=480,
framerate=30,
```

### Memory Considerations

- **1080p capture:** ~6 MB per frame
- **4K capture:** ~24 MB per frame
- **TX1 has 4GB shared memory**
- Keep frame buffer small for stability

---

## Hardware Setup

### Cable Connection

1. **Power off Jetson TX1**
2. **Connect FFC cable to CSI port**
   - Blue side facing away from Jetson
   - Pins facing toward Jetson board
3. **Lock connector**
4. **Power on Jetson**

### Camera Position

For license plate detection:
- **Height:** 1-2 meters above ground
- **Angle:** Straight or slight downward tilt
- **Distance:** 2-8 meters from target
- **Lighting:** Avoid direct sun behind camera

---

## Summary

✅ **Camera:** IMX477 12MP ArduCam
✅ **Interface:** CSI via GStreamer pipeline
✅ **Capture:** 1080p @ 30fps (recommended)
✅ **Processing:** 640×480 downscaled
✅ **Clean Start:** Automatic process cleanup and nvargus restart
✅ **Performance:** 15-18 FPS with TensorRT on TX1

**To run:**
```bash
./run_fr01.sh
```

**Script automatically handles:**
- Process cleanup
- nvargus-daemon restart
- Camera initialization
- Environment setup

**No manual intervention needed!**

---

## Quick Reference

```bash
# Run system with clean camera init
./run_fr01.sh

# Check camera device
ls -l /dev/video*

# Restart nvargus manually
sudo systemctl restart nvargus-daemon

# Test camera
gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink

# View nvargus logs
sudo journalctl -u nvargus-daemon -f

# Kill stuck processes
pkill -f nvarguscamera
sudo systemctl restart nvargus-daemon
```
