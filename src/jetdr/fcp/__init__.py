"""
fcp - Final Cut Pro export module

Provides FCPXML v1.10 export functionality for Final Cut Pro.
Includes frame-accurate time calculations and timeline building.
"""

from jetdr.fcp.exporter import FCPExporter, create_fcp_exporter
from jetdr.fcp.fcpxml_builder import FCPXMLBuilder, validate_fcpxml
from jetdr.fcp.time_utils import FCPTime, format_frame_duration, get_frame_duration

__all__ = [
    # Exporter
    "FCPExporter",
    "create_fcp_exporter",
    # FCPXML Builder
    "FCPXMLBuilder",
    "validate_fcpxml",
    # Time utilities
    "FCPTime",
    "format_frame_duration",
    "get_frame_duration",
]
