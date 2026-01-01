"""
exporters - Timeline export modules

Provides abstract interfaces and concrete implementations for
exporting timelines to various NLE formats.
"""

from jetdr.exporters.base import (
    BaseTimelineExporter,
    ExportConfig,
    ExportResult,
    FileExporter,
    LiveConnectionExporter,
)
from jetdr.exporters.factory import ExporterRegistry, create_exporter

__all__ = [
    "BaseTimelineExporter",
    "ExportConfig",
    "ExportResult",
    "FileExporter",
    "LiveConnectionExporter",
    "ExporterRegistry",
    "create_exporter",
]


def _register_exporters() -> None:
    """Register built-in exporters."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        from jetdr.davinci.exporter import DaVinciExporter

        ExporterRegistry.register("davinci", DaVinciExporter)
    except ImportError as e:
        logger.debug(f"DaVinci exporter not available: {e}")

    try:
        from jetdr.fcp.exporter import FCPExporter

        ExporterRegistry.register("fcp", FCPExporter)
    except ImportError as e:
        logger.debug(f"FCP exporter not available: {e}")


# Auto-register on import
_register_exporters()
