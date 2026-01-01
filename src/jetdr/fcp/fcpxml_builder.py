"""
fcpxml_builder - FCPXML document generator

Builds FCPXML v1.10 documents from segments.
Handles resource management, timeline structure, and XML formatting.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote

from jetdr.fcp.time_utils import FCPTime, format_frame_duration
from jetdr.utils.logger import get_logger

if TYPE_CHECKING:
    from jetdr.editor.segment import Segment
    from jetdr.exporters.base import ExportConfig

logger = get_logger(__name__)


class FCPXMLBuilder:
    """
    Builder for FCPXML v1.10 documents.

    Generates complete FCPXML structure with resources, library, event,
    project, sequence, and timeline clips.
    """

    FCPXML_VERSION = "1.10"
    DOCTYPE = "fcpxml"

    def __init__(self, config: ExportConfig) -> None:
        """
        Initialize FCPXML builder.

        Args:
            config: Export configuration with video path, FPS, dimensions, etc.
        """
        self.config = config
        self.fps = config.fps
        self.width = config.width or 1920
        self.height = config.height or 1080

        # Resource IDs
        self.format_id = "r1"
        self.asset_id = "r2"

        # Default names from metadata or config
        metadata = config.metadata or {}
        self.event_name = metadata.get("event_name", "jetDR Event")
        self.project_name = metadata.get("project_name", config.output_name)

    def build(self, segments: list[Segment]) -> ET.Element:
        """
        Build complete FCPXML element tree.

        Args:
            segments: List of segments to include in timeline

        Returns:
            Root fcpxml Element

        Raises:
            ValueError: If segments list is empty or invalid
        """
        if not segments:
            raise ValueError("Cannot build FCPXML with empty segments list")

        logger.info(f"Building FCPXML with {len(segments)} segments")

        # Create root element
        root = ET.Element("fcpxml", version=self.FCPXML_VERSION)

        # Add resources
        resources = self._build_resources()
        root.append(resources)

        # Add library structure
        library = self._build_library(segments)
        root.append(library)

        return root

    def _build_resources(self) -> ET.Element:
        """
        Build resources section with format and asset.

        Returns:
            resources Element
        """
        resources = ET.Element("resources")

        # Format resource
        ET.SubElement(
            resources,
            "format",
            id=self.format_id,
            frameDuration=format_frame_duration(self.fps),
            width=str(self.width),
            height=str(self.height),
        )

        # Asset resource
        video_uri = self._path_to_uri(self.config.video_path)
        asset_elem = ET.SubElement(
            resources,
            "asset",
            id=self.asset_id,
            src=video_uri,
            format=self.format_id,
        )

        # Add video name if available
        if self.config.video_path:
            asset_elem.set("name", self.config.video_path.stem)

        logger.debug(f"Created resources: format={self.format_id}, asset={self.asset_id}")

        return resources

    def _build_library(self, segments: list[Segment]) -> ET.Element:
        """
        Build library > event > project structure.

        Args:
            segments: List of segments to include

        Returns:
            library Element
        """
        library = ET.Element("library")

        # Event
        event = ET.SubElement(library, "event", name=self.event_name)

        # Project
        project = ET.SubElement(event, "project", name=self.project_name)

        # Sequence
        sequence = self._build_sequence(segments)
        project.append(sequence)

        return library

    def _build_sequence(self, segments: list[Segment]) -> ET.Element:
        """
        Build sequence with spine containing asset clips.

        Args:
            segments: List of segments to include

        Returns:
            sequence Element
        """
        sequence = ET.Element("sequence", format=self.format_id)

        # Spine (main timeline track)
        spine = ET.SubElement(sequence, "spine")

        # Add asset-clip for each segment
        for idx, segment in enumerate(segments):
            clip = self._build_asset_clip(segment, idx)
            spine.append(clip)

        logger.debug(f"Created sequence with {len(segments)} clips in spine")

        return sequence

    def _build_asset_clip(self, segment: Segment, index: int) -> ET.Element:
        """
        Build asset-clip element for a segment.

        Args:
            segment: Segment to convert to clip
            index: Clip index for naming

        Returns:
            asset-clip Element
        """
        # Calculate times
        start_time = FCPTime.from_ms(segment.start_ms, self.fps)
        duration_time = FCPTime.from_ms(segment.duration_ms, self.fps)

        # Create asset-clip
        clip = ET.Element(
            "asset-clip",
            ref=self.asset_id,
            offset=start_time.to_fcpxml_string(),
            duration=duration_time.to_fcpxml_string(),
        )

        # Add name if available in metadata
        clip_name = segment.metadata.get("name")
        if clip_name:
            clip.set("name", str(clip_name))
        else:
            clip.set("name", f"Clip {index + 1}")

        # Add start time (position in source video)
        clip.set("start", start_time.to_fcpxml_string())

        logger.debug(
            f"Created asset-clip {index + 1}: "
            f"start={start_time.to_fcpxml_string()}, "
            f"duration={duration_time.to_fcpxml_string()}"
        )

        return clip

    def _path_to_uri(self, path: Path) -> str:
        """
        Convert file path to file:// URI.

        Args:
            path: File path

        Returns:
            file:// URI string

        Examples:
            >>> builder._path_to_uri(Path("/Users/test/video.mp4"))
            'file:///Users/test/video.mp4'
        """
        # Resolve to absolute path
        abs_path = path.resolve()

        # Convert to URI format
        # Use quote to handle special characters, but don't quote '/'
        path_str = str(abs_path)
        encoded_path = quote(path_str, safe="/:")

        # Ensure it starts with file://
        if not encoded_path.startswith("/"):
            encoded_path = "/" + encoded_path

        return f"file://{encoded_path}"

    def to_string(self, segments: list[Segment], indent: bool = True) -> str:
        """
        Build FCPXML and convert to string.

        Args:
            segments: List of segments to include
            indent: Whether to indent XML for readability

        Returns:
            Complete FCPXML string with XML declaration and DOCTYPE
        """
        root = self.build(segments)

        if indent:
            self._indent_xml(root)

        # Convert to string
        xml_str = ET.tostring(root, encoding="unicode")

        # Add XML declaration and DOCTYPE
        header = f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE {self.DOCTYPE}>\n'

        return header + xml_str

    def write(self, segments: list[Segment], output_path: Path) -> Path:
        """
        Build FCPXML and write to file.

        Args:
            segments: List of segments to include
            output_path: Output file path

        Returns:
            Path to written file

        Raises:
            IOError: If file cannot be written
        """
        xml_content = self.to_string(segments, indent=True)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        output_path.write_text(xml_content, encoding="utf-8")

        logger.info(f"Wrote FCPXML to: {output_path}")

        return output_path

    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """
        Add indentation to XML for pretty printing.

        Modifies element tree in-place.

        Args:
            elem: Element to indent
            level: Current indentation level
        """
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent


def validate_fcpxml(xml_string: str) -> tuple[bool, str]:
    """
    Validate FCPXML string for basic correctness.

    Args:
        xml_string: FCPXML content to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is empty string
    """
    try:
        # Try to parse XML
        root = ET.fromstring(xml_string.split("\n", 2)[-1])  # Skip declaration/DOCTYPE

        # Check root element
        if root.tag != "fcpxml":
            return False, "Root element must be 'fcpxml'"

        # Check version
        version = root.get("version")
        if not version:
            return False, "Missing version attribute"

        # Check for resources
        resources = root.find("resources")
        if resources is None:
            return False, "Missing resources element"

        # Check for library
        library = root.find("library")
        if library is None:
            return False, "Missing library element"

        return True, ""

    except ET.ParseError as e:
        return False, f"XML parse error: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"
