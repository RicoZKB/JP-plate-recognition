#!/bin/bash

# Simple ALPR Camera Launcher with GStreamer Fix
# This script includes the LD_PRELOAD workaround for Jetson GStreamer issues

cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
source /home/jetson/yolo/yolov7/myenv/bin/activate

# GStreamer workaround for Jetson
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0

# Run with default settings (CSV enabled, duplicates filtered)
python run_simple_alpr.py \
    --camera \
    --model models/best.onnx \
    --enable-csv \
    --csv-no-duplicates \
    --verbose \
    "$@"
