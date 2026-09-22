"""
Monitering Package
Contains modules for face monitoring and event logging.
"""

from .face_monitoring import detect_face
from .face_logger import log_face_state

__all__ = ["detect_face", "log_face_state"]
