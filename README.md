# License Plate Detection System - User Documentation

**For: Kobe Denshi Customer**
**Version: 2.0**
**Date: February 2026**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Software Requirements](#software-requirements)
4. [System Features](#system-features)
5. [Quick Start Guide](#quick-start-guide)
6. [Configuration Settings](#configuration-settings)
7. [Output and Logs](#output-and-logs)
8. [Troubleshooting](#troubleshooting)
9. [Support Contact](#support-contact)

---

## System Overview

This is an AI-powered license plate detection and recognition system designed for parking management and vehicle tracking. The system uses:

- **YOLOv7** for vehicle detection
- **PaddleOCR** for Japanese license plate recognition
- **TensorRT** for GPU acceleration on NVIDIA Jetson devices

The system can detect and read Japanese license plates in real-time from camera feeds or video files, logging all detections to CSV files.

---

## Hardware Requirements

### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| **Device** | NVIDIA Jetson Nano 4GB (or higher) |
| **Camera** | IMX477 12MP CSI Camera (ArduCam) |
| **Storage** | 32GB microSD card (minimum) |
| **Power Supply** | 5V 4A DC barrel jack adapter |
| **Memory** | 4GB RAM (included in Jetson Nano) |

### Recommended Setup

- NVIDIA Jetson Nano 4GB Developer Kit
- ArduCam IMX477 12.3MP CSI Camera Module
- 64GB microSD card (SanDisk or Samsung)
- Active cooling fan for Jetson Nano
- Stable 5V 4A power supply

---

## Software Requirements

### Pre-installed Software (Already Configured)

The following software is already installed and configured on your system:

- **Operating System**: Ubuntu 18.04 (Jetson)
- **Python**: 3.6 or higher
- **CUDA**: 10.2
- **TensorRT**: 8.x
- **OpenCV**: 4.x with GStreamer support
- **PaddleOCR**: Latest version
- **YOLOv7**: Custom trained model

### Python Environment

A virtual environment is located at `../myenv` with all required packages:
- torch
- torchvision
- opencv-python
- paddlepaddle
- paddleocr
- numpy
- pandas

---

## System Features

### Core Features

1. **Real-time Detection**: Process live camera feed at 15-25 FPS
2. **Japanese Plate Recognition**: Read all components of Japanese license plates:
   - City name (地域名)
   - Class number (分類番号)
   - Kana character (ひらがな)
   - Plate suffix (指定番号)

3. **Event Tracking**: Log vehicles as "IN" or "OUT" events
4. **Digital Zoom**: 2.4x zoom for distant plates (configurable)
5. **Smart Deduplication**: Prevent duplicate logging (15-second window)
6. **CSV Logging**: Daily CSV files with all plate data
7. **Video Recording**: Save detection videos with annotations

### Advanced Features

- Kana retry system for improved accuracy
- Quality filtering to prevent false detections
- Position-based tracking to handle OCR variations
- Best detection collector (2-second window)

---

## Quick Start Guide

### Starting the System

1. **Navigate to the project directory**:
   ```bash
   cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
   ```

2. **Run the system**:
   ```bash
   ./run_fr01.sh
   ```

3. **The system will**:
   - Initialize the camera
   - Load AI models
   - Start detecting and logging plates
   - Display live feed with detections

4. **To stop the system**:
   - Press `ESC` key in the video window, OR
   - Press `Ctrl+C` in the terminal

### First-Time Setup Verification

When you run the system for the first time, you should see:

```
================================================================================
LICENSE PLATE DETECTION SYSTEM - STARTUP
================================================================================
  CSV Log File:       logs/parking_log_YYYYMMDD.csv
  Video Output:       output_videos/fast_output_YYYYMMDD_HHMMSS.avi
  Mode:               Fast Real-time (front-facing)
  Event Direction:    IN (change in settings)
  Digital Zoom:       2.4x (for distant plates)
  Dedup Window:       15 seconds
  Quality Filter:     ON (min city length: 2)
  Video Recording:    ON
================================================================================
```

---

## Configuration Settings

### Changing Event Direction (IN/OUT)

**Location**: `fr01.py` line 25

**To track ENTRY events**:
```python
EVENT_DIRECTION = "in"
```

**To track EXIT events**:
```python
EVENT_DIRECTION = "out"
```

**Steps**:
1. Open `fr01.py` in a text editor
2. Find line 25: `EVENT_DIRECTION = "in"`
3. Change to `"out"` if needed
4. Save the file
5. Restart the system with `./run_fr01.sh`

---

### Adjusting Digital Zoom

**Location**: `fr01.py` line 64

**Default**: `FIXED_ZOOM = 2.4`

**Recommended values**:
- `2.0` = Medium zoom (5-10 meters distance)
- `2.4` = Default zoom (parking barriers)
- `2.8` = High zoom (10-15 meters)
- `3.5` = Maximum zoom (15-20 meters)

**Steps**:
1. Open `fr01.py` in a text editor
2. Find line 64: `FIXED_ZOOM = 2.4`
3. Change the value
4. Save and restart

---

### Changing Deduplication Window

**Location**: `fr01.py` line 36

**Default**: `DEDUP_WINDOW_SECONDS = 15`

This prevents logging the same plate multiple times within 15 seconds.

**Recommended values**:
- `10` = Faster traffic flow
- `15` = Default (parking barriers)
- `30` = Slower traffic, ensure no duplicates

---

### Video Source Configuration

**Location**: `fr01.py` lines 20-22

**For live camera** (default):
```python
USE_CAMERA = True
USE_FILE = False
```

**For video file**:
```python
USE_CAMERA = False
USE_FILE = True
INPUT_VIDEO_PATH = "input_videos/your_video.mp4"
```

---

## Output and Logs

### CSV Log Files

**Location**: `logs/parking_log_YYYYMMDD.csv`

**Format**:
```csv
timestamp,object_id,vehicle_type,direction,city,engine_size,kana,four-digit number
2026-02-06 14:30:15,01,car,in,品川,589,ろ,70-50
2026-02-06 14:31:22,02,car,in,多摩,330,な,12-34
```

**Columns**:
- `timestamp`: Detection time (YYYY-MM-DD HH:MM:SS)
- `object_id`: Sequential ID (01, 02, 03...)
- `vehicle_type`: Always "car"
- `direction`: "in" or "out" (configurable)
- `city`: City name (地域名)
- `engine_size`: Class number (分類番号)
- `kana`: Hiragana character
- `four-digit number`: Plate suffix (e.g., 70-50)

### Video Output

**Location**: `output_videos/fast_output_YYYYMMDD_HHMMSS.avi`

- Timestamped video files
- Shows bounding boxes around detected plates
- Displays FPS and detection status
- Automatically created for each run

---

## Troubleshooting

### Camera Not Working

**Symptoms**: "Could not open video source" error

**Solutions**:
1. Check camera connection:
   ```bash
   ls /dev/video*
   ```
   Should show `/dev/video0`

2. Restart the camera daemon:
   ```bash
   sudo systemctl restart nvargus-daemon
   ```

3. The `run_fr01.sh` script already handles this automatically

---

### Low FPS / Slow Performance

**Symptoms**: FPS below 10

**Solutions**:
1. Close other running applications
2. Ensure proper cooling (check fan)
3. Reduce zoom level (lower `FIXED_ZOOM` value)
4. Increase frame skip (change `DETECT_EVERY_N` to 3 or 4)

---

### No Plates Detected

**Symptoms**: Camera works but no plates logged

**Possible Causes**:
1. **Plates too far**: Increase `FIXED_ZOOM`
2. **Plates too close**: Decrease `FIXED_ZOOM`
3. **Poor lighting**: Add lighting or adjust camera angle
4. **Quality filter**: Lower `MIN_CITY_LENGTH` to 1

---

### Duplicate Detections

**Symptoms**: Same plate logged multiple times

**Solutions**:
1. Increase `DEDUP_WINDOW_SECONDS` to 30 or 60
2. System already has position-based deduplication
3. Check if vehicles are moving slowly

---

### CSV File Not Created

**Symptoms**: No log file in `logs/` directory

**Solutions**:
1. Check directory permissions:
   ```bash
   sudo chmod -R 777 logs/
   ```

2. Ensure `logs/` directory exists:
   ```bash
   mkdir -p logs
   ```

3. Already handled by the system automatically

---

### System Crashes / Out of Memory

**Symptoms**: System freezes or shuts down

**Solutions**:
1. Run the optimized script:
   ```bash
   ./run_fr01_optimized.sh
   ```

2. Enable swap memory:
   ```bash
   sudo sysctl -w vm.swappiness=60
   ```

3. Close background applications

---

## Daily Operations

### Starting the System Each Day

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_fr01.sh
```

### Accessing Today's Log

```bash
cd logs/
ls -lt | head -5    # Show recent logs
cat parking_log_$(date +%Y%m%d).csv    # View today's log
```

### Viewing Detection Videos

```bash
cd output_videos/
ls -lt | head -5    # Show recent videos
```

---

## File Structure

```
Licence-Plate-Detection-Recognition-Recording/
├── fr01.py                    # Main detection script
├── run_fr01.sh                # Startup script
├── logs/                      # CSV log files (daily)
├── output_videos/             # Recorded videos
├── input_videos/              # Input video files (if using files)
├── models/                    # AI model files
│   └── best_2026.engine       # TensorRT model
├── detections/                # Detection modules
├── utils/                     # Utility functions
└── CUSTOMER_DOCUMENTATION.md  # This file
```

---

## Performance Specifications

### Expected Performance

| Metric | Value |
|--------|-------|
| Detection FPS | 15-25 FPS |
| Processing Latency | 50-80ms per frame |
| Accuracy (good lighting) | 90-95% |
| Accuracy (poor lighting) | 70-85% |
| Detection Range | 2-20 meters (with zoom) |
| Max Concurrent Plates | 5-10 per frame |

---

## Support Contact

For technical support or questions:

**Provider**: License Plate Detection System Development Team
**Customer**: Kobe Denshi Senmon Gakkou

**System Files**:
- Main script: `fr01.py`
- Run script: `run_fr01.sh`
- Documentation: `CUSTOMER_DOCUMENTATION.md`

**Important Files to Keep**:
- All files in `models/` directory
- Configuration in `fr01.py`
- Virtual environment in `../myenv/`

---

## Backup and Maintenance

### Daily Maintenance

- CSV logs are created automatically
- No manual cleanup required
- Videos can be deleted after review to save space

### Backup Recommendations

**Weekly backup**:
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz logs/ output_videos/
```

**Important files to backup**:
- `logs/` - All detection logs
- `fr01.py` - Your configuration
- `models/` - AI models

---

## Quick Reference Commands

### Start System
```bash
./run_fr01.sh
```

### Stop System
Press `ESC` in video window or `Ctrl+C`

### View Today's Log
```bash
cat logs/parking_log_$(date +%Y%m%d).csv
```

### Check System Status
```bash
ls /dev/video*                    # Check camera
systemctl status nvargus-daemon   # Check camera daemon
nvidia-smi                        # Check GPU (if available)
```

### Change Settings
1. Edit `fr01.py` with text editor
2. Modify configuration values
3. Save file
4. Run `./run_fr01.sh` to apply changes

---

## Appendix: Configuration Quick Reference

| Setting | Location | Default | Description |
|---------|----------|---------|-------------|
| Event Direction | Line 25 | "in" | "in" or "out" |
| Digital Zoom | Line 64 | 2.4 | 1.0-3.5 |
| Dedup Window | Line 36 | 15 | Seconds |
| Target Width | Line 33 | 640 | Resolution |
| Detect Interval | Line 31 | 2 | Process every N frames |
| Video Recording | Line 49 | True | Enable/disable |
| Show FPS | Line 51 | True | Display FPS |

---

**End of Documentation**

*For the latest updates and additional information, refer to the project's QUICK_START.md and OPTIMIZATION_SUMMARY.md files.*
