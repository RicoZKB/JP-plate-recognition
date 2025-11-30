#!/usr/bin/env python3
"""
Simple ALPR - License Plate Detection, Crop, and Extract
No gate system, no tracking, no IN/OUT logic
Just pure detection and OCR
"""

import sys
# Insert system packages AFTER site-packages to prioritize venv protobuf
# but still get CUDA-enabled OpenCV
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.append('/usr/lib/python3/dist-packages')

import cv2
import time
from detections.licence_plate_detection import LicencePlateDetection

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
    # ========== CONFIGURATION ==========
    USE_CAMERA = False         # True for CSI camera, False for video file
    VIDEO_PATH = "input_videos/Trim03.mp4"  # Video file path if USE_CAMERA=False

    # Camera settings
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480

    # Model path
    MODEL_PATH = "models/best.onnx"  # Use ONNX for better performance

    # Display settings
    SHOW_FPS = True
    SAVE_OUTPUT = False  # Set to True to save output video
    OUTPUT_PATH = "output_simple_alpr.avi"

    # ===================================

    print("=" * 60)
    print("Simple ALPR - License Plate Detection & OCR")
    print("=" * 60)
    print(f"Model: {MODEL_PATH}")

    # Initialize camera/video
    if USE_CAMERA:
        print("Initializing CSI Camera...")
        gst_pipeline = gstreamer_csi_pipeline(
            capture_width=1280,
            capture_height=720,
            display_width=CAMERA_WIDTH,
            display_height=CAMERA_HEIGHT,
            framerate=30,
            flip_method=0
        )
        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        print(f"Camera: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    else:
        print(f"Loading video: {VIDEO_PATH}")
        cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        raise RuntimeError("Could not open video source")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Resolution: {width}x{height} @ {fps} FPS")

    # Initialize license plate detector
    print("Loading License Plate Detector...")
    lp_detector = LicencePlateDetection(
        model_path=MODEL_PATH,
        verbose=True,      # Print detection info
        debug_ocr=False    # Set True for OCR debug output
    )
    print("Detector loaded successfully!")

    # Optional: video writer
    out = None
    if SAVE_OUTPUT:
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (width, height))
        print(f"Saving output to: {OUTPUT_PATH}")

    print("\n" + "=" * 60)
    print("Starting detection... (Press ESC to quit)")
    print("=" * 60 + "\n")

    # FPS tracking
    frame_count = 0
    start_time = time.time()
    fps_display = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("End of video or camera error")
                break

            frame_count += 1

            # Detect license plates and run OCR
            lp_bboxes, lp_texts, lp_statuses = lp_detector.detect_frame(frame)

            # Draw bounding boxes and text on frame
            for (x1, y1, x2, y2), text, status in zip(lp_bboxes, lp_texts, lp_statuses):
                # Draw rectangle around plate (green for NEW, yellow for CACHED)
                color = (0, 255, 0) if status == "NEW" else (0, 255, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # Draw yellow text above plate
                cv2.putText(
                    frame, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
                )

                # Optional: draw filled background for better text visibility
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                cv2.rectangle(
                    frame,
                    (x1, y1 - text_size[1] - 15),
                    (x1 + text_size[0], y1 - 5),
                    (0, 0, 0),
                    -1
                )
                cv2.putText(
                    frame, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
                )

            # Calculate and display FPS
            if SHOW_FPS:
                elapsed = time.time() - start_time
                if elapsed > 0:
                    fps_display = frame_count / elapsed

                # Draw FPS on frame
                fps_text = f"FPS: {fps_display:.1f}"
                cv2.putText(
                    frame, fps_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2
                )

                # Draw frame count
                count_text = f"Frames: {frame_count}"
                cv2.putText(
                    frame, count_text, (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
                )

                # Draw detection count
                det_text = f"Detections: {len(lp_bboxes)}"
                cv2.putText(
                    frame, det_text, (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
                )

            # Show frame
            cv2.imshow("Simple ALPR - License Plate Detection", frame)

            # Save frame if enabled
            if out is not None:
                out.write(frame)

            # Check for ESC key
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("\nESC pressed - stopping...")
                break
            elif key == ord('s'):  # Save current frame
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_path = f"frame_{timestamp}.jpg"
                cv2.imwrite(save_path, frame)
                print(f"Frame saved: {save_path}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Cleanup
        print("\nCleaning up...")
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()

        # Print statistics
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("Session Statistics:")
        print("=" * 60)
        print(f"Total frames processed: {frame_count}")
        print(f"Total time: {elapsed:.2f} seconds")
        print(f"Average FPS: {frame_count/elapsed:.2f}")
        print("=" * 60)

if __name__ == "__main__":
    main()
