"""
exporter - Final Cut Pro exporter

Implements FileExporter interface for exporting segments to FCPXML format.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jetcutter.editor.segment import Segment, SegmentType
from jetcutter.exporters.base import ExportConfig, ExportResult, FileExporter
from jetcutter.fcp.fcpxml_builder import FCPXMLBuilder, validate_fcpxml
from jetcutter.utils.logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class FCPExporter(FileExporter):
    """
    Final Cut Pro exporter.

    Exports segments to FCPXML v1.10 format for import into Final Cut Pro.
    Only exports KEEP segments to create a trimmed timeline.
    """

    @property
    def name(self) -> str:
        """Human-readable name of the exporter."""
        return "Final Cut Pro"

    @property
    def file_extension(self) -> str:
        """File extension for exported files."""
        return ".fcpxml"

    def validate_config(self, config: ExportConfig) -> list[str]:
        """
        Validate export configuration.

        Args:
            config: Export configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Check video path
        if not config.video_path:
            errors.append("video_path is required")
        elif not config.video_path.exists():
            errors.append(f"video_path does not exist: {config.video_path}")
        elif not config.video_path.is_file():
            errors.append(f"video_path is not a file: {config.video_path}")

        # Check output name
        if not config.output_name:
            errors.append("output_name is required")

        # Check FPS
        if config.fps <= 0:
            errors.append(f"fps must be positive, got {config.fps}")

        # Check dimensions if provided
        if config.width is not None and config.width <= 0:
            errors.append(f"width must be positive, got {config.width}")

        if config.height is not None and config.height <= 0:
            errors.append(f"height must be positive, got {config.height}")

        return errors

    def export(
        self,
        segments: list[Segment],
        config: ExportConfig,
    ) -> ExportResult:
        """
        Export segments to FCPXML file.

        Only KEEP segments are exported to create the final timeline.

        Args:
            segments: List of Segment objects to export
            config: Export configuration

        Returns:
            ExportResult with success status and output path
        """
        try:
            # Validate configuration
            validation_errors = self.validate_config(config)
            if validation_errors:
                error_msg = "; ".join(validation_errors)
                logger.error(f"Configuration validation failed: {error_msg}")
                return ExportResult(
                    success=False,
                    message=f"Invalid configuration: {error_msg}",
                    details={"validation_errors": validation_errors},
                )

            # Filter for KEEP segments only
            keep_segments = [s for s in segments if s.type == SegmentType.KEEP]

            if not keep_segments:
                logger.warning("No KEEP segments to export")
                return ExportResult(
                    success=False,
                    message="No KEEP segments found in segment list",
                    details={"total_segments": len(segments), "keep_segments": 0},
                )

            logger.info(
                f"Exporting {len(keep_segments)} KEEP segments "
                f"(out of {len(segments)} total segments)"
            )

            # Build FCPXML
            builder = FCPXMLBuilder(config)
            output_path = self.get_default_output_path(config)

            # Write to file
            written_path = builder.write(keep_segments, output_path)

            # Validate output
            xml_content = written_path.read_text(encoding="utf-8")
            is_valid, validation_msg = validate_fcpxml(xml_content)

            if not is_valid:
                logger.error(f"Generated FCPXML failed validation: {validation_msg}")
                return ExportResult(
                    success=False,
                    output_path=written_path,
                    message=f"FCPXML validation failed: {validation_msg}",
                    details={"validation_error": validation_msg},
                )

            # Calculate statistics
            total_duration_ms = sum(s.duration_ms for s in keep_segments)
            details = {
                "total_segments": len(segments),
                "keep_segments": len(keep_segments),
                "cut_segments": len(segments) - len(keep_segments),
                "total_duration_ms": total_duration_ms,
                "fps": config.fps,
                "resolution": f"{config.width or 'auto'}x{config.height or 'auto'}",
            }

            logger.info(
                f"Successfully exported FCPXML to: {written_path}\n"
                f"  Keep segments: {len(keep_segments)}\n"
                f"  Total duration: {total_duration_ms / 1000:.2f}s"
            )

            return ExportResult(
                success=True,
                output_path=written_path,
                message=f"Successfully exported {len(keep_segments)} segments to FCPXML",
                details=details,
            )

        except Exception as e:
            logger.exception(f"Export failed: {e}")
            return ExportResult(
                success=False,
                message=f"Export failed: {e}",
                details={"error": str(e), "error_type": type(e).__name__},
            )

    def export_to_string(
        self,
        segments: list[Segment],
        config: ExportConfig,
    ) -> str:
        """
        Export segments to FCPXML string.

        Useful for testing and programmatic manipulation.

        Args:
            segments: List of Segment objects to export
            config: Export configuration

        Returns:
            String representation of FCPXML

        Raises:
            ValueError: If configuration is invalid or no KEEP segments
        """
        # Validate configuration
        validation_errors = self.validate_config(config)
        if validation_errors:
            raise ValueError(f"Invalid configuration: {'; '.join(validation_errors)}")

        # Filter for KEEP segments only
        keep_segments = [s for s in segments if s.type == SegmentType.KEEP]

        if not keep_segments:
            raise ValueError("No KEEP segments to export")

        # Build FCPXML
        builder = FCPXMLBuilder(config)
        return builder.to_string(keep_segments, indent=True)

    def get_default_output_path(self, config: ExportConfig) -> Path:
        """
        Generate default output path based on config.

        Args:
            config: Export configuration

        Returns:
            Default output file path in same directory as video
        """
        # Use metadata output_dir if provided
        metadata = config.metadata or {}
        output_dir = metadata.get("output_dir")

        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = config.video_path.parent

        return output_dir / f"{config.output_name}{self.file_extension}"


def create_fcp_exporter() -> FCPExporter:
    """
    Factory function to create FCP exporter instance.

    Returns:
        FCPExporter instance
    """
    return FCPExporter()
