"""
Camera module re-exporting functions from cemara.py
Provides both capture_photo and save_captured_photo.
"""

from cemara import capture_photo, save_captured_photo, UPLOAD_FOLDER

__all__ = ["capture_photo", "save_captured_photo", "UPLOAD_FOLDER"]
