"""
segment - 区間データモデル

時間区間を表すデータクラスと、区間の種類を表す列挙型を定義。
すべてのモジュールが共有する共通データモデル。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SegmentType(Enum):
    """区間の種類を表す列挙型"""

    SILENCE = "silence"  # 無音区間
    FILLER = "filler"  # フィラー区間（「あー」「えっと」等）
    KEEP = "keep"  # 保持区間（編集後に残す区間）
    CUT = "cut"  # 削除区間


@dataclass
class Segment:
    """
    時間区間を表すデータクラス

    Attributes:
        start_ms: 開始時間（ミリ秒）
        end_ms: 終了時間（ミリ秒）
        type: 区間の種類
        metadata: 追加情報（検出単語、信頼度など）
    """

    start_ms: int
    end_ms: int
    type: SegmentType
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.start_ms < 0:
            raise ValueError(f"start_ms must be >= 0, got {self.start_ms}")
        if self.end_ms < self.start_ms:
            raise ValueError(
                f"end_ms must be >= start_ms, got start_ms={self.start_ms}, end_ms={self.end_ms}"
            )

    @property
    def duration_ms(self) -> int:
        """区間の長さ（ミリ秒）"""
        return self.end_ms - self.start_ms

    def overlaps(self, other: Segment) -> bool:
        """
        他の区間と重複するかチェック

        Args:
            other: 比較対象の区間

        Returns:
            重複する場合True
        """
        return self.start_ms < other.end_ms and other.start_ms < self.end_ms

    def contains(self, other: Segment) -> bool:
        """
        他の区間を完全に含むかチェック

        Args:
            other: 比較対象の区間

        Returns:
            完全に含む場合True
        """
        return self.start_ms <= other.start_ms and self.end_ms >= other.end_ms

    def merge(self, other: Segment) -> Segment:
        """
        他の区間とマージして新しいSegmentを返す

        Args:
            other: マージ対象の区間

        Returns:
            マージされた新しいSegment（typeは自身のtypeを継承）
        """
        merged_metadata = {**self.metadata, **other.metadata}
        return Segment(
            start_ms=min(self.start_ms, other.start_ms),
            end_ms=max(self.end_ms, other.end_ms),
            type=self.type,
            metadata=merged_metadata,
        )

    def apply_margin(
        self,
        before_ms: int,
        after_ms: int,
        max_duration_ms: int | None = None,
    ) -> Segment:
        """
        マージンを適用した新しいSegmentを返す

        Args:
            before_ms: 開始前のバッファ（ミリ秒）
            after_ms: 終了後のバッファ（ミリ秒）
            max_duration_ms: 動画の総時間（ミリ秒）。指定時は範囲を制限

        Returns:
            マージン適用後の新しいSegment
        """
        new_start = max(0, self.start_ms - before_ms)
        new_end = self.end_ms + after_ms

        if max_duration_ms is not None:
            new_end = min(max_duration_ms, new_end)

        return Segment(
            start_ms=new_start,
            end_ms=new_end,
            type=self.type,
            metadata=self.metadata.copy(),
        )

    def align_to_frame(self, fps: float) -> Segment:
        """
        フレーム境界にアラインした新しいSegmentを返す

        Args:
            fps: フレームレート

        Returns:
            フレーム境界にアライン済みの新しいSegment
        """
        import math

        frame_duration_ms = 1000.0 / fps

        # 開始時間は切り捨て（前方向）、終了時間は切り上げ（後方向）
        start_frame = int(self.start_ms / frame_duration_ms)
        end_frame = math.ceil(self.end_ms / frame_duration_ms)

        aligned_start = int(start_frame * frame_duration_ms)
        aligned_end = int(end_frame * frame_duration_ms)

        return Segment(
            start_ms=aligned_start,
            end_ms=aligned_end,
            type=self.type,
            metadata=self.metadata.copy(),
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "duration_ms": self.duration_ms,
            "type": self.type.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Segment:
        """辞書形式から生成"""
        return cls(
            start_ms=data["start_ms"],
            end_ms=data["end_ms"],
            type=SegmentType(data["type"]),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        return (
            f"Segment(start_ms={self.start_ms}, end_ms={self.end_ms}, "
            f"type={self.type.value}, duration_ms={self.duration_ms})"
        )


def merge_overlapping_segments(segments: list[Segment]) -> list[Segment]:
    """
    重複・隣接する区間をマージする

    Args:
        segments: マージ対象の区間リスト

    Returns:
        マージ後の区間リスト（開始時間順）
    """
    if not segments:
        return []

    # 開始時間でソート
    sorted_segments = sorted(segments, key=lambda s: s.start_ms)

    merged: list[Segment] = [sorted_segments[0]]

    for current in sorted_segments[1:]:
        last = merged[-1]

        # 重複または隣接している場合はマージ
        if current.start_ms <= last.end_ms:
            merged[-1] = last.merge(current)
        else:
            merged.append(current)

    return merged


def calculate_complement_segments(
    segments: list[Segment],
    total_duration_ms: int,
    complement_type: SegmentType = SegmentType.KEEP,
) -> list[Segment]:
    """
    区間リストの補集合を計算する（削除区間から保持区間を算出）

    Args:
        segments: 削除対象の区間リスト
        total_duration_ms: 動画の総時間（ミリ秒）
        complement_type: 補集合区間の種類（デフォルト: KEEP）

    Returns:
        補集合の区間リスト
    """
    if not segments:
        return [Segment(start_ms=0, end_ms=total_duration_ms, type=complement_type)]

    # まず区間をマージしてソート
    merged = merge_overlapping_segments(segments)

    complement: list[Segment] = []
    current_pos = 0

    for seg in merged:
        if current_pos < seg.start_ms:
            complement.append(
                Segment(
                    start_ms=current_pos,
                    end_ms=seg.start_ms,
                    type=complement_type,
                )
            )
        current_pos = max(current_pos, seg.end_ms)

    # 最後の区間
    if current_pos < total_duration_ms:
        complement.append(
            Segment(
                start_ms=current_pos,
                end_ms=total_duration_ms,
                type=complement_type,
            )
        )

    return complement
