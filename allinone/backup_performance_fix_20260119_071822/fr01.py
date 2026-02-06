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

# Suppress harmless numpy warnings on Jetson Nano (ARM architecture)
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='numpy')

import os, cv2, csv, re, time
from datetime import datetime
from detections import LicencePlateDetection  # Most reliable overall
from collections import deque

# ===================== User settings =====================
USE_CAMERA               = True
USE_FILE                 = False
INPUT_VIDEO_PATH         = "input_videos/Trim20.mp4"

# YouTube source (optional)
USE_YOUTUBE              = False
YOUTUBE_URL              = "https://www.youtube.com/watch?v=jqtsC5BYlIk"
YOUTUBE_MAX_HEIGHT       = 480

# Performance settings
TARGET_WIDTH             = 640    # Input resolution
DETECT_EVERY_N           = 3      # Process every 3rd frame for stability
MAX_INFER_WIDTH          = 640    # Downscale for detection if wider

# Deduplication: Use time-based dedup (in seconds) instead of frame-based
# This handles variable frame rates and slow-moving traffic better
DEDUP_WINDOW_SECONDS     = 30     # Ignore same plate for 30 seconds

# Detector selection
USE_REGION_BASED_OCR     = False # True = Region-based (6× kana upscaling), False = Basic (faster)

# Quality filter: Require minimum fields to log
REQUIRE_CITY_OR_CLASS    = True   # Must have city OR class_number (not just suffix)
MIN_CITY_LENGTH          = 2      # City name must be at least 2 chars (filters "D", "C", etc.)

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

# Valid kana characters used on Japanese license plates
# Hiragana: All 41 hiragana used on JP plates - Excluded: お し へ を ん (to avoid confusion)
# Katakana: Common katakana equivalents that may appear on plates
VALID_PLATE_KANA = set(
    'あいうえかきくけこさすせそたちつてとなにぬねのはひふほまみむめもやゆよらりるれろわ'  # Hiragana
    'アイウエカキクケコサスセソタチツテトナニヌネノハヒフホマミムメモヤユヨラリルレロワ'  # Katakana
)

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

def clean_kana(kana_raw):
    """Clean and validate kana using grammar rules (Fix 1 & 2 from ChatGPT).

    Args:
        kana_raw: Raw kana character from OCR

    Returns:
        Cleaned kana or None if invalid
    """
    if not kana_raw:
        return None

    # Fix 1: Grammar-based correction - Digits in kana position are OCR errors!
    # Common misreads: 0→ろ, 3→ろ, O→ろ, I→い, 1→い
    DIGIT_TO_KANA = {
        '0': 'ろ',  # Very common: ろ looks like 0
        '3': 'ろ',  # Common: ろ looks like 3
        'O': 'ろ',  # Latin O → ろ
        'I': 'い',  # Latin I → い
        '1': 'い',  # Digit 1 → い
    }

    if kana_raw in DIGIT_TO_KANA:
        corrected = DIGIT_TO_KANA[kana_raw]
        print(f"[KANA-GRAMMAR] Corrected '{kana_raw}' → '{corrected}' (digit in kana slot)")
        return corrected

    # Fix 2: Whitelist validation - Only allow legal plate hiragana
    if kana_raw in VALID_PLATE_KANA:
        return kana_raw

    # Invalid kana (katakana, romaji, etc.) - reject it
    print(f"[KANA-REJECT] Invalid kana '{kana_raw}' not in whitelist")
    return None

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
    kana_raw = None
    kana_matches = re.findall(u"[ぁ-ゖァ-ヿ]", t)
    if kana_matches:
        kana_raw = kana_matches[-1]

    # Also check for digits in kana position (common OCR error)
    if not kana_raw:
        # Look for lone digits that might be misread kana
        digit_matches = re.findall(r'\b([0-9OI])\b', t)
        if digit_matches:
            kana_raw = digit_matches[-1]

    # Clean and validate kana using grammar rules
    kana = clean_kana(kana_raw)

    return city, class_number, kana, suf

def validate_plate_data(city, class_number, kana, suffix):
    """
    Post-processing validation of plate data.
    Returns (is_valid, quality_score, error_reasons)
    """
    errors = []
    quality_score = 0

    # Valid Japanese regions (major cities/prefectures commonly seen on plates)
    VALID_REGIONS = {
        '山口', '山形', '山梨', '品川', '大阪', '東京', '横浜', '名古屋', '京都',
        '神戸', '福岡', '札幌', '仙台', '広島', '北九州', '川崎', '相模', '千葉',
        '埼玉', '多摩', '群馬', '栃木', '茨城', '静岡', '浜松', '岐阜', '三重',
        '滋賀', '奈良', '和歌山', '岡山', '鳥取', '島根', '山陰', '香川', '徳島',
        '愛媛', '高知', '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島', '沖縄',
        '富士山', '飛鳥', '伊勢志摩', '堺', '春日井', '鈴鹿', 'いわき', '山国', '山目'
    }

    # City validation
    if city:
        # Remove common OCR misreads
        city_clean = city.replace('1', '').replace('!', '').replace('」', '').replace('D', '').strip()

        # Check length (valid cities are usually 2-4 characters)
        if len(city_clean) >= 2 and len(city_clean) <= 4:
            quality_score += 3
            # Bonus if it's a known region
            if city_clean in VALID_REGIONS:
                quality_score += 2
        elif len(city_clean) < 2:
            errors.append(f"City too short: '{city}' (len={len(city_clean)})")
        elif len(city_clean) > 4:
            errors.append(f"City too long: '{city}' (len={len(city_clean)})")

        # Check for invalid characters (numbers, symbols)
        if re.search(r'[0-9]', city_clean):
            errors.append(f"City contains numbers: '{city}'")
            quality_score -= 1
    else:
        errors.append("City missing")

    # Class number validation
    if class_number:
        # Valid class numbers are typically 2-4 digits: 33, 330, 589, 599, etc.
        if re.match(r'^\d{2,4}$', class_number):
            quality_score += 2
        else:
            errors.append(f"Invalid class number format: '{class_number}'")
    else:
        # Class number is optional in some cases
        pass

    # Kana validation
    if kana:
        if kana in VALID_PLATE_KANA:
            quality_score += 2
        else:
            errors.append(f"Invalid kana: '{kana}'")
    else:
        # Kana missing is common, not a critical error
        errors.append("Kana missing")

    # Suffix validation (XX-YY format)
    if suffix:
        if re.match(r'^\d{2,3}[-−–—ーｰ~〜－]\d{2}$', suffix):
            quality_score += 1
        else:
            errors.append(f"Invalid suffix format: '{suffix}'")
    else:
        errors.append("Suffix missing")

    # Overall validation
    is_valid = quality_score >= 4 and len(errors) <= 2

    return is_valid, quality_score, errors

def make_plate_key(city, class_number, suffix):
    """Create unique key for deduplication.
    Uses class_number + normalized suffix (digits are more stable than city kanji).
    Falls back to city if no class_number.
    Normalizes class_number (strip trailing 0 from 4-digit: "5890" → "589")
    Normalizes suffix to last 5 chars (e.g., "320-46" → "20-46")
    """
    if not suffix:
        return None

    # Normalize suffix: take last 5 chars to handle OCR errors like "320-46" vs "20-46"
    normalized_suffix = suffix[-5:] if len(suffix) >= 5 else suffix

    # Prefer class_number (digits = stable) over city (kanji = unstable OCR)
    # This prevents duplicates from city misreads: "多摩" vs "零摩", "品川" vs "S川"
    if class_number and len(class_number) >= 2:
        # Normalize class_number: remove trailing "0" if 4 digits
        # Japanese plates have 3-digit class numbers; 4th digit is usually misread kana "ろ"
        # Examples: "5890" → "589", "5990" → "599" (prevents duplicates)
        normalized_class = class_number
        if len(class_number) == 4 and class_number.endswith('0'):
            normalized_class = class_number[:3]  # Strip trailing 0
        return f"{normalized_class}_{normalized_suffix}"

    # Fallback to city if no class_number
    city_part = city[:2] if city and len(city) >= 2 else (city if city else "?")
    return f"{city_part}_{normalized_suffix}"

def is_valid_plate(city, class_number, kana, suffix):
    """Check if plate meets minimum quality requirements."""
    # Must have suffix
    if not suffix:
        return False

    # Reject partial city names (if city exists but too short, it's a partial OCR result)
    if city and len(city) < MIN_CITY_LENGTH:
        return False  # Reject "摩", "品", "号" - wait for full "多摩", "品川", etc.

    # If quality filter enabled, must have city OR class_number
    if REQUIRE_CITY_OR_CLASS:
        has_city = city and len(city) >= MIN_CITY_LENGTH
        has_class = class_number and len(class_number) >= 2
        if not (has_city or has_class):
            return False

    return True

def count_filled_fields(city, class_number, kana, suffix):
    """Count how many fields are filled (higher = better detection)."""
    score = 0
    if city and len(city) >= MIN_CITY_LENGTH:
        score += 2  # City is important
    if class_number and len(class_number) >= 2:
        score += 2  # Class number is important
    if kana:
        score += 3  # Kana is MOST important (often missing)
    if suffix:
        score += 1  # Suffix is baseline (always required)
    return score

def open_daily_csv():
    """Open daily CSV for logging plates with proper date/time formatting."""
    date_str = datetime.now().strftime("%Y%m%d")
    os.makedirs("logs", exist_ok=True)
    path = os.path.join("logs", f"parking_log_{date_str}.csv")
    new = not os.path.exists(path)
    f = open(path, "a", newline="", encoding="utf-8", buffering=1)
    w = csv.writer(f)
    if new:
        # CSV Header: Match old format
        w.writerow(["timestamp", "object_id", "vehicle_type", "direction",
                   "city", "engine_size", "kana", "four-digit number"])
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

# ===================== Image Preprocessing =====================
def preprocess_for_detection(frame):
    """
    Preprocess frame before YOLO detection for better accuracy.
    Applies contrast enhancement and sharpening while maintaining speed.
    """
    # Convert to LAB color space for better contrast enhancement
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L-channel (brightness)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    # Merge back
    enhanced_lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # Subtle sharpening (avoid over-sharpening which can hurt detection)
    gaussian = cv2.GaussianBlur(enhanced, (0, 0), 1.0)
    sharpened = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)

    return sharpened

# ===================== Kana Retry System =====================
def save_plate_for_retry(crop, plate_id, city, class_number, suffix):
    """Save plate image without kana for retry OCR."""
    try:
        os.makedirs("retry_queue", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"retry_queue/plate_{plate_id}_{timestamp}.jpg"
        cv2.imwrite(filename, crop)

        # Save metadata for later CSV update
        meta_file = filename.replace(".jpg", ".txt")
        with open(meta_file, "w", encoding="utf-8") as mf:
            mf.write(f"{plate_id}|{city}|{class_number}|{suffix}\n")

        return filename
    except Exception as e:
        print(f"[WARN] Failed to save retry image: {e}")
        return None

def retry_kana_ocr(image_path, ocr_detector):
    """Retry kana detection with LIGHTWEIGHT preprocessing (1 strategy only to avoid FPS drop)."""
    try:
        # Load saved image
        img = cv2.imread(image_path)
        if img is None:
            return None

        # SINGLE STRATEGY: Extreme CLAHE + Unsharp mask (best for tiny kana)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        blur = cv2.GaussianBlur(enhanced, (0, 0), 1.5)
        sharp = cv2.addWeighted(enhanced, 2.0, blur, -1.0, 0)
        upscaled = cv2.resize(sharp, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        prep = cv2.cvtColor(upscaled, cv2.COLOR_GRAY2BGR)

        # Use PaddleOCR .ocr() method (not .predict())
        result = ocr_detector.ocr(prep, cls=False)

        # Extract text from OCR result
        text = ""
        if result and isinstance(result, list):
            if len(result) == 1 and isinstance(result[0], list):
                result = result[0]
            for item in result:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    if isinstance(item[1], (list, tuple)) and len(item[1]) >= 1:
                        text += str(item[1][0]) + " "

        text = normalize_ocr_text(text)
        _, _, kana, _ = parse_plate_fields(text)

        return kana if kana else None
    except Exception as e:
        print(f"[WARN] Retry OCR failed: {e}")
        return None

def append_kana_correction(csv_path, plate_id, kana):
    """Append kana correction to CSV as a note/update row."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            # Write correction row with special marker
            w.writerow([timestamp, f"{plate_id}_KANA_FIX", "correction", "", "", "", kana, f"Retry OCR found kana for ID:{plate_id}"])
            f.flush()

        # Print formatted kana correction
        print("-" * 80)
        print(f"✓ KANA CORRECTION FOUND")
        print("-" * 80)
        print(f"  Timestamp:      {timestamp}")
        print(f"  Original ID:    {plate_id}")
        print(f"  Found Kana:     {kana}")
        print(f"  Status:         Appended to CSV")
        print("-" * 80)
        print()

        return True
    except Exception as e:
        print(f"[WARN] Failed to append correction: {e}")
        return False

# =============================================================

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

# ===================== GStreamer CSI Camera Pipeline =====================
def get_csi_camera_pipeline(sensor_id=0, capture_width=3840, capture_height=2160,
                            display_width=640, display_height=480, framerate=30, flip_method=0):
    """
    Create GStreamer pipeline for IMX477 CSI camera (12MP ArduCam)

    Args:
        sensor_id: Camera sensor ID (0 or 1)
        capture_width: Native sensor width (IMX477: 3840 for 4K, 1920 for 1080p)
        capture_height: Native sensor height (IMX477: 2160 for 4K, 1080 for 1080p)
        display_width: Output width for processing
        display_height: Output height for processing
        framerate: Camera framerate
        flip_method: Image flip (0=none, 2=rotate-180)

    Returns:
        GStreamer pipeline string
    """
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width=(int){capture_width}, height=(int){capture_height}, "
        f"format=(string)NV12, framerate=(fraction){framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! "
        f"videoconvert ! "
        f"video/x-raw, format=(string)BGR ! "
        f"queue max-size-buffers=2 leaky=downstream ! "
        f"appsink emit-signals=true sync=false max-buffers=2 drop=true"
    )

# ===================== Main loop =====================
def main():
    # Choose source
    chosen = [name for name, val in [("Camera", USE_CAMERA), ("YouTube", USE_YOUTUBE), ("File", USE_FILE)] if val]
    if len(chosen) != 1:
        raise RuntimeError("Exactly one of USE_CAMERA, USE_YOUTUBE, USE_FILE must be True.")

    source_name = chosen[0]
    if source_name == "Camera":
        # Use GStreamer pipeline for CSI camera (IMX477 12MP ArduCam)
        print("[INFO] Initializing CSI camera with GStreamer pipeline...")
        print("[INFO] Camera: IMX477 12MP ArduCam")

        # IMX477 optimal settings for license plate detection
        # Using 1920x1080 @ 30fps (native supported mode for best performance)
        gst_pipeline = get_csi_camera_pipeline(
            sensor_id=0,
            capture_width=1920,      # 1080p capture (native supported mode)
            capture_height=1080,
            display_width=TARGET_WIDTH,
            display_height=int(TARGET_WIDTH * 9 / 16),  # 16:9 aspect ratio
            framerate=30,            # 30 FPS (native supported framerate)
            flip_method=0            # Change to 2 if camera is upside down
        )
        src = gst_pipeline
        print(f"[INFO] GStreamer pipeline: {src}")
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

    cap = cv2.VideoCapture(src, cv2.CAP_GSTREAMER) if source_name == "Camera" else cv2.VideoCapture(src)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {src}")

    using_camera = (source_name == "Camera")
    if using_camera:
        # CSI camera with GStreamer doesn't need additional settings
        # Resolution and format already set in pipeline
        print("[INFO] CSI camera initialized successfully")
    else:
        # For file/YouTube sources, set resolution
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_WIDTH)
        except:
            pass

    # Initialize detector with TensorRT FP16 engine (GPU accelerated)
    print(f"[INFO] Initializing license plate detector with TensorRT engine...")
    lp_det = LicencePlateDetection(
        model_path="models/best_2026.engine",
        verbose=using_camera,
        debug_ocr=False
    )

    # Video writer - create unique filename with timestamp for each run
    os.makedirs("output_videos", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or TARGET_WIDTH)
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or int(TARGET_WIDTH * 3 / 5))

    # Generate unique filename with date and time
    video_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"output_videos/fast_output_{video_timestamp}.avi"
    out = cv2.VideoWriter(video_filename, fourcc, fps, (W, H)) if WRITE_VIDEO else None

    # CSV logging
    csv_file, csv_writer, csv_path = open_daily_csv()

    # Print startup information
    print("\n" + "=" * 80)
    print("LICENSE PLATE DETECTION SYSTEM - STARTUP")
    print("=" * 80)
    print(f"  CSV Log File:       {csv_path}")
    if WRITE_VIDEO:
        print(f"  Video Output:       {video_filename}")
    print(f"  CSV Format:         timestamp | object_id | vehicle_type | direction |")
    print(f"                      city | class_number | kana | suffix")
    print(f"  Mode:               Fast Real-time (front-facing)")
    print(f"  Dedup Window:       {DEDUP_WINDOW_SECONDS} seconds")
    print(f"  Quality Filter:     {'ON' if REQUIRE_CITY_OR_CLASS else 'OFF'} (min city length: {MIN_CITY_LENGTH})")
    print(f"  Collection Window:  6 seconds (best detection)")
    print(f"  Video Recording:    {'ON' if WRITE_VIDEO else 'OFF'}")
    print("=" * 80)
    print()

    # Time-based deduplication: track plate_key -> last_seen_timestamp
    recent_plates = {}  # {plate_key: timestamp}

    # Position-based tracking: track plate positions to handle OCR variations
    recent_positions = {}  # {position_key: {'plate_key': str, 'timestamp': float, 'bbox': tuple}}
    POSITION_THRESHOLD = 100  # pixels: plates within this distance are considered same vehicle

    # Best detection collector: Wait 6 seconds, collect all detections, log the best one
    pending_plates = {}  # {plate_key: {'first_seen': timestamp, 'best': (city, class_number, kana, suffix, score), 'det': detection}}
    PENDING_WINDOW = 6.0  # Collect detections for 3 seconds before logging (realistic for parking barriers)

    # Sequential object ID counter (format: 01, 02, 03, ...)
    object_id_counter = 1

    def bbox_distance(bbox1, bbox2):
        """Calculate distance between two bounding boxes (center points)."""
        x1_c = (bbox1[0] + bbox1[2]) / 2
        y1_c = (bbox1[1] + bbox1[3]) / 2
        x2_c = (bbox2[0] + bbox2[2]) / 2
        y2_c = (bbox2[1] + bbox2[3]) / 2
        return ((x1_c - x2_c)**2 + (y1_c - y2_c)**2)**0.5

    def find_matching_position(bbox, recent_positions, threshold):
        """Find if this bbox matches any recently seen position."""
        for pos_key, pos_data in recent_positions.items():
            cached_bbox = pos_data['bbox']
            distance = bbox_distance(bbox, cached_bbox)
            if distance < threshold:
                return pos_data['plate_key']  # Return the plate_key from this position
        return None

    # Kana retry system (LIGHTWEIGHT: runs rarely to avoid FPS drop)
    last_retry_check = time.time()
    RETRY_CHECK_INTERVAL = 120.0  # Process retry queue every 2 minutes (reduces blocking interference)

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

            # Preprocessing DISABLED for speed (YOLO works fine without it)
            # detect_frame = preprocess_for_detection(detect_frame)

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
            recent_positions = {k: v for k, v in recent_positions.items() if v['timestamp'] >= cutoff_time}

            # Check pending_plates and log any that have expired
            expired_keys = []
            for plate_key, info in pending_plates.items():
                time_pending = now - info['first_seen']
                if time_pending >= PENDING_WINDOW:
                    # Log the best detection
                    city, class_number, kana, suf, score = info['best']

                    # Post-processing validation
                    is_valid, quality_score, errors = validate_plate_data(city, class_number, kana, suf)

                    # Skip low-quality detections
                    if not is_valid:
                        if using_camera:  # Only print validation warnings in camera mode
                            print(f"[VALIDATION] Skipping low-quality plate: {city} {class_number} {kana} {suf}")
                            print(f"[VALIDATION] Quality: {quality_score}/9, Errors: {', '.join(errors)}")
                        expired_keys.append(plate_key)
                        continue

                    ts_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    object_id_str = f"{object_id_counter:02d}"

                    # Write to CSV with all fields separated
                    write_row_flush(csv_writer, csv_file,
                                  [ts_log, object_id_str, "car", "in",
                                   city or "", class_number or "", kana or "", suf or ""])

                    # Print detailed terminal output
                    print("=" * 80)
                    print(f"🚗 LICENSE PLATE DETECTED")
                    print("=" * 80)
                    print(f"  Timestamp:      {ts_log}")
                    print(f"  Object ID:      {object_id_str}")
                    print(f"  Vehicle Type:   car")
                    print(f"  Direction:      in")
                    print(f"  City:           {city or '(not detected)'}")
                    print(f"  Class Number:   {class_number or '(not detected)'}")
                    print(f"  Kana:           {kana or '(not detected)'}")
                    print(f"  Suffix:         {suf or '(not detected)'}")
                    print(f"  Quality Score:  {quality_score}/9 (validated)")
                    print("=" * 80)
                    print()

                    object_id_counter += 1
                    recent_plates[plate_key] = now

                    # Track position to prevent duplicates from OCR variations
                    det_data = info['det']
                    det_bbox = (0, 0, 0, 0)
                    try:
                        if isinstance(det_data, dict):
                            if "bbox" in det_data:
                                det_bbox = tuple(det_data["bbox"])
                            elif "xyxy" in det_data:
                                det_bbox = tuple(det_data["xyxy"])
                        elif isinstance(det_data, (list, tuple)) and len(det_data) >= 4:
                            det_bbox = tuple(det_data[:4])
                    except Exception:
                        pass

                    if det_bbox != (0, 0, 0, 0):
                        pos_key = f"{int((det_bbox[0] + det_bbox[2]) / 2)}_{int((det_bbox[1] + det_bbox[3]) / 2)}"
                        recent_positions[pos_key] = {
                            'plate_key': plate_key,
                            'timestamp': now,
                            'bbox': det_bbox
                        }

                    # KANA RETRY: DISABLED (causes false/wrong values)
                    # if not kana and city and class_number and suf:
                    #     det = info['det']
                    #     xy = xyxy_from_det(det)
                    #     if xy:
                    #         x1, y1, x2, y2 = map(int, xy)
                    #         crop = frame[y1:y2, x1:x2]
                    #         if crop.size > 0:
                    #             saved_path = save_plate_for_retry(crop, object_id_str, city, class_number, suf)
                    #             if saved_path:
                    #                 print(f"[RETRY-QUEUE] Saved plate ID:{object_id_str} for kana retry → {saved_path}")

                    expired_keys.append(plate_key)

            # Remove expired pending plates
            for key in expired_keys:
                del pending_plates[key]

            # KANA RETRY: DISABLED (causes false/wrong values)
            # if now - last_retry_check >= RETRY_CHECK_INTERVAL:
            #     last_retry_check = now
            #     import glob
            #     retry_images = glob.glob("retry_queue/plate_*.jpg")
            #
            #     for img_path in retry_images[:1]:  # Process ONLY 1 at a time to avoid FPS drop
            #         meta_path = img_path.replace(".jpg", ".txt")
            #         if os.path.exists(meta_path):
            #             try:
            #                 with open(meta_path, "r", encoding="utf-8") as mf:
            #                     metadata = mf.read().strip().split("|")
            #                     if len(metadata) == 4:
            #                         plate_id, _, _, _ = metadata
            #
            #                         # Try to find kana with aggressive preprocessing
            #                         found_kana = retry_kana_ocr(img_path, lp_det.ocr)
            #
            #                         if found_kana:
            #                             # Success! Append correction to CSV
            #                             append_kana_correction(csv_path, plate_id, found_kana)
            #                             # Move to success folder
            #                             success_path = img_path.replace("retry_queue", "retry_success")
            #                             os.rename(img_path, success_path)
            #                             os.rename(meta_path, meta_path.replace("retry_queue", "retry_success"))
            #                         else:
            #                             # No kana found, delete retry files
            #                             os.remove(img_path)
            #                             os.remove(meta_path)
            #             except Exception as e:
            #                 print(f"[WARN] Retry processing failed for {img_path}: {e}")

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

                # Get bounding box for position-based tracking
                x1, y1, x2, y2 = (0, 0, 0, 0)
                try:
                    if isinstance(det, dict):
                        if "bbox" in det:
                            x1, y1, x2, y2 = det["bbox"]
                        elif "xyxy" in det:
                            x1, y1, x2, y2 = det["xyxy"]
                    elif isinstance(det, (list, tuple)) and len(det) >= 4:
                        x1, y1, x2, y2 = det[:4]
                except Exception:
                    pass

                current_bbox = (x1, y1, x2, y2)

                # Check if this position matches a recently logged plate
                matched_plate_key = find_matching_position(current_bbox, recent_positions, POSITION_THRESHOLD)

                # Create unique key for deduplication (use class_number for stability)
                plate_key = make_plate_key(city, class_number, suf)
                if not plate_key:
                    continue

                # If position matches a recent plate, use that plate_key instead
                # This handles OCR variations (e.g., "山目" vs "山国" at same position = same vehicle)
                if matched_plate_key and matched_plate_key in recent_plates:
                    # This is the same physical plate we already logged
                    if DRAW_BBOXES:
                        cx, cy = center_from_det(det)
                        if cx and cy:
                            cv2.putText(frame, f"{suf} (same position, logged)", (int(cx) - 80, int(cy)),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 2, cv2.LINE_AA)
                    continue

                # Skip if already logged recently (by text-based key)
                if plate_key in recent_plates:
                    time_since = now - recent_plates[plate_key]
                    if DRAW_BBOXES:
                        cx, cy = center_from_det(det)
                        if cx and cy:
                            cv2.putText(frame, f"{suf} (logged)", (int(cx) - 40, int(cy)),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 2, cv2.LINE_AA)
                    continue

                # Calculate score for this detection
                score = count_filled_fields(city, class_number, kana, suf)

                # Add to pending or update if better
                if plate_key not in pending_plates:
                    # First time seeing this plate
                    pending_plates[plate_key] = {
                        'first_seen': now,
                        'best': (city, class_number, kana, suf, score),
                        'det': det
                    }
                    if DRAW_BBOXES:
                        cx, cy = center_from_det(det)
                        if cx and cy:
                            cv2.putText(frame, f"{suf} (collecting...)", (int(cx) - 60, int(cy)),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2, cv2.LINE_AA)
                else:
                    # Update if this detection is better
                    current_best_score = pending_plates[plate_key]['best'][4]
                    if score > current_best_score:
                        pending_plates[plate_key]['best'] = (city, class_number, kana, suf, score)
                        pending_plates[plate_key]['det'] = det
                    if DRAW_BBOXES:
                        cx, cy = center_from_det(det)
                        if cx and cy:
                            cv2.putText(frame, f"{suf} (updating...)", (int(cx) - 60, int(cy)),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 255, 0), 2, cv2.LINE_AA)

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
        print("\n" + "=" * 80)
        print("SYSTEM STOPPED")
        print("=" * 80)
        print(f"  CSV saved to:   {csv_path}")
        if WRITE_VIDEO:
            print(f"  Video saved to: {video_filename}")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
