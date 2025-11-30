#!/bin/bash
# EASIEST RUN SCRIPT - Just 3 steps!

echo "Starting License Plate Detection..."

cd /home/jetson/yolo/yolov7/Licence-Plate-Detection-Recognition-Recording
source ../myenv/bin/activate
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0

python3 inout_event.py

echo "Done! Check logs/parking_log_*.csv for results"
