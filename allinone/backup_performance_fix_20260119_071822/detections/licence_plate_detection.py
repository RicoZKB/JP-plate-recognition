import cv2
import re
from ultralytics import YOLO
from paddleocr import PaddleOCR

# Romaji to Hiragana conversion for YOLO kana class labels
# Japanese license plates use 41 hiragana characters (excludes お し へ を ん)
ROMAJI_TO_HIRAGANA = {
    'a': 'あ', 'i': 'い', 'u': 'う', 'e': 'え',
    'ka': 'か', 'ki': 'き', 'ku': 'く', 'ke': 'け', 'ko': 'こ',
    'sa': 'さ', 'su': 'す', 'se': 'せ', 'so': 'そ',
    'ta': 'た', 'ti': 'ち', 'tu': 'つ', 'te': 'て', 'to': 'と',
    'na': 'な', 'ni': 'に', 'nu': 'ぬ', 'ne': 'ね', 'no': 'の',
    'ha': 'は', 'hi': 'ひ', 'hu': 'ふ', 'ho': 'ほ',
    'ma': 'ま', 'mi': 'み', 'mu': 'む', 'me': 'め', 'mo': 'も',
    'ya': 'や', 'yu': 'ゆ', 'yo': 'よ',
    'ra': 'ら', 'ri': 'り', 'ru': 'る', 're': 'れ', 'ro': 'ろ',
    'wa': 'わ',
}

class LicencePlateDetection:
    def __init__(self, model_path, verbose=False, debug_ocr=False, enable_ocr_cache=True, cache_threshold=50, cache_max_age=3):
        # load your YOLO model (supports .pt, .onnx, .engine)
        # Try TensorRT engine first, fallback to ONNX if engine fails
        import os
        if model_path.endswith('.engine'):
            if not os.path.exists(model_path):
                # Try FP16 version first
                fp16_path = model_path.replace('best.engine', 'best_fp16.engine')
                if os.path.exists(fp16_path):
                    print(f"[INFO] Using FP16 engine: {fp16_path}")
                    model_path = fp16_path
                else:
                    # Fallback to ONNX
                    onnx_path = model_path.replace('.engine', '.onnx')
                    if os.path.exists(onnx_path):
                        print(f"[WARN] TensorRT engine not found, using ONNX: {onnx_path}")
                        model_path = onnx_path

        self.model = YOLO(model_path, task='detect')  # Explicitly specify detection task
        print(f"[INFO] Loaded model: {model_path}")

        # initialize PaddleOCR with GPU acceleration
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='japan',
            use_gpu=True,
            gpu_mem=300,
            show_log=False
        )
        # logging options
        self.verbose = bool(verbose)
        self.debug_ocr = bool(debug_ocr)

        # Smart OCR caching to improve FPS
        self.enable_ocr_cache = enable_ocr_cache
        self.cache_threshold = cache_threshold  # pixels: if bbox moved less than this, use cache
        self.cache_max_age = cache_max_age  # frames: re-run OCR after this many frames
        self.ocr_cache = {}  # {cache_key: {'text': str, 'age': int, 'bbox': tuple}}
        self.frame_count = 0

        if self.enable_ocr_cache:
            print(f"[INFO] OCR cache enabled: threshold={cache_threshold}px, max_age={cache_max_age} frames")

    def _bbox_distance(self, bbox1, bbox2):
        """Calculate distance between two bounding boxes (center points)."""
        x1_c = (bbox1[0] + bbox1[2]) / 2
        y1_c = (bbox1[1] + bbox1[3]) / 2
        x2_c = (bbox2[0] + bbox2[2]) / 2
        y2_c = (bbox2[1] + bbox2[3]) / 2
        return ((x1_c - x2_c)**2 + (y1_c - y2_c)**2)**0.5

    def _find_cached_ocr(self, bbox):
        """Find cached OCR result for similar bbox, return (text, cache_hit) tuple."""
        if not self.enable_ocr_cache:
            return None, False

        best_match = None
        best_distance = float('inf')

        for cache_key, cache_data in list(self.ocr_cache.items()):
            cached_bbox = cache_data['bbox']
            age = cache_data['age']

            # Skip if cache is too old
            if age >= self.cache_max_age:
                continue

            # Calculate distance between bboxes
            distance = self._bbox_distance(bbox, cached_bbox)

            # If close enough and better than previous best
            if distance < self.cache_threshold and distance < best_distance:
                best_match = cache_data['text']
                best_distance = distance

        return best_match, (best_match is not None)

    def _update_ocr_cache(self, bbox, text):
        """Update OCR cache with new result."""
        if not self.enable_ocr_cache:
            return

        # Use bbox center as cache key
        cache_key = (int((bbox[0] + bbox[2]) / 2), int((bbox[1] + bbox[3]) / 2))

        self.ocr_cache[cache_key] = {
            'text': text,
            'age': 0,
            'bbox': bbox
        }

    def _age_ocr_cache(self):
        """Increment age of all cached entries and remove stale ones."""
        if not self.enable_ocr_cache:
            return

        # Increment age and remove stale entries
        stale_keys = []
        for cache_key, cache_data in self.ocr_cache.items():
            cache_data['age'] += 1
            if cache_data['age'] > self.cache_max_age * 2:  # Remove entries 2x older than max
                stale_keys.append(cache_key)

        for key in stale_keys:
            del self.ocr_cache[key]

    def detect_frames(self, frames, ocr_filter=None):
        all_bboxes = []
        all_texts = []
        for frame in frames:
            bboxes, texts = self.detect_frame(frame, ocr_filter=ocr_filter)
            all_bboxes.append(bboxes)
            all_texts.append(texts)
        return all_bboxes, all_texts

    def detect_frame(self, frame, ocr_filter=None):
        # Age the OCR cache at the start of each frame
        self._age_ocr_cache()
        self.frame_count += 1

        results = self.model.predict(frame)[0]
        detections = []
        texts = []

        # Resolve class names and count (handle list/dict/other)
        names = getattr(results, "names", {})
        try:
            num_classes = len(names)
        except Exception:
            num_classes = None

        # NEW STRATEGY: Collect ALL detections, find kana from YOLO classes
        plate_boxes = []  # Full plate detections (NumberPLATE class)
        kana_detections = {}  # {bbox: hiragana_char} - kana detected by YOLO

        for box in results.boxes:
            # Determine class id and name robustly
            cls_id = None
            try:
                # ultralytics boxes.cls is a tensor
                cls_id = int(box.cls[0].item())
            except Exception:
                try:
                    cls_id = int(box.cls.tolist()[0])
                except Exception:
                    cls_id = None

            cls_name = ""
            if isinstance(names, dict) and cls_id is not None:
                cls_name = str(names.get(cls_id, ""))
            elif isinstance(names, list) and cls_id is not None and 0 <= cls_id < len(names):
                cls_name = str(names[cls_id])

            # get bounding box coords
            x1, y1, x2, y2 = map(int, box.xyxy.tolist()[0])
            bbox_tuple = (x1, y1, x2, y2)

            # DISABLED: YOLO kana detection (unreliable, causes false values)
            # Skip kana classes entirely - rely on main plate OCR only
            if cls_name.lower() in ROMAJI_TO_HIRAGANA:
                continue  # Skip kana detections

            # Keep full plate boxes only
            keep = False
            if num_classes == 1:
                keep = True
            else:
                nm = cls_name.lower()
                if ("plate" in nm) or ("licence" in nm) or ("license" in nm) or (nm == "lp") or ("number" in nm):
                    keep = True
            if not keep:
                continue

            plate_boxes.append(bbox_tuple)

        # Process each plate box with OCR
        for bbox_tuple in plate_boxes:
            x1, y1, x2, y2 = bbox_tuple

            # Check OCR cache first
            cached_text, cache_hit = self._find_cached_ocr(bbox_tuple)

            if cache_hit:
                # Use cached OCR result (YOLO kana injection DISABLED)
                plate_str = cached_text

                if self.verbose:
                    try:
                        print(f"LP DET: bbox=({x1},{y1},{x2},{y2}) text='{plate_str}' [CACHED]")
                    except Exception:
                        pass

                detections.append(bbox_tuple)
                texts.append(plate_str)
                continue  # Skip OCR processing

            # No cache hit, run OCR
            crop = frame[y1:y2, x1:x2]

            run_ocr = True
            if ocr_filter is not None:
                try:
                    run_ocr = bool(ocr_filter(bbox_tuple))
                except Exception:
                    run_ocr = True

            # FAST preprocessing for OCR (target: 5+ FPS)
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

            # Light CLAHE only (fast)
            try:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)
            except Exception:
                pass

            # NO bilateral filter (too slow)
            # NO unsharp mask (too slow)

            # 2x upscaling only (fast, good enough)
            up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
            prep = cv2.cvtColor(up, cv2.COLOR_GRAY2BGR)

            # RUN OCR — no cls=True
            ocr_res = []
            if run_ocr:
                ocr_res = self.ocr.ocr(prep)
                if self.debug_ocr:
                    try:
                        print("DEBUG OCR_RES:", ocr_res)
                    except Exception:
                        pass

            # normalize each line into (y_top, text)
            lines = []

            # Handle PaddleOCR result format: [[[bbox], (text, conf)], ...]
            if ocr_res and isinstance(ocr_res, list):
                # PaddleOCR returns nested list structure
                # Format: [[[bbox], (text, conf)]] or [[bbox, text, conf], ...]

                # Check if it's wrapped in extra list
                if len(ocr_res) == 1 and isinstance(ocr_res[0], list):
                    ocr_res = ocr_res[0]  # Unwrap

                for item in ocr_res:
                    try:
                        # PaddleOCR format: [bbox, (text, confidence)]
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            bbox = item[0]

                            # Extract text from tuple (text, conf) or just text
                            if isinstance(item[1], (list, tuple)) and len(item[1]) >= 1:
                                txt = str(item[1][0])
                            elif isinstance(item[1], str):
                                txt = item[1]
                            else:
                                continue

                            if not txt or txt.strip() == '':
                                continue

                            # Get y position from bbox for sorting
                            try:
                                if isinstance(bbox, (list, tuple)) and len(bbox) > 0:
                                    if isinstance(bbox[0], (list, tuple)):
                                        # 4-point polygon: [[x1,y1], [x2,y2], ...]
                                        y_top = min(int(p[1]) for p in bbox if len(p) >= 2)
                                    else:
                                        # Simple bbox: [x1, y1, x2, y2]
                                        y_top = int(bbox[1])
                                else:
                                    y_top = 0
                            except Exception:
                                y_top = 0

                            lines.append((y_top, txt))
                    except Exception as e:
                        if self.debug_ocr:
                            print(f"[DEBUG] Failed to parse OCR item: {item}, error: {e}")
                        continue

            # sort by vertical position and join
            lines.sort(key=lambda x: x[0])
            plate_str = " ".join(txt for _, txt in lines).strip()

            # Update OCR cache
            self._update_ocr_cache(bbox_tuple, plate_str)

            # DISABLED: YOLO kana injection (unreliable, causes false values)
            # Rely on main plate OCR only

            if self.verbose:
                try:
                    print(f"LP DET: bbox=({x1},{y1},{x2},{y2}) text='{plate_str}'")
                except Exception:
                    pass

            detections.append(bbox_tuple)
            texts.append(plate_str)

        return detections, texts

    def draw_bboxes(self, video_frames, licence_plate_detections, licence_plate_texts):
        output_frames = []
        for frame, bbox_list, text_list in zip(video_frames, licence_plate_detections, licence_plate_texts):
            for (x1, y1, x2, y2), text in zip(bbox_list, text_list):
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,0), 2)
            output_frames.append(frame)
        return output_frames
