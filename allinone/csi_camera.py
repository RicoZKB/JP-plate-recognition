"""
CSI Camera Utility for Jetson with IMX477 12MP Arducam
Based on JetsonHacks CSI-Camera implementation
Optimized for license plate detection with high resolution capture

MIT License
Reference: https://github.com/JetsonHacksNano/CSI-Camera
"""

import cv2


def gstreamer_pipeline(
    sensor_id=0,
    capture_width=3840,
    capture_height=2160,
    display_width=1920,
    display_height=1080,
    framerate=21,
    flip_method=0,
):
    """
    Generate GStreamer pipeline for IMX477 12MP Arducam CSI camera

    Args:
        sensor_id: Camera sensor ID (0 or 1 for dual camera setups)
        capture_width: Width of camera capture (IMX477 supports up to 4032)
        capture_height: Height of camera capture (IMX477 supports up to 3040)
        display_width: Width of output frame
        display_height: Height of output frame
        framerate: Frame rate (depends on resolution - 4K@21fps, 1080p@60fps max)
        flip_method: Flip method (0=none, 1=ccw90, 2=180, 3=cw90, 4=horizontal, 5=up-right, 6=vertical, 7=up-left)

    Returns:
        GStreamer pipeline string for OpenCV VideoCapture

    IMX477 Sensor Modes:
        - 4032x3040 @ 10fps (Mode 0) - Full 12MP
        - 3840x2160 @ 21fps (Mode 1) - 4K
        - 1920x1080 @ 60fps (Mode 2) - 1080p
    """
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


def get_csi_camera(
    sensor_id=0,
    capture_width=3840,
    capture_height=2160,
    display_width=1920,
    display_height=1080,
    framerate=21,
    flip_method=0,
):
    """
    Open CSI camera with GStreamer pipeline

    Returns:
        cv2.VideoCapture object or None if failed
    """
    pipeline = gstreamer_pipeline(
        sensor_id=sensor_id,
        capture_width=capture_width,
        capture_height=capture_height,
        display_width=display_width,
        display_height=display_height,
        framerate=framerate,
        flip_method=flip_method,
    )

    print(f"GStreamer Pipeline: {pipeline}")
    video_capture = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if video_capture.isOpened():
        print(f"✓ CSI Camera opened successfully (sensor_id={sensor_id})")
        return video_capture
    else:
        print(f"✗ Error: Unable to open CSI camera (sensor_id={sensor_id})")
        return None


# Preset configurations for common use cases
PRESETS = {
    "high_res": {  # Best quality for license plate detection
        "capture_width": 3840,
        "capture_height": 2160,
        "display_width": 1920,
        "display_height": 1080,
        "framerate": 21,
    },
    "balanced": {  # Good balance between quality and speed
        "capture_width": 1920,
        "capture_height": 1080,
        "display_width": 1920,
        "display_height": 1080,
        "framerate": 60,
    },
    "fast": {  # Maximum speed for real-time processing
        "capture_width": 1280,
        "capture_height": 720,
        "display_width": 1280,
        "display_height": 720,
        "framerate": 60,
    },
}


def get_csi_camera_preset(preset="balanced", sensor_id=0, flip_method=0):
    """
    Open CSI camera with preset configuration

    Args:
        preset: "high_res", "balanced", or "fast"
        sensor_id: Camera sensor ID
        flip_method: Flip method

    Returns:
        cv2.VideoCapture object or None if failed
    """
    if preset not in PRESETS:
        print(f"Warning: Unknown preset '{preset}', using 'balanced'")
        preset = "balanced"

    config = PRESETS[preset]
    print(f"Using preset: {preset}")

    return get_csi_camera(
        sensor_id=sensor_id,
        flip_method=flip_method,
        **config
    )


def test_camera():
    """
    Test CSI camera capture and display
    """
    window_title = "CSI Camera - IMX477 12MP Arducam"

    # Try balanced preset first
    video_capture = get_csi_camera_preset("balanced", flip_method=0)

    if video_capture is None:
        return

    try:
        cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
        print("Press 'q' or ESC to quit")

        while True:
            ret_val, frame = video_capture.read()

            if not ret_val:
                print("Error: Failed to capture frame")
                break

            # Display frame info
            cv2.putText(
                frame,
                f"Resolution: {frame.shape[1]}x{frame.shape[0]}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            # Check if window is closed
            if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                cv2.imshow(window_title, frame)
            else:
                break

            keyCode = cv2.waitKey(10) & 0xFF
            # Stop on ESC key or 'q'
            if keyCode == 27 or keyCode == ord('q'):
                break

    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        print("Camera released")


if __name__ == "__main__":
    print("=" * 60)
    print("CSI Camera Test - IMX477 12MP Arducam")
    print("=" * 60)
    test_camera()
