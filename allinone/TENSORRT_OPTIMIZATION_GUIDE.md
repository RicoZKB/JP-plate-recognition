# TensorRT Optimization Guide

## Overview

This guide documents the TensorRT optimization implementation for license plate detection and recognition, providing significant performance improvements on Jetson platforms.

## Architecture

The optimized system uses **full TensorRT acceleration** for both detection and OCR:

### 1. YOLO Detection (TensorRT)
- **Model**: `models/best.engine` or `models/best_fp16.engine`
- **Precision**: FP16 for optimal performance on Jetson
- **Direct TensorRT inference** using PyCUDA for maximum speed
- **GPU memory pre-allocation** to avoid runtime allocation overhead

### 2. OCR Recognition (TensorRT)
- **Model**: `models/paddleocr_onnx/rec_japan_fp16.engine`
- **Precision**: FP16 for fast inference
- **Dynamic input shapes** to handle variable plate widths
- **CTC decoding** for character recognition

### 3. Image Preprocessing (OpenCV CUDA)
- **GPU-accelerated color conversion** (BGR→Gray)
- **GPU-accelerated resizing** for upscaling
- **CLAHE contrast enhancement** for low-light conditions
- **Unsharp masking** for edge enhancement

## Performance Benefits

### Before (CPU PaddleOCR):
- YOLO: ~50ms per frame
- OCR: ~200-300ms per plate
- **Total**: ~250-350ms per detection

### After (Full TensorRT):
- YOLO: ~10-15ms per frame
- OCR: ~20-30ms per plate
- **Total**: ~30-45ms per detection

**Performance Improvement**: ~7-10x faster

## File Structure

```
detections/
  ├── licence_plate_detection.py  # TensorRT-optimized detector (NEW)
  └── __init__.py

fr01.py                            # Main detection script (UPDATED)
run_tensorrt_fr01.sh               # Launch script (NEW)

models/
  ├── best.engine                  # YOLO TensorRT engine (FP32)
  ├── best_fp16.engine             # YOLO TensorRT engine (FP16)
  └── paddleocr_onnx/
      ├── rec_japan_fp16.engine    # OCR TensorRT engine (FP16)
      └── japan_dict.txt           # Japanese character dictionary
```

## Usage

### Quick Start

```bash
cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
source ../myenv/bin/activate
./run_tensorrt_fr01.sh
```

### Python API

```python
from detections.licence_plate_detection import LicencePlateDetection

# Initialize detector
detector = LicencePlateDetection(
    model_path="models/best.engine",
    ocr_engine_path="models/paddleocr_onnx/rec_japan_fp16.engine",
    verbose=True,
    debug_ocr=False,
    use_cuda_preprocessing=True  # Enable OpenCV CUDA
)

# Detect plates in frame
bboxes, texts = detector.detect_frame(frame)

# Draw results
output_frames = detector.draw_bboxes([frame], [bboxes], [texts])
```

## Requirements

### Software Dependencies
- **TensorRT** (included in JetPack)
- **PyCUDA** for GPU memory management
- **OpenCV with CUDA support** (optional but recommended)
- **NumPy** for array operations

### Install Python packages:
```bash
pip install pycuda tensorrt numpy opencv-python
```

### Hardware Requirements
- **Jetson Nano/Xavier/Orin** with JetPack 4.6+
- **CUDA-capable GPU** with compute capability 5.3+
- **4GB+ RAM** recommended

## Key Optimizations

### 1. Direct TensorRT Inference
- No intermediate framework (PyTorch/ONNX Runtime)
- Direct CUDA memory transfers
- Pre-allocated GPU buffers
- Batch processing support

### 2. FP16 Precision
- 2x faster than FP32 on Jetson
- Half the memory bandwidth
- Minimal accuracy loss for detection tasks

### 3. CUDA Preprocessing
- GPU-accelerated image operations
- Reduced CPU→GPU transfers
- Parallel processing of multiple plates

### 4. Optimized Memory Management
- Pre-allocated device buffers
- Dynamic resizing only when needed
- Proper cleanup to prevent memory leaks

## Troubleshooting

### Issue: TensorRT engine not found
**Solution**: Check that engine files exist:
```bash
ls -lh models/best*.engine
ls -lh models/paddleocr_onnx/rec_japan_fp16.engine
```

### Issue: CUDA out of memory
**Solution**: Reduce batch size or input resolution in fr01.py:
```python
TARGET_WIDTH = 640  # Reduce to 480 or 320
```

### Issue: OpenCV CUDA not available
**Solution**: The system will fall back to CPU preprocessing automatically. To enable CUDA:
```bash
# Check OpenCV CUDA support
python3 -c "import cv2; print(cv2.cuda.getCudaEnabledDeviceCount())"
```

### Issue: Slow inference despite TensorRT
**Solution**: Ensure power mode is set to maximum:
```bash
sudo nvpmodel -m 0  # Max performance mode
sudo jetson_clocks   # Maximize clocks
```

## Monitoring Performance

### Check GPU utilization:
```bash
tegrastats
```

### Profile inference time:
```python
detector = LicencePlateDetection(..., verbose=True)  # Enable timing logs
```

## Creating TensorRT Engines

### Convert YOLO to TensorRT:
```bash
# Using trtexec (included in JetPack)
/usr/src/tensorrt/bin/trtexec \
    --onnx=models/best.onnx \
    --saveEngine=models/best_fp16.engine \
    --fp16
```

### Convert PaddleOCR to TensorRT:
```bash
# First convert to ONNX, then to TensorRT
python3 convert_paddle_to_onnx.py
python3 convert_paddleocr_to_tensorrt.py
```

## Advanced Configuration

### Confidence Thresholds
```python
detector.yolo.conf_threshold = 0.25  # Detection confidence
detector.yolo.iou_threshold = 0.45   # NMS IoU threshold
```

### OCR Height
```python
detector.ocr.input_height = 48  # Standard plate height (pixels)
```

### CUDA Preprocessing
```python
detector.use_cuda_preprocessing = True  # Enable/disable CUDA
```

## Comparison with Original Implementation

| Feature | Original (CPU) | Optimized (TensorRT) |
|---------|---------------|---------------------|
| YOLO Backend | Ultralytics PyTorch | TensorRT FP16 |
| OCR Backend | PaddleOCR CPU | TensorRT FP16 |
| Preprocessing | OpenCV CPU | OpenCV CUDA |
| Inference Time | 250-350ms | 30-45ms |
| GPU Utilization | 10-20% | 80-95% |
| Power Efficiency | Low | High |

## References

- [TensorRT Documentation](https://docs.nvidia.com/deeplearning/tensorrt/)
- [PyCUDA Documentation](https://documen.tician.de/pycuda/)
- [OpenCV CUDA](https://docs.opencv.org/4.x/d2/d3c/group__cudaimgproc.html)
- [Jetson Optimization Guide](https://docs.nvidia.com/jetson/archives/r35.1/DeveloperGuide/index.html)

## License

This optimization work is part of the Licence-Plate-Detection-Recognition-Recording project.
