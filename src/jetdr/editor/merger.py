"""
merger - 区間マージロジックモジュール

無音区間とフィラー区間を統合し、保持区間を算出する。
"""

from __future__ import annotations

from jetdr.editor.segment import (
    Segment,
    SegmentType,
    calculate_complement_segments,
    merge_overlapping_segments,
)
from jetdr.utils.logger import get_logger

logger = get_logger(__name__)


class SegmentMerger:
    """
    区間のマージと保持区間算出を行うクラス

    無音区間とフィラー区間を統合し、
    マージン適用・フレームアライン後の保持区間リストを生成する。
    """

    def __init__(
        self,
        margin_before_ms: int = 100,
        margin_after_ms: int = 100,
        min_keep_duration_ms: int = 500,
        fps: float = 29.97,
    ) -> None:
        """
        Args:
            margin_before_ms: 保持区間開始前のバッファ（ミリ秒）
            margin_after_ms: 保持区間終了後のバッファ（ミリ秒）
            min_keep_duration_ms: 最小保持区間長（ミリ秒）
            fps: フレームレート
        """
        self.margin_before_ms = margin_before_ms
        self.margin_after_ms = margin_after_ms
        self.min_keep_duration_ms = min_keep_duration_ms
        self.fps = fps

    def calculate_keep_segments(
        self,
        silence_segments: list[Segment],
        filler_segments: list[Segment],
        total_duration_ms: int,
    ) -> list[Segment]:
        """
        保持区間を計算する

        手順:
        1. 削除対象区間（無音 + フィラー）を統合
        2. 重複区間をマージ
        3. 削除区間の補集合として保持区間を算出
        4. マージンを適用
        5. 隣接した保持区間を結合
        6. 最小長でフィルタ
        7. フレーム境界にアライン

        Args:
            silence_segments: 無音区間リスト
            filler_segments: フィラー区間リスト
            total_duration_ms: 動画の総時間（ミリ秒）

        Returns:
            保持区間のリスト
        """
        logger.info(
            f"Calculating keep segments: "
            f"{len(silence_segments)} silence, {len(filler_segments)} filler, "
            f"total duration: {total_duration_ms}ms"
        )

        # Step 1: 削除対象区間を統合
        cut_segments = silence_segments + filler_segments
        logger.debug(f"Total cut segments before merge: {len(cut_segments)}")

        # Step 2: 重複区間をマージ
        merged_cuts = merge_overlapping_segments(cut_segments)
        logger.debug(f"Cut segments after merge: {len(merged_cuts)}")

        # Step 3: 補集合として保持区間を算出
        keep_segments = calculate_complement_segments(
            merged_cuts,
            total_duration_ms,
            complement_type=SegmentType.KEEP,
        )
        logger.debug(f"Keep segments (before margin): {len(keep_segments)}")

        # Step 4: マージンを適用
        keep_segments = [
            seg.apply_margin(
                before_ms=self.margin_before_ms,
                after_ms=self.margin_after_ms,
                max_duration_ms=total_duration_ms,
            )
            for seg in keep_segments
        ]

        # Step 5: マージン適用後の重複をマージ
        keep_segments = merge_overlapping_segments(keep_segments)
        logger.debug(f"Keep segments (after margin merge): {len(keep_segments)}")

        # Step 6: 最小長でフィルタ
        keep_segments = [
            seg for seg in keep_segments if seg.duration_ms >= self.min_keep_duration_ms
        ]
        logger.debug(f"Keep segments (after min duration filter): {len(keep_segments)}")

        # Step 7: フレーム境界にアライン
        keep_segments = [seg.align_to_frame(self.fps) for seg in keep_segments]

        # 統計を計算
        total_keep_ms = sum(seg.duration_ms for seg in keep_segments)
        reduction_percent = (1 - total_keep_ms / total_duration_ms) * 100 if total_duration_ms > 0 else 0

        logger.info(
            f"Result: {len(keep_segments)} keep segments, "
            f"total: {total_keep_ms}ms, "
            f"reduction: {reduction_percent:.1f}%"
        )

        return keep_segments

    def merge_overlapping(self, segments: list[Segment]) -> list[Segment]:
        """
        重複・隣接する区間をマージする

        Args:
            segments: マージ対象の区間リスト

        Returns:
            マージ後の区間リスト
        """
        return merge_overlapping_segments(segments)

    def get_cut_summary(
        self,
        silence_segments: list[Segment],
        filler_segments: list[Segment],
        keep_segments: list[Segment],
        total_duration_ms: int,
    ) -> dict:
        """
        カット処理のサマリーを取得する

        Args:
            silence_segments: 無音区間リスト
            filler_segments: フィラー区間リスト
            keep_segments: 保持区間リスト
            total_duration_ms: 動画の総時間（ミリ秒）

        Returns:
            サマリー情報の辞書
        """
        silence_total_ms = sum(s.duration_ms for s in silence_segments)
        filler_total_ms = sum(s.duration_ms for s in filler_segments)
        keep_total_ms = sum(s.duration_ms for s in keep_segments)

        return {
            "total_duration_ms": total_duration_ms,
            "silence_segments_count": len(silence_segments),
            "silence_total_ms": silence_total_ms,
            "filler_segments_count": len(filler_segments),
            "filler_total_ms": filler_total_ms,
            "keep_segments_count": len(keep_segments),
            "keep_total_ms": keep_total_ms,
            "cut_total_ms": total_duration_ms - keep_total_ms,
            "reduction_percent": (1 - keep_total_ms / total_duration_ms) * 100
            if total_duration_ms > 0
            else 0,
        }


def quick_merge(
    silence_segments: list[Segment],
    filler_segments: list[Segment],
    total_duration_ms: int,
    margin_ms: int = 100,
    min_keep_ms: int = 500,
    fps: float = 29.97,
) -> list[Segment]:
    """
    保持区間を計算するユーティリティ関数

    Args:
        silence_segments: 無音区間リスト
        filler_segments: フィラー区間リスト
        total_duration_ms: 動画の総時間（ミリ秒）
        margin_ms: 前後のマージン（ミリ秒）
        min_keep_ms: 最小保持区間長（ミリ秒）
        fps: フレームレート

    Returns:
        保持区間のリスト
    """
    merger = SegmentMerger(
        margin_before_ms=margin_ms,
        margin_after_ms=margin_ms,
        min_keep_duration_ms=min_keep_ms,
        fps=fps,
    )
    return merger.calculate_keep_segments(
        silence_segments,
        filler_segments,
        total_duration_ms,
    )
