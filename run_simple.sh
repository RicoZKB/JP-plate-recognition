#!/bin/bash

# Simple ALPR Runner - No Gate System
# Just pure license plate detection and OCR

cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording

# Activate virtual environment (in parent directory)
source ../myenv/bin/activate

# Run simple ALPR with GStreamer workaround
echo "========================================="
echo "Running Simple ALPR (No Gate System)"
echo "========================================="
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1
python3 simple_alpr.py

deactivate
