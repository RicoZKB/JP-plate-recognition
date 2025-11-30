#!/usr/bin/env python3
"""
Simple ALPR Demo - Optimized for real-world deployment
No IN/OUT tracking, no gates, just efficient plate detection and recognition

Usage:
    # Camera mode
    python run_simple_alpr.py --camera

    # Video file mode
    python run_simple_alpr.py --video path/to/video.mp4

    # Image mode
    python run_simple_alpr.py --image path/to/image.jpg
"""

import sys
# System path for CUDA-enabled OpenCV
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.append('/usr/lib/python3/dist-packages')

import cv2
import argparse
import time
from detections.optimized_plate_detection import OptimizedPlateDetection
from utils.csv_logger import CSVLogger

def gstreamer_csi_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=640,
    display_height=480,
    framerate=30,
    flip_method=0,
):
    """GStreamer pipeline for CSI camera"""
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
    parser = argparse.ArgumentParser(description='Simple ALPR Demo')
    parser.add_argument('--camera', action='store_true', help='Use CSI camera')
    parser.add_argument('--video', type=str, help='Path to video file')
    parser.add_argument('--image', type=str, help='Path to image file')
    parser.add_argument('--model', type=str, default='models/best.onnx',
                       help='Path to YOLO model (default: models/best.onnx)')
    parser.add_argument('--padding', type=float, default=0.15,
                       help='Padding ratio for plate crops (default: 0.15)')
    parser.add_argument('--cooldown', type=float, default=2.0,
                       help='OCR cooldown in seconds (default: 2.0)')
    parser.add_argument('--no-display', action='store_true',
                       help='Disable display window (headless mode)')
    parser.add_argument('--save-output', type=str,
                       help='Save output video to this path')
    parser.add_argument('--fps-limit', type=int, default=None,
                       help='Limit processing FPS (for performance tuning)')
    parser.add_argument('--show-padding', action='store_true',
                       help='Show padded bounding boxes (debug mode)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')

    # CSV Logging options
    parser.add_argument('--enable-csv', action='store_true',
                       help='Enable CSV logging of detections')
    parser.add_argument('--csv-dir', type=str, default='logs',
                       help='Directory for CSV log files (default: logs)')
    parser.add_argument('--csv-prefix', type=str, default='plate_log',
                       help='Prefix for CSV log filename (default: plate_log)')
    parser.add_argument('--csv-no-duplicates', action='store_true',
                       help='Filter duplicate plates in CSV (same plate within 5s)')

    args = parser.parse_args()

    # Validate input source
    if not any([args.camera, args.video, args.image]):
        print("[ERROR] Please specify input source: --camera, --video, or --image")
        return

    # Initialize detector
    print(f"[INFO] Loading model: {args.model}")
    detector = OptimizedPlateDetection(
        model_path=args.model,
        padding_ratio=args.padding,
        ocr_cooldown=args.cooldown,
        verbose=args.verbose
    )

    # Initialize CSV logger (if enabled)
    csv_logger = None
    if args.enable_csv:
        csv_logger = CSVLogger(
            log_dir=args.csv_dir,
            log_prefix=args.csv_prefix,
            enable_duplicate_filter=args.csv_no_duplicates,
            duplicate_window=5.0  # 5 seconds duplicate filter
        )
        print(f"[INFO] CSV logging enabled: {csv_logger.log_file}")

    # Setup input source
    cap = None
    if args.camera:
        print("[INFO] Opening CSI camera...")
        pipeline = gstreamer_csi_pipeline(
            capture_width=1280,
            capture_height=720,
            display_width=640,
            display_height=480,
            framerate=30
        )
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        source_type = "camera"

    elif args.video:
        print(f"[INFO] Opening video: {args.video}")
        cap = cv2.VideoCapture(args.video)
        source_type = "video"

    elif args.image:
        print(f"[INFO] Loading image: {args.image}")
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"[ERROR] Could not load image: {args.image}")
            return
        source_type = "image"

    # Setup output video writer
    writer = None
    if args.save_output and source_type != "image":
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS) if cap else 30.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if cap else 640
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if cap else 480
        writer = cv2.VideoWriter(args.save_output, fourcc, fps, (w, h))
        print(f"[INFO] Saving output to: {args.save_output}")

    # Process image mode
    if source_type == "image":
        print("[INFO] Processing image...")
        detections = detector.detect_and_recognize(frame, run_ocr=True)

        print(f"\n[RESULTS] Found {len(detections)} plate(s):")
        for i, det in enumerate(detections):
            print(f"  Plate {i+1}: {det['text']} (conf: {det['confidence']:.2f})")

        # Log to CSV
        if csv_logger:
            logged = csv_logger.log_multiple(detections, frame_number=0, source='image')
            if logged > 0:
                print(f"[CSV] Logged {logged} detection(s)")

        # Draw and show results
        frame = detector.draw_results(frame, detections, show_padding=args.show_padding)

        if not args.no_display:
            cv2.imshow("ALPR Result", frame)
            print("\n[INFO] Press any key to exit...")
            cv2.waitKey(0)

        if args.save_output:
            cv2.imwrite(args.save_output, frame)
            print(f"[INFO] Saved result to: {args.save_output}")

        # Cleanup
        if csv_logger:
            csv_logger.close()

        cv2.destroyAllWindows()
        return

    # Process video/camera mode
    if not cap.isOpened():
        print("[ERROR] Could not open video source")
        return

    print("\n[INFO] Starting detection... Press 'q' to quit, 'c' to clear cache\n")

    frame_count = 0
    fps_time = time.time()
    fps_counter = 0
    last_frame_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if source_type == "video":
                    print("[INFO] End of video")
                    break
                else:
                    print("[WARN] Failed to read frame")
                    continue

            # FPS limiting
            if args.fps_limit:
                current_time = time.time()
                time_per_frame = 1.0 / args.fps_limit
                elapsed = current_time - last_frame_time
                if elapsed < time_per_frame:
                    time.sleep(time_per_frame - elapsed)
                last_frame_time = time.time()

            frame_count += 1
            fps_counter += 1

            # Run detection and recognition
            start_time = time.time()
            detections = detector.detect_and_recognize(frame, run_ocr=True)
            detection_time = (time.time() - start_time) * 1000  # ms

            # Draw results
            frame = detector.draw_results(frame, detections, show_padding=args.show_padding)

            # Calculate FPS
            if time.time() - fps_time > 1.0:
                fps = fps_counter / (time.time() - fps_time)
                fps_time = time.time()
                fps_counter = 0
            else:
                fps = fps_counter / (time.time() - fps_time + 0.001)

            # Draw stats overlay
            stats_text = [
                f"FPS: {fps:.1f}",
                f"Detection: {detection_time:.0f}ms",
                f"Plates: {len(detections)}",
                f"Frame: {frame_count}"
            ]

            y_offset = 30
            for text in stats_text:
                cv2.putText(frame, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 30

            # Print new detections and log to CSV
            for det in detections:
                if det['new_detection'] and det['text']:
                    print(f"[NEW PLATE] {det['text']} (conf: {det['confidence']:.2f})")

            # Log to CSV (only new detections)
            if csv_logger and detections:
                new_detections = [d for d in detections if d['new_detection']]
                if new_detections:
                    logged = csv_logger.log_multiple(new_detections, frame_number=frame_count, source=source_type)

            # Show frame
            if not args.no_display:
                cv2.imshow("Simple ALPR", frame)

            # Save frame
            if writer:
                writer.write(frame)

            # Handle key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n[INFO] Quit requested")
                break
            elif key == ord('c'):
                detector.clear_cache()
                print("[INFO] Cache cleared")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")

    finally:
        # Cleanup
        if cap:
            cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()

        # Close CSV logger
        if csv_logger:
            csv_stats = csv_logger.get_stats()
            print(f"\n[CSV] CSV Logging Statistics:")
            print(f"  Log file: {csv_stats['log_file']}")
            print(f"  Total logged: {csv_stats['total_logged']}")
            print(f"  File size: {csv_stats['file_size_bytes']} bytes")
            csv_logger.close()

        # Print final stats
        cache_stats = detector.get_cache_stats()
        print(f"\n[STATS] Final statistics:")
        print(f"  Total frames: {frame_count}")
        print(f"  Cached plates: {cache_stats['cached_plates']}")
        print(f"  Cache size: {cache_stats['cache_size_bytes']} bytes")

if __name__ == "__main__":
    main()
