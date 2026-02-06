# CSI Camera Integration for IMX477 12MP Arducam

This module provides GStreamer pipeline integration for the IMX477 12MP Arducam CSI camera on NVIDIA Jetson devices, optimized for license plate detection applications.

## Reference

Based on [JetsonHacks CSI-Camera](https://github.com/JetsonHacksNano/CSI-Camera) implementation.

## Hardware Requirements

- NVIDIA Jetson (Nano, Xavier NX, AGX Xavier, Orin series)
- IMX477 12MP Arducam CSI camera
- Properly connected CSI ribbon cable

## Camera Specifications (IMX477)

- **Resolution**: Up to 4032 x 3040 (12.3 MP)
- **Sensor Modes**:
  - Mode 0: 4032x3040 @ 10fps (Full 12MP)
  - Mode 1: 3840x2160 @ 21fps (4K)
  - Mode 2: 1920x1080 @ 60fps (1080p)

## Quick Start

### 1. Test Camera Connection

```bash
# Activate virtual environment
source /home/jetson/yolo/yolov7/aenv/bin/activate

# Run camera test
python3 test_csi_camera.py
```

### 2. Basic Usage

```python
from csi_camera import get_csi_camera_preset

# Open camera with balanced preset (1080p @ 60fps)
cap = get_csi_camera_preset("balanced", flip_method=0)

if cap is not None:
    ret, frame = cap.read()
    if ret:
        print(f"Captured frame: {frame.shape}")
    cap.release()
```

## Presets

### 1. **high_res** - Best Quality
```python
cap = get_csi_camera_preset("high_res")
# 3840x2160 capture → 1920x1080 output @ 21fps
# Best for detailed license plate detection
```

### 2. **balanced** - Recommended (Default)
```python
cap = get_csi_camera_preset("balanced")
# 1920x1080 @ 60fps
# Good balance of quality and speed
```

### 3. **fast** - Maximum Speed
```python
cap = get_csi_camera_preset("fast")
# 1280x720 @ 60fps
# For real-time processing with lower latency
```

## Advanced Usage

### Custom Pipeline

```python
from csi_camera import get_csi_camera

cap = get_csi_camera(
    sensor_id=0,
    capture_width=3840,
    capture_height=2160,
    display_width=1920,
    display_height=1080,
    framerate=21,
    flip_method=0  # 0=none, 2=180°, 4=horizontal, 6=vertical
)
```

### Direct GStreamer Pipeline

```python
from csi_camera import gstreamer_pipeline
import cv2

pipeline = gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=1920,
    display_height=1080,
    framerate=30,
    flip_method=0
)

cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
```

## Integration with License Plate Detection

### Example: Replace Video File with CSI Camera

```python
import cv2
from csi_camera import get_csi_camera_preset

# Instead of:
# cap = cv2.VideoCapture("video.mp4")

# Use:
cap = get_csi_camera_preset("balanced", flip_method=0)

if cap is None:
    print("Failed to open CSI camera")
    exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Your license plate detection code here
    # detected_plates = detect_license_plates(frame)
    # ...

    cv2.imshow("License Plate Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## Flip Methods

Use the `flip_method` parameter to rotate/flip the image:

- `0` - No flip
- `1` - Rotate 90° counter-clockwise
- `2` - Rotate 180°
- `3` - Rotate 90° clockwise
- `4` - Horizontal flip
- `5` - Upper right diagonal flip
- `6` - Vertical flip
- `7` - Upper left diagonal flip

## Troubleshooting

### Camera Not Opening

1. **Check physical connection**:
   ```bash
   ls -l /dev/video*
   ```
   Should show `/dev/video0` (and `/dev/video1` for dual camera)

2. **Test with gst-launch-1.0**:
   ```bash
   gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! \
       'video/x-raw(memory:NVMM), width=1920, height=1080, framerate=30/1' ! \
       nvvidconv ! 'video/x-raw, format=BGRx' ! \
       videoconvert ! 'video/x-raw, format=BGR' ! \
       autovideosink
   ```

3. **Check camera detection**:
   ```bash
   v4l2-ctl --list-devices
   ```

4. **Verify GStreamer plugins**:
   ```bash
   gst-inspect-1.0 nvarguscamerasrc
   ```

### Low FPS

- Use lower resolution preset ("fast" or "balanced")
- Reduce capture resolution
- Check system load with `tegrastats`
- Enable maximum performance mode:
  ```bash
  sudo nvpmodel -m 0  # Max performance mode
  sudo jetson_clocks   # Max clock speeds
  ```

### Image Quality Issues

- Use "high_res" preset for better quality
- Adjust camera focus (IMX477 has adjustable focus)
- Check lens for dust/smudges
- Ensure good lighting conditions

## Performance Benchmarks (Expected)

On Jetson Nano (with proper cooling):
- **fast preset**: ~60 FPS
- **balanced preset**: ~50-60 FPS
- **high_res preset**: ~20-21 FPS

On Jetson Xavier NX / AGX:
- All presets: Full rated FPS

*Note: Actual FPS depends on additional processing load*

## Environment Setup

The `aenv` virtual environment should already have all required packages:
- OpenCV with GStreamer support
- NumPy
- System packages (paddlepaddle, ultralytics, paddleocr)

## Testing Checklist

- [ ] Camera physically connected
- [ ] Virtual environment activated (`source aenv/bin/activate`)
- [ ] Run `python3 test_csi_camera.py` - all tests pass
- [ ] Image orientation correct (adjust flip_method if needed)
- [ ] FPS meets requirements
- [ ] Integration with detection code works

## Additional Resources

- [JetsonHacks CSI Camera Guide](https://jetsonhacks.com/2022/01/25/jetson-camera-coding/)
- [IMX477 Datasheet](https://www.arducam.com/product/12mp-imx477-mini-high-quality-camera/)
- [NVIDIA Jetson Camera Architecture](https://developer.nvidia.com/embedded/learn/tutorials/first-picture-csi-usb-camera)

## License

MIT License (following JetsonHacks implementation)
