# Fix libgomp TLS issue on Jetson
import os
os.environ['LD_PRELOAD'] = '/usr/lib/aarch64-linux-gnu/libgomp.so.1'

from .licence_plate_detection import LicencePlateDetection

__all__ = ['LicencePlateDetection']
