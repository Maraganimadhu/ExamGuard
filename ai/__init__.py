import sys
from . import integrity_agent
from .integrity_agent import generate_real_integrity_report, create_integrity_report

# Alias 'ai' package and submodules in sys.modules
sys.modules["ai"] = sys.modules[__name__]
sys.modules["ai.integrity_agent"] = integrity_agent

__all__ = ["generate_real_integrity_report", "create_integrity_report"]
