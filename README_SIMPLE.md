# 🚗 License Plate Detection - Quick Start Guide

## 📍 You Are Here
```
/home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
```

---

## ⚡ Super Quick Start (3 Commands)

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./easy_run.sh
# Press Ctrl+C to stop
```

**That's it!** 🎉

---

## 🎯 What Each Script Does

| Script | Description | Use When |
|--------|-------------|----------|
| `./easy_run.sh` | ⭐ Easiest way to run | First time testing |
| `./test_run.sh` | Detailed with step explanations | Learning how it works |
| `./test_tensorrt.sh` | Test TensorRT speed | Checking performance |
| `./run_simple.sh` | Simple ALPR only | No gate tracking needed |
| `./run_optimized.sh` | Optimized full system | Production use |

---

## 📖 Complete Tutorial

### Method 1: Copy & Paste (Easiest)
```bash
./easy_run.sh
```

### Method 2: Step by Step
```bash
# Step 1: Navigate
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording

# Step 2: Run
./easy_run.sh

# Step 3: Stop when done
# Press: Ctrl + C
```

---

## 🎬 What You'll See

### Terminal Output:
```
Starting License Plate Detection...
Loading YOLO model...
FPS: 4.3 | Detection Time: 1045ms
```

### OpenCV Window:
- Video playback
- Green boxes around plates
- Text: "世田谷310 70-50" (OCR result)
- FPS counter

---

## 📊 Results

Check the CSV log:
```bash
cat logs/parking_log_*.csv
```

Example output:
```csv
timestamp,object_id,vehicle_type,direction,city,number
2025-11-28 08:10:23,01,car,in,世田谷,70-50
```

---

## 🚀 Test TensorRT (3x Faster!)

```bash
./test_tensorrt.sh
```

If it works, you can get **8-12 FPS instead of 4.3 FPS**!

---

## ⚙️ Change Video Source

Edit `inout_event.py`:
```bash
nano inout_event.py
```

Find and change (around line 32):
```python
USE_CAMERA = False   # True = CSI camera, False = video file
USE_FILE = True      # True = video file
INPUT_VIDEO_PATH = "input_videos/Trim03.mp4"  # Change this
```

Save: `Ctrl+X` → `Y` → `Enter`

---

## 🐛 Problems?

**Permission denied:**
```bash
chmod +x easy_run.sh
```

**Can't find file:**
```bash
pwd  # Check you're in the right directory
```

**Module not found:**
```bash
source ../myenv/bin/activate
```

---

## 📚 Learn More

Read the complete guide:
```bash
cat HOW_TO_RUN.txt
```

---

## ✅ Recommended First Run

```bash
# 1. Test TensorRT
./test_tensorrt.sh

# 2. Run the system
./easy_run.sh

# 3. Check results
cat logs/parking_log_*.csv
```

---

**Happy Testing! 🎉**
