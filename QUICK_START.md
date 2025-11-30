# Quick Start Guide - Simple ALPR with CSV Logging

**Last Updated:** November 25, 2025

---

## ✅ Test Results Confirmed

CSV logging has been tested and works perfectly!

**Detected plate:** 世田谷310 70-50 ふ (Japanese license plate)

---

## 🚀 Quick Commands

### 1. Camera Mode with CSV Logging
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
source /home/jetson/yolo/yolov7/myenv/bin/activate

python run_simple_alpr.py \
    --camera \
    --model models/best.onnx \
    --enable-csv \
    --csv-no-duplicates \
    --verbose
```

**Output:** `logs/plate_log_YYYYMMDD.csv`

---

### 2. Video File with CSV Logging
```bash
python run_simple_alpr.py \
    --video input_videos/Trim03.mp4 \
    --model models/best.onnx \
    --enable-csv \
    --csv-prefix video_analysis
```

**Output:** `logs/video_analysis_YYYYMMDD.csv`

---

### 3. Production Mode (24/7 Monitoring)
```bash
python run_simple_alpr.py \
    --camera \
    --model models/best.onnx \
    --enable-csv \
    --csv-no-duplicates \
    --no-display
```

---

## 📊 CSV Output Format

**Example:**
```csv
2025-11-25T11:53:34,2025-11-25,11:53:34,世田谷310 70-50 ふ,0.815,1388,598,1527,684,,image
```

---

## 📖 View Logs

```bash
# Real-time monitoring
tail -f logs/plate_log_$(date +%Y%m%d).csv

# View latest entries
tail -20 logs/plate_log_$(date +%Y%m%d).csv
```

---

## 📚 Full Documentation

- `SIMPLE_ALPR_GUIDE.md` - Complete system guide
- `CSV_LOGGING_GUIDE.md` - CSV logging details
- `OPTIMIZATION_SUMMARY_20251125.md` - Performance notes
