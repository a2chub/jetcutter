"""
Tests for FCP exporter.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from jetdr.editor.segment import Segment, SegmentType
from jetdr.exporters.base import ExportConfig
from jetdr.fcp.exporter import FCPExporter, create_fcp_exporter


class TestFCPExporter:
    """Tests for FCPExporter class."""

    @pytest.fixture
    def exporter(self) -> FCPExporter:
        """Create FCPExporter instance."""
        return FCPExporter()

    @pytest.fixture
    def temp_video(self, tmp_path: Path) -> Path:
        """Create a dummy video file for testing."""
        video_path = tmp_path / "test_video.mp4"
        video_path.write_bytes(b"dummy video content")
        return video_path

    @pytest.fixture
    def sample_segments(self) -> list[Segment]:
        """Create sample segments for testing."""
        return [
            Segment(start_ms=0, end_ms=1000, type=SegmentType.KEEP),
            Segment(start_ms=1000, end_ms=2000, type=SegmentType.SILENCE),
            Segment(start_ms=2000, end_ms=5000, type=SegmentType.KEEP),
            Segment(start_ms=5000, end_ms=6000, type=SegmentType.FILLER),
            Segment(start_ms=6000, end_ms=10000, type=SegmentType.KEEP),
        ]

    def test_name_property(self, exporter: FCPExporter) -> None:
        """Test exporter name property."""
        assert exporter.name == "Final Cut Pro"

    def test_file_extension_property(self, exporter: FCPExporter) -> None:
        """Test exporter file extension property."""
        assert exporter.file_extension == ".fcpxml"

    def test_validate_config_valid(
        self, exporter: FCPExporter, temp_video: Path
    ) -> None:
        """Test configuration validation with valid config."""
        config = ExportConfig(
            video_path=temp_video,
            output_name="test_output",
            fps=30.0,
            width=1920,
            height=1080,
        )
        errors = exporter.validate_config(config)
        assert errors == []

    def test_validate_config_missing_video_path(
        self, exporter: FCPExporter
    ) -> None:
        """Test validation fails without video path."""
        config = ExportConfig(
            video_path=None,  # type: ignore
            output_name="test_output",
            fps=30.0,
        )
        errors = exporter.validate_config(config)
        assert "video_path is required" in errors

    def test_validate_config_nonexistent_video(
        self, exporter: FCPExporter
    ) -> None:
        """Test validation fails with nonexistent video."""
        config = ExportConfig(
            video_path=Path("/nonexistent/video.mp4"),
            output_name="test_output",
            fps=30.0,
        )
        errors = exporter.validate_config(config)
        assert any("does not exist" in e for e in errors)

    def test_validate_config_missing_output_name(
        self, exporter: FCPExporter, temp_video: Path
    ) -> None:
        """Test validation fails without output name."""
        config = ExportConfig(
            video_path=temp_video,
            output_name="",
            fps=30.0,
        )
        errors = exporter.validate_config(config)
        assert "output_name is required" in errors

    def test_validate_config_invalid_fps(
        self, exporter: FCPExporter, temp_video: Path
    ) -> None:
        """Test validation fails with invalid FPS."""
        config = ExportConfig(
            video_path=temp_video,
            output_name="test_output",
            fps=-30.0,
        )
        errors = exporter.validate_config(config)
        assert any("fps must be positive" in e for e in errors)

    def test_validate_config_invalid_dimensions(
        self, exporter: FCPExporter, temp_video: Path
    ) -> None:
        """Test validation fails with invalid dimensions."""
        config = ExportConfig(
            video_path=temp_video,
            output_name="test_output",
            fps=30.0,
            width=-1920,
            height=0,
        )
        errors = exporter.validate_config(config)
        assert any("width must be positive" in e for e in errors)
        assert any("height must be positive" in e for e in errors)

    def test_export_success(
        self,
        exporter: FCPExporter,
        temp_video: Path,
        sample_segments: list[Segment],
    ) -> None:
        """Test successful export to FCPXML."""
        config = ExportConfig(
            video_path=temp_video,
            output_name="test_export",
            fps=30.0,
            width=1920,
            height=1080,
        )

        result = exporter.export(sample_segments, config)

        assert result.success is True
        assert result.output_path is not None
        assert result.output_path.exists()
        assert result.output_path.suffix == ".fcpxml"

        # Verify FCPXML content
        content = result.output_path.read_text(encoding="utf-8")
        assert "<?xml" in content
        assert "<fcpxml" in content
        assert "test_export" in content

        # Check details
        assert result.details is not None
        assert result.details["keep_segments"] == 3
        assert result.details["cut_segments"] == 2

    def test_export_no_keep_segments(
        self, exporter: FCPExporter, temp_video: Path
    ) -> None:
        """Test export fails with no KEEP segments."""
        segments = [
            Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE),
            Segment(start_ms=1000, end_ms=2000, type=SegmentType.FILLER),
        ]
        config = ExportConfig(
            video_path=temp_video,
            output_name="test_output",
            fps=30.0,
        )

        result = exporter.export(segments, config)

        assert result.success is False
        assert "No KEEP segments" in result.message

    def test_export_invalid_config(self, exporter: FCPExporter) -> None:
        """Test export fails with invalid config."""
        segments = [Segment(start_ms=0, end_ms=1000, type=SegmentType.KEEP)]
        config = ExportConfig(
            video_path=Path("/nonexistent/video.mp4"),
            output_name="test_output",
            fps=30.0,
        )

        result = exporter.export(segments, config)

        assert result.success is False
        assert "Invalid configuration" in result.message

    def test_export_to_string(
        self,
        exporter: FCPExporter,
        temp_video: Path,
        sample_segments: list[Segment],
    ) -> None:
        """Test export to string."""
        config = ExportConfig(
            video_path=temp_video,
            output_name="test_string_export",
            fps=30.0,
            width=1920,
            height=1080,
        )

        xml_string = exporter.export_to_string(sample_segments, config)

        assert "<?xml" in xml_string
        assert "<fcpxml" in xml_string
        assert "test_string_export" in xml_string

    def test_export_to_string_no_keep_segments(
        self, exporter: FCPExporter, temp_video: Path
    ) -> None:
        """Test export_to_string fails with no KEEP segments."""
        segments = [
            Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE),
        ]
        config = ExportConfig(
            video_path=temp_video,
            output_name="test_output",
            fps=30.0,
        )

        with pytest.raises(ValueError, match="No KEEP segments"):
            exporter.export_to_string(segments, config)

    def test_export_to_string_invalid_config(
        self, exporter: FCPExporter
    ) -> None:
        """Test export_to_string fails with invalid config."""
        segments = [Segment(start_ms=0, end_ms=1000, type=SegmentType.KEEP)]
        config = ExportConfig(
            video_path=Path("/nonexistent/video.mp4"),
            output_name="test_output",
            fps=30.0,
        )

        with pytest.raises(ValueError, match="Invalid configuration"):
            exporter.export_to_string(segments, config)

    def test_get_default_output_path(
        self, exporter: FCPExporter, temp_video: Path
    ) -> None:
        """Test default output path generation."""
        config = ExportConfig(
            video_path=temp_video,
            output_name="my_project",
            fps=30.0,
        )

        output_path = exporter.get_default_output_path(config)

        assert output_path.parent == temp_video.parent
        assert output_path.name == "my_project.fcpxml"

    def test_get_default_output_path_with_output_dir(
        self, exporter: FCPExporter, temp_video: Path, tmp_path: Path
    ) -> None:
        """Test output path with custom output directory."""
        output_dir = tmp_path / "custom_output"
        output_dir.mkdir()

        config = ExportConfig(
            video_path=temp_video,
            output_name="my_project",
            fps=30.0,
            metadata={"output_dir": str(output_dir)},
        )

        output_path = exporter.get_default_output_path(config)

        assert output_path.parent == output_dir
        assert output_path.name == "my_project.fcpxml"


class TestCreateFCPExporter:
    """Tests for create_fcp_exporter factory function."""

    def test_create_returns_exporter(self) -> None:
        """Test factory function returns FCPExporter instance."""
        exporter = create_fcp_exporter()
        assert isinstance(exporter, FCPExporter)


class TestExporterRegistry:
    """Tests for exporter registration."""

    def test_fcp_exporter_registered(self) -> None:
        """Test FCP exporter is registered in the registry."""
        from jetdr.exporters import ExporterRegistry

        available = ExporterRegistry.list_available()
        assert "fcp" in available

    def test_create_fcp_exporter_from_registry(self) -> None:
        """Test creating FCP exporter via registry."""
        from jetdr.exporters import create_exporter

        exporter = create_exporter("fcp")
        assert isinstance(exporter, FCPExporter)
