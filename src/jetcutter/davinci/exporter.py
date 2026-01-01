"""
exporter - DaVinci Resolve用タイムラインエクスポーター

既存のTimelineBuilderをLiveConnectionExporterインターフェースでラップし、
統一的なエクスポートAPIを提供する。
"""

from __future__ import annotations

from jetcutter.davinci.connection import DaVinciConnectionError, DRConnection
from jetcutter.davinci.media_pool import DRMediaPool
from jetcutter.davinci.project import DRProject
from jetcutter.davinci.timeline_builder import TimelineBuilder, TimelineCreationError
from jetcutter.editor.segment import Segment
from jetcutter.exporters.base import ExportConfig, ExportResult, LiveConnectionExporter
from jetcutter.utils.logger import get_logger

logger = get_logger(__name__)


class DaVinciExporter(LiveConnectionExporter):
    """
    DaVinci Resolve timeline exporter.

    Wraps the existing TimelineBuilder for the LiveConnectionExporter interface.
    Requires DaVinci Resolve Studio to be running for API access.
    """

    def __init__(self) -> None:
        self._connection: DRConnection | None = None
        self._project: DRProject | None = None
        self._media_pool: DRMediaPool | None = None
        self._builder: TimelineBuilder | None = None

    @property
    def name(self) -> str:
        """Human-readable name of the exporter"""
        return "DaVinci Resolve"

    @property
    def file_extension(self) -> str:
        """File extension for exported files (empty for live API)"""
        return ""  # No file output - direct API

    def validate_config(self, config: ExportConfig) -> list[str]:
        """
        Validate export configuration.

        Args:
            config: Export configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Check video file exists
        if not config.video_path.exists():
            errors.append(f"Video file not found: {config.video_path}")
        elif not config.video_path.is_file():
            errors.append(f"Video path is not a file: {config.video_path}")

        # Check output name is not empty
        if not config.output_name or not config.output_name.strip():
            errors.append("Output name cannot be empty")

        # Check FPS is positive
        if config.fps <= 0:
            errors.append(f"FPS must be positive, got: {config.fps}")

        # Check resolution if provided
        if config.width is not None and config.width <= 0:
            errors.append(f"Width must be positive, got: {config.width}")
        if config.height is not None and config.height <= 0:
            errors.append(f"Height must be positive, got: {config.height}")

        # Check connection if already established
        if self._connection is not None and not self.is_connected:
            errors.append("DaVinci Resolve connection was established but is no longer active")

        return errors

    def connect(self) -> bool:
        """
        Establish connection to DaVinci Resolve.

        Returns:
            True if connection successful, False otherwise
        """
        if self._connection is not None and self._connection.is_connected:
            logger.debug("Already connected to DaVinci Resolve")
            return True

        try:
            logger.info("Connecting to DaVinci Resolve...")

            # Create connection
            self._connection = DRConnection()
            if not self._connection.connect():
                logger.error("Failed to connect to DaVinci Resolve")
                self._connection = None
                return False

            # Initialize project and media pool
            self._project = DRProject(self._connection)
            self._media_pool = DRMediaPool(self._project)
            self._builder = TimelineBuilder(self._project, self._media_pool)

            # Get current project or fail
            try:
                self._project.get_current_project()
                logger.info(
                    f"Connected to DaVinci Resolve "
                    f"(Project: {self._project.get_project_name()})"
                )
                return True
            except DaVinciConnectionError as e:
                logger.error(f"No project is currently open: {e}")
                self.disconnect()
                return False

        except DaVinciConnectionError as e:
            logger.error(f"Connection failed: {e}")
            self.disconnect()
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Disconnect from DaVinci Resolve."""
        if self._connection is not None:
            self._connection.disconnect()

        self._connection = None
        self._project = None
        self._media_pool = None
        self._builder = None

        logger.info("Disconnected from DaVinci Resolve")

    @property
    def is_connected(self) -> bool:
        """Whether currently connected to DaVinci Resolve."""
        return self._connection is not None and self._connection.is_connected

    def export(self, segments: list[Segment], config: ExportConfig) -> ExportResult:
        """
        Export segments to DaVinci Resolve timeline.

        Args:
            segments: List of Segment objects to export
            config: Export configuration

        Returns:
            ExportResult with success status and details
        """
        # Validate configuration
        errors = self.validate_config(config)
        if errors:
            error_msg = "; ".join(errors)
            logger.error(f"Configuration validation failed: {error_msg}")
            return ExportResult(
                success=False,
                message=f"Configuration validation failed: {error_msg}",
                details={"errors": errors},
            )

        # Check connection
        if not self.is_connected:
            logger.error("Not connected to DaVinci Resolve")
            return ExportResult(
                success=False,
                message="Not connected to DaVinci Resolve. Please call connect() first.",
            )

        # Check segments
        if not segments:
            logger.warning("No segments to export")
            return ExportResult(
                success=False,
                message="No segments to export",
            )

        # Ensure builder is available
        if self._builder is None:
            logger.error("TimelineBuilder not initialized")
            return ExportResult(
                success=False,
                message="TimelineBuilder not initialized",
            )

        try:
            logger.info(
                f"Exporting {len(segments)} segments to timeline '{config.output_name}'"
            )

            # Create timeline from segments
            timeline = self._builder.create_timeline_from_segments(
                video_path=config.video_path,
                segments=segments,
                timeline_name=config.output_name,
                fps=config.fps,
            )

            # Get timeline info for result details
            timeline_info = self._builder.get_timeline_info(timeline)

            logger.info(f"Successfully created timeline: {config.output_name}")

            return ExportResult(
                success=True,
                output_path=None,  # No file output for live API
                message=f"Timeline '{config.output_name}' created successfully in DaVinci Resolve",
                details={
                    "timeline_name": config.output_name,
                    "timeline_info": timeline_info,
                    "segments_count": len(segments),
                    "fps": config.fps,
                    "project_name": self._project.get_project_name()
                    if self._project
                    else None,
                },
            )

        except TimelineCreationError as e:
            logger.error(f"Timeline creation failed: {e}")
            return ExportResult(
                success=False,
                message=f"Timeline creation failed: {e}",
                details={"error_type": "TimelineCreationError"},
            )
        except DaVinciConnectionError as e:
            logger.error(f"DaVinci Resolve error: {e}")
            return ExportResult(
                success=False,
                message=f"DaVinci Resolve error: {e}",
                details={"error_type": "DaVinciConnectionError"},
            )
        except Exception as e:
            logger.error(f"Unexpected error during export: {e}")
            return ExportResult(
                success=False,
                message=f"Unexpected error: {e}",
                details={"error_type": type(e).__name__},
            )

    def get_project_info(self) -> dict | None:
        """
        Get current DaVinci Resolve project information.

        Returns:
            Dictionary with project info, or None if not connected
        """
        if not self.is_connected or self._project is None:
            return None

        try:
            return self._project.get_project_settings()
        except Exception as e:
            logger.error(f"Failed to get project info: {e}")
            return None

    def list_timelines(self) -> list[str]:
        """
        List all timelines in the current project.

        Returns:
            List of timeline names, or empty list if not connected
        """
        if not self.is_connected or self._builder is None:
            return []

        try:
            return self._builder.list_timelines()
        except Exception as e:
            logger.error(f"Failed to list timelines: {e}")
            return []
