# Option A Status - GPU PaddlePaddle Performance Fix

**Date:** January 15, 2026
**Status:** ⚠️ **BLOCKED - Dependency Issues**

---

## Summary

Attempted to switch from myenv (CPU PaddlePaddle) to paddle_py37_env (GPU PaddlePaddle) to improve OCR performance from 0.6 FPS → 10-15 FPS target.

## What Was Done

✅ **Verified GPU PaddlePaddle Available:**
- paddle_py37_env has paddlepaddle-gpu 2.5.2 with CUDA support
- Python 3.7.17

✅ **Installed Dependencies:**
- paddleocr 2.7.0.2
- ultralytics 8.0.145
- Fixed lmdb build issues (required liblmdb-dev system package)

✅ **Updated run_fr01.sh:**
- Changed from `source ../myenv/bin/activate`
- To `source ../paddle_py37_env/bin/activate`

## Issues Encountered

### Issue 1: lmdb Permission Errors ✅ FIXED
**Problem:** lmdb package failed to compile with permission errors

**Solution:**
```bash
sudo apt-get install -y liblmdb-dev
pip uninstall lmdb -y
pip install lmdb --no-cache-dir --no-binary :all:
```

### Issue 2: TensorRT Not Available ❌ BLOCKING
**Problem:** paddle_py37_env cannot import TensorRT, which is needed for best_optimized.engine

**Error:**
```
ModuleNotFoundError: No module named 'tensorrt'
```

**Root Cause:** TensorRT is installed in system Python 3.8, but paddle_py37_env uses Python 3.7. Cross-version import incompatible.

**Attempted Solutions:**
1. Added .pth file to include system packages → Failed (version mismatch)
2. Symlinked tensorrt module → Failed (Python version incompatibility)
3. Need to either:
   - Rebuild TensorRT Python bindings for Python 3.7, or
   - Use ONNX model instead of TensorRT engine (slower)

### Issue 3: No Camera Available
**Problem:** Cannot test with real camera (I2C "no acknowledge" errors in dmesg)

**Impact:** Cannot measure actual FPS improvement

---

## Options Moving Forward

### Option A1: Fix TensorRT in paddle_py37_env (Complex)
**Steps:**
1. Install TensorRT Python 3.7 bindings from NVIDIA
2. Or rebuild pycuda for Python 3.7
3. Test with camera when available

**Effort:** High
**Risk:** Medium (might not work due to version incompatibilities)

### Option A2: Use ONNX Instead of TensorRT (Simpler)
**Steps:**
1. Change model_path from `best_optimized.engine` to `best.onnx`
2. Accept slightly slower YOLO inference (~70-80ms instead of ~48ms)
3. Still get GPU PaddleOCR speedup

**Effort:** Low (just change one line)
**Risk:** Low
**Expected FPS:** 8-12 FPS (still much better than 0.6!)

### Option B: TensorRT OCR Engines (Best Performance)
**Steps:**
1. Keep using myenv (works with TensorRT for YOLO)
2. Convert PaddleOCR models to TensorRT engines
3. Replace PaddleOCR library with custom TensorRT inference

**Effort:** Medium
**Risk:** Low (already have ONNX models ready)
**Expected FPS:** 15-20 FPS

### Option C: Revert to myenv (Current Working State)
**Steps:**
1. Change run_fr01.sh back to myenv
2. Accept 0.6 FPS for now
3. Implement Option B when ready

**Effort:** Minimal
**Risk:** None
**Expected FPS:** 0.6 FPS (current baseline)

---

## Recommendation

**Use Option A2 (ONNX + GPU PaddleOCR) as quickest win:**

1. Revert run_fr01.sh to myenv (TensorRT works there)
2. Copy GPU PaddleOCR from paddle_py37_env to myenv:
   ```bash
   source ../myenv/bin/activate
   pip install paddlepaddle-gpu==2.5.2
   ```
3. Test if myenv can use both TensorRT engine AND GPU PaddleOCR

**If that fails, proceed to Option B (TensorRT OCR)**

---

## Files Modified

1. `run_fr01.sh` - Line 83 changed to paddle_py37_env (needs revert if not using)
2. `test_ocr_performance.py` - Created for benchmarking
3. `paddle_py37_env/` - lmdb rebuilt, paddleocr installed

---

## Next Steps

**User Decision Needed:**

1. **Try Option A2:** Install GPU PaddlePaddle in myenv (keeps TensorRT working)
2. **Skip to Option B:** Convert PaddleOCR to TensorRT engines
3. **Wait:** Keep current setup until camera is available for testing

---

## Performance Targets

| Method | YOLO Time | OCR Time | Total FPS | Status |
|--------|-----------|----------|-----------|---------|
| Current (CPU) | 48ms | 1500ms | 0.6 | ❌ Too slow |
| Option A (GPU) | 48ms | 100-300ms | 10-15 | ⏳ Blocked |
| Option A2 (ONNX+GPU) | 70ms | 100-300ms | 8-12 | ✅ Feasible |
| Option B (TensorRT All) | 48ms | 15-45ms | 15-20 | ✅ Best |

---

## Summary

Option A is technically viable but blocked by TensorRT/Python version issues. Recommend either:
- **Option A2** (simpler, 8-12 FPS improvement), or
- **Option B** (best performance, 15-20 FPS)

Both are better than current 0.6 FPS!
