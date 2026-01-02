"""
processing_controller - バックグラウンド処理コントローラ

音声/動画の分析処理をバックグラウンドスレッドで実行し、
ProgressReporterProtocolを通じて進捗を通知する。
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from jetcutter.gui.constants import STAGE_PROGRESS
from jetcutter.gui.utils.threading import dispatch_to_main_thread

if TYPE_CHECKING:
    from jetcutter.config.settings import AppConfig
    from jetcutter.core.processor import AudioProcessingResult
    from jetcutter.gui.protocols import ProgressReporterProtocol


class NativeProgressCallback:
    """
    ネイティブGUI用のProgressCallback実装

    core.processor.process_audio()から呼び出され、
    ProgressReporterProtocolを通じてUIを更新する。
    """

    def __init__(
        self, reporter: ProgressReporterProtocol, cancel_event: threading.Event
    ) -> None:
        self._reporter = reporter
        self._cancel_event = cancel_event

    def on_stage_start(self, stage: str) -> None:
        """ステージ開始時に呼ばれる"""
        progress = STAGE_PROGRESS.get(stage, 0)
        dispatch_to_main_thread(lambda: self._reporter.report_stage(stage, progress))

    def on_stage_complete(self, stage: str) -> None:
        """ステージ完了時に呼ばれる"""
        # 次のステージの進捗に更新（on_stage_startで処理）
        pass

    def is_cancelled(self) -> bool:
        """キャンセルされたかどうかを返す"""
        return self._cancel_event.is_set()

    def cancel(self) -> None:
        """処理をキャンセル"""
        self._cancel_event.set()


class ProcessingController:
    """
    バックグラウンド処理の制御

    ProgressReporterProtocolを通じて状態を通知。
    キャンセル可能な処理をサポート。
    """

    def __init__(self, reporter: ProgressReporterProtocol) -> None:
        """
        Args:
            reporter: 状態通知先（ProgressReporterProtocol）
        """
        self._reporter = reporter
        self._thread: threading.Thread | None = None
        self._cancel_event = threading.Event()
        self._cleanup_files: list[Path] = []

    @property
    def is_running(self) -> bool:
        """処理実行中かどうか"""
        return self._thread is not None and self._thread.is_alive()

    def start(
        self,
        video_path: Path,
        config: AppConfig,
        output_path: Path | None,
        editor: str,
    ) -> None:
        """
        処理を開始

        Args:
            video_path: 入力動画パス
            config: 処理設定
            output_path: 出力先ディレクトリ（Noneで動画と同じ場所）
            editor: エディタ種別（"fcp" / "davinci"）
        """
        if self.is_running:
            logger.warning("Processing already running")
            return

        self._cancel_event.clear()
        self._cleanup_files.clear()

        self._thread = threading.Thread(
            target=self._worker,
            args=(video_path, config, output_path, editor),
            daemon=True,
        )
        self._thread.start()

    def cancel(self) -> None:
        """処理をキャンセル"""
        if self.is_running:
            self._cancel_event.set()
            logger.info("Processing cancellation requested")

    def _worker(
        self,
        video_path: Path,
        config: AppConfig,
        output_path: Path | None,
        editor: str,
    ) -> None:
        """ワーカースレッドで実行される処理"""
        try:
            # Import here to avoid slow startup
            from jetcutter.core.processor import (
                ProcessingCancelledError,
                process_audio,
            )

            # Create callback
            callback = NativeProgressCallback(self._reporter, self._cancel_event)

            # Process audio
            result = process_audio(
                video_path=video_path,
                config=config,
                callback=callback,
                cleanup_files=self._cleanup_files,
            )

            if self._cancel_event.is_set():
                logger.info("Processing cancelled after audio processing")
                return

            # Export
            dispatch_to_main_thread(lambda: self._reporter.report_stage("export", 95))
            export_result = self._export(
                video_path=video_path,
                result=result,
                config=config,
                output_path=output_path,
                editor=editor,
            )

            if export_result["success"]:
                dispatch_to_main_thread(
                    lambda: self._reporter.report_complete(result)
                )
            else:
                dispatch_to_main_thread(
                    lambda: self._reporter.report_error(export_result["message"])
                )

        except ProcessingCancelledError:
            logger.info("Processing cancelled by user")
            # No error report needed - user initiated

        except Exception as e:
            logger.exception(f"Processing error: {e}")
            error_msg = str(e)
            dispatch_to_main_thread(lambda: self._reporter.report_error(error_msg))

        finally:
            self._cleanup()

    def _export(
        self,
        video_path: Path,
        result: AudioProcessingResult,
        config: AppConfig,
        output_path: Path | None,
        editor: str,
    ) -> dict[str, Any]:
        """エクスポート処理"""
        from jetcutter.audio.extractor import AudioExtractor
        from jetcutter.exporters import create_exporter
        from jetcutter.exporters.base import ExportConfig, FileExporter, LiveConnectionExporter

        # Get video metadata
        extractor = AudioExtractor()
        video_info = extractor.get_video_info(video_path)

        # Extract metadata
        actual_fps = video_info.get("fps", config.fps)
        actual_width = video_info.get("width", config.output.default_width)
        actual_height = video_info.get("height", config.output.default_height)
        timecode_start_ms = video_info.get("timecode_start_ms", 0)

        logger.info(
            f"Video info: fps={actual_fps}, {actual_width}x{actual_height}, "
            f"timecode_start={timecode_start_ms}ms"
        )

        # Create export config
        timeline_name = f"{config.output.timeline_prefix}{video_path.stem}"
        export_config = ExportConfig(
            video_path=video_path,
            output_name=timeline_name,
            fps=actual_fps,
            width=actual_width,
            height=actual_height,
            metadata={
                "actual_duration_ms": video_info.get("duration_ms", 0),
                "timecode_start_ms": timecode_start_ms,
            },
        )

        # Create exporter
        exporter = create_exporter(editor)

        # Export based on exporter type
        if isinstance(exporter, FileExporter):
            # File-based export (FCP, EDL, etc.)
            if output_path is not None:
                export_config.metadata["output_dir"] = str(output_path)

            export_result = exporter.export(result.keep_segments, export_config)

            return {
                "success": export_result.success,
                "message": export_result.message,
                "output_path": (
                    str(export_result.output_path) if export_result.output_path else None
                ),
            }

        elif isinstance(exporter, LiveConnectionExporter):
            # Live connection export (DaVinci Resolve)
            with exporter:
                if not exporter.is_connected:
                    return {
                        "success": False,
                        "message": "DaVinci Resolveに接続できませんでした。アプリケーションが起動しているか確認してください。",
                        "output_path": None,
                    }

                export_result = exporter.export(result.keep_segments, export_config)
                return {
                    "success": export_result.success,
                    "message": export_result.message,
                    "output_path": None,
                }

        return {
            "success": False,
            "message": "Unknown exporter type",
            "output_path": None,
        }

    def _cleanup(self) -> None:
        """一時ファイルのクリーンアップ"""
        for file_path in self._cleanup_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Cleaned up: {file_path}")
            except OSError as e:
                logger.warning(f"Failed to cleanup {file_path}: {e}")
        self._cleanup_files.clear()
