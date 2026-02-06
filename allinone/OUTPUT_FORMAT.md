# License Plate Detection - Output Format

**Date:** January 15, 2026
**Status:** ✅ Fully Implemented

---

## CSV Output Format

### File Location
- **Directory:** `logs/`
- **Filename:** `plates_fast_YYYYMMDD.csv`
- **Example:** `logs/plates_fast_20260115.csv`

### CSV Structure

Each detection is logged as a separate row with the following columns:

| Column | Name | Description | Example |
|--------|------|-------------|---------|
| 1 | timestamp | Date and time of detection | `2026-01-15 10:23:45` |
| 2 | object_id | Sequential ID (2 digits) | `01`, `02`, `03` |
| 3 | vehicle_type | Type of vehicle | `car`, `truck` |
| 4 | direction | Direction of travel | `in`, `out` |
| 5 | city | City name (Japanese) | `品川`, `横浜`, `世田谷` |
| 6 | class_number | Vehicle class number (3 digits) | `330`, `500`, `589` |
| 7 | kana | Kana character | `あ`, `さ`, `ろ` |
| 8 | suffix | Four-digit number (XX-XX format) | `12-34`, `56-78` |

### Example CSV Content

```csv
timestamp,object_id,vehicle_type,direction,city,class_number,kana,suffix
2026-01-15 10:23:45,01,car,in,品川,330,あ,12-34
2026-01-15 10:24:12,02,car,in,横浜,500,さ,56-78
2026-01-15 10:25:33,03,car,in,世田谷,310,ろ,90-12
2026-01-15 10:26:01,04,car,in,多摩,589,,20-46
```

### Field Details

#### Timestamp
- **Format:** `YYYY-MM-DD HH:MM:SS`
- **Timezone:** System local time
- **Updates:** Real-time with immediate flush to disk

#### Object ID
- **Format:** Zero-padded 2-digit number (`01`, `02`, ...)
- **Range:** 01-99 (resets daily or on restart)
- **Sequential:** Increments for each new plate detected

#### Vehicle Type
- **Current:** Always `car`
- **Future:** May support `truck`, `motorcycle`, `bus`

#### Direction
- **Current:** Always `in`
- **Configurable:** Can be changed to `out` or made dynamic

#### City (Region)
- **Language:** Japanese (Kanji/Hiragana)
- **Examples:** `品川`, `横浜`, `世田谷`, `多摩`, `練馬`
- **Empty if:** OCR fails to detect city name
- **Minimum length:** 2 characters (filters partial reads)

#### Class Number
- **Format:** 3-digit number
- **Examples:** `330`, `500`, `589`, `310`
- **Range:** Typically 100-999
- **Empty if:** OCR fails to detect class number

#### Kana
- **Format:** Single hiragana character
- **Examples:** `あ`, `い`, `う`, `さ`, `ろ`, `ま`
- **Valid characters:** 41 legal hiragana for Japanese plates
- **Empty if:** OCR fails to detect kana
- **Retry:** System will retry OCR for missing kana

#### Suffix
- **Format:** XX-XX (2 digits, hyphen, 2 digits)
- **Examples:** `12-34`, `56-78`, `90-12`, `20-46`
- **Required:** Must be present for logging
- **Normalized:** System handles OCR variations

### Empty Fields

Fields may be empty if OCR cannot detect them:
- Empty city: `,,,` (two consecutive commas)
- Empty kana: `,,20-46` (kana column empty)
- System will retry OCR for missing kana in background

---

## Terminal Output Format

### Startup Message

```
================================================================================
LICENSE PLATE DETECTION SYSTEM - STARTUP
================================================================================
  CSV Log File:       logs/plates_fast_20260115.csv
  CSV Format:         timestamp | object_id | vehicle_type | direction |
                      city | class_number | kana | suffix
  Mode:               Fast Real-time (front-facing)
  Dedup Window:       30 seconds
  Quality Filter:     ON (min city length: 2)
  Collection Window:  6 seconds (best detection)
================================================================================
```

### Detection Output

For each detected license plate, the system prints:

```
================================================================================
🚗 LICENSE PLATE DETECTED
================================================================================
  Timestamp:      2026-01-15 10:23:45
  Object ID:      01
  Vehicle Type:   car
  Direction:      in
  City:           品川
  Class Number:   330
  Kana:           あ
  Suffix:         12-34
  Quality Score:  8/8
================================================================================
```

### Field Status Indicators

| Display | Meaning |
|---------|---------|
| `品川` | Field detected successfully |
| `(not detected)` | Field not detected by OCR |

### Quality Score

- **Maximum:** 8/8 (all fields detected)
- **Scoring:**
  - City: +2 points
  - Class Number: +2 points
  - Kana: +3 points (most important)
  - Suffix: +1 point (baseline)

### Kana Retry Correction

When the system finds missing kana through retry OCR:

```
--------------------------------------------------------------------------------
✓ KANA CORRECTION FOUND
--------------------------------------------------------------------------------
  Timestamp:      2026-01-15 10:28:30
  Original ID:    04
  Found Kana:     ろ
  Status:         Appended to CSV
--------------------------------------------------------------------------------
```

The correction is appended to CSV as:
```csv
2026-01-15 10:28:30,04_KANA_FIX,correction,,,ろ,Retry OCR found kana for ID:04
```

---

## Real-Time Display (Video Window)

### FPS Overlay
```
FPS: 17.2
Mode: Fast Real-time | Source: Camera
Super-res: OFF | Tracked: 3 | Dedup: 30s
```

### Detection Status
- **Green boxes:** Detected plates
- **Text overlay:**
  - `70-50 (collecting...)` - First detection, collecting data
  - `70-50 (updating...)` - Better detection found
  - `70-50 (logged)` - Already logged (deduplication)
  - `(no-suffix)` - Rejected (missing suffix)
  - `(low-quality)` - Rejected (quality filter)

---

## Output Files Management

### Video File Naming

Each time you run the system, a new video file is created with a unique timestamp:

**Filename Format:** `fast_output_YYYYMMDD_HHMMSS.avi`

**Examples:**
```
output_videos/fast_output_20260115_102345.avi  (Run at 10:23:45 AM)
output_videos/fast_output_20260115_143021.avi  (Run at 02:30:21 PM)
output_videos/fast_output_20260115_185512.avi  (Run at 06:55:12 PM)
```

**Benefits:**
- ✅ No overwriting - all recordings preserved
- ✅ Easy to identify when each recording was made
- ✅ Can run multiple times per day without losing data
- ✅ Chronologically sorted by filename

**Disk Space Management:**
```bash
# List all video files with sizes
ls -lh output_videos/

# Delete videos older than 7 days
find output_videos/ -name "*.avi" -mtime +7 -delete

# Keep only the 10 most recent videos
ls -t output_videos/*.avi | tail -n +11 | xargs rm -f

# Archive old videos
tar -czf videos_archive_$(date +%Y%m).tar.gz output_videos/*.avi
```

## Log Files

### Daily CSV Files
- **Pattern:** `logs/plates_fast_YYYYMMDD.csv`
- **Rotation:** Automatic daily rotation
- **Encoding:** UTF-8 (supports Japanese characters)
- **Flush:** Immediate (data saved instantly)

### Retry Queue
- **Directory:** `retry_queue/`
- **Files:** `plate_XX_YYYYMMDD_HHMMSS.jpg` + `.txt` metadata
- **Purpose:** Plates missing kana for retry OCR

### Retry Success
- **Directory:** `retry_success/`
- **Files:** Successfully retried plates moved here
- **Purpose:** Archive of successful kana corrections

### Video Output
- **Directory:** `output_videos/`
- **Filename Pattern:** `fast_output_YYYYMMDD_HHMMSS.avi`
- **Example:** `fast_output_20260115_102345.avi`
- **Format:** MJPEG
- **FPS:** Same as input source
- **Enable:** Set `WRITE_VIDEO = True` in fr01.py
- **Behavior:** Each run creates a new video file (no overwriting)

---

## Data Export

### Excel/LibreOffice
1. Open Excel/LibreOffice Calc
2. Import CSV: `logs/plates_fast_YYYYMMDD.csv`
3. Encoding: UTF-8
4. Delimiter: Comma

### Python/Pandas
```python
import pandas as pd

# Read CSV
df = pd.read_csv('logs/plates_fast_20260115.csv')

# Filter by time range
df['timestamp'] = pd.to_datetime(df['timestamp'])
morning = df[df['timestamp'].dt.hour < 12]

# Count by city
city_counts = df['city'].value_counts()

# Export to Excel
df.to_excel('plates_export.xlsx', index=False)
```

### Database Import
```sql
CREATE TABLE plates (
    timestamp DATETIME,
    object_id VARCHAR(10),
    vehicle_type VARCHAR(20),
    direction VARCHAR(10),
    city VARCHAR(50),
    class_number VARCHAR(10),
    kana VARCHAR(10),
    suffix VARCHAR(10)
);

LOAD DATA INFILE 'plates_fast_20260115.csv'
INTO TABLE plates
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

---

## Testing

### Run Test Script
```bash
python3 test_csv_output.py
```

This will:
1. Create sample CSV file
2. Display formatted terminal output
3. Show CSV structure
4. Verify all fields are properly separated

### Verify Real Output
```bash
# Watch CSV file in real-time
tail -f logs/plates_fast_$(date +%Y%m%d).csv

# Count detections
wc -l logs/plates_fast_*.csv

# View recent detections
tail -n 5 logs/plates_fast_$(date +%Y%m%d).csv
```

---

## Troubleshooting

### CSV Not Creating
- **Check:** Permissions on `logs/` directory
- **Fix:** `mkdir -p logs && chmod 755 logs`

### Japanese Characters Garbled
- **Issue:** Wrong encoding
- **Fix:** Open CSV with UTF-8 encoding
- **Excel:** Import data with UTF-8 encoding option

### Missing Fields
- **Normal:** OCR may not detect all fields
- **Solution:** System retries kana detection automatically
- **Check:** `retry_queue/` folder for pending retries

### Duplicate Detections
- **Prevented:** 30-second deduplication window
- **Adjustable:** Change `DEDUP_WINDOW_SECONDS` in fr01.py

---

## Configuration

### Enable/Disable CSV Logging
```python
# fr01.py - Always enabled (required for system)
# CSV automatically created and flushed in real-time
```

### Change Output Directory
```python
# fr01.py - line 256
path = os.path.join("logs", f"plates_fast_{date_str}.csv")
# Change "logs" to your preferred directory
```

### Adjust Quality Filter
```python
# fr01.py - lines 41-43
REQUIRE_CITY_OR_CLASS = True   # Must have city OR class_number
MIN_CITY_LENGTH = 2            # Minimum city name length
```

---

## Summary

✅ **CSV Format:** 8 columns, properly separated, UTF-8 encoded
✅ **Timestamp:** Full date and time in each row
✅ **Fields Separated:** Each plate region in its own column
✅ **Terminal Output:** Detailed formatted display for each detection
✅ **Real-time Logging:** Immediate flush to disk
✅ **Retry System:** Automatic kana correction with separate log entries
✅ **Daily Rotation:** Automatic daily CSV files

**Ready to use!** Run `./run_fr01.sh` to start detecting and logging plates.
