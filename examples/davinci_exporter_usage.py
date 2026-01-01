"""
DaVinciExporter Usage Example

Demonstrates how to use the DaVinciExporter to create jet-cut timelines
directly in DaVinci Resolve.
"""

from pathlib import Path

# Note: These imports will work once the package is properly installed
from jetdr.davinci.exporter import DaVinciExporter
from jetdr.editor.segment import Segment, SegmentType
from jetdr.exporters.base import ExportConfig


def example_basic_usage():
    """Basic usage example: Connect, export, and disconnect."""

    # Create exporter instance
    exporter = DaVinciExporter()

    # Connect to DaVinci Resolve
    if not exporter.connect():
        print("Failed to connect to DaVinci Resolve")
        print("Make sure DaVinci Resolve Studio is running and a project is open")
        return

    try:
        # Create some example segments (KEEP segments will be exported)
        segments = [
            Segment(start_ms=0, end_ms=5000, type=SegmentType.KEEP),
            Segment(start_ms=5000, end_ms=8000, type=SegmentType.SILENCE),  # Will be skipped
            Segment(start_ms=8000, end_ms=15000, type=SegmentType.KEEP),
            Segment(start_ms=15000, end_ms=18000, type=SegmentType.FILLER),  # Will be skipped
            Segment(start_ms=18000, end_ms=25000, type=SegmentType.KEEP),
        ]

        # Create export configuration
        config = ExportConfig(
            video_path=Path("/path/to/your/video.mp4"),
            output_name="JetCut_Timeline",
            fps=29.97,
            width=1920,
            height=1080,
        )

        # Validate configuration
        errors = exporter.validate_config(config)
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return

        # Export to DaVinci Resolve
        result = exporter.export(segments, config)

        if result.success:
            print(f"✓ Success: {result.message}")
            print(f"  Timeline: {result.details.get('timeline_name')}")
            print(f"  Segments exported: {result.details.get('segments_exported')}")
        else:
            print(f"✗ Failed: {result.message}")

    finally:
        # Always disconnect when done
        exporter.disconnect()


def example_context_manager():
    """Example using context manager (auto-connect/disconnect)."""

    # Using context manager ensures connection is properly closed
    with DaVinciExporter() as exporter:
        if not exporter.is_connected:
            print("Failed to connect")
            return

        # Get project information
        project_info = exporter.get_project_info()
        if project_info:
            print(f"Current project: {project_info.get('name')}")
            print(f"Frame rate: {project_info.get('frame_rate')}")

        # List existing timelines
        timelines = exporter.list_timelines()
        print(f"Existing timelines: {timelines}")

        # Export segments (same as basic example)
        segments = [
            Segment(start_ms=0, end_ms=10000, type=SegmentType.KEEP),
        ]

        config = ExportConfig(
            video_path=Path("/path/to/video.mp4"),
            output_name="MyTimeline",
            fps=29.97,
        )

        result = exporter.export(segments, config)
        print(result.message)


def example_using_factory():
    """Example using the exporter factory pattern."""

    from jetdr.exporters import create_exporter

    # Create exporter using factory
    exporter = create_exporter("davinci")

    # Connect and use as normal
    if exporter.connect():
        print(f"Connected to {exporter.name}")

        # ... use exporter ...

        exporter.disconnect()


def example_error_handling():
    """Example with comprehensive error handling."""

    exporter = DaVinciExporter()

    try:
        # Connect
        if not exporter.connect():
            print("Connection failed. Please ensure:")
            print("  1. DaVinci Resolve Studio is running")
            print("  2. A project is open")
            print("  3. Scripting API is enabled")
            return

        # Validate before export
        config = ExportConfig(
            video_path=Path("/path/to/video.mp4"),
            output_name="Test",
            fps=29.97,
        )

        validation_errors = exporter.validate_config(config)
        if validation_errors:
            print("Configuration errors found:")
            for error in validation_errors:
                print(f"  - {error}")
            return

        # Export
        segments = [
            Segment(start_ms=0, end_ms=5000, type=SegmentType.KEEP),
        ]

        result = exporter.export(segments, config)

        if result.success:
            print(f"✓ {result.message}")
            # Access detailed information
            timeline_info = result.details.get("timeline_info", {})
            print(f"  Start frame: {timeline_info.get('start_frame')}")
            print(f"  End frame: {timeline_info.get('end_frame')}")
        else:
            print(f"✗ Export failed: {result.message}")
            print(f"  Error type: {result.details.get('error_type')}")

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        if exporter.is_connected:
            exporter.disconnect()


if __name__ == "__main__":
    print("DaVinciExporter Usage Examples")
    print("=" * 60)

    # Choose which example to run
    # example_basic_usage()
    # example_context_manager()
    # example_using_factory()
    # example_error_handling()

    print("\nNOTE: Update the video paths before running examples!")
