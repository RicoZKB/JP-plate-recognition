from csi_camera import get_csi_camera_preset

print("Testing CSI camera...")
cap = get_csi_camera_preset('fast')

if cap:
    ret, frame = cap.read()
    if ret:
        print(f"SUCCESS - Frame shape: {frame.shape}")
    else:
        print("FAILED - Could not read frame")
    cap.release()
else:
    print("FAILED - Could not open camera")
