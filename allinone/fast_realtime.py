# -*- coding: utf-8 -*-
# fast_realtime.py — Ultra-fast front-facing camera plate detection
# Optimized for: Cars approaching from front, no gate logic needed
# Strategy: Capture on first good detection, move on immediately
#
# Key optimizations:
# ✅ No gate/ROI logic - detect anywhere in frame
# ✅ No capture window - accept first valid plate
# ✅ No sharpness calculation - saves ~30% processing time
# ✅ Simple time-based deduplication (60 frames ~3 sec)
# ✅ Log and forget - no entry/exit tracking
# ✅ Super-resolution DISABLED by default (enable if quality needed)

import os, cv2, csv, re, time
from datetime import datetime
from detections import LicencePlateDetection
from collections import deque

# ===================== User settings =====================
USE_CAMERA               = True
USE_FILE                 = False
INPUT_VIDEO_PATH         = "input_videos/number.mp4"

# YouTube source (optional)
USE_YOUTUBE              = False
YOUTUBE_URL              = "https://www.youtube.com/watch?v=jqtsC5BYlIk"
YOUTUBE_MAX_HEIGHT       = 480

# Performance settings
TARGET_WIDTH             = 640    # Input resolution
DETECT_EVERY_N           = 1      # Process every frame (or throttle to 2-3 if too slow)
MAX_INFER_WIDTH          = 640    # Downscale for detection if wider

# Deduplication: Use time-based dedup (in seconds) instead of frame-based
# This handles variable frame rates and slow-moving traffic better
# Common values:
#   30 = 30 seconds (fast-moving traffic)
#   60 = 1 minute (normal traffic)
#   300 = 5 minutes (slow parking lot)
#   1800 = 30 minutes (long stay monitoring)
#   3600 = 1 hour
#   86400 = 1 day (24 hours)
DEDUP_WINDOW_SECONDS     = 60     # Ignore same plate for this many seconds

# Quality filter: Require minimum fields to log
REQUIRE_CITY_OR_CLASS    = True   # Must have city OR class_number (not just suffix)
MIN_CITY_LENGTH          = 2      # City name must be at least 2 chars (filters "D", "C", etc.)

# Sharpness filter (motion blur rejection)
USE_SHARPNESS_FILTER     = False   # Reject blurry plates
MIN_SHARPNESS_THRESHOLD  = 60.0   # Laplacian variance threshold (higher = sharper)
                                  # 60 = good quality, 40 = acceptable, 20 = very lenient

# Super-resolution (DISABLED by default for speed)
USE_SUPER_RESOLUTION     = False  # Enable only if quality is poor

# Display settings
WRITE_VIDEO              = True
DRAW_BBOXES              = True
SHOW_FPS                 = True
BOX_THICK                = 2

# Plate validation
PLATE_SUFFIX_RE          = re.compile(r"(\d{2,3})\s*[-−–—ーｰ~〜－]\s*(\d{2})")
# =========================================================

# Reduce OpenCV overhead
cv2.setUseOptimized(True)
os.environ.setdefault("OPENCV_LOG_LEVEL", "SILENT")
os.environ.setdefault("FLAGS_minloglevel", "2")

def _resolve_youtube_opencv_url(url: str, max_height: int = 480) -> str:
    """Return a direct progressive HTTP URL suitable for OpenCV from a YouTube link."""
    try:
        import yt_dlp
    except Exception:
        print("[WARN] yt-dlp not installed. pip install yt-dlp to use YouTube input.")
        return None

    fmt = f"best[acodec!=none][vcodec!=none][ext=mp4][height<={max_height}]/best[acodec!=none][vcodec!=none][ext=mp4]/best[acodec!=none][vcodec!=none]"
    ydl_opts = {'quiet': True, 'no_warnings': True, 'format': fmt, 'noplaylist': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                return info['url']
            fmt_id = info.get('format_id')
            fmts = info.get('formats') or []
            for f in fmts:
                if f.get('format_id') == fmt_id and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    return f.get('url')
            for f in fmts:
                if (f.get('acodec') != 'none' and f.get('vcodec') != 'none' and
                    (f.get('protocol','').startswith('http'))):
                    return f.get('url')
    except Exception as e:
        print('[WARN] yt-dlp extraction failed:', e)
    return None

# ===================== OCR parsing utilities =====================
CITY_KANA_RE = re.compile(u"^\\s*([^\\s\\d]+)\\s*[0-9]{2,4}.*?([ぁ-ゖァ-ヿA-Za-z])", re.UNICODE)
REGION_WITH_NUM_RE = re.compile(u"([ぁ-ゖァ-ヿ一-龯A-Za-z]+)\\s*([0-9]{2,4})", re.UNICODE)

def normalize_ocr_text(text: str) -> str:
    if not text:
        return ""
    # Convert full-width digits to ASCII
    fw_digits = "０１２３４５６７８９"
    ascii_digits = "0123456789"
    trans = str.maketrans({fw: ascii for fw, ascii in zip(fw_digits, ascii_digits)})
    t = text.translate(trans)
    # Normalize hyphen-like characters
    t = re.sub(r"[−–—ーｰ~〜－]", "-", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t

def plate_suffix(text):
    """Extract normalized suffix like '70-50' from OCR text."""
    if not text:
        return None
    t = normalize_ocr_text(text)
    m = PLATE_SUFFIX_RE.search(t)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"

def parse_plate_fields(text):
    """Extract (city, class_number, kana, suffix) from OCR text."""
    if not text:
        return None, None, None, None

    t = normalize_ocr_text(text)
    suf = plate_suffix(t)

    # City and class number
    city = None
    class_number = None
    m = REGION_WITH_NUM_RE.search(t)
    if m:
        city = m.group(1)
        class_number = m.group(2)

    # Kana: last kana character
    kana = None
    kana_matches = re.findall(u"[ぁ-ゖァ-ヿ]", t)
    if kana_matches:
        kana = kana_matches[-1]

    return city, class_number, kana, suf

def make_plate_key(city, suffix):
    """Create unique key for deduplication.
    Uses suffix-only for dedup to handle OCR errors on city names.
    Same suffix = same plate, even if city is read differently each time.
    """
    if suffix:
        return f"{suffix}"  # Use suffix only for reliable deduplication
    return None

def variance_of_laplacian(img):
    """Calculate sharpness using Laplacian variance.
    Higher values = sharper image, lower values = more blurry.
    Typical values: >100 very sharp, 60-100 good, 40-60 acceptable, <40 blurry
    """
    if img is None or img.size == 0:
        return 0.0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

def is_valid_plate(city, class_number, kana, suffix):
    """Check if plate meets minimum quality requirements."""
    # Must have suffix
    if not suffix:
        return False

    # If quality filter enabled, must have city OR class_number
    if REQUIRE_CITY_OR_CLASS:
        has_city = city and len(city) >= MIN_CITY_LENGTH
        has_class = class_number and len(class_number) >= 2
        if not (has_city or has_class):
            return False

    return True

def open_daily_csv():
    """Open daily CSV for logging plates."""
    date_str = datetime.now().strftime("%Y%m%d")
    os.makedirs("logs", exist_ok=True)
    path = os.path.join("logs", f"plates_fast_{date_str}.csv")
    new = not os.path.exists(path)
    f = open(path, "a", newline="", encoding="utf-8", buffering=1)
    w = csv.writer(f)
    if new:
        w.writerow(["timestamp", "object_id", "vehicle_type", "direction", "city", "class_number", "kana", "suffix"])
        f.flush()
    return f, w, path

def write_row_flush(w, f, row):
    """Write CSV row and flush immediately."""
    w.writerow(row)
    f.flush()
    try:
        os.fsync(f.fileno())
    except Exception:
        pass

def xyxy_from_det(det):
    """Extract bounding box coordinates from detection."""
    if isinstance(det, (list, tuple)) and len(det) >= 4:
        return float(det[0]), float(det[1]), float(det[2]), float(det[3])
    if isinstance(det, dict):
        box = det.get("bbox") or det.get("xyxy")
        if box and len(box) >= 4:
            return float(box[0]), float(box[1]), float(box[2]), float(box[3])
    return None

def center_from_det(det):
    """Get center point of detection."""
    xy = xyxy_from_det(det)
    if not xy:
        return None, None
    x1, y1, x2, y2 = xy
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0

def draw_lp_boxes(frame, dets, color=(0, 255, 0)):
    """Draw bounding boxes for license plates."""
    for d in dets:
        xy = xyxy_from_det(d)
        if not xy:
            continue
        x1, y1, x2, y2 = map(int, xy)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, BOX_THICK)

# ===================== Main loop =====================
def main():
    # Choose source
    chosen = [name for name, val in [("Camera", USE_CAMERA), ("YouTube", USE_YOUTUBE), ("File", USE_FILE)] if val]
    if len(chosen) != 1:
        raise RuntimeError("Exactly one of USE_CAMERA, USE_YOUTUBE, USE_FILE must be True.")

    source_name = chosen[0]
    if source_name == "Camera":
        src = 0
    elif source_name == "YouTube":
        print("[INFO] Resolving YouTube URL...", YOUTUBE_URL)
        src = _resolve_youtube_opencv_url(YOUTUBE_URL, max_height=YOUTUBE_MAX_HEIGHT)
        if not src:
            raise RuntimeError("Failed to resolve YouTube stream.")
        print("[INFO] Using YouTube stream")
    else:
        src = INPUT_VIDEO_PATH
        if not os.path.exists(src):
            raise RuntimeError(f"Input file not found: {src}")

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {src}")

    using_camera = (source_name == "Camera")
    if using_camera:
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except:
            pass

    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_WIDTH)
    except:
        pass

    # Initialize detector
    print(f"[INFO] Initializing detector (super-res={'ON' if USE_SUPER_RESOLUTION else 'OFF'})...")
    lp_det = LicencePlateDetection(
        model_path="models/best.pt",
        verbose=using_camera,
        debug_ocr=False
    )

    # Video writer
    os.makedirs("output_videos", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or TARGET_WIDTH)
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or int(TARGET_WIDTH * 3 / 5))
    out = cv2.VideoWriter("output_videos/fast_output.avi", fourcc, fps, (W, H)) if WRITE_VIDEO else None

    # CSV logging
    csv_file, csv_writer, csv_path = open_daily_csv()
    print(f"[INFO] Logging to: {csv_path}")
    print(f"[INFO] Mode: Fast Real-time (front-facing)")
    print(f"[INFO] Dedup window: {DEDUP_WINDOW_SECONDS} seconds")
    print(f"[INFO] Quality filter: {'ON' if REQUIRE_CITY_OR_CLASS else 'OFF'} (min city length: {MIN_CITY_LENGTH})")
    print(f"[INFO] Sharpness filter: {'ON' if USE_SHARPNESS_FILTER else 'OFF'} (threshold: {MIN_SHARPNESS_THRESHOLD if USE_SHARPNESS_FILTER else 'N/A'})")
    print(f"[INFO] Super-resolution: {'ON' if USE_SUPER_RESOLUTION else 'OFF'}")

    # Time-based deduplication: track plate_key -> last_seen_timestamp
    recent_plates = {}  # {plate_key: timestamp}

    # Sequential object ID counter (format: 01, 02, 03, ...)
    object_id_counter = 1

    # FPS tracking
    frame_idx = 0
    t0 = time.time()
    fcount = 0
    fps_est = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame_idx += 1
            fcount += 1

            # Skip frames if throttled
            if frame_idx % DETECT_EVERY_N != 0:
                # Still show frame for smooth video
                if WRITE_VIDEO and out is not None:
                    out.write(frame)
                cv2.imshow("Fast Real-time Detection", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                continue

            # Downscale if needed for faster detection
            detect_frame = frame
            scale = 1.0
            if W > MAX_INFER_WIDTH:
                scale = MAX_INFER_WIDTH / float(W)
                new_w = int(W * scale)
                new_h = int(H * scale)
                detect_frame = cv2.resize(frame, (new_w, new_h))

            # Detect plates (single batch call)
            all_dets, all_texts = lp_det.detect_frames([detect_frame])
            lp_dets = all_dets[0]
            lp_texts = all_texts[0]

            # Scale boxes back to original if needed
            if scale != 1.0:
                inv_scale = 1.0 / scale
                for i, det in enumerate(lp_dets):
                    xy = xyxy_from_det(det)
                    if xy:
                        x1, y1, x2, y2 = xy
                        x1, y1, x2, y2 = x1 * inv_scale, y1 * inv_scale, x2 * inv_scale, y2 * inv_scale
                        if isinstance(det, dict):
                            if "bbox" in det:
                                det["bbox"] = [x1, y1, x2, y2]
                            else:
                                det["xyxy"] = [x1, y1, x2, y2]
                        elif isinstance(det, (list, tuple)):
                            lp_dets[i] = [x1, y1, x2, y2]

            # Process detections
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            now = time.time()

            # Clean up old entries from dedup dict (older than window)
            cutoff_time = now - DEDUP_WINDOW_SECONDS
            recent_plates = {k: v for k, v in recent_plates.items() if v >= cutoff_time}

            for det, text in zip(lp_dets, lp_texts):
                if not text:
                    continue

                # Parse fields
                city, class_number, kana, suf = parse_plate_fields(text)

                # Quality filter: must meet minimum requirements
                if not is_valid_plate(city, class_number, kana, suf):
                    # Draw box but mark as rejected
                    if DRAW_BBOXES:
                        cx, cy = center_from_det(det)
                        if cx and cy:
                            reason = "no-suffix" if not suf else "low-quality"
                            cv2.putText(frame, f"({reason})", (int(cx) - 40, int(cy)),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 2, cv2.LINE_AA)
                    continue

                # Sharpness filter: reject blurry plates (motion blur)
                if USE_SHARPNESS_FILTER:
                    xy = xyxy_from_det(det)
                    if xy:
                        x1, y1, x2, y2 = map(int, xy)
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(W, x2), min(H, y2)
                        plate_img = frame[y1:y2, x1:x2]

                        if plate_img.size > 0:
                            sharpness = variance_of_laplacian(plate_img)

                            if sharpness < MIN_SHARPNESS_THRESHOLD:
                                # Reject blurry plate
                                if DRAW_BBOXES:
                                    cx, cy = center_from_det(det)
                                    if cx and cy:
                                        cv2.putText(frame, f"blur:{sharpness:.1f}", (int(cx) - 40, int(cy)),
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 128, 255), 2, cv2.LINE_AA)
                                continue

                # Create unique key for deduplication
                plate_key = make_plate_key(city, suf)
                if not plate_key:
                    continue

                # Deduplication: skip if seen recently
                if plate_key in recent_plates:
                    time_since = now - recent_plates[plate_key]
                    # Still draw box but mark as duplicate
                    if DRAW_BBOXES:
                        cx, cy = center_from_det(det)
                        if cx and cy:
                            cv2.putText(frame, f"{suf} (seen {int(time_since)}s ago)", (int(cx) - 50, int(cy)),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 2, cv2.LINE_AA)
                    continue

                # NEW PLATE - Log it!
                object_id_str = f"{object_id_counter:02d}"  # Format as 01, 02, 03, etc.
                write_row_flush(csv_writer, csv_file,
                              [ts, object_id_str, "car", "in", city or "", class_number or "", kana or "", suf or ""])

                # Increment object ID for next plate
                object_id_counter += 1

                # Record timestamp for dedup
                recent_plates[plate_key] = now

                # Calculate sharpness for display/logging
                sharpness_display = ""
                if USE_SHARPNESS_FILTER:
                    xy = xyxy_from_det(det)
                    if xy:
                        x1, y1, x2, y2 = map(int, xy)
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(W, x2), min(H, y2)
                        plate_img = frame[y1:y2, x1:x2]
                        if plate_img.size > 0:
                            sharp = variance_of_laplacian(plate_img)
                            sharpness_display = f" | sharp:{sharp:.1f}"

                # Draw with "NEW" indicator
                if DRAW_BBOXES:
                    cx, cy = center_from_det(det)
                    if cx and cy:
                        display = f"{object_id_str}: {city}:{suf}" if city else f"{object_id_str}: {suf}"
                        cv2.putText(frame, f"IN {display}", (int(cx) - 60, int(cy)),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

                print(f"[LOG] {ts} | ID:{object_id_str} | {city or '?'} {class_number or '?'} {kana or '?'} {suf}{sharpness_display}")

            # Draw all boxes
            if DRAW_BBOXES:
                draw_lp_boxes(frame, lp_dets, color=(0, 255, 0))

            # FPS overlay
            if SHOW_FPS:
                now = time.time()
                if now - t0 >= 0.5:
                    fps_est = fcount / (now - t0)
                    t0 = now
                    fcount = 0

                cv2.putText(frame, f"FPS: {fps_est:.1f}", (10, 24),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, f"Mode: Fast Real-time | Source: {source_name}", (10, 48),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 255, 180), 2, cv2.LINE_AA)
                cv2.putText(frame, f"Super-res: {'ON' if USE_SUPER_RESOLUTION else 'OFF'} | Tracked: {len(recent_plates)} | Dedup: {DEDUP_WINDOW_SECONDS}s", (10, 68),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 220, 255), 2, cv2.LINE_AA)

            # Display
            cv2.imshow("Fast Real-time Detection", frame)
            if WRITE_VIDEO and out is not None:
                out.write(frame)

            # ESC to quit
            if cv2.waitKey(1) & 0xFF == 27:
                break

    finally:
        try:
            cap.release()
        except:
            pass
        try:
            if WRITE_VIDEO and out is not None:
                out.release()
        except:
            pass
        cv2.destroyAllWindows()
        csv_file.close()
        print(f"[INFO] CSV saved to {csv_path}")
        if WRITE_VIDEO:
            print("[INFO] Video saved to output_videos/fast_output.avi")

if __name__ == "__main__":
    main()
