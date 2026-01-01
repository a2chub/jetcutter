"""
segment モジュールのテスト
"""

import pytest

from jetcutter.editor.segment import (
    Segment,
    SegmentType,
    calculate_complement_segments,
    merge_overlapping_segments,
)


class TestSegment:
    """Segmentクラスのテスト"""

    def test_create_segment(self) -> None:
        """Segmentの生成テスト"""
        seg = Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE)
        assert seg.start_ms == 0
        assert seg.end_ms == 1000
        assert seg.type == SegmentType.SILENCE
        assert seg.duration_ms == 1000

    def test_segment_validation_negative_start(self) -> None:
        """開始時間が負の場合のバリデーションテスト"""
        with pytest.raises(ValueError, match="start_ms must be >= 0"):
            Segment(start_ms=-1, end_ms=1000, type=SegmentType.SILENCE)

    def test_segment_validation_end_before_start(self) -> None:
        """終了時間が開始時間より前の場合のバリデーションテスト"""
        with pytest.raises(ValueError, match="end_ms must be >= start_ms"):
            Segment(start_ms=1000, end_ms=500, type=SegmentType.SILENCE)

    def test_overlaps_true(self) -> None:
        """重複するセグメントのテスト"""
        seg1 = Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE)
        seg2 = Segment(start_ms=500, end_ms=1500, type=SegmentType.SILENCE)
        assert seg1.overlaps(seg2)
        assert seg2.overlaps(seg1)

    def test_overlaps_false(self) -> None:
        """重複しないセグメントのテスト"""
        seg1 = Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE)
        seg2 = Segment(start_ms=2000, end_ms=3000, type=SegmentType.SILENCE)
        assert not seg1.overlaps(seg2)
        assert not seg2.overlaps(seg1)

    def test_overlaps_adjacent(self) -> None:
        """隣接するセグメント（重複なし）のテスト"""
        seg1 = Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE)
        seg2 = Segment(start_ms=1000, end_ms=2000, type=SegmentType.SILENCE)
        assert not seg1.overlaps(seg2)

    def test_contains(self) -> None:
        """包含テスト"""
        seg1 = Segment(start_ms=0, end_ms=2000, type=SegmentType.SILENCE)
        seg2 = Segment(start_ms=500, end_ms=1500, type=SegmentType.SILENCE)
        assert seg1.contains(seg2)
        assert not seg2.contains(seg1)

    def test_merge(self) -> None:
        """マージテスト"""
        seg1 = Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE)
        seg2 = Segment(start_ms=500, end_ms=2000, type=SegmentType.SILENCE)
        merged = seg1.merge(seg2)
        assert merged.start_ms == 0
        assert merged.end_ms == 2000
        assert merged.type == SegmentType.SILENCE

    def test_apply_margin(self) -> None:
        """マージン適用テスト"""
        seg = Segment(start_ms=1000, end_ms=2000, type=SegmentType.KEEP)
        with_margin = seg.apply_margin(before_ms=100, after_ms=100)
        assert with_margin.start_ms == 900
        assert with_margin.end_ms == 2100

    def test_apply_margin_with_bounds(self) -> None:
        """境界付きマージン適用テスト"""
        seg = Segment(start_ms=50, end_ms=1000, type=SegmentType.KEEP)
        with_margin = seg.apply_margin(before_ms=100, after_ms=100, max_duration_ms=1050)
        assert with_margin.start_ms == 0  # 0未満にはならない
        assert with_margin.end_ms == 1050  # max_durationを超えない

    def test_align_to_frame(self) -> None:
        """フレームアライメントテスト"""
        seg = Segment(start_ms=1001, end_ms=2001, type=SegmentType.KEEP)
        aligned = seg.align_to_frame(fps=30.0)
        # 30fpsでは1フレーム≒33.33ms
        # 開始は切り捨て、終了は切り上げ
        assert aligned.start_ms <= seg.start_ms  # 開始は元の値以下
        assert aligned.end_ms >= seg.end_ms  # 終了は元の値以上
        # フレーム境界にアラインされている（整数フレーム数に変換可能）
        frame_duration_ms = 1000 / 30
        start_frames = aligned.start_ms / frame_duration_ms
        end_frames = aligned.end_ms / frame_duration_ms
        # 浮動小数点の精度を考慮して許容範囲を0.02に設定
        assert abs(start_frames - round(start_frames)) < 0.02
        assert abs(end_frames - round(end_frames)) < 0.02

    def test_to_dict_and_from_dict(self) -> None:
        """辞書変換の往復テスト"""
        original = Segment(
            start_ms=1000,
            end_ms=2000,
            type=SegmentType.FILLER,
            metadata={"word": "えっと"},
        )
        data = original.to_dict()
        restored = Segment.from_dict(data)
        assert restored.start_ms == original.start_ms
        assert restored.end_ms == original.end_ms
        assert restored.type == original.type
        assert restored.metadata == original.metadata


class TestMergeOverlappingSegments:
    """merge_overlapping_segments関数のテスト"""

    def test_empty_list(self) -> None:
        """空リストのテスト"""
        result = merge_overlapping_segments([])
        assert result == []

    def test_single_segment(self) -> None:
        """単一セグメントのテスト"""
        segments = [Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE)]
        result = merge_overlapping_segments(segments)
        assert len(result) == 1
        assert result[0].start_ms == 0
        assert result[0].end_ms == 1000

    def test_no_overlap(self) -> None:
        """重複なしのテスト"""
        segments = [
            Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE),
            Segment(start_ms=2000, end_ms=3000, type=SegmentType.SILENCE),
        ]
        result = merge_overlapping_segments(segments)
        assert len(result) == 2

    def test_with_overlap(self) -> None:
        """重複ありのテスト"""
        segments = [
            Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE),
            Segment(start_ms=500, end_ms=1500, type=SegmentType.SILENCE),
        ]
        result = merge_overlapping_segments(segments)
        assert len(result) == 1
        assert result[0].start_ms == 0
        assert result[0].end_ms == 1500

    def test_unsorted_input(self) -> None:
        """ソートされていない入力のテスト"""
        segments = [
            Segment(start_ms=2000, end_ms=3000, type=SegmentType.SILENCE),
            Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE),
        ]
        result = merge_overlapping_segments(segments)
        assert len(result) == 2
        assert result[0].start_ms == 0  # ソート済み


class TestCalculateComplementSegments:
    """calculate_complement_segments関数のテスト"""

    def test_empty_segments(self) -> None:
        """空リストの場合は全体が補集合"""
        result = calculate_complement_segments([], total_duration_ms=10000)
        assert len(result) == 1
        assert result[0].start_ms == 0
        assert result[0].end_ms == 10000
        assert result[0].type == SegmentType.KEEP

    def test_full_coverage(self) -> None:
        """全体をカバーする場合は補集合なし"""
        segments = [Segment(start_ms=0, end_ms=10000, type=SegmentType.SILENCE)]
        result = calculate_complement_segments(segments, total_duration_ms=10000)
        assert len(result) == 0

    def test_gaps_in_segments(self) -> None:
        """ギャップがある場合のテスト"""
        segments = [
            Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE),
            Segment(start_ms=3000, end_ms=5000, type=SegmentType.SILENCE),
            Segment(start_ms=8000, end_ms=10000, type=SegmentType.SILENCE),
        ]
        result = calculate_complement_segments(segments, total_duration_ms=10000)
        assert len(result) == 2
        assert result[0].start_ms == 1000
        assert result[0].end_ms == 3000
        assert result[1].start_ms == 5000
        assert result[1].end_ms == 8000
