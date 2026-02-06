# Video Output Guide

**Date:** January 15, 2026
**Status:** ✅ Unique filenames per run

---

## Video File Naming

### Automatic Unique Filenames

Every time you run the system, a new video file is created with a timestamp:

**Format:** `fast_output_YYYYMMDD_HHMMSS.avi`

**Components:**
- `YYYYMMDD` - Date (Year, Month, Day)
- `HHMMSS` - Time (Hour, Minute, Second)
- `.avi` - MJPEG format

### Examples

```
output_videos/
├── fast_output_20260115_102345.avi  ← Run 1: January 15, 10:23:45 AM
├── fast_output_20260115_143021.avi  ← Run 2: January 15, 02:30:21 PM
├── fast_output_20260115_185512.avi  ← Run 3: January 15, 06:55:12 PM
└── fast_output_20260116_090130.avi  ← Run 4: January 16, 09:01:30 AM
```

### Benefits

✅ **No Data Loss** - Previous recordings are never overwritten
✅ **Easy Identification** - Filename shows when recording was made
✅ **Chronological Order** - Files sorted naturally by timestamp
✅ **Multiple Runs** - Can run system many times per day
✅ **Archive-Friendly** - Easy to organize and backup

---

## Startup Message

When the system starts, you'll see:

```
================================================================================
LICENSE PLATE DETECTION SYSTEM - STARTUP
================================================================================
  CSV Log File:       logs/plates_fast_20260115.csv
  Video Output:       output_videos/fast_output_20260115_102345.avi
  CSV Format:         timestamp | object_id | vehicle_type | direction |
                      city | class_number | kana | suffix
  Mode:               Fast Real-time (front-facing)
  Dedup Window:       30 seconds
  Quality Filter:     ON (min city length: 2)
  Collection Window:  6 seconds (best detection)
  Video Recording:    ON
================================================================================
```

## Stop Message

When the system stops, you'll see:

```
================================================================================
SYSTEM STOPPED
================================================================================
  CSV saved to:   logs/plates_fast_20260115.csv
  Video saved to: output_videos/fast_output_20260115_102345.avi
================================================================================
```

---

## Video Settings

### Enable/Disable Recording

Edit `fr01.py` line 49:

```python
WRITE_VIDEO = True   # Enable video recording
WRITE_VIDEO = False  # Disable video recording (saves CPU/disk)
```

### Video Properties

| Property | Value | Note |
|----------|-------|------|
| **Format** | MJPEG | Standard AVI format |
| **Codec** | MJPG | Compatible with all players |
| **Resolution** | 640×480 (default) | Same as `TARGET_WIDTH` |
| **FPS** | 15-20 | Matches camera/input FPS |
| **Size** | ~50-100 MB per minute | Depends on content |

---

## Disk Space Management

### Check Available Space

```bash
# Check disk space
df -h .

# Check output_videos directory size
du -sh output_videos/

# List videos with sizes
ls -lh output_videos/
```

### Automatic Cleanup Scripts

#### Delete Old Videos (7+ days)

```bash
# Delete videos older than 7 days
find output_videos/ -name "fast_output_*.avi" -mtime +7 -delete
```

Add to cron for automatic cleanup:
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * find /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording/output_videos/ -name "*.avi" -mtime +7 -delete
```

#### Keep Only Recent Videos

```bash
# Keep only the 10 most recent videos
cd output_videos/
ls -t fast_output_*.avi | tail -n +11 | xargs rm -f
```

#### Archive Old Videos

```bash
# Archive videos by month
cd output_videos/
tar -czf videos_202601.tar.gz fast_output_202601*.avi
rm fast_output_202601*.avi

# Or use date-based archive
tar -czf videos_$(date +%Y%m).tar.gz fast_output_$(date +%Y%m)*.avi
```

### Manual Cleanup

```bash
# Delete all videos
rm output_videos/*.avi

# Delete videos from specific date
rm output_videos/fast_output_20260115*.avi

# Delete videos from specific time range
rm output_videos/fast_output_20260115_10*.avi  # All from 10:00-10:59
```

---

## Playing Videos

### VLC Player (Recommended)

```bash
# Play latest video
vlc $(ls -t output_videos/*.avi | head -1)

# Play all videos in sequence
vlc output_videos/*.avi

# Play videos from specific date
vlc output_videos/fast_output_20260115*.avi
```

### FFplay (Lightweight)

```bash
# Play latest video
ffplay -autoexit $(ls -t output_videos/*.avi | head -1)
```

### OpenCV Python

```python
import cv2

# Read video
cap = cv2.VideoCapture('output_videos/fast_output_20260115_102345.avi')

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow('Video', frame)
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

---

## Video Conversion

### Convert to MP4 (Smaller Size)

```bash
# Single file
ffmpeg -i output_videos/fast_output_20260115_102345.avi \
       -c:v libx264 -preset medium -crf 23 \
       output_videos/fast_output_20260115_102345.mp4

# Batch convert all AVI to MP4
for file in output_videos/*.avi; do
    ffmpeg -i "$file" -c:v libx264 -preset medium -crf 23 \
           "${file%.avi}.mp4"
done

# Delete original AVI files after conversion
rm output_videos/*.avi
```

### Convert to WebM (Web-Friendly)

```bash
ffmpeg -i output_videos/fast_output_20260115_102345.avi \
       -c:v libvpx-vp9 -crf 30 -b:v 0 \
       output_videos/fast_output_20260115_102345.webm
```

### Extract Frames

```bash
# Extract frames to images
ffmpeg -i output_videos/fast_output_20260115_102345.avi \
       -vf fps=1 frames/frame_%04d.jpg

# Extract one frame per second
```

---

## Video Analysis

### Get Video Information

```bash
# Using ffprobe
ffprobe output_videos/fast_output_20260115_102345.avi

# Get duration
ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 \
        output_videos/fast_output_20260115_102345.avi

# Get frame count
ffprobe -v error -select_streams v:0 \
        -count_packets -show_entries stream=nb_read_packets \
        -of csv=p=0 output_videos/fast_output_20260115_102345.avi
```

### Python Analysis

```python
import cv2
from datetime import datetime

def analyze_video(filename):
    cap = cv2.VideoCapture(filename)

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps

    print(f"Video: {filename}")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps:.2f}")
    print(f"  Frames: {frame_count}")
    print(f"  Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

    cap.release()

# Analyze latest video
import glob
videos = sorted(glob.glob('output_videos/*.avi'), reverse=True)
if videos:
    analyze_video(videos[0])
```

---

## Troubleshooting

### Video File is Empty (0 bytes)

**Cause:** System crashed before closing video file

**Solution:**
- Video writer needs to be properly closed
- Make sure to stop with ESC key or Ctrl+C (not kill -9)

### Video Won't Play

**Cause:** Codec not supported

**Solution:**
```bash
# Convert to standard MP4
ffmpeg -i output_videos/problem_video.avi \
       -c:v libx264 output_videos/fixed_video.mp4
```

### Video is Corrupt

**Cause:** System crashed during recording

**Solution:**
```bash
# Try to recover
ffmpeg -i output_videos/corrupt_video.avi \
       -c copy output_videos/recovered_video.avi
```

### Disk Full

**Cause:** Too many video files

**Solution:**
```bash
# Check disk usage
df -h .

# Delete old videos
find output_videos/ -name "*.avi" -mtime +3 -delete

# Or disable video recording
# Edit fr01.py: WRITE_VIDEO = False
```

---

## Best Practices

### 1. Regular Cleanup

Set up automatic cleanup:
```bash
# Add to crontab (runs weekly on Sunday at 3 AM)
0 3 * * 0 find /path/to/output_videos/ -name "*.avi" -mtime +7 -delete
```

### 2. Backup Important Videos

```bash
# Create backup directory
mkdir -p backups/

# Copy important videos
cp output_videos/fast_output_20260115_102345.avi backups/
```

### 3. Monitor Disk Space

```bash
# Create monitoring script
cat > check_disk.sh << 'EOF'
#!/bin/bash
USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
    echo "Warning: Disk usage is ${USAGE}%"
    echo "Cleaning old videos..."
    find output_videos/ -name "*.avi" -mtime +3 -delete
fi
EOF

chmod +x check_disk.sh
```

### 4. Compress Before Archiving

```bash
# Convert to MP4 (much smaller)
for avi in output_videos/*.avi; do
    mp4="${avi%.avi}.mp4"
    ffmpeg -i "$avi" -c:v libx264 -crf 23 "$mp4" && rm "$avi"
done
```

---

## Summary

✅ **Unique Filenames** - No overwriting, each run creates new file
✅ **Timestamp Format** - Easy to identify when recording was made
✅ **Automatic Creation** - System handles naming automatically
✅ **Easy Management** - Simple cleanup and archival scripts
✅ **Standard Format** - MJPEG AVI compatible with all players

**Default behavior:** Every run creates a new video file with timestamp

**To disable video recording:** Set `WRITE_VIDEO = False` in fr01.py

---

**Quick Commands:**

```bash
# List all videos
ls -lh output_videos/

# Play latest video
vlc $(ls -t output_videos/*.avi | head -1)

# Delete videos older than 7 days
find output_videos/ -name "*.avi" -mtime +7 -delete

# Check disk usage
du -sh output_videos/
```
