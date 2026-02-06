# OCR Performance Fix - GPU Acceleration

**Date:** January 15, 2026
**Issue:** OCR causing FPS drop from 20 FPS → 0.6 FPS
**Solution:** Switch to GPU-accelerated PaddlePaddle

---

## Problem Analysis

### Performance Bottleneck Identified

| Component | Processing Time | FPS Impact |
|-----------|----------------|------------|
| **YOLO Detection** | ~48ms | ✅ 20 FPS |
| **PaddleOCR (CPU)** | ~1500ms | ❌ 0.6 FPS |
| **Total** | ~1548ms | ❌ 0.6 FPS |

**Root Cause:** Current `myenv` uses CPU-only PaddlePaddle

---

## Solution: Option A (Quick Fix)

### Switch to GPU-Accelerated PaddlePaddle

**Environment Comparison:**

| Feature | Current (myenv) | New (paddle_py37_env) |
|---------|----------------|----------------------|
| **Python** | 3.8.10 | 3.7.17 |
| **PaddlePaddle** | 2.6.2 (CPU) ❌ | 2.5.2 (GPU) ✅ |
| **GPU Support** | No | Yes |
| **Expected OCR Speed** | 1500ms | 100-300ms |
| **Expected Total FPS** | 0.6 | **10-15 FPS** |

### Changes Made

**File: `run_fr01.sh` (Line 83)**
```bash
# OLD
source ../myenv/bin/activate

# NEW
source ../paddle_py37_env/bin/activate
```

### Expected Performance Improvement

```
Before (CPU PaddlePaddle):
  YOLO: 48ms
  OCR:  1500ms
  Total: 1548ms → 0.6 FPS ❌

After (GPU PaddlePaddle):
  YOLO: 48ms
  OCR:  100-300ms
  Total: 148-348ms → 10-15 FPS ✅
```

---

## Testing Option A

### How to Test

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./run_fr01.sh
```

### What to Check

- ✅ System starts without errors
- ✅ License plates detected
- ✅ OCR text extracted properly
- ✅ FPS improves to 10-15 FPS
- ✅ No Python 3.7/3.8 compatibility issues

### If Option A is Not Fast Enough

Proceed to **Option B: TensorRT OCR Engines**

---

## Solution: Option B (Ultimate Performance)

### Convert PaddleOCR to TensorRT Engines

If Option A doesn't reach 15+ FPS, rebuild PaddleOCR models as TensorRT engines.

### Available ONNX Models

Already converted and ready in `models/paddleocr_onnx/`:
- `det.onnx` (2.4 MB) - Text detection
- `rec_japan.onnx` (9.3 MB) - Japanese recognition
- `cls.onnx` (559 KB) - Angle classifier

### Build TensorRT Engines

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
./rebuild_paddle_tensorrt.sh
```

**Build Time:** ~10-15 minutes

### Expected Output

```
models/paddleocr_onnx/det_fp16.engine (~2 MB)
models/paddleocr_onnx/rec_japan_fp16_gpu.engine (~9 MB)
models/paddleocr_onnx/cls_fp16.engine (~500 KB)
```

### Expected Performance (TensorRT)

```
YOLO: 48ms
OCR Detection: 5-10ms
OCR Recognition: 10-30ms
OCR Classifier: 2-5ms
Total: 65-93ms → 15-20 FPS ✅✅
```

### After Building TensorRT Engines

Need to create custom OCR inference class to use TensorRT engines instead of PaddleOCR library.

---

## Performance Comparison

| Method | OCR Time | Total FPS | Complexity | Status |
|--------|----------|-----------|------------|--------|
| **Current (CPU)** | 1500ms | 0.6 | Simple | ❌ Too slow |
| **Option A (GPU)** | 100-300ms | 10-15 | Easy | ✅ Testing |
| **Option B (TensorRT)** | 15-45ms | 15-20 | Medium | ⏳ Backup plan |

---

## Decision Tree

```
Start
  ↓
Try Option A (GPU PaddlePaddle)
  ↓
FPS ≥ 10?
  ├─ Yes → Done! ✅
  └─ No → Try Option B (TensorRT OCR)
           ↓
         FPS ≥ 15?
           ├─ Yes → Done! ✅
           └─ No → Consider reducing OCR frequency
```

---

## Current Status

✅ **Step 1:** Updated `run_fr01.sh` to use `paddle_py37_env`
✅ **Step 2:** Installed dependencies in `paddle_py37_env`
   - paddleocr 2.7.0.2
   - paddlepaddle-gpu 2.5.2
   - ultralytics 8.0.145
✅ **Step 3:** Ready to test Option A

**Next:** Run `./run_fr01.sh` and measure FPS improvement

---

## Rollback (if needed)

If Option A causes issues, revert to CPU version:

```bash
# Edit run_fr01.sh line 83
source ../myenv/bin/activate  # Back to original
```

---

## Notes

### Why GPU PaddlePaddle is Faster

- **CPU Inference:** Sequential processing, limited cores
- **GPU Inference:** Parallel processing, 256 CUDA cores on TX1
- **Expected Speedup:** 5-15x faster

### Python 3.7 vs 3.8

- Minor version difference, unlikely to cause issues
- All required packages compatible with both versions
- TensorRT engines work with both Python versions

### Next Steps After Testing

1. **If FPS ≥ 10:** Keep Option A ✅
2. **If FPS < 10:** Proceed to Option B (TensorRT rebuild)
3. **If errors occur:** Check compatibility, may need to adjust code

---

## Quick Reference

```bash
# Test with GPU PaddlePaddle (Option A)
./run_fr01.sh

# If not fast enough, build TensorRT OCR (Option B)
./rebuild_paddle_tensorrt.sh

# Check current FPS while running
# Look for "Speed: X.Xms preprocess, X.Xms inference" in output
```

**Goal:** Achieve 10-15+ FPS for smooth real-time license plate detection! 🚀
