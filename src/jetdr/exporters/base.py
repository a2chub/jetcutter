"""
base - Abstract base classes for timeline exporters

Defines the interface that all editor-specific exporters must implement.
This enables the processing pipeline to be editor-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExportConfig:
    """
    Common export configuration shared by all exporters.

    Attributes:
        video_path: Path to the source video file
        output_name: Name for the exported timeline
        fps: Frame rate for timeline
        width: Video width (optional, auto-detect if None)
        height: Video height (optional, auto-detect if None)
        metadata: Additional exporter-specific settings
    """

    video_path: Path
    output_name: str
    fps: float = 29.97
    width: int | None = None
    height: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.video_path, str):
            self.video_path = Path(self.video_path)


@dataclass
class ExportResult:
    """
    Result of an export operation.

    Attributes:
        success: Whether the export completed successfully
        output_path: Path to the exported file (if applicable)
        message: Human-readable status message
        details: Additional export details (editor-specific)
    """

    success: bool
    output_path: Path | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class BaseTimelineExporter(ABC):
    """
    Abstract base class for timeline exporters.

    All editor-specific exporters (DaVinci, FCP, Premiere, etc.)
    must inherit from this class and implement the required methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the exporter (e.g., 'Final Cut Pro')"""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for exported files (e.g., '.fcpxml')"""
        ...

    @abstractmethod
    def validate_config(self, config: ExportConfig) -> list[str]:
        """
        Validate export configuration.

        Args:
            config: Export configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        ...

    @abstractmethod
    def export(
        self,
        segments: list,
        config: ExportConfig,
    ) -> ExportResult:
        """
        Export segments to editor-specific format.

        Args:
            segments: List of Segment objects to export
            config: Export configuration

        Returns:
            ExportResult with success status and output path
        """
        ...

    def get_default_output_path(self, config: ExportConfig) -> Path:
        """
        Generate default output path based on config.

        Args:
            config: Export configuration

        Returns:
            Default output file path
        """
        return config.video_path.parent / f"{config.output_name}{self.file_extension}"


class FileExporter(BaseTimelineExporter):
    """
    Extended interface for exporters that generate static files.

    Used by exporters like FCP (FCPXML), EDL, AAF, etc.
    that create importable files without live connection.
    """

    @abstractmethod
    def export_to_string(
        self,
        segments: list,
        config: ExportConfig,
    ) -> str:
        """
        Export segments to string representation.

        Useful for testing and programmatic manipulation.

        Args:
            segments: List of Segment objects to export
            config: Export configuration

        Returns:
            String representation of the export format
        """
        ...


class LiveConnectionExporter(BaseTimelineExporter):
    """
    Extended interface for exporters that connect to live applications.

    Used by exporters like DaVinci Resolve that require a running
    application instance rather than generating static files.
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the editor application.

        Returns:
            True if connection successful, False otherwise
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the editor application."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Whether currently connected to the editor."""
        ...

    def __enter__(self) -> LiveConnectionExporter:
        """Context manager entry - connect to editor."""
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - disconnect from editor."""
        self.disconnect()
