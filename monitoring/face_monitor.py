"""
Compatibility module: monitoring.face_monitor
"""
from Monitering.face_monitoring import detect_face
from Monitering.intigrity_score import close_open_face_event

__all__ = ["detect_face", "close_open_face_event"]
