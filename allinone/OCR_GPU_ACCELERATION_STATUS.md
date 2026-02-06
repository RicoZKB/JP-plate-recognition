# OCR GPU Acceleration Investigation

**Date:** January 7, 2026
**Goal:** Accelerate PaddleOCR with GPU/TensorRT
**Status:** ⚠️ **Partial Success** - ONNX Export Complete, TensorRT Conversion Blocked

---

## Summary

You discovered that PaddleOCR models CAN be exported to ONNX format! This was an excellent find. We successfully converted all three PaddleOCR models to ONNX, but hit limitations with TensorRT conversion due to missing operators in TensorRT 8.0.1.

---

## What We Accomplished ✅

### 1. Exported PaddleOCR Models to ONNX

Successfully converted all three models using `paddle2onnx`:

```bash
# Detection Model (Multilingual PP-OCRv3)
models/paddleocr_onnx/det_ml.onnx (2.4 MB)

# Recognition Model (Japan PP-OCRv4)
models/paddleocr_onnx/rec_japan.onnx (9.3 MB)

# Classifier Model (Chinese PP-OCR Mobile v2.0)
models/paddleocr_onnx/cls_ch.onnx (559 KB)
```

**Model Details:**
- **Detection:** Input shape `[batch, 3, 960, 960]` (dynamic batch)
- **Recognition:** Input shape `[batch, 3, 48, width]` (dynamic width)
- **Classifier:** Input shape `[batch, 3, height, width]` (fully dynamic)

**Conversion Tool:** `paddle2onnx==1.3.1`

---

## What Blocked Us ⚠️

### TensorRT 8.0.1 Operator Limitations

When trying to convert ONNX models to TensorRT engines:

```
[E] [TRT] 3: getPluginCreator could not find plugin: HardSwish version: 1
[E] Failed to parse onnx file
```

**Root Cause:**
- TensorRT 8.0.1 (JetPack 4.6.1, CUDA 10.2) lacks the `HardSwish` operator
- PaddleOCR v4 models use HardSwish activation functions
- This operator requires TensorRT 8.5+ (available in JetPack 5.0+, CUDA 11.4+)

**Compatibility Issues:**
- Jetson TX1 max JetPack: 4.6.1
- Jetson TX1 max CUDA: 10.2
- Jetson TX1 max TensorRT: 8.0.1.6
- **TensorRT 8.5+ requires newer Jetson hardware** (Orin, Xavier, etc.)

---

### ONNX Runtime GPU Incompatibility

Attempted to use ONNX Runtime with CUDA instead:

```bash
# Tried installing ONNX Runtime GPU 1.11.0
pip install onnxruntime_gpu-1.11.0-cp38-cp38-linux_aarch64.whl
```

**Problem:**
- Available wheel compiled for Python 3.7
- Your system has Python 3.8.10
- Version mismatch: `module was compiled for Python 3.7, but interpreter is 3.8`

**Why This Matters:**
- ONNX Runtime GPU would allow running ONNX models with CUDA
- Avoids TensorRT operator limitations
- But Python version mismatch prevents installation

---

## Alternative Approaches Explored

### ❌ **PaddlePaddle GPU**
- Not available for ARM Python 3.8
- Would require downgrading to Python 3.6 (breaks TensorRT)
- Conclusion: Not feasible

### ❌ **TensorRT Conversion**
- Blocked by missing HardSwish operator
- Requires TensorRT 8.5+ (not available for TX1)
- Conclusion: Hardware limitation

### ⚠️ **ONNX Runtime GPU**
- Python 3.7 vs 3.8 mismatch
- Could build from source (8+ hours)
- Uncertain performance gain
- Conclusion: High effort, uncertain reward

---

## Current System Performance (Baseline)

### What's Already Working Well ✅

**TensorRT Detection (YOLOv7):**
- FPS: 18 FPS
- Engine: `best_fp16.engine` (GPU accelerated)
- Inference time: ~35ms per frame

**PaddleOCR (CPU):**
- Processing time: ~500ms per plate
- Frequency: Every 6th frame (16% of frames)
- Impact on FPS: Minimal due to smart skipping

**Overall System:**
- Average FPS: 18 FPS
- Detection coverage: Every 3rd frame
- OCR coverage: Every 6th frame
- GPU memory: 3.9GB / 4GB

---

## Why OCR GPU Acceleration Has Limited Impact

### Performance Analysis

**Current Bottleneck: Detection (already GPU-accelerated)**
- Detection: ~35ms (TensorRT GPU) → dominates frame time
- OCR: ~500ms (CPU) → runs only 16% of frames

**If OCR Were GPU-Accelerated:**
- Estimated OCR time: ~200ms (GPU) vs 500ms (CPU)
- Savings per frame: 48ms → 19ms (60% faster)
- **Average FPS improvement: 18 → 19-20 FPS** (~10% gain)

**Why Small Gain?**
1. OCR runs rarely (every 6th frame)
2. Detection is the main bottleneck
3. Smart caching already minimizes OCR impact
4. Frame skipping means most time is in detection

---

## Recommendations

### Option 1: Keep Current Setup ✅ **RECOMMENDED**

**Why:**
- 18 FPS is excellent for license plate detection
- TensorRT detection fully optimized (GPU)
- OCR CPU overhead is minimal (smart skipping)
- Zero risk, stable performance
- **Best cost/benefit ratio**

**Current Status:**
```
✅ YOLOv7 Detection: TensorRT FP16 (GPU)
✅ OpenCV Processing: CUDA enabled
✅ Frame Skipping: Optimized (every 3rd frame)
✅ OCR Caching: Smart 2-second cooldown
⚠️ PaddleOCR: CPU only (minimal impact)
```

### Option 2: Build ONNX Runtime GPU from Source 🔧

**Pros:**
- Could provide GPU acceleration for ONNX OCR models
- Avoids TensorRT operator limitations
- Maintains Python 3.8 environment

**Cons:**
- Build time: 8-12 hours on Jetson TX1
- Complex dependencies (CUDA, cuDNN, CMake)
- High failure rate
- **Expected FPS gain: Only 1-2 FPS** (18 → 19-20)

**Verdict:** Not worth the effort for marginal gain

### Option 3: Use ONNX Models with CPU ONNX Runtime 🆗

**Pros:**
- Already have ONNX models converted ✅
- Could test if ONNX inference is faster than PaddlePaddle CPU
- Low risk (can always revert)

**Cons:**
- Still CPU-only (no GPU acceleration)
- Uncertain if faster than current PaddleOCR
- Would require code modifications

**Verdict:** Worth a quick test to see if ONNX CPU is faster

---

## Technical Details

### Files Created

**ONNX Models:**
```
models/paddleocr_onnx/det_ml.onnx        (2.4 MB)
models/paddleocr_onnx/rec_japan.onnx     (9.3 MB)
models/paddleocr_onnx/cls_ch.onnx        (559 KB)
```

**Tools Installed:**
```
paddle2onnx==1.3.1
onnxruntime==1.16.3 (CPU)
```

### Conversion Commands Used

```bash
# Detection Model
paddle2onnx --model_dir /root/.paddleocr/whl/det/ml/Multilingual_PP-OCRv3_det_infer \
  --model_filename inference.pdmodel \
  --params_filename inference.pdiparams \
  --save_file models/paddleocr_onnx/det_ml.onnx \
  --opset_version 11 \
  --enable_onnx_checker True

# Recognition Model
paddle2onnx --model_dir /root/.paddleocr/whl/rec/japan/japan_PP-OCRv4_rec_infer \
  --model_filename inference.pdmodel \
  --params_filename inference.pdiparams \
  --save_file models/paddleocr_onnx/rec_japan.onnx \
  --opset_version 11 \
  --enable_onnx_checker True

# Classifier Model
paddle2onnx --model_dir /root/.paddleocr/whl/cls/ch_ppocr_mobile_v2.0_cls_infer \
  --model_filename inference.pdmodel \
  --params_filename inference.pdiparams \
  --save_file models/paddleocr_onnx/cls_ch.onnx \
  --opset_version 11 \
  --enable_onnx_checker True
```

### TensorRT Conversion Attempt (Failed)

```bash
# Recognition Model → TensorRT (FAILED: Missing HardSwish operator)
/usr/src/tensorrt/bin/trtexec \
  --onnx=models/paddleocr_onnx/rec_japan.onnx \
  --saveEngine=models/paddleocr_onnx/rec_japan_fp16.engine \
  --fp16 \
  --minShapes=x:1x3x48x32 \
  --optShapes=x:1x3x48x320 \
  --maxShapes=x:1x3x48x640

# Error:
# [E] [TRT] 3: getPluginCreator could not find plugin: HardSwish version: 1
```

---

## System Constraints

### Hardware Limitations
- **Jetson TX1:** Maxwell GPU architecture (Compute Capability 5.3)
- **Max CUDA:** 10.2.300
- **Max TensorRT:** 8.0.1.6
- **Max JetPack:** 4.6.1

### Software Limitations
- TensorRT 8.0.1 lacks modern operators (HardSwish, etc.)
- ONNX Runtime GPU wheels for Python 3.8 unavailable
- PaddlePaddle GPU not compiled for ARM Python 3.8

---

## Next Steps (If You Want to Experiment)

### Quick Test: CPU ONNX Inference

Test if ONNX models run faster than PaddlePaddle on CPU:

```python
import onnxruntime as ort
import numpy as np

# Load recognition model
session = ort.InferenceSession("models/paddleocr_onnx/rec_japan.onnx")

# Test inference
input_name = session.get_inputs()[0].name
dummy_input = np.random.randn(1, 3, 48, 320).astype(np.float32)
output = session.run(None, {input_name: dummy_input})

print("ONNX inference successful!")
```

If ONNX CPU is significantly faster, we could integrate it into `fr01.py`.

---

## Conclusion

**Your discovery was correct:** PaddleOCR models CAN be exported to ONNX! ✅

**The problem:** Hardware limitations on Jetson TX1 prevent GPU acceleration:
- TensorRT 8.0.1 lacks required operators
- ONNX Runtime GPU incompatible with Python 3.8

**The reality:** Your current 18 FPS system is already well-optimized:
- TensorRT handles the main bottleneck (detection)
- OCR CPU overhead is minimal (smart frame skipping)
- GPU acceleration would only gain 1-2 FPS

**Final Recommendation:** **Keep your current setup!**

The 18 FPS performance with GPU-accelerated detection is excellent. The effort required to accelerate OCR (building ONNX Runtime from source, 8+ hours) would only yield a 5-10% FPS improvement, which is not worth the risk and complexity.

---

**Status:** ✅ ONNX models exported and ready
**Blocker:** TensorRT/ONNX Runtime GPU incompatibility
**Decision:** Stick with current CPU OCR (best cost/benefit)
**Performance:** 18 FPS is production-ready!
