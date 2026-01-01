"""
editor - カットロジック・区間管理モジュール

区間データモデル、マージロジック、タイムライン生成を担当。
"""

from jetcutter.editor.merger import SegmentMerger, quick_merge
from jetcutter.editor.segment import (
    Segment,
    SegmentType,
    calculate_complement_segments,
    merge_overlapping_segments,
)

__all__ = [
    "Segment",
    "SegmentType",
    "merge_overlapping_segments",
    "calculate_complement_segments",
    "SegmentMerger",
    "quick_merge",
]
