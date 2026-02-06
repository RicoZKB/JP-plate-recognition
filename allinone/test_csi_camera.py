"""
Test script for CSI Camera with License Plate Detection
Demonstrates integration of IMX477 12MP Arducam with YOLO detection
"""

import cv2
import time
from csi_camera import get_csi_camera_preset, gstreamer_pipeline


def test_basic_capture():
    """Test basic CSI camera capture"""
    print("\n=== Test 1: Basic Camera Capture ===")

    cap = get_csi_camera_preset("balanced", flip_method=0)

    if cap is None:
        print("Failed to open camera")
        return False

    print("Reading 10 frames...")
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            print(f"Frame {i+1}: {frame.shape}")
        else:
            print(f"Frame {i+1}: Failed to read")

    cap.release()
    print("✓ Basic capture test passed\n")
    return True


def test_fps_measurement():
    """Test FPS measurement"""
    print("\n=== Test 2: FPS Measurement ===")

    # Test different presets
    for preset in ["fast", "balanced", "high_res"]:
        print(f"\nTesting preset: {preset}")
        cap = get_csi_camera_preset(preset, flip_method=0)

        if cap is None:
            continue

        # Warm up
        for _ in range(10):
            cap.read()

        # Measure FPS
        num_frames = 100
        start_time = time.time()

        for _ in range(num_frames):
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break

        elapsed = time.time() - start_time
        fps = num_frames / elapsed

        print(f"  → FPS: {fps:.2f} ({num_frames} frames in {elapsed:.2f}s)")

        cap.release()

    print("\n✓ FPS measurement test completed\n")
    return True


def test_resolution_info():
    """Test resolution and camera info"""
    print("\n=== Test 3: Resolution Info ===")

    cap = get_csi_camera_preset("balanced", flip_method=0)

    if cap is None:
        return False

    ret, frame = cap.read()
    if ret:
        print(f"Frame shape: {frame.shape}")
        print(f"Resolution: {frame.shape[1]}x{frame.shape[0]}")
        print(f"Channels: {frame.shape[2]}")
        print(f"Dtype: {frame.dtype}")

    cap.release()
    print("✓ Resolution info test passed\n")
    return True


def test_display_with_info():
    """Test live display with frame info overlay"""
    print("\n=== Test 4: Live Display with Info ===")
    print("Press 'q' to quit, '1/2/3' to switch presets")

    current_preset = "balanced"
    cap = get_csi_camera_preset(current_preset, flip_method=0)

    if cap is None:
        return False

    window_name = "CSI Camera Test"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    fps_counter = 0
    fps_start_time = time.time()
    current_fps = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break

            # Calculate FPS
            fps_counter += 1
            if fps_counter >= 30:
                elapsed = time.time() - fps_start_time
                current_fps = fps_counter / elapsed
                fps_counter = 0
                fps_start_time = time.time()

            # Add info overlay
            info_y = 30
            cv2.putText(frame, f"Preset: {current_preset}", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            info_y += 30
            cv2.putText(frame, f"Resolution: {frame.shape[1]}x{frame.shape[0]}", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            info_y += 30
            cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            info_y += 30
            cv2.putText(frame, "Press 1:fast 2:balanced 3:high_res q:quit", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:
                break
            elif key == ord('1'):
                cap.release()
                current_preset = "fast"
                cap = get_csi_camera_preset(current_preset, flip_method=0)
                fps_counter = 0
                fps_start_time = time.time()
            elif key == ord('2'):
                cap.release()
                current_preset = "balanced"
                cap = get_csi_camera_preset(current_preset, flip_method=0)
                fps_counter = 0
                fps_start_time = time.time()
            elif key == ord('3'):
                cap.release()
                current_preset = "high_res"
                cap = get_csi_camera_preset(current_preset, flip_method=0)
                fps_counter = 0
                fps_start_time = time.time()

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print("✓ Display test completed\n")
    return True


def test_custom_pipeline():
    """Test custom GStreamer pipeline"""
    print("\n=== Test 5: Custom Pipeline ===")

    # Create custom pipeline for specific needs
    pipeline = gstreamer_pipeline(
        sensor_id=0,
        capture_width=1920,
        capture_height=1080,
        display_width=1280,
        display_height=720,
        framerate=30,
        flip_method=0
    )

    print(f"Custom pipeline:\n{pipeline}\n")

    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Custom pipeline works! Frame: {frame.shape}")
        cap.release()
        return True
    else:
        print("✗ Custom pipeline failed")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CSI Camera Integration Test")
    print("IMX477 12MP Arducam for Jetson")
    print("=" * 60)

    tests = [
        ("Basic Capture", test_basic_capture),
        ("FPS Measurement", test_fps_measurement),
        ("Resolution Info", test_resolution_info),
        ("Custom Pipeline", test_custom_pipeline),
        ("Live Display", test_display_with_info),  # Run this last as it's interactive
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with error: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    print("=" * 60)
