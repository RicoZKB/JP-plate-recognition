# CSV Logging Guide for Simple ALPR System

**Date:** November 25, 2025

---

## 📊 Overview

The CSV logging system automatically records all detected license plates with timestamps, bounding box coordinates, and metadata. Perfect for:
- Traffic monitoring and analytics
- Parking lot management
- Security logging
- Data collection and analysis

---

## 🚀 Quick Start

### Enable CSV Logging (Basic)
```bash
python run_simple_alpr.py --camera --enable-csv
```

This creates a log file at: `logs/plate_log_YYYYMMDD.csv`

### Enable CSV with Duplicate Filter
```bash
python run_simple_alpr.py --camera --enable-csv --csv-no-duplicates
```

Filters out duplicate plates within 5 seconds (same plate won't be logged twice)

### Custom Log Directory
```bash
python run_simple_alpr.py --camera --enable-csv --csv-dir /path/to/logs
```

### Custom Log Prefix
```bash
python run_simple_alpr.py --camera --enable-csv --csv-prefix traffic_log
```

Creates: `logs/traffic_log_YYYYMMDD.csv`

---

## 📝 CSV Format

### Headers:
```csv
timestamp,date,time,plate_text,confidence,bbox_x1,bbox_y1,bbox_x2,bbox_y2,frame_number,source
```

### Example Data:
```csv
timestamp,date,time,plate_text,confidence,bbox_x1,bbox_y1,bbox_x2,bbox_y2,frame_number,source
2025-11-25T14:30:15.123456,2025-11-25,14:30:15,世田谷310 70-50,0.892,120,340,280,420,42,camera
2025-11-25T14:30:17.456789,2025-11-25,14:30:17,品川500 あ 12-34,0.945,150,360,310,440,89,camera
2025-11-25T14:30:22.789012,2025-11-25,14:30:22,横浜330 56-78,0.876,135,355,295,435,156,camera
```

### Field Descriptions:

| Field | Description | Example |
|-------|-------------|---------|
| **timestamp** | ISO 8601 timestamp | 2025-11-25T14:30:15.123456 |
| **date** | Date only (YYYY-MM-DD) | 2025-11-25 |
| **time** | Time only (HH:MM:SS) | 14:30:15 |
| **plate_text** | Full OCR result | 世田谷310 70-50 |
| **confidence** | YOLO detection confidence (0-1) | 0.892 |
| **bbox_x1** | Top-left X coordinate | 120 |
| **bbox_y1** | Top-left Y coordinate | 340 |
| **bbox_x2** | Bottom-right X coordinate | 280 |
| **bbox_y2** | Bottom-right Y coordinate | 420 |
| **frame_number** | Frame number in video/stream | 42 |
| **source** | Input source type | camera/video/image |

---

## ⚙️ Command-Line Options

### CSV Logging Options:

```bash
--enable-csv                # Enable CSV logging
--csv-dir DIR               # Directory for log files (default: logs)
--csv-prefix PREFIX         # Log filename prefix (default: plate_log)
--csv-no-duplicates         # Filter duplicate plates (5 second window)
```

---

## 🎯 Usage Examples

### Example 1: Basic Camera Monitoring
```bash
python run_simple_alpr.py \
    --camera \
    --enable-csv \
    --model models/best.onnx
```

**Output:** `logs/plate_log_20251125.csv`

---

### Example 2: Video Analysis with Custom Directory
```bash
python run_simple_alpr.py \
    --video input_videos/traffic.mp4 \
    --enable-csv \
    --csv-dir /mnt/storage/traffic_logs \
    --csv-prefix highway_cam1
```

**Output:** `/mnt/storage/traffic_logs/highway_cam1_20251125.csv`

---

### Example 3: Parking Lot (No Duplicates)
```bash
python run_simple_alpr.py \
    --camera \
    --enable-csv \
    --csv-no-duplicates \
    --csv-prefix parking_entrance \
    --cooldown 10.0
```

**Features:**
- Duplicate filter (won't log same plate twice within 5 seconds)
- OCR cooldown of 10 seconds (for slow-moving traffic)

---

### Example 4: Headless Mode (Production)
```bash
python run_simple_alpr.py \
    --camera \
    --enable-csv \
    --csv-no-duplicates \
    --no-display \
    --csv-dir /var/log/alpr \
    --csv-prefix camera_main
```

Perfect for 24/7 monitoring without display

---

## 📊 Analyzing CSV Data

### Using Python (Pandas)
```python
import pandas as pd

# Load CSV
df = pd.read_csv('logs/plate_log_20251125.csv')

# Count unique plates
unique_plates = df['plate_text'].nunique()
print(f"Unique plates: {unique_plates}")

# Plates per hour
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
hourly_counts = df.groupby('hour').size()
print(hourly_counts)

# Most common plates
top_plates = df['plate_text'].value_counts().head(10)
print(top_plates)

# Average confidence
avg_conf = df['confidence'].mean()
print(f"Average confidence: {avg_conf:.3f}")
```

---

### Using Excel
1. Open Excel
2. Data → From Text/CSV
3. Select your CSV file
4. Use PivotTables for analysis

---

### Using Command-Line Tools

**Count total entries:**
```bash
wc -l logs/plate_log_20251125.csv
```

**View latest 10 entries:**
```bash
tail -10 logs/plate_log_20251125.csv
```

**Search for specific plate:**
```bash
grep "世田谷310" logs/plate_log_20251125.csv
```

**Count unique plates:**
```bash
cut -d',' -f4 logs/plate_log_20251125.csv | sort | uniq | wc -l
```

---

## 🔧 Advanced Features

### Duplicate Filtering

The duplicate filter prevents logging the same plate multiple times within a short time window.

**How it works:**
1. When a plate is logged, its text is stored with a timestamp
2. When the same plate appears again, the system checks the timestamp
3. If less than 5 seconds have passed, it's skipped
4. If more than 5 seconds have passed, it's logged again

**Benefits:**
- Reduces log file size
- Prevents spam from stationary vehicles
- Cleaner data for analysis

**Configure in code** (edit `run_simple_alpr.py`):
```python
csv_logger = CSVLogger(
    log_dir=args.csv_dir,
    log_prefix=args.csv_prefix,
    enable_duplicate_filter=args.csv_no_duplicates,
    duplicate_window=5.0  # Change to 10.0, 30.0, etc.
)
```

---

### Log Rotation

Logs are automatically rotated daily. Each day gets a new file:
```
logs/
├── plate_log_20251125.csv
├── plate_log_20251126.csv
├── plate_log_20251127.csv
└── ...
```

**Automatic benefits:**
- Smaller file sizes
- Easy to archive old logs
- Better performance

---

### Multiple Log Files

Run multiple instances with different prefixes:

**Camera 1:**
```bash
python run_simple_alpr.py --camera --enable-csv --csv-prefix cam1
```

**Camera 2:**
```bash
python run_simple_alpr.py --camera --enable-csv --csv-prefix cam2
```

**Output:**
```
logs/
├── cam1_20251125.csv
└── cam2_20251125.csv
```

---

## 📈 Real-Time Monitoring

### Watch log file in real-time:
```bash
tail -f logs/plate_log_20251125.csv
```

### Monitor with automatic updates:
```bash
watch -n 1 'tail -5 logs/plate_log_20251125.csv'
```

---

## 🔍 CSV Logger Class API

For custom integration, use the `CSVLogger` class directly:

```python
from utils.csv_logger import CSVLogger

# Initialize logger
logger = CSVLogger(
    log_dir='custom_logs',
    log_prefix='my_log',
    enable_duplicate_filter=True,
    duplicate_window=5.0
)

# Log a detection
detection = {
    'bbox': (100, 200, 300, 400),
    'text': '世田谷310 70-50',
    'confidence': 0.92,
    'timestamp': time.time()
}

logger.log_detection(detection, frame_number=42, source='camera')

# Log multiple detections
logger.log_multiple(detections, frame_number=43, source='camera')

# Get statistics
stats = logger.get_stats()
print(stats)

# Close logger
logger.close()
```

---

## 🐛 Troubleshooting

### Issue: Permission denied when creating log directory
**Solution:**
```bash
sudo chmod 777 logs/
# or
python run_simple_alpr.py --enable-csv --csv-dir /home/jetson/my_logs
```

---

### Issue: CSV file too large
**Solutions:**

1. **Enable duplicate filter:**
   ```bash
   --csv-no-duplicates
   ```

2. **Compress old logs:**
   ```bash
   gzip logs/plate_log_20251124.csv
   ```

3. **Archive old logs:**
   ```bash
   mkdir archive
   mv logs/plate_log_202511*.csv archive/
   ```

---

### Issue: Empty plate_text fields
**Causes:**
- OCR failed to read plate
- Plate was detected but not recognized
- Text was filtered out (empty/whitespace)

**Solution:**
Check OCR settings, increase padding, or adjust confidence threshold

---

## 📊 CSV Statistics

At the end of each session, the system prints CSV statistics:

```
[CSV] CSV Logging Statistics:
  Log file: logs/plate_log_20251125.csv
  Total logged: 156
  File size: 12847 bytes
```

---

## 🔐 Security & Privacy

### Best Practices:

1. **Secure log directory:**
   ```bash
   chmod 700 logs/
   ```

2. **Encrypt logs:**
   ```bash
   gpg -c logs/plate_log_20251125.csv
   ```

3. **Regular cleanup:**
   ```bash
   # Delete logs older than 30 days
   find logs/ -name "*.csv" -mtime +30 -delete
   ```

4. **Anonymize data:**
   - Consider hashing plate numbers
   - Remove timestamps if not needed
   - Store only aggregated statistics

---

## 📝 Sample Analysis Scripts

### Script 1: Daily Summary
```python
#!/usr/bin/env python3
import pandas as pd
from datetime import datetime

# Load today's log
today = datetime.now().strftime('%Y%m%d')
df = pd.read_csv(f'logs/plate_log_{today}.csv')

print(f"=== Daily Summary for {today} ===")
print(f"Total detections: {len(df)}")
print(f"Unique plates: {df['plate_text'].nunique()}")
print(f"Average confidence: {df['confidence'].mean():.3f}")
print(f"\nTop 10 plates:")
print(df['plate_text'].value_counts().head(10))
```

---

### Script 2: Hourly Traffic Chart
```python
#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('logs/plate_log_20251125.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour

hourly = df.groupby('hour').size()

plt.figure(figsize=(12, 6))
hourly.plot(kind='bar')
plt.title('Hourly Traffic')
plt.xlabel('Hour of Day')
plt.ylabel('Number of Vehicles')
plt.savefig('hourly_traffic.png')
print("Saved: hourly_traffic.png")
```

---

## ✅ Summary

### CSV Logging Features:
- ✅ Automatic daily rotation
- ✅ Duplicate filtering (optional)
- ✅ Full metadata (bbox, confidence, timestamp)
- ✅ Real-time writing (safe for crashes)
- ✅ UTF-8 support (Japanese, Chinese, etc.)
- ✅ Minimal performance impact
- ✅ Easy to analyze with Excel/Python/SQL

### File Structure:
```
Licence-Plate-Detection-Recognition-Recording/
├── logs/                           # Default log directory
│   ├── plate_log_20251125.csv     # Today's log
│   ├── plate_log_20251124.csv     # Yesterday's log
│   └── ...
├── utils/
│   └── csv_logger.py              # CSV logger class
└── run_simple_alpr.py             # Main script with CSV support
```

---

## 🎯 Next Steps

1. **Test CSV logging:**
   ```bash
   python run_simple_alpr.py --camera --enable-csv --verbose
   ```

2. **Check log file:**
   ```bash
   cat logs/plate_log_$(date +%Y%m%d).csv
   ```

3. **Analyze data:**
   ```bash
   python analyze_logs.py  # Create your own analysis script!
   ```

4. **Set up production monitoring:**
   ```bash
   python run_simple_alpr.py --camera --enable-csv --csv-no-duplicates --no-display
   ```

---

**Questions?** Check the main guide: `SIMPLE_ALPR_GUIDE.md`

**Happy logging!** 📊
