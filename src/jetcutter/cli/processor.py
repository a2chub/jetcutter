"""
processor - CLI用音声処理ラッパー

Rich Progressを使用したCLI向けのプログレス表示を提供。
コア処理ロジックはjetcutter.coreを使用。
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn

from jetcutter.config.settings import AppConfig
from jetcutter.core.callbacks import ProgressCallback
from jetcutter.core.processor import AudioProcessingResult
from jetcutter.core.processor import process_audio as core_process_audio

console = Console()

# Re-export for backward compatibility
__all__ = ["AudioProcessingResult", "process_audio"]


class RichProgressCallback:
    """
    Rich Progressを使用するプログレスコールバック実装

    CLI用のスピナー付きプログレス表示を提供。
    """

    def __init__(self, progress: Progress) -> None:
        self._progress = progress
        self._current_task: TaskID | None = None
        self._cancelled = False

    def on_stage_start(self, stage: str) -> None:
        """新しいステージを開始（スピナー表示）"""
        self._current_task = self._progress.add_task(stage, total=None)

    def on_stage_complete(self, stage: str) -> None:
        """ステージを完了としてマーク"""
        if self._current_task is not None:
            self._progress.update(self._current_task, completed=True)
            self._current_task = None

    def is_cancelled(self) -> bool:
        """キャンセル状態を返す"""
        return self._cancelled

    def cancel(self) -> None:
        """処理をキャンセル"""
        self._cancelled = True


def process_audio(
    video_path: Path,
    config: AppConfig,
    progress: Progress | None = None,
    cleanup_files: list[Path] | None = None,
) -> AudioProcessingResult:
    """
    動画から音声を抽出し、無音・フィラー検知を実行する（CLI用ラッパー）

    Args:
        video_path: 動画ファイルパス
        config: アプリケーション設定
        progress: 進捗表示用Progressインスタンス（省略時は内部で作成）
        cleanup_files: クリーンアップ対象ファイルリスト

    Returns:
        AudioProcessingResult - 処理結果

    Raises:
        AudioExtractionError: 音声抽出に失敗
        SilenceDetectionError: 無音検知に失敗
        TranscriptionError: 文字起こしに失敗
    """

    def _process_with_progress(prog: Progress) -> AudioProcessingResult:
        callback = RichProgressCallback(prog)
        return core_process_audio(
            video_path=video_path,
            config=config,
            callback=callback,
            cleanup_files=cleanup_files,
        )

    if progress is not None:
        return _process_with_progress(progress)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as prog:
            return _process_with_progress(prog)
