"""
timeline_builder - DaVinci Resolveタイムライン構築モジュール

保持区間に基づいてタイムラインを作成し、クリップを配置する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jetdr.davinci.media_pool import DRMediaPool
from jetdr.davinci.project import DRProject
from jetdr.editor.segment import Segment
from jetdr.utils.logger import get_logger
from jetdr.utils.time_utils import ms_to_frames

logger = get_logger(__name__)


class TimelineCreationError(Exception):
    """タイムライン作成エラー"""

    pass


class TimelineBuilder:
    """
    DaVinci Resolveでタイムラインを構築するクラス

    保持区間リストに基づいて、ジェットカット済みタイムラインを生成する。
    """

    def __init__(
        self,
        project: DRProject,
        media_pool: DRMediaPool | None = None,
    ) -> None:
        """
        Args:
            project: DRProjectインスタンス
            media_pool: DRMediaPoolインスタンス（省略時は自動作成）
        """
        self.project = project
        self.media_pool = media_pool or DRMediaPool(project)
        self._timeline: Any = None

    def create_timeline(
        self,
        name: str,
        fps: float | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> Any:
        """
        新しいタイムラインを作成

        Args:
            name: タイムライン名
            fps: フレームレート（省略時はプロジェクト設定）
            width: 幅（省略時はプロジェクト設定）
            height: 高さ（省略時はプロジェクト設定）

        Returns:
            作成されたTimeline
        """
        mp = self.media_pool.media_pool

        # タイムライン設定
        settings: dict[str, Any] = {"timelineName": name}

        if fps is not None:
            settings["timelineFrameRate"] = str(fps)
        if width is not None:
            settings["timelineResolutionWidth"] = str(width)
        if height is not None:
            settings["timelineResolutionHeight"] = str(height)

        timeline = mp.CreateEmptyTimeline(name)

        if timeline is None:
            raise TimelineCreationError(f"Failed to create timeline: {name}")

        self._timeline = timeline
        logger.info(f"Created timeline: {name}")
        return timeline

    def get_current_timeline(self) -> Any:
        """現在のタイムラインを取得"""
        if self._timeline is None:
            self._timeline = self.project.project.GetCurrentTimeline()
        return self._timeline

    def set_current_timeline(self, timeline: Any) -> bool:
        """現在のタイムラインを設定"""
        result = self.project.project.SetCurrentTimeline(timeline)
        if result:
            self._timeline = timeline
        return result

    def add_clip_to_timeline(
        self,
        clip: Any,
        track_index: int = 1,
        start_frame: int = 0,
    ) -> Any:
        """
        クリップをタイムラインに追加

        .. deprecated::
            このメソッドは使用されていません。
            代わりに add_clip_with_in_out() を使用してください。

        Args:
            clip: MediaPoolItem
            track_index: トラック番号（1始まり）
            start_frame: 配置開始フレーム

        Returns:
            追加されたTimelineItem
        """
        import warnings

        warnings.warn(
            "add_clip_to_timeline is deprecated, use add_clip_with_in_out instead",
            DeprecationWarning,
            stacklevel=2,
        )
        mp = self.media_pool.media_pool
        timeline = self.get_current_timeline()

        if timeline is None:
            raise TimelineCreationError("No timeline is set")

        # クリップを追加
        result = mp.AppendToTimeline([clip])

        if not result:
            raise TimelineCreationError("Failed to add clip to timeline")

        return result

    def add_clip_with_in_out(
        self,
        clip: Any,
        in_frame: int,
        out_frame: int,
        record_frame: int,
        track_index: int = 1,
    ) -> bool:
        """
        In/Outポイントを指定してクリップを追加

        Args:
            clip: MediaPoolItem
            in_frame: ソースのInポイント（フレーム）
            out_frame: ソースのOutポイント（フレーム）
            record_frame: タイムライン上の配置位置（フレーム）
            track_index: トラック番号（1始まり）

        Returns:
            成功したかどうか
        """
        mp = self.media_pool.media_pool

        # クリップ情報の設定
        clip_info = {
            "mediaPoolItem": clip,
            "startFrame": in_frame,
            "endFrame": out_frame,
            "trackIndex": track_index,
            "recordFrame": record_frame,
        }

        result = mp.AppendToTimeline([clip_info])
        return bool(result)

    def create_timeline_from_segments(
        self,
        video_path: str | Path,
        segments: list[Segment],
        timeline_name: str,
        fps: float = 29.97,
    ) -> Any:
        """
        保持区間からタイムラインを作成する

        Args:
            video_path: 元動画ファイルのパス
            segments: 保持区間リスト
            timeline_name: タイムライン名
            fps: フレームレート

        Returns:
            作成されたTimeline

        Raises:
            TimelineCreationError: タイムライン作成に失敗した場合
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise TimelineCreationError(f"Video file not found: {video_path}")

        logger.info(f"Creating timeline '{timeline_name}' from {len(segments)} segments")

        # メディアをインポート
        clip = self.media_pool.import_media_single(video_path)

        # タイムラインを作成
        timeline = self.create_timeline(timeline_name, fps=fps)
        self.set_current_timeline(timeline)

        # 各保持区間をタイムラインに追加
        record_frame = 0

        for i, segment in enumerate(segments):
            in_frame = ms_to_frames(segment.start_ms, fps)
            out_frame = ms_to_frames(segment.end_ms, fps)
            duration_frames = out_frame - in_frame

            logger.debug(
                f"Adding segment {i + 1}/{len(segments)}: "
                f"in={in_frame}, out={out_frame}, record={record_frame}"
            )

            success = self.add_clip_with_in_out(
                clip=clip,
                in_frame=in_frame,
                out_frame=out_frame,
                record_frame=record_frame,
            )

            if not success:
                logger.warning(f"Failed to add segment {i + 1}")

            record_frame += duration_frames

        logger.info(f"Timeline created with {len(segments)} clips")
        return timeline

    def get_timeline_info(self, timeline: Any | None = None) -> dict:
        """
        タイムライン情報を取得

        Args:
            timeline: 対象タイムライン（省略時は現在のタイムライン）

        Returns:
            タイムライン情報の辞書
        """
        if timeline is None:
            timeline = self.get_current_timeline()

        if timeline is None:
            return {}

        return {
            "name": timeline.GetName(),
            "start_frame": timeline.GetStartFrame(),
            "end_frame": timeline.GetEndFrame(),
            "track_count": {
                "video": timeline.GetTrackCount("video"),
                "audio": timeline.GetTrackCount("audio"),
            },
        }

    def export_timeline(
        self,
        output_path: str | Path,
        preset: str = "H.264 Master",
    ) -> bool:
        """
        タイムラインをレンダリング・エクスポート

        Args:
            output_path: 出力ファイルパス
            preset: レンダリングプリセット名

        Returns:
            成功したかどうか
        """
        timeline = self.get_current_timeline()
        if timeline is None:
            raise TimelineCreationError("No timeline to export")

        project = self.project.project

        # レンダー設定
        project.SetRenderSettings({
            "TargetDir": str(Path(output_path).parent),
            "CustomName": Path(output_path).stem,
        })

        # プリセットを適用
        project.LoadRenderPreset(preset)

        # レンダーキューに追加
        project.AddRenderJob()

        # レンダリング開始
        project.StartRendering()

        # 完了を待機
        while project.IsRenderingInProgress():
            import time

            time.sleep(1)

        logger.info(f"Exported to: {output_path}")
        return True

    def list_timelines(self) -> list[str]:
        """プロジェクト内のタイムライン一覧を取得"""
        project = self.project.project
        count = project.GetTimelineCount()
        timelines = []

        for i in range(1, count + 1):
            timeline = project.GetTimelineByIndex(i)
            if timeline:
                timelines.append(timeline.GetName())

        return timelines
