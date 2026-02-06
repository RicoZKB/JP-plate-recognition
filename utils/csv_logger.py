"""
CSV Logger for ALPR System
Logs detected license plates with timestamps and metadata
"""

import csv
import os
from datetime import datetime
from pathlib import Path

class CSVLogger:
    """
    CSV logger for license plate detections

    Features:
    - Automatic directory creation
    - Header management
    - Duplicate detection (optional)
    - Configurable fields
    """

    def __init__(self, log_dir='logs', log_prefix='plate_log',
                 enable_duplicate_filter=True, duplicate_window=5.0):
        """
        Args:
            log_dir: Directory to store logs
            log_prefix: Prefix for log filename (will add date)
            enable_duplicate_filter: Skip logging if same plate logged recently
            duplicate_window: Seconds to wait before logging same plate again
        """
        self.log_dir = Path(log_dir)
        self.log_prefix = log_prefix
        self.enable_duplicate_filter = enable_duplicate_filter
        self.duplicate_window = duplicate_window

        # Create log directory if needed
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Generate log filename with today's date
        today = datetime.now().strftime('%Y%m%d')
        self.log_file = self.log_dir / f"{log_prefix}_{today}.csv"

        # Duplicate tracking
        self.recent_plates = {}  # plate_text -> last_log_time

        # Check if file exists (to know if we need headers)
        self.file_exists = self.log_file.exists()

        # Open CSV file in append mode
        self.csv_file = open(self.log_file, 'a', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)

        # Write header if new file
        if not self.file_exists:
            self._write_header()
            print(f"[CSV] Created new log file: {self.log_file}")
        else:
            print(f"[CSV] Appending to existing log: {self.log_file}")

        self.log_count = 0

    def _write_header(self):
        """Write CSV header"""
        headers = [
            'timestamp',           # ISO format timestamp
            'date',                # YYYY-MM-DD
            'time',                # HH:MM:SS
            'plate_text',          # Full OCR text
            'confidence',          # YOLO detection confidence
            'bbox_x1',             # Bounding box coordinates
            'bbox_y1',
            'bbox_x2',
            'bbox_y2',
            'frame_number',        # Frame number (if available)
            'source',              # camera/video/image
        ]
        self.csv_writer.writerow(headers)
        self.csv_file.flush()

    def should_log(self, plate_text, current_time):
        """
        Check if plate should be logged (duplicate filter)

        Returns:
            bool: True if should log, False if duplicate
        """
        if not self.enable_duplicate_filter:
            return True

        if not plate_text or len(plate_text.strip()) == 0:
            return False

        # Check if plate was logged recently
        if plate_text in self.recent_plates:
            last_time = self.recent_plates[plate_text]
            time_elapsed = current_time - last_time

            if time_elapsed < self.duplicate_window:
                return False  # Skip duplicate

        return True

    def log_detection(self, detection, frame_number=None, source='unknown'):
        """
        Log a single detection to CSV

        Args:
            detection: Detection dict from OptimizedPlateDetection
                       {bbox, text, confidence, timestamp, ...}
            frame_number: Optional frame number
            source: Source type (camera/video/image)
        """
        plate_text = detection.get('text', '').strip()
        timestamp = detection.get('timestamp', None)

        # Skip empty plates
        if not plate_text:
            return False

        # Get current time if not provided
        if timestamp is None:
            timestamp = datetime.now().timestamp()

        # Duplicate filter
        if not self.should_log(plate_text, timestamp):
            return False

        # Format timestamp
        dt = datetime.fromtimestamp(timestamp)
        timestamp_iso = dt.isoformat()
        date_str = dt.strftime('%Y-%m-%d')
        time_str = dt.strftime('%H:%M:%S')

        # Get bbox
        bbox = detection.get('bbox', (0, 0, 0, 0))
        x1, y1, x2, y2 = bbox

        # Get confidence
        confidence = detection.get('confidence', 0.0)

        # Write row
        row = [
            timestamp_iso,
            date_str,
            time_str,
            plate_text,
            f"{confidence:.3f}",
            x1, y1, x2, y2,
            frame_number if frame_number else '',
            source
        ]

        self.csv_writer.writerow(row)
        self.csv_file.flush()  # Ensure immediate write

        # Update duplicate tracker
        self.recent_plates[plate_text] = timestamp

        self.log_count += 1
        return True

    def log_multiple(self, detections, frame_number=None, source='unknown'):
        """
        Log multiple detections from a single frame

        Returns:
            int: Number of detections actually logged
        """
        logged = 0
        for det in detections:
            if self.log_detection(det, frame_number, source):
                logged += 1
        return logged

    def cleanup_old_entries(self, current_time):
        """
        Clean up old entries from duplicate tracker
        (keeps memory usage low)
        """
        to_remove = []
        for plate, last_time in self.recent_plates.items():
            if current_time - last_time > (self.duplicate_window * 2):
                to_remove.append(plate)

        for plate in to_remove:
            del self.recent_plates[plate]

    def get_stats(self):
        """Get logging statistics"""
        return {
            'log_file': str(self.log_file),
            'total_logged': self.log_count,
            'tracked_plates': len(self.recent_plates),
            'file_size_bytes': self.log_file.stat().st_size if self.log_file.exists() else 0
        }

    def close(self):
        """Close CSV file"""
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.close()
            print(f"[CSV] Closed log file. Total entries logged: {self.log_count}")

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()
        return False


class MinimalCSVLogger:
    """
    Minimal CSV logger with just plate text and timestamp
    (for simple use cases)
    """

    def __init__(self, log_file='plate_log.csv'):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        file_exists = self.log_file.exists()
        self.csv_file = open(self.log_file, 'a', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)

        if not file_exists:
            self.csv_writer.writerow(['timestamp', 'plate_text', 'confidence'])
            self.csv_file.flush()

        print(f"[CSV] Logging to: {self.log_file}")

    def log(self, plate_text, confidence=0.0):
        """Log a plate detection (minimal)"""
        if not plate_text or len(plate_text.strip()) == 0:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.csv_writer.writerow([timestamp, plate_text, f"{confidence:.3f}"])
        self.csv_file.flush()

    def close(self):
        """Close file"""
        if hasattr(self, 'csv_file'):
            self.csv_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
