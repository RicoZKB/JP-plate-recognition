#!/usr/bin/env python3
import cv2

print("Testing CSI camera with OpenCV + GStreamer...")

# Test 1: Simple pipeline
print("\nTest 1: Minimal pipeline...")
pipeline1 = (
    "nvarguscamerasrc sensor-id=0 ! "
    "video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 ! "
    "nvvidconv ! "
    "video/x-raw, format=BGRx ! "
    "videoconvert ! "
    "appsink"
)

cap1 = cv2.VideoCapture(pipeline1, cv2.CAP_GSTREAMER)
if cap1.isOpened():
    print("✓ Minimal pipeline works!")
    ret, frame = cap1.read()
    if ret:
        print(f"  Frame shape: {frame.shape}")
    cap1.release()
else:
    print("✗ Minimal pipeline failed")

# Test 2: Pipeline with explicit appsink settings
print("\nTest 2: Pipeline with appsink settings...")
pipeline2 = (
    "nvarguscamerasrc sensor-id=0 ! "
    "video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 ! "
    "nvvidconv ! "
    "video/x-raw, width=640, height=360, format=BGRx ! "
    "videoconvert ! "
    "video/x-raw, format=BGR ! "
    "appsink drop=true max-buffers=2"
)

cap2 = cv2.VideoCapture(pipeline2, cv2.CAP_GSTREAMER)
if cap2.isOpened():
    print("✓ Pipeline with settings works!")
    ret, frame = cap2.read()
    if ret:
        print(f"  Frame shape: {frame.shape}")
    cap2.release()
else:
    print("✗ Pipeline with settings failed")

# Test 3: Original fr01.py pipeline
print("\nTest 3: Original fr01.py pipeline...")
pipeline3 = (
    "nvarguscamerasrc sensor-id=0 ! "
    "video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, "
    "format=(string)NV12, framerate=(fraction)30/1 ! "
    "nvvidconv flip-method=0 ! "
    "video/x-raw, width=(int)640, height=(int)360, format=(string)BGRx ! "
    "videoconvert ! "
    "video/x-raw, format=(string)BGR ! "
    "queue max-size-buffers=2 leaky=downstream ! "
    "appsink emit-signals=true sync=false max-buffers=2 drop=true"
)

cap3 = cv2.VideoCapture(pipeline3, cv2.CAP_GSTREAMER)
if cap3.isOpened():
    print("✓ Original pipeline works!")
    ret, frame = cap3.read()
    if ret:
        print(f"  Frame shape: {frame.shape}")
    cap3.release()
else:
    print("✗ Original pipeline failed")

print("\nDone!")
