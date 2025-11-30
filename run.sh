#!/bin/bash
# Launcher script for inout_event.py with GStreamer fix

cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
source /home/jetson/yolo/yolov7/myenv/bin/activate

# GStreamer workaround (MUST be set before Python starts)
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0

# Run the script
python3 inout_event.py "$@"
