"""
Compatibility wrapper for monitoring package.
Re-exports from Monitering package.
"""

from Monitering import (
    event_detector,
    alert_manager,
    ai_repor_manager,
    evidence_manager,
    reviewer_manager,
    incident_logger,
    face_logger,
)
from Monitering.face_monitoring import detect_face
from Monitering.intigrity_score import compute_integrity_score, close_open_face_event

__all__ = [
    "event_detector",
    "alert_manager",
    "ai_repor_manager",
    "evidence_manager",
    "reviewer_manager",
    "incident_logger",
    "face_logger",
    "detect_face",
    "compute_integrity_score",
    "close_open_face_event",
]
