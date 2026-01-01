"""Tests for editor.merger module."""

import pytest

from jetcutter.editor.merger import SegmentMerger, quick_merge
from jetcutter.editor.segment import Segment, SegmentType


class TestSegmentMerger:
    """Tests for SegmentMerger class."""

    def test_init_with_defaults(self) -> None:
        """Creates merger with default parameters."""
        merger = SegmentMerger()

        assert merger.margin_before_ms == 100
        assert merger.margin_after_ms == 100
        assert merger.min_keep_duration_ms == 500
        assert merger.fps == pytest.approx(29.97, rel=0.01)

    def test_init_with_custom_params(self) -> None:
        """Creates merger with custom parameters."""
        merger = SegmentMerger(
            margin_before_ms=200,
            margin_after_ms=300,
            min_keep_duration_ms=1000,
            fps=30.0,
        )

        assert merger.margin_before_ms == 200
        assert merger.margin_after_ms == 300
        assert merger.min_keep_duration_ms == 1000
        assert merger.fps == 30.0

    def test_calculate_keep_segments_empty_inputs(self) -> None:
        """Returns full duration when no silence or fillers."""
        merger = SegmentMerger()
        keep_segments = merger.calculate_keep_segments(
            silence_segments=[],
            filler_segments=[],
            total_duration_ms=10000,
        )

        assert len(keep_segments) == 1
        assert keep_segments[0].start_ms == 0
        # Duration should cover most of the video (minus frame alignment)
        assert keep_segments[0].duration_ms >= 9500

    def test_calculate_keep_segments_with_silence(self) -> None:
        """Correctly excludes silence regions."""
        merger = SegmentMerger(
            margin_before_ms=0,
            margin_after_ms=0,
            min_keep_duration_ms=100,
            fps=30.0,
        )
        silence = [Segment(2000, 3000, SegmentType.SILENCE)]

        keep_segments = merger.calculate_keep_segments(
            silence_segments=silence,
            filler_segments=[],
            total_duration_ms=5000,
        )

        # Should have two keep segments: 0-2000 and 3000-5000
        assert len(keep_segments) == 2
        assert keep_segments[0].start_ms == 0
        assert keep_segments[0].end_ms <= 2000
        assert keep_segments[1].start_ms >= 3000

    def test_calculate_keep_segments_with_overlapping_silence_and_filler(self) -> None:
        """Merges overlapping silence and filler regions."""
        merger = SegmentMerger(
            margin_before_ms=0,
            margin_after_ms=0,
            min_keep_duration_ms=100,
            fps=30.0,
        )
        silence = [Segment(1000, 2500, SegmentType.SILENCE)]
        filler = [Segment(2000, 3000, SegmentType.FILLER)]  # Overlaps with silence

        keep_segments = merger.calculate_keep_segments(
            silence_segments=silence,
            filler_segments=filler,
            total_duration_ms=5000,
        )

        # Should have two keep segments: 0-1000 and 3000-5000
        assert len(keep_segments) == 2
        assert keep_segments[0].end_ms <= 1000
        assert keep_segments[1].start_ms >= 3000

    def test_calculate_keep_segments_applies_margin(self) -> None:
        """Applies margins to keep segments."""
        merger = SegmentMerger(
            margin_before_ms=100,
            margin_after_ms=100,
            min_keep_duration_ms=100,
            fps=30.0,
        )
        silence = [Segment(2000, 3000, SegmentType.SILENCE)]

        keep_segments = merger.calculate_keep_segments(
            silence_segments=silence,
            filler_segments=[],
            total_duration_ms=5000,
        )

        # With margin, first segment should extend towards silence
        assert keep_segments[0].end_ms >= 2000  # Margin extends into silence
        # Second segment should start earlier
        assert keep_segments[1].start_ms <= 3000  # Margin extends into silence

    def test_calculate_keep_segments_filters_short_segments(self) -> None:
        """Filters out segments shorter than minimum duration."""
        merger = SegmentMerger(
            margin_before_ms=0,
            margin_after_ms=0,
            min_keep_duration_ms=1000,  # High minimum
            fps=30.0,
        )
        # Two silences leaving only a short gap
        silence = [
            Segment(0, 2000, SegmentType.SILENCE),
            Segment(2500, 5000, SegmentType.SILENCE),  # Only 500ms gap
        ]

        keep_segments = merger.calculate_keep_segments(
            silence_segments=silence,
            filler_segments=[],
            total_duration_ms=5000,
        )

        # The 500ms gap should be filtered out (below 1000ms minimum)
        assert len(keep_segments) == 0

    def test_get_cut_summary(self) -> None:
        """Returns correct summary statistics."""
        merger = SegmentMerger()
        silence = [Segment(0, 1000, SegmentType.SILENCE)]
        filler = [Segment(4000, 4500, SegmentType.FILLER)]
        keep = [Segment(1000, 4000, SegmentType.KEEP)]

        summary = merger.get_cut_summary(
            silence_segments=silence,
            filler_segments=filler,
            keep_segments=keep,
            total_duration_ms=5000,
        )

        assert summary["total_duration_ms"] == 5000
        assert summary["silence_segments_count"] == 1
        assert summary["silence_total_ms"] == 1000
        assert summary["filler_segments_count"] == 1
        assert summary["filler_total_ms"] == 500
        assert summary["keep_segments_count"] == 1
        assert summary["keep_total_ms"] == 3000
        assert summary["cut_total_ms"] == 2000
        assert summary["reduction_percent"] == pytest.approx(40.0, rel=0.01)

    def test_get_cut_summary_zero_duration(self) -> None:
        """Handles zero duration edge case."""
        merger = SegmentMerger()
        summary = merger.get_cut_summary(
            silence_segments=[],
            filler_segments=[],
            keep_segments=[],
            total_duration_ms=0,
        )

        assert summary["reduction_percent"] == 0

    def test_merge_overlapping(self) -> None:
        """Merges overlapping segments correctly."""
        merger = SegmentMerger()
        segments = [
            Segment(0, 1000, SegmentType.KEEP),
            Segment(500, 1500, SegmentType.KEEP),  # Overlaps
            Segment(3000, 4000, SegmentType.KEEP),  # No overlap
        ]

        merged = merger.merge_overlapping(segments)

        assert len(merged) == 2
        assert merged[0].start_ms == 0
        assert merged[0].end_ms == 1500
        assert merged[1].start_ms == 3000


class TestQuickMerge:
    """Tests for quick_merge function."""

    def test_quick_merge_basic(self) -> None:
        """Quick merge produces expected results."""
        silence = [Segment(1000, 2000, SegmentType.SILENCE)]
        filler = [Segment(3000, 3500, SegmentType.FILLER)]

        keep_segments = quick_merge(
            silence_segments=silence,
            filler_segments=filler,
            total_duration_ms=5000,
            margin_ms=50,
            min_keep_ms=100,
            fps=30.0,
        )

        # Should have multiple keep segments excluding silence and filler
        assert len(keep_segments) >= 2

    def test_quick_merge_uses_default_params(self) -> None:
        """Quick merge works with default parameters."""
        keep_segments = quick_merge(
            silence_segments=[],
            filler_segments=[],
            total_duration_ms=10000,
        )

        assert len(keep_segments) == 1
