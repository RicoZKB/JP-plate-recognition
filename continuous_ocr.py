#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuous OCR ALPR - Fast Continuous License Plate Detection & Recognition
- Single direction mode only (IN or OUT)
- Continuous OCR on every detected plate (like Roboflow/YouTube demos)
- No gate logic, no complex tracking
- Simple, fast, real-time display
"""

# ========== AUTO-RESTART WITH LD_PRELOAD IF MISSING ==========
import os
import sys

# Check if LD_PRELOAD is set, if not, restart with it
if 'LD_PRELOAD' not in os.environ or '/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0' not in os.environ.get('LD_PRELOAD', ''):
    print("[INFO] Restarting with GStreamer workaround...")
    os.environ['LD_PRELOAD'] = '/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0'
    os.execvp('python3', ['python3'] + sys.argv)
# ================================================================================

# Add system packages for CUDA-enabled OpenCV
import sys
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.append('/usr/lib/python3/dist-packages')

import cv2
import time
import re
from datetime import datetime
from detections.licence_plate_detection import LicencePlateDetection

# ===================== USER SETTINGS =====================
# Direction mode: "IN" or "OUT" (single direction only)
DIRECTION = "IN"  # Change to "OUT" if needed

# Video source
USE_CAMERA = False  # Changed to False for video file testing
VIDEO_PATH = "input_videos/Trim03.mp4"

# Model path
MODEL_PATH = "models/best.onnx"  # ONNX for best performance

# Performance settings
TARGET_WIDTH = 480          # Resize frame width
SHOW_FPS = True             # Display FPS counter
RUN_OCR_EVERY_N_FRAMES = 1  # Run OCR every N frames (1 = continuous, 2 = every other frame, etc.)

# Display settings
BOX_COLOR = (0, 255, 0)     # Green for detected plates
TEXT_COLOR = (255, 255, 255) # White text
FONT_SCALE = 0.6
FONT_THICKNESS = 2

# Camera settings (for CSI camera)
CAMERA_CAPTURE_WIDTH = 1280
CAMERA_CAPTURE_HEIGHT = 720
CAMERA_DISPLAY_WIDTH = 480
CAMERA_DISPLAY_HEIGHT = 360
# =========================================================

def gstreamer_csi_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=640,
    display_height=480,
    framerate=30,
    flip_method=0,
):
    """Create GStreamer pipeline for CSI camera"""
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width=(int){capture_width}, height=(int){capture_height}, "
        f"format=(string)NV12, framerate=(fraction){framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! "
        f"videoconvert ! "
        f"video/x-raw, format=(string)BGR ! appsink"
    )

def main():
    print("=" * 60)
    print("Continuous OCR ALPR - Real-time License Plate Recognition")
    print("=" * 60)
    print(f"Direction Mode: {DIRECTION}")
    print(f"Model: {MODEL_PATH}")
    print(f"OCR Frequency: Every {RUN_OCR_EVERY_N_FRAMES} frame(s)")

    # Initialize video source
    if USE_CAMERA:
        print("Initializing CSI Camera...")
        gst_pipeline = gstreamer_csi_pipeline(
            capture_width=CAMERA_CAPTURE_WIDTH,
            capture_height=CAMERA_CAPTURE_HEIGHT,
            display_width=CAMERA_DISPLAY_WIDTH,
            display_height=CAMERA_DISPLAY_HEIGHT,
            framerate=30,
            flip_method=0
        )
        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        print(f"Camera: {CAMERA_DISPLAY_WIDTH}x{CAMERA_DISPLAY_HEIGHT}")
    else:
        print(f"Loading video: {VIDEO_PATH}")
        cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        raise RuntimeError("Could not open video source")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Resolution: {width}x{height} @ {fps:.1f} FPS")

    # Initialize license plate detector
    print("Loading License Plate Detector...")
    lp_detector = LicencePlateDetection(
        model_path=MODEL_PATH,
        verbose=False,
        debug_ocr=False
    )

    # DISABLE caching for continuous OCR (always run fresh OCR on every plate)
    lp_detector.cache_timeout = 0.0  # Disable cache by setting timeout to 0

    print("Detector loaded successfully!")
    print("[INFO] Caching disabled - running continuous OCR")
    print("\nStarting continuous OCR detection...")
    print("Press ESC to quit\n")

    # Performance tracking
    frame_count = 0
    start_time = time.time()
    fps_display = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[INFO] End of video stream")
                break

            frame_count += 1

            # Resize frame for performance
            if frame.shape[1] != TARGET_WIDTH:
                scale = TARGET_WIDTH / frame.shape[1]
                new_h = int(frame.shape[0] * scale)
                frame = cv2.resize(frame, (TARGET_WIDTH, new_h))

            # Run detection + OCR using detect_frame method
            bboxes, texts, statuses = lp_detector.detect_frame(frame, ocr_filter=None)

            # Draw detections
            for idx, bbox in enumerate(bboxes):
                x1, y1, x2, y2 = bbox
                ocr_text = texts[idx] if idx < len(texts) else ''
                status = statuses[idx] if idx < len(statuses) else 'NEW'

                # Draw bounding box
                box_color = (0, 255, 0) if status == 'NEW' else (255, 128, 0)  # Green for NEW, Blue for CACHED
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

                # Prepare display text
                if ocr_text:
                    display_text = f"{ocr_text}"
                    if status == 'CACHED':
                        display_text += " [CACHED]"

                    # Draw OCR text above bbox
                    (text_w, text_h), baseline = cv2.getTextSize(
                        display_text, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, FONT_THICKNESS
                    )

                    # Background rectangle for text
                    cv2.rectangle(
                        frame,
                        (x1, y1 - text_h - 10),
                        (x1 + text_w + 10, y1),
                        (0, 0, 0),
                        -1
                    )

                    # Draw text
                    cv2.putText(
                        frame,
                        display_text,
                        (x1 + 5, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        FONT_SCALE,
                        TEXT_COLOR,
                        FONT_THICKNESS
                    )

            # Calculate and display FPS
            if SHOW_FPS:
                elapsed = time.time() - start_time
                if elapsed > 0:
                    fps_display = frame_count / elapsed

                fps_text = f"FPS: {fps_display:.1f} | Direction: {DIRECTION}"
                cv2.putText(
                    frame,
                    fps_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )

            # Show frame
            cv2.imshow('Continuous OCR ALPR', frame)

            # Check for ESC key
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("\n[INFO] User stopped the system")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")

    finally:
        # Cleanup
        elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"Session Summary:")
        print(f"  Total frames processed: {frame_count}")
        print(f"  Total time: {elapsed:.1f}s")
        print(f"  Average FPS: {frame_count/elapsed if elapsed > 0 else 0:.1f}")
        print(f"{'=' * 60}")

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
