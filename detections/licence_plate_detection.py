import sys
# Insert system packages AFTER site-packages to prioritize venv protobuf
# but still get CUDA-enabled OpenCV
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.append('/usr/lib/python3/dist-packages')

import cv2
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
from paddleocr import PaddleOCR  # PRIMARY: PaddleOCR with GPU optimization
# import easyocr  # BACKUP: EasyOCR (commented out, slower than PaddleOCR)
import torch
import time
import hashlib

class LicencePlateDetection:
    def __init__(self, model_path, verbose=False, debug_ocr=False):
        # ========== GPU/CUDA/TensorRT Optimizations ==========
        # Check CUDA availability
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        print(f"[INFO] Using device: {self.device}")

        # Load YOLO model with GPU and TensorRT optimizations
        # Note: TensorRT engines (.engine) already have device embedded, no need to call .to(device)
        # Device will be specified in predict() call
        self.model = YOLO(model_path)

        # Check model type
        self.is_engine = model_path.endswith('.engine') or model_path.endswith('.trt')
        self.is_onnx = model_path.endswith('.onnx')
        self.is_pytorch = model_path.endswith('.pt')

        if self.is_engine:
            print(f"[INFO] TensorRT engine loaded: {model_path}")
            print(f"[INFO] Engine will run on GPU with FP16 optimization")
        elif self.is_onnx:
            print(f"[INFO] ONNX model loaded: {model_path}")
            print(f"[INFO] Model will run on GPU with CUDA acceleration")
        elif self.is_pytorch and torch.cuda.is_available():
            # Only call .to() for PyTorch models
            self.model.to(self.device)
            print(f"[INFO] PyTorch model loaded on {self.device}")

        # ===== PRIMARY: PaddleOCR with GPU optimization =====
        # PaddleOCR optimized for Jetson TX1 (4GB shared memory)
        print("[INFO] Initializing PaddleOCR with GPU acceleration...")
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=True,      # Enable angle classification for rotated plates
                lang='japan',            # Japanese language support
                use_gpu=True,            # Enable GPU acceleration
                gpu_mem=300,             # REDUCED: 300MB for better system memory balance
                enable_mkldnn=False,     # Disable MKLDNN (not needed on GPU)
                show_log=False,          # Suppress verbose logs
                det_db_box_thresh=0.3,   # Lower detection threshold for better recall
                det_db_unclip_ratio=1.8, # Adjust text region expansion
                use_mp=False,            # Disable multiprocessing (saves memory)
                total_process_num=1,     # Single process mode
                rec_batch_num=1,         # Process one plate at a time (saves memory)
            )
            print("[INFO] PaddleOCR initialized with GPU acceleration (400MB limit)")
            self.ocr_engine = "paddleocr"
        except Exception as e:
            print(f"[WARN] PaddleOCR GPU init failed ({e}), falling back to CPU")
            try:
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='japan',
                    use_gpu=False,
                    show_log=False,
                    use_mp=False,
                    total_process_num=1,
                    rec_batch_num=1,
                )
                print("[INFO] PaddleOCR initialized with CPU fallback")
                self.ocr_engine = "paddleocr"
            except Exception as e2:
                print(f"[ERROR] PaddleOCR completely failed: {e2}")
                print("[INFO] Falling back to EasyOCR...")
                import easyocr
                self.ocr = easyocr.Reader(['ja', 'en'], gpu=True, verbose=False)
                self.ocr_engine = "easyocr"
                print("[INFO] EasyOCR initialized as fallback")
        # ===== END PRIMARY =====

        # logging options
        self.verbose = bool(verbose)
        self.debug_ocr = bool(debug_ocr)

        # Check if CUDA preprocessing is available (cv2.cuda)
        self.cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if self.cuda_available:
            print(f"[INFO] OpenCV CUDA available: {cv2.cuda.getCudaEnabledDeviceCount()} device(s)")
        else:
            print("[INFO] OpenCV CUDA not available, using CPU preprocessing")

        # ========== Position-based OCR caching for stationary plates ==========
        self.plate_cache = {}  # position_hash -> {'text': str, 'timestamp': float, 'bbox': tuple}
        self.cache_timeout = 2.0  # seconds - cache expires after 2s (for stationary plates)
        self.position_tolerance = 20  # pixels - consider same position if within 20px

    def _gpu_preprocess_crop(self, crop):
        """GPU-accelerated preprocessing for OCR (if CUDA available)"""
        try:
            if not self.cuda_available:
                raise Exception("CUDA not available")

            # Upload to GPU
            gpu_crop = cv2.cuda_GpuMat()
            gpu_crop.upload(crop)

            # Convert to grayscale on GPU
            gpu_gray = cv2.cuda.cvtColor(gpu_crop, cv2.COLOR_BGR2GRAY)

            # CLAHE on GPU (if available)
            clahe = cv2.cuda.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gpu_gray = clahe.apply(gpu_gray)

            # Download back to CPU for PaddleOCR
            gray = gpu_gray.download()

            # Resize on CPU (cv2.cuda.resize can be unstable)
            up = cv2.resize(gray, None, fx=2, fy=2)
            prep = cv2.cvtColor(up, cv2.COLOR_GRAY2BGR)

            return prep

        except Exception as e:
            # Fallback to CPU preprocessing
            return self._cpu_preprocess_crop(crop)

    def _cpu_preprocess_crop(self, crop):
        """FAST preprocessing for real-time OCR (industry standard)"""
        # Simple grayscale conversion
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        # Fast bilateral filter for edge-preserving deblur (FAST! ~5ms)
        gray = cv2.bilateralFilter(gray, 5, 50, 50)

        # Adaptive histogram equalization (FAST! ~3ms)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Simple resize 2x (FAST! ~2ms with INTER_LINEAR)
        up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

        # Convert to BGR for PaddleOCR
        prep = cv2.cvtColor(up, cv2.COLOR_GRAY2BGR)
        return prep

    def _compute_position_hash(self, bbox):
        """Compute hash based on bbox position (for stationary plate detection)"""
        x1, y1, x2, y2 = bbox
        # Round to tolerance grid to handle small movements
        grid_x1 = (x1 // self.position_tolerance) * self.position_tolerance
        grid_y1 = (y1 // self.position_tolerance) * self.position_tolerance
        grid_x2 = (x2 // self.position_tolerance) * self.position_tolerance
        grid_y2 = (y2 // self.position_tolerance) * self.position_tolerance
        hash_str = f"{grid_x1}_{grid_y1}_{grid_x2}_{grid_y2}"
        return hashlib.md5(hash_str.encode()).hexdigest()

    def _check_cache(self, bbox, current_time):
        """Check if plate at this position is cached and still valid"""
        pos_hash = self._compute_position_hash(bbox)

        if pos_hash in self.plate_cache:
            cache_entry = self.plate_cache[pos_hash]
            time_elapsed = current_time - cache_entry['timestamp']

            # Cache valid if not expired
            if time_elapsed < self.cache_timeout:
                return True, cache_entry['text']

        return False, None

    def _update_cache(self, bbox, text, current_time):
        """Update cache with new OCR result"""
        pos_hash = self._compute_position_hash(bbox)
        self.plate_cache[pos_hash] = {
            'text': text,
            'timestamp': current_time,
            'bbox': bbox
        }

    def _cleanup_old_cache(self, current_time):
        """Remove expired cache entries"""
        to_remove = []
        for pos_hash, entry in self.plate_cache.items():
            if current_time - entry['timestamp'] > (self.cache_timeout * 2):
                to_remove.append(pos_hash)

        for pos_hash in to_remove:
            del self.plate_cache[pos_hash]

    def detect_frames(self, frames, ocr_filter=None):
        all_bboxes = []
        all_texts = []
        all_statuses = []
        for frame in frames:
            bboxes, texts, statuses = self.detect_frame(frame, ocr_filter=ocr_filter)
            all_bboxes.append(bboxes)
            all_texts.append(texts)
            all_statuses.append(statuses)
        return all_bboxes, all_texts, all_statuses

    def detect_frame(self, frame, ocr_filter=None):
        # GPU-optimized YOLO inference
        # Different handling for TensorRT, ONNX, and PyTorch models
        if self.is_engine:
            # TensorRT engine - device as integer, no half parameter (precision baked in)
            results = self.model.predict(
                frame,
                device=0,  # Integer device ID for engines
                verbose=False,
                conf=0.25,  # Confidence threshold
                iou=0.45,   # NMS IoU threshold
                max_det=10  # Max detections per image
            )[0]
        elif self.is_onnx:
            # ONNX model - automatically uses GPU through CUDA
            results = self.model.predict(
                frame,
                device=self.device,
                verbose=False,
                conf=0.25,
                iou=0.45,
                max_det=10
            )[0]
        else:
            # PyTorch model - use half=True for FP16
            results = self.model.predict(
                frame,
                device=self.device,
                half=True,  # FP16 inference for 2x speed boost (PyTorch only)
                verbose=False,
                conf=0.25,
                iou=0.45,
                max_det=10
            )[0]
        detections = []
        texts = []
        statuses = []  # NEW: track if plate is 'NEW' or 'CACHED'

        # Get current time for caching
        current_time = time.time()

        # Cleanup old cache entries periodically
        self._cleanup_old_cache(current_time)

        # Resolve class names and count (handle list/dict/other)
        names = getattr(results, "names", {})
        try:
            num_classes = len(names)
        except Exception:
            num_classes = None

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

            # Keep boxes if:
            # - model is single-class, or
            # - class name suggests it's a plate (case-insensitive contains)
            keep = False
            if num_classes == 1:
                keep = True
            else:
                nm = cls_name.lower()
                if ("plate" in nm) or ("licence" in nm) or ("license" in nm) or (nm == "lp") or ("number" in nm):
                    keep = True
            if not keep:
                continue

            # get bounding box coords
            x1, y1, x2, y2 = map(int, box.xyxy.tolist()[0])
            bbox = (x1, y1, x2, y2)
            crop = frame[y1:y2, x1:x2]

            # Check if this plate position is cached (stationary plate)
            is_cached, cached_text = self._check_cache(bbox, current_time)

            plate_str = ""
            status = "CACHED" if is_cached else "NEW"

            if is_cached:
                # Use cached result (stationary plate, in queue, not moving)
                plate_str = cached_text
                if self.verbose:
                    print(f"[CACHED] bbox=({x1},{y1},{x2},{y2}) text='{plate_str}'")
            else:
                # NEW PLATE or MOVED PLATE - Always run OCR!
                run_ocr = True
                if ocr_filter is not None:
                    try:
                        run_ocr = bool(ocr_filter((x1, y1, x2, y2)))
                    except Exception:
                        run_ocr = True

                # GPU-accelerated preprocessing (falls back to CPU if CUDA unavailable)
                if self.cuda_available:
                    prep = self._gpu_preprocess_crop(crop)
                else:
                    prep = self._cpu_preprocess_crop(crop)

                # RUN OCR with GPU (PaddleOCR or EasyOCR)
                ocr_res = []
                if run_ocr:
                    if self.ocr_engine == "paddleocr":
                        # PaddleOCR returns list of [line_result, ...]
                        # line_result = [bbox, (text, confidence)]
                        ocr_res = self.ocr.ocr(prep, cls=True)
                        if self.debug_ocr:
                            try:
                                print("DEBUG OCR_RES (PaddleOCR):", ocr_res)
                            except Exception:
                                pass
                    else:
                        # EasyOCR returns list of (bbox, text, confidence)
                        ocr_res = self.ocr.readtext(prep)
                        if self.debug_ocr:
                            try:
                                print("DEBUG OCR_RES (EasyOCR):", ocr_res)
                            except Exception:
                                pass

                # Parse OCR results (support both PaddleOCR and EasyOCR)
                lines = []

                if self.ocr_engine == "paddleocr":
                    # PaddleOCR format: [[[bbox], (text, confidence)], ...]
                    # bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    if ocr_res and isinstance(ocr_res, list) and len(ocr_res) > 0:
                        # PaddleOCR returns nested list, first element is results for the image
                        results_list = ocr_res[0] if ocr_res[0] is not None else []
                        for line in results_list:
                            if line and len(line) >= 2:
                                ocr_bbox, (text, conf) = line[0], line[1]
                                # Get vertical position for sorting
                                try:
                                    y_top = min(pt[1] for pt in ocr_bbox)
                                except:
                                    y_top = 0
                                if text and len(text.strip()) > 0:
                                    lines.append((y_top, str(text)))
                else:
                    # EasyOCR format: [(bbox, text, confidence), ...]
                    for detection in ocr_res:
                        if len(detection) >= 2:
                            ocr_bbox, text = detection[0], detection[1]
                            # Get vertical position for sorting
                            try:
                                y_top = min(pt[1] for pt in ocr_bbox)
                            except:
                                y_top = 0
                            if text and len(text.strip()) > 0:
                                lines.append((y_top, str(text)))

                # sort by vertical position and join
                lines.sort(key=lambda x: x[0])
                plate_str = " ".join(txt for _, txt in lines).strip()

                # Update cache with new OCR result
                self._update_cache(bbox, plate_str, current_time)

                if self.verbose:
                    print(f"[NEW] bbox=({x1},{y1},{x2},{y2}) text='{plate_str}'")

            # Store results
            detections.append((x1, y1, x2, y2))
            texts.append(plate_str)
            statuses.append(status)

        return detections, texts, statuses

    def draw_bboxes(self, video_frames, licence_plate_detections, licence_plate_texts, licence_plate_statuses=None):
        """Draw bboxes with Ultralytics colors and NEW/CACHED status"""
        output_frames = []

        # Handle old calls without status
        if licence_plate_statuses is None:
            licence_plate_statuses = [["NEW"] * len(bbox_list) for bbox_list in licence_plate_detections]

        for frame, bbox_list, text_list, status_list in zip(video_frames, licence_plate_detections, licence_plate_texts, licence_plate_statuses):
            # Use Ultralytics Annotator for professional visualization
            annotator = Annotator(frame, line_width=2)

            for idx, ((x1, y1, x2, y2), text, status) in enumerate(zip(bbox_list, text_list, status_list)):
                # Color based on status: Green for NEW, Blue for CACHED
                if status == "NEW":
                    color = (0, 255, 0)  # Green - new plate detected
                    label_bg = (0, 200, 0)
                else:  # CACHED
                    color = (255, 100, 0)  # Blue - cached (stationary)
                    label_bg = (200, 80, 0)

                # Draw bounding box
                annotator.box_label(
                    box=(x1, y1, x2, y2),
                    label=text if text else "Plate",
                    color=color
                )

                # Draw status label below bbox
                status_y = y2 + 20
                status_text = f"[{status}]"

                # Background for status
                (status_w, status_h), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(frame, (x1, status_y - status_h - 4), (x1 + status_w + 4, status_y + 2), label_bg, -1)

                # Status text
                cv2.putText(frame, status_text, (x1 + 2, status_y - 2),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            output_frames.append(annotator.result())
        return output_frames
