"""
fcp - Final Cut Pro export module

Provides FCPXML v1.10 export functionality for Final Cut Pro.
Includes frame-accurate time calculations and timeline building.
"""

from jetcutter.fcp.exporter import FCPExporter, create_fcp_exporter
from jetcutter.fcp.fcpxml_builder import FCPXMLBuilder, validate_fcpxml
from jetcutter.fcp.time_utils import FCPTime, format_frame_duration, get_frame_duration

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
