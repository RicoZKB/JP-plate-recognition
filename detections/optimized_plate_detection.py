import sys
# Insert system packages AFTER site-packages to prioritize venv protobuf
# but still get CUDA-enabled OpenCV
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.append('/usr/lib/python3/dist-packages')

import cv2
import numpy as np
from ultralytics import YOLO
from paddleocr import PaddleOCR
import torch
import time
from collections import defaultdict
import hashlib

class OptimizedPlateDetection:
    """
    Optimized ALPR system with:
    - Smart OCR triggering (only on new/unique plates)
    - Crop padding for better OCR accuracy
    - Tracking to avoid duplicate processing
    - GPU-accelerated pipeline
    """

    def __init__(self, model_path, padding_ratio=0.15, ocr_cooldown=2.0, verbose=False):
        """
        Args:
            model_path: Path to YOLO model (.pt, .onnx, or .engine)
            padding_ratio: Padding around detected plate (0.15 = 15% on each side)
            ocr_cooldown: Seconds to wait before re-OCR'ing same plate location
            verbose: Enable debug logging
        """
        # ========== GPU/CUDA Setup ==========
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        print(f"[INFO] Using device: {self.device}")

        # Load YOLO model
        self.model = YOLO(model_path)
        self.is_engine = model_path.endswith('.engine') or model_path.endswith('.trt')
        self.is_onnx = model_path.endswith('.onnx')
        self.is_pytorch = model_path.endswith('.pt')

        if self.is_pytorch and torch.cuda.is_available():
            self.model.to(self.device)
            print(f"[INFO] PyTorch model loaded on {self.device}")
        elif self.is_onnx:
            print(f"[INFO] ONNX model loaded: {model_path}")
        elif self.is_engine:
            print(f"[INFO] TensorRT engine loaded: {model_path}")

        # ========== PaddleOCR with GPU ==========
        print("[INFO] Initializing PaddleOCR with GPU acceleration...")
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='japan',  # Change to 'en' for English/European plates
                use_gpu=True,
                gpu_mem=400,
                enable_mkldnn=False,
                show_log=False,
                det_db_box_thresh=0.3,
                det_db_unclip_ratio=1.8,
                use_mp=False,
                total_process_num=1,
                rec_batch_num=1,
            )
            print("[INFO] PaddleOCR GPU initialized (400MB limit)")
        except Exception as e:
            print(f"[WARN] PaddleOCR GPU init failed: {e}")
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='japan',
                use_gpu=False,
                show_log=False,
            )
            print("[INFO] PaddleOCR CPU fallback enabled")

        # ========== OpenCV CUDA Check ==========
        self.cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if self.cuda_available:
            print(f"[INFO] OpenCV CUDA available")

        # ========== Smart OCR Settings ==========
        self.padding_ratio = padding_ratio
        self.ocr_cooldown = ocr_cooldown
        self.verbose = verbose

        # Tracking for smart OCR triggering
        self.plate_tracker = {}  # track_id -> {'bbox', 'text', 'last_ocr_time', 'hash'}
        self.next_track_id = 0
        self.ocr_hash_cache = {}  # position_hash -> (text, timestamp)

    def _compute_bbox_hash(self, bbox, frame_shape):
        """Compute hash of bbox location (for deduplication)"""
        x1, y1, x2, y2 = bbox
        h, w = frame_shape[:2]
        # Normalize to 0-1 and discretize to grid (10x10 pixels)
        norm_x1 = int((x1 / w) * 100) / 100
        norm_y1 = int((y1 / h) * 100) / 100
        norm_x2 = int((x2 / w) * 100) / 100
        norm_y2 = int((y2 / h) * 100) / 100
        hash_str = f"{norm_x1:.2f}_{norm_y1:.2f}_{norm_x2:.2f}_{norm_y2:.2f}"
        return hashlib.md5(hash_str.encode()).hexdigest()

    def _should_run_ocr(self, bbox, frame_shape, current_time):
        """Smart OCR trigger: only run if plate is new or cooldown expired"""
        bbox_hash = self._compute_bbox_hash(bbox, frame_shape)

        if bbox_hash in self.ocr_hash_cache:
            cached_text, cached_time = self.ocr_hash_cache[bbox_hash]
            time_elapsed = current_time - cached_time

            if time_elapsed < self.ocr_cooldown:
                if self.verbose:
                    print(f"[SKIP OCR] Cached result (age: {time_elapsed:.1f}s): {cached_text}")
                return False, cached_text
            else:
                if self.verbose:
                    print(f"[RUN OCR] Cooldown expired ({time_elapsed:.1f}s)")
                return True, None
        else:
            if self.verbose:
                print(f"[RUN OCR] New plate detected")
            return True, None

    def _add_padding(self, frame, bbox, padding_ratio=None):
        """Add padding around bbox for better OCR"""
        if padding_ratio is None:
            padding_ratio = self.padding_ratio

        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]

        # Calculate padding
        width = x2 - x1
        height = y2 - y1
        pad_x = int(width * padding_ratio)
        pad_y = int(height * padding_ratio)

        # Apply padding with bounds checking
        x1_padded = max(0, x1 - pad_x)
        y1_padded = max(0, y1 - pad_y)
        x2_padded = min(w, x2 + pad_x)
        y2_padded = min(h, y2 + pad_y)

        return x1_padded, y1_padded, x2_padded, y2_padded

    def _preprocess_crop(self, crop):
        """Preprocess cropped plate for OCR (GPU-accelerated if available)"""
        try:
            if self.cuda_available:
                # GPU preprocessing
                gpu_crop = cv2.cuda_GpuMat()
                gpu_crop.upload(crop)
                gpu_gray = cv2.cuda.cvtColor(gpu_crop, cv2.COLOR_BGR2GRAY)

                # CLAHE on GPU
                clahe = cv2.cuda.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gpu_gray = clahe.apply(gpu_gray)
                gray = gpu_gray.download()
            else:
                # CPU preprocessing
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)

            # Upscale for better OCR
            up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            prep = cv2.cvtColor(up, cv2.COLOR_GRAY2BGR)
            return prep

        except Exception as e:
            if self.verbose:
                print(f"[WARN] Preprocessing failed: {e}, using original")
            return crop

    def _run_ocr(self, prep_crop):
        """Run PaddleOCR on preprocessed crop"""
        try:
            ocr_res = self.ocr.ocr(prep_crop, cls=True)

            if not ocr_res or not ocr_res[0]:
                return ""

            # Parse PaddleOCR results
            lines = []
            for line in ocr_res[0]:
                if line and len(line) >= 2:
                    bbox, (text, conf) = line[0], line[1]
                    if text and len(text.strip()) > 0:
                        # Get y-position for sorting
                        y_top = min(pt[1] for pt in bbox)
                        lines.append((y_top, str(text), conf))

            # Sort by vertical position and join
            lines.sort(key=lambda x: x[0])
            plate_text = " ".join(txt for _, txt, _ in lines).strip()

            # Calculate average confidence
            if lines:
                avg_conf = sum(conf for _, _, conf in lines) / len(lines)
                if self.verbose:
                    print(f"[OCR] Text: '{plate_text}' (conf: {avg_conf:.2f})")

            return plate_text

        except Exception as e:
            if self.verbose:
                print(f"[ERROR] OCR failed: {e}")
            return ""

    def detect_and_recognize(self, frame, run_ocr=True):
        """
        Detect license plates and optionally run OCR

        Args:
            frame: Input frame (BGR)
            run_ocr: If False, only detect plates without OCR

        Returns:
            List of detections: [{'bbox': (x1,y1,x2,y2), 'text': str, 'new_detection': bool}, ...]
        """
        current_time = time.time()

        # YOLO detection
        if self.is_engine:
            results = self.model.predict(frame, device=0, verbose=False, conf=0.25, iou=0.45, max_det=10)[0]
        elif self.is_onnx:
            results = self.model.predict(frame, device=self.device, verbose=False, conf=0.25, iou=0.45, max_det=10)[0]
        else:
            results = self.model.predict(frame, device=self.device, half=True, verbose=False, conf=0.25, iou=0.45, max_det=10)[0]

        detections = []

        for box in results.boxes:
            # Get bbox
            x1, y1, x2, y2 = map(int, box.xyxy.tolist()[0])
            confidence = float(box.conf.item())

            bbox = (x1, y1, x2, y2)

            # Check if we should run OCR
            should_ocr, cached_text = self._should_run_ocr(bbox, frame.shape, current_time)

            plate_text = ""
            new_detection = False

            if run_ocr:
                if should_ocr:
                    # Add padding to bbox
                    x1_pad, y1_pad, x2_pad, y2_pad = self._add_padding(frame, bbox)
                    crop = frame[y1_pad:y2_pad, x1_pad:x2_pad]

                    if crop.size > 0:
                        # Preprocess and run OCR
                        prep = self._preprocess_crop(crop)
                        plate_text = self._run_ocr(prep)

                        # Cache result
                        bbox_hash = self._compute_bbox_hash(bbox, frame.shape)
                        self.ocr_hash_cache[bbox_hash] = (plate_text, current_time)
                        new_detection = True
                else:
                    # Use cached result
                    plate_text = cached_text if cached_text else ""

            detections.append({
                'bbox': bbox,
                'bbox_padded': self._add_padding(frame, bbox) if run_ocr else None,
                'text': plate_text,
                'confidence': confidence,
                'new_detection': new_detection,
                'timestamp': current_time
            })

        return detections

    def draw_results(self, frame, detections, show_padding=False):
        """
        Draw detection results on frame

        Args:
            frame: Input frame (will be modified in-place)
            detections: List from detect_and_recognize()
            show_padding: Draw padded bbox in addition to tight bbox
        """
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            text = det['text']
            confidence = det['confidence']
            new_detection = det['new_detection']

            # Color coding: green for new, blue for cached
            color = (0, 255, 0) if new_detection else (255, 200, 0)

            # Draw tight bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Draw padded bbox (optional, for debugging)
            if show_padding and det['bbox_padded']:
                x1p, y1p, x2p, y2p = det['bbox_padded']
                cv2.rectangle(frame, (x1p, y1p), (x2p, y2p), (0, 255, 255), 1)

            # Draw text label
            label = f"{text}" if text else f"Plate {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

            # Background for text
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            # Status indicator
            status = "NEW" if new_detection else "CACHED"
            cv2.putText(frame, status, (x1, y2 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        return frame

    def clear_cache(self):
        """Clear OCR cache (useful when scene changes)"""
        self.ocr_hash_cache.clear()
        if self.verbose:
            print("[INFO] OCR cache cleared")

    def get_cache_stats(self):
        """Get cache statistics"""
        return {
            'cached_plates': len(self.ocr_hash_cache),
            'cache_size_bytes': sum(len(k) + len(v[0]) for k, v in self.ocr_hash_cache.items())
        }
