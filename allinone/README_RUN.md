# How to Run - License Plate Detection

## 🚀 Quick Start (ONE Command)

```bash
./run.sh
```

That's it! This single script does **everything**:
- ✅ Kills old camera processes
- ✅ Restarts Argus daemon
- ✅ Activates virtual environment
- ✅ Sets max performance mode
- ✅ Runs TensorRT-optimized detection

## 📁 What You Get

**Logs**: `logs/plates_fast_20260114.csv`
**Video**: `output_videos/fast_output.avi`

## ⚙️ Configuration

Edit `fr01.py` to change settings:

```python
# Camera
CSI_RESOLUTION = '720p'      # '640p', '720p', '1080p'
CSI_FPS        = 30          # Frame rate

# Detection
TARGET_WIDTH   = 640         # Lower = faster
```

## 🎮 Controls

- **ESC** - Stop and save
- **CTRL+C** - Emergency stop

## 📊 Output Format

```csv
timestamp,object_id,vehicle_type,direction,city,class_number,kana,suffix
2026-01-14 15:30:45,01,car,in,品川,589,ろ,70-50
```

## 🔧 Troubleshooting

**Camera not working?**
```bash
# Check camera
ls /dev/video*

# Check Argus daemon
ps aux | grep nvargus-daemon

# Re-run the script (it auto-fixes issues)
./run.sh
```

**Slow performance?**
```python
# In fr01.py
CSI_RESOLUTION = '640p'  # Lower resolution
DETECT_EVERY_N = 2       # Skip frames
```

That's all you need to know! Just run `./run.sh` 🎉
