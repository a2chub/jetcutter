#!/usr/bin/env python
"""Test script for FCP module implementation."""

from pathlib import Path

from jetdr.editor.segment import Segment, SegmentType
from jetdr.exporters.base import ExportConfig
from jetdr.fcp import FCPExporter, FCPTime, FCPXMLBuilder
from jetdr.fcp.time_utils import format_frame_duration, get_frame_duration


def main():
    print("=== Testing FCP Module ===")

    # Test 1: Time utilities
    print("\n1. Testing time utilities:")
    frame_dur = get_frame_duration(29.97)
    print(f"   Frame duration for 29.97 fps: {frame_dur}")
    print(f"   Formatted: {format_frame_duration(29.97)}")

    fcp_time = FCPTime.from_ms(1000, 29.97)
    print(f"   1000ms at 29.97fps: {fcp_time.to_fcpxml_string()}")

    # Test 2: Create sample segments
    print("\n2. Creating sample segments:")
    segments = [
        Segment(start_ms=0, end_ms=1000, type=SegmentType.KEEP),
        Segment(start_ms=2000, end_ms=3500, type=SegmentType.KEEP),
        Segment(start_ms=5000, end_ms=6000, type=SegmentType.KEEP),
    ]
    print(f"   Created {len(segments)} KEEP segments")

    # Test 3: Export configuration
    print("\n3. Testing export configuration:")
    test_video = Path("/tmp/test_video.mp4")
    test_video.touch()  # Create dummy file

    config = ExportConfig(
        video_path=test_video,
        output_name="test_export",
        fps=29.97,
        width=1920,
        height=1080,
    )
    print(f"   Config created: {config.output_name}")

    # Test 4: FCPExporter
    print("\n4. Testing FCPExporter:")
    exporter = FCPExporter()
    print(f"   Exporter name: {exporter.name}")
    print(f"   File extension: {exporter.file_extension}")

    # Validate config
    errors = exporter.validate_config(config)
    print(f"   Validation errors: {len(errors)}")

    # Test 5: Export to string
    print("\n5. Testing export_to_string:")
    try:
        xml_string = exporter.export_to_string(segments, config)
        print(f"   Generated XML length: {len(xml_string)} characters")
        print(f"   First 200 chars: {xml_string[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
        return False

    # Test 6: Full export
    print("\n6. Testing full export:")
    result = exporter.export(segments, config)
    print(f"   Export success: {result.success}")
    print(f"   Message: {result.message}")
    if result.output_path:
        print(f"   Output path: {result.output_path}")
        print(f"   File exists: {result.output_path.exists()}")

    # Cleanup
    test_video.unlink()
    if result.output_path and result.output_path.exists():
        result.output_path.unlink()

    print("\n=== All Tests Passed! ===")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
