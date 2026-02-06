# -*- coding: utf-8 -*-
"""
Plate Region Segmenter - Segments license plate into regions for targeted OCR
"""

import cv2
import numpy as np

class PlateRegionSegmenter:
    """
    Segments license plate into regions: city, class_number, kana, suffix.
    Uses geometric segmentation based on Japanese plate layout.
    """

    def __init__(self):
        """Initialize segmenter with Japanese plate layout ratios."""
        pass

    def segment_plate(self, plate_crop):
        """
        Segment plate into regions based on Japanese license plate layout.

        Japanese plate layout (approximate):
        +----------------------------------+
        | City Name       Class Number     | <- Top line (60% height)
        | Kana    Suffix (XX-XX)           | <- Bottom line (40% height)
        +----------------------------------+

        Args:
            plate_crop: Cropped plate image

        Returns:
            dict with keys: 'city', 'class_number', 'kana', 'suffix'
        """
        if plate_crop is None or plate_crop.size == 0:
            return {'city': None, 'class_number': None, 'kana': None, 'suffix': None}

        h, w = plate_crop.shape[:2]

        # Split horizontally: top 60% and bottom 40%
        split_y = int(h * 0.6)
        top_region = plate_crop[0:split_y, :]
        bottom_region = plate_crop[split_y:, :]

        # Top line: City (left 60%) + Class Number (right 40%)
        city_split_x = int(w * 0.6)
        city_crop = top_region[:, 0:city_split_x]
        class_number_crop = top_region[:, city_split_x:]

        # Bottom line: Kana (left 20%) + Suffix (right 80%)
        kana_split_x = int(w * 0.2)
        kana_crop = bottom_region[:, 0:kana_split_x]
        suffix_crop = bottom_region[:, kana_split_x:]

        return {
            'city': city_crop if city_crop.size > 0 else None,
            'class_number': class_number_crop if class_number_crop.size > 0 else None,
            'kana': kana_crop if kana_crop.size > 0 else None,
            'suffix': suffix_crop if suffix_crop.size > 0 else None,
        }

    def preprocess_kana_region(self, kana_crop, debug_save_path=None):
        """
        Apply aggressive preprocessing for kana character detection.

        Kana characters are small and often misread. This applies:
        - 6× upscaling (from 2× in basic OCR)
        - Extreme CLAHE for contrast
        - Unsharp masking for edge enhancement
        - Adaptive thresholding

        Args:
            kana_crop: Cropped kana region
            debug_save_path: Optional path to save debug image

        Returns:
            Preprocessed image ready for OCR
        """
        if kana_crop is None or kana_crop.size == 0:
            return kana_crop

        # Convert to grayscale
        if len(kana_crop.shape) == 3:
            gray = cv2.cvtColor(kana_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = kana_crop.copy()

        # Extreme CLAHE for contrast (higher clipLimit for tiny characters)
        try:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
            enhanced = clahe.apply(gray)
        except Exception:
            enhanced = gray

        # Unsharp masking for edge enhancement
        try:
            blur = cv2.GaussianBlur(enhanced, (0, 0), 1.5)
            sharpened = cv2.addWeighted(enhanced, 2.0, blur, -1.0, 0)
        except Exception:
            sharpened = enhanced

        # 6× upscaling (critical for small kana)
        try:
            upscaled = cv2.resize(sharpened, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
        except Exception:
            upscaled = sharpened

        # Optional: Adaptive thresholding for better character separation
        # (Commented out by default - enable if needed)
        # try:
        #     upscaled = cv2.adaptiveThreshold(
        #         upscaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        #     )
        # except Exception:
        #     pass

        # Convert back to BGR for PaddleOCR
        preprocessed = cv2.cvtColor(upscaled, cv2.COLOR_GRAY2BGR)

        # Save debug image if requested
        if debug_save_path:
            try:
                # Create side-by-side comparison
                original_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR) if len(gray.shape) == 2 else kana_crop

                # Resize original to match preprocessed height for comparison
                orig_h, orig_w = original_bgr.shape[:2]
                prep_h, prep_w = preprocessed.shape[:2]
                scale = prep_h / orig_h
                original_scaled = cv2.resize(original_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

                # Concatenate side by side
                comparison = np.hstack([original_scaled, preprocessed])

                # Add labels
                cv2.putText(comparison, "Original (6x)", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(comparison, "Preprocessed", (orig_w + 10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.imwrite(debug_save_path, comparison)
            except Exception as e:
                print(f"[WARN] Failed to save debug image: {e}")

        return preprocessed
