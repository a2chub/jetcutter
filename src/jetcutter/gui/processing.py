"""
processing - バックグラウンド処理

別スレッドでの動画処理とGUIへの進捗通知。
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jetcutter.config.settings import AppConfig
from jetcutter.core.processor import AudioProcessingResult, ProcessingCancelledError
from jetcutter.core.processor import process_audio as core_process_audio
from jetcutter.gui.constants import EVENT_CANCELLED, EVENT_COMPLETE, EVENT_ERROR, EVENT_STAGE

if TYPE_CHECKING:
    import PySimpleGUI4 as sg


class GUIProgressCallback:
    """
    PySimpleGUI用のプログレスコールバック実装

    write_event_valueを使用してGUIスレッドに進捗を通知。
    """

    def __init__(self, window: sg.Window) -> None:
        self._window = window
        self._cancelled = threading.Event()

    def on_stage_start(self, stage: str) -> None:
        """ステージ開始を通知"""
        self._window.write_event_value(EVENT_STAGE, stage)

    def on_stage_complete(self, stage: str) -> None:
        """ステージ完了を通知（現在は特にUIアクションなし）"""
        pass

    def is_cancelled(self) -> bool:
        """キャンセル状態を確認"""
        return self._cancelled.is_set()

    def cancel(self) -> None:
        """処理をキャンセル"""
        self._cancelled.set()


class BackgroundProcessor:
    """
    バックグラウンドで動画処理を実行するクラス

    処理結果はwrite_event_valueでGUIに通知される。
    """

    def __init__(self, window: sg.Window) -> None:
        self._window = window
        self._thread: threading.Thread | None = None
        self._callback: GUIProgressCallback | None = None

    def start(
        self,
        video_path: Path,
        config: AppConfig,
        output_path: Path | None = None,
        editor: str = "fcp",
    ) -> None:
        """
        バックグラウンド処理を開始

        Args:
            video_path: 処理する動画ファイルパス
            config: アプリケーション設定
            output_path: 出力先パス（FCPの場合）
            editor: エディタ種別（fcp/davinci）
        """
        self._callback = GUIProgressCallback(self._window)
        self._thread = threading.Thread(
            target=self._worker,
            args=(video_path, config, output_path, editor),
            daemon=True,
        )
        self._thread.start()

    def cancel(self) -> None:
        """処理をキャンセル"""
        if self._callback is not None:
            self._callback.cancel()

    def is_running(self) -> bool:
        """処理が実行中かどうか"""
        return self._thread is not None and self._thread.is_alive()

    def _worker(
        self,
        video_path: Path,
        config: AppConfig,
        output_path: Path | None,
        editor: str,
    ) -> None:
        """バックグラウンドワーカー"""
        from loguru import logger
        logger.info("[DEBUG] Worker started")
        cleanup_files: list[Path] = []

        try:
            # 処理実行
            result = core_process_audio(
                video_path=video_path,
                config=config,
                callback=self._callback,
                cleanup_files=cleanup_files,
            )

            # エクスポート実行
            export_result = self._export(
                result=result,
                video_path=video_path,
                config=config,
                output_path=output_path,
                editor=editor,
            )

            # 完了通知
            logger.info(f"[DEBUG] Sending EVENT_COMPLETE with result: {len(result.keep_segments)} keep segments")
            self._window.write_event_value(
                EVENT_COMPLETE,
                {
                    "result": result,
                    "export_result": export_result,
                },
            )
            logger.info("[DEBUG] EVENT_COMPLETE sent")

        except ProcessingCancelledError:
            self._window.write_event_value(EVENT_CANCELLED, None)

        except Exception as e:
            self._window.write_event_value(EVENT_ERROR, str(e))

        finally:
            # 一時ファイルのクリーンアップ
            for f in cleanup_files:
                try:
                    f.unlink(missing_ok=True)
                except Exception:
                    pass

    def _export(
        self,
        result: AudioProcessingResult,
        video_path: Path,
        config: AppConfig,
        output_path: Path | None,
        editor: str,
    ) -> dict[str, Any]:
        """エクスポート処理"""
        from loguru import logger

        from jetcutter.audio.extractor import AudioExtractor
        from jetcutter.exporters import ExportConfig, create_exporter
        from jetcutter.exporters.base import FileExporter, LiveConnectionExporter

        exporter = create_exporter(editor)

        # 出力ファイル名を生成
        timeline_name = f"{config.output.timeline_prefix}{video_path.stem}"

        # 動画のメタデータを取得（実際のFPSと解像度を使用）
        extractor = AudioExtractor()
        video_info = extractor.get_video_info(video_path)
        actual_fps = video_info.get("fps", config.fps)
        actual_width = video_info.get("width", config.output.default_width)
        actual_height = video_info.get("height", config.output.default_height)

        logger.info(f"[DEBUG] Video info: fps={actual_fps}, {actual_width}x{actual_height}")

        # ExportConfigを作成（実際の動画のFPSと解像度を使用）
        timecode_start_ms = video_info.get("timecode_start_ms", 0)
        if timecode_start_ms > 0:
            logger.info(f"[DEBUG] Video has non-zero timecode start: {timecode_start_ms}ms")

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

        # ファイルエクスポータの場合
        if isinstance(exporter, FileExporter):
            if output_path is not None:
                output_file = Path(output_path) / f"{timeline_name}.fcpxml"
            else:
                output_file = video_path.parent / f"{timeline_name}.fcpxml"

            export_config.output_path = output_file
            export_result = exporter.export(result.keep_segments, export_config)

            return {
                "success": export_result.success,
                "message": export_result.message,
                "output_path": str(export_result.output_path) if export_result.output_path else None,
            }

        # ライブ接続エクスポータの場合（DaVinci）
        elif isinstance(exporter, LiveConnectionExporter):
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

        return {"success": False, "message": "Unknown exporter type", "output_path": None}
