#!/bin/bash

# Continuous OCR ALPR Runner
# Fast real-time license plate detection with continuous OCR

cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording

# Activate virtual environment (in parent directory)
source ../myenv/bin/activate

# Run continuous OCR with GStreamer workaround
echo "========================================="
echo "Continuous OCR ALPR"
echo "Fast Real-time Detection"
echo "========================================="
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1
python3 continuous_ocr.py

deactivate
