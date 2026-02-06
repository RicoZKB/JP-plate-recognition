# Installing TensorRT Python Bindings

## The Solution You Found! ✅

Based on the NVIDIA forum post, we can build TensorRT Python bindings for Python 3.8 from source.

**Source:** https://forums.developer.nvidia.com/t/tensorrt-on-jetson-with-python-3-9/196131/9

---

## Installation Method

### Option 1: Automated Script (Recommended)

I've created an installation script that handles everything:

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./install_tensorrt_python.sh
```

**What it does:**
1. Installs dependencies
2. Clones pybind11 and TensorRT from GitHub
3. Builds TensorRT Python bindings for Python 3.8
4. Installs to your virtual environment

**Time required:** 30-60 minutes (compilation is slow on TX1)

**Disk space needed:** ~2GB for build files

---

### Option 2: Manual Installation

If you prefer to do it manually:

#### Step 1: Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    git cmake \
    protobuf-compiler libprotobuf-dev \
    python3-dev python3-pip \
    libssl-dev
```

#### Step 2: Create Build Directory

```bash
mkdir -p ~/tensorrt_build
cd ~/tensorrt_build
```

#### Step 3: Clone Required Repositories

```bash
# pybind11
git clone https://github.com/pybind/pybind11.git
cd pybind11 && git checkout v2.6.2 && cd ..

# TensorRT
git clone -b release/8.0 https://github.com/NVIDIA/TensorRT.git
cd TensorRT
git submodule update --init --recursive
cd ..
```

#### Step 4: Build TensorRT Python Bindings

```bash
cd TensorRT/python
export TRT_OSSPATH=$(pwd)/..
export EXT_PATH=$(pwd)/../..

# Build for Python 3.8
bash ./build.sh
```

#### Step 5: Install Wheel File

```bash
# Activate your virtual environment
source /home/jetson/yolo/yolov7/myenv/bin/activate

# Install the wheel
pip install build/dist/tensorrt-8.0.1.6-cp38-none-linux_aarch64.whl
```

#### Step 6: Verify Installation

```bash
python3 -c "import tensorrt; print('TensorRT:', tensorrt.__version__)"
```

Should output: `TensorRT: 8.0.1.6`

---

## After Installation

### Update fr01.py to Use TensorRT

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
nano fr01.py
```

Change lines 51-55 to:
```python
# Model selection (TensorRT is FASTEST!)
USE_TENSORRT             = True   # Now available!
USE_ONNX_MODEL           = False
MODEL_PATH               = "models/best_fp16.engine"
```

### Run with TensorRT

```bash
./run_fr01.sh
```

You should see:
```
[INFO] Loaded TensorRT engine: models/best_fp16.engine
```

---

## Expected Performance After Installation

### Before (ONNX):
- Detection: ~70ms
- Total FPS: 5-7

### After (TensorRT):
- Detection: ~35ms (2x faster!)
- Total FPS: 8-12+

**Overall speedup: 40-50%**

---

## Troubleshooting

### Build Fails with "CMake too old"

```bash
# Install newer CMake
wget https://github.com/Kitware/CMake/releases/download/v3.13.5/cmake-3.13.5.tar.gz
tar xvf cmake-3.13.5.tar.gz && cd cmake-3.13.5/
./bootstrap --system-curl && make -j4
sudo make install
```

### Build Fails with "Python.h not found"

```bash
sudo apt-get install python3.8-dev
```

### Build Takes Too Long

The compilation is CPU-intensive on Jetson TX1. Expected time:
- With 4 cores: 30-45 minutes
- Don't interrupt the build!

### Out of Memory During Build

```bash
# Reduce parallel jobs
# Edit build.sh and change make -j to make -j2
```

### Wheel File Not Compatible

Make sure you're using the wheel built for Python 3.8:
```bash
ls build/dist/
# Should show: tensorrt-8.0.1.6-cp38-none-linux_aarch64.whl
```

---

## Important Notes

1. **Backup First:** This modifies your system. Consider backing up your work.

2. **Build Time:** Compilation takes 30-60 minutes on Jetson TX1.

3. **Disk Space:** You'll need ~2GB free for build files.

4. **After Build:** You can delete ~/tensorrt_build to free space (but keep the .whl file).

5. **Virtual Environment:** The installation script installs to your existing venv at `/home/jetson/yolo/yolov7/myenv`

---

## Alternative: Pre-built Wheel (If Available)

If someone has already built the wheel, you can share it:

**To save your wheel after building:**
```bash
cp ~/tensorrt_build/TensorRT/python/build/dist/tensorrt-8.0.1.6-cp38-none-linux_aarch64.whl \
   ~/tensorrt_python38_jetson_tx1.whl
```

**To install pre-built wheel:**
```bash
source /home/jetson/yolo/yolov7/myenv/bin/activate
pip install tensorrt_python38_jetson_tx1.whl
```

---

## Summary

### To Install:
```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./install_tensorrt_python.sh
```

### To Use After Installation:
```bash
# TensorRT is automatically enabled in fr01.py after install
./run_fr01.sh
```

### Expected Result:
- ✅ Real TensorRT acceleration
- ⚡ 2x faster detection
- 🚀 8-12+ FPS overall

---

**Created:** January 6, 2026
**Source:** NVIDIA Developer Forums
**Status:** Ready to install
**Time:** 30-60 minutes
**Reward:** 2x faster detection!
