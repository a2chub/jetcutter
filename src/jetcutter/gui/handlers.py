"""
handlers - イベントハンドラ

GUIイベントの処理ロジック。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from jetcutter.config.settings import AppConfig
from jetcutter.core.processor import AudioProcessingResult
from jetcutter.gui.constants import (
    EVENT_CANCEL,
    EVENT_CANCELLED,
    EVENT_COMPLETE,
    EVENT_ERROR,
    EVENT_LOAD_DEFAULTS,
    EVENT_SAVE_SETTINGS,
    EVENT_STAGE,
    EVENT_START,
    LANGUAGES,
    SEGMENT_TYPE_NAMES,
    STAGE_NAMES,
    STAGE_PROGRESS,
)
from jetcutter.gui.processing import BackgroundProcessor

if TYPE_CHECKING:
    import PySimpleGUI as sg


def format_time(ms: int) -> str:
    """ミリ秒を MM:SS.S 形式に変換"""
    total_seconds = ms / 1000
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:05.2f}"


class EventHandler:
    """GUIイベントハンドラ"""

    def __init__(
        self,
        window: sg.Window,
        config: AppConfig,
        config_path: Path,
    ) -> None:
        self._window = window
        self._config = config
        self._config_path = config_path
        self._processor = BackgroundProcessor(window)
        self._result: AudioProcessingResult | None = None

    def handle(self, event: str, values: dict[str, Any]) -> bool:
        """
        イベントを処理

        Args:
            event: イベント名
            values: ウィンドウの値

        Returns:
            Trueで継続、Falseで終了
        """
        import PySimpleGUI as sg

        if event == sg.WIN_CLOSED:
            return False

        if event == EVENT_START:
            self._handle_start(values)

        elif event == EVENT_CANCEL:
            self._handle_cancel()

        elif event == EVENT_STAGE:
            self._handle_stage(values[EVENT_STAGE])

        elif event == EVENT_COMPLETE:
            self._handle_complete(values[EVENT_COMPLETE])

        elif event == EVENT_ERROR:
            self._handle_error(values[EVENT_ERROR])

        elif event == EVENT_CANCELLED:
            self._handle_cancelled()

        elif event == EVENT_SAVE_SETTINGS:
            self._handle_save_settings(values)

        elif event == EVENT_LOAD_DEFAULTS:
            self._handle_load_defaults()

        return True

    def _handle_start(self, values: dict[str, Any]) -> None:
        """処理開始"""
        import PySimpleGUI as sg

        # 入力検証
        video_path_str = values.get("-VIDEO-PATH-", "")
        if not video_path_str:
            sg.popup_error("動画ファイルを選択してください", title="エラー")
            return

        video_path = Path(video_path_str)
        if not video_path.exists():
            sg.popup_error(f"ファイルが見つかりません: {video_path}", title="エラー")
            return

        # 設定を更新
        self._update_config_from_values(values)

        # エディタを決定
        editor = "fcp" if values.get("-EDITOR-FCP-", True) else "davinci"

        # 出力先
        output_path_str = values.get("-OUTPUT-PATH-", "")
        output_path = Path(output_path_str) if output_path_str else None

        # UI更新
        self._set_processing_ui(True)
        self._window["-STATUS-TEXT-"].update("処理を開始しています...")
        self._window["-FOOTER-STATUS-"].update("処理中...")

        # バックグラウンド処理開始
        self._processor.start(
            video_path=video_path,
            config=self._config,
            output_path=output_path,
            editor=editor,
        )

    def _handle_cancel(self) -> None:
        """キャンセル"""
        self._processor.cancel()
        self._window["-STATUS-TEXT-"].update("キャンセル中...")

    def _handle_stage(self, stage: str) -> None:
        """ステージ更新"""
        # 日本語に変換
        stage_ja = STAGE_NAMES.get(stage, stage)
        self._window["-STATUS-TEXT-"].update(stage_ja)

        # プログレスバー更新
        progress = STAGE_PROGRESS.get(stage, 0)
        self._window["-PROGRESS-BAR-"].update(progress)

    def _handle_complete(self, data: dict[str, Any]) -> None:
        """処理完了"""
        import PySimpleGUI as sg

        self._set_processing_ui(False)
        self._window["-PROGRESS-BAR-"].update(100)

        result: AudioProcessingResult = data["result"]
        export_result: dict[str, Any] = data["export_result"]

        self._result = result

        # 結果タブを更新
        self._update_results_tab(result)

        # 完了メッセージ
        if export_result.get("success"):
            msg = "処理が完了しました"
            if export_result.get("output_path"):
                msg += f"\n\n出力先: {export_result['output_path']}"
            sg.popup_ok(msg, title="完了")
            self._window["-STATUS-TEXT-"].update("完了")
            self._window["-FOOTER-STATUS-"].update("Ready")

            # 結果タブに切り替え
            self._window["-TAB-GROUP-"].Widget.select(2)  # 0-indexed

        else:
            sg.popup_error(
                f"エクスポートに失敗しました:\n{export_result.get('message', 'Unknown error')}",
                title="エラー",
            )
            self._window["-STATUS-TEXT-"].update("エクスポート失敗")
            self._window["-FOOTER-STATUS-"].update("Ready")

    def _handle_error(self, error_msg: str) -> None:
        """エラー発生"""
        import PySimpleGUI as sg

        self._set_processing_ui(False)
        sg.popup_error(f"処理中にエラーが発生しました:\n\n{error_msg}", title="エラー")
        self._window["-STATUS-TEXT-"].update("エラー")
        self._window["-FOOTER-STATUS-"].update("Ready")

    def _handle_cancelled(self) -> None:
        """キャンセル完了"""
        import PySimpleGUI as sg

        self._set_processing_ui(False)
        sg.popup_ok("処理がキャンセルされました", title="キャンセル")
        self._window["-STATUS-TEXT-"].update("キャンセルされました")
        self._window["-FOOTER-STATUS-"].update("Ready")

    def _handle_save_settings(self, values: dict[str, Any]) -> None:
        """設定を保存"""
        import PySimpleGUI as sg

        try:
            self._update_config_from_values(values)
            self._config.to_yaml(self._config_path)
            sg.popup_ok(f"設定を保存しました:\n{self._config_path}", title="保存完了")
        except Exception as e:
            sg.popup_error(f"設定の保存に失敗しました:\n{e}", title="エラー")

    def _handle_load_defaults(self) -> None:
        """デフォルト設定に戻す"""
        import PySimpleGUI as sg

        self._config = AppConfig()
        self._update_settings_ui()
        sg.popup_ok("デフォルト設定に戻しました", title="リセット")

    def _update_config_from_values(self, values: dict[str, Any]) -> None:
        """UIの値から設定を更新"""
        # 無音検知
        self._config.silence.threshold_db = float(values.get("-THRESHOLD-DB-", -40.0))
        try:
            self._config.silence.min_duration_ms = int(values.get("-MIN-SILENCE-MS-", 300))
        except ValueError:
            pass

        # フィラー検知
        self._config.filler.model_name = values.get("-MODEL-NAME-", "large-v3")

        # 言語コードに変換
        lang_display = values.get("-LANGUAGE-", "日本語")
        lang_code = next(
            (lang[1] for lang in LANGUAGES if lang[0] == lang_display), "ja"
        )
        self._config.filler.language = lang_code

        self._config.filler.device = values.get("-DEVICE-", "auto")

        # マージン
        try:
            self._config.margin.before_ms = int(values.get("-MARGIN-BEFORE-", 100))
        except ValueError:
            pass
        try:
            self._config.margin.after_ms = int(values.get("-MARGIN-AFTER-", 100))
        except ValueError:
            pass

        # 一般
        try:
            self._config.fps = float(values.get("-FPS-", 29.97))
        except ValueError:
            pass
        try:
            self._config.min_keep_duration_ms = int(values.get("-MIN-KEEP-MS-", 500))
        except ValueError:
            pass

        # 出力設定
        self._config.output.timeline_prefix = values.get("-TIMELINE-PREFIX-", "JetCut_")
        if values.get("-EDITOR-FCP-", True):
            self._config.output.default_editor = "fcp"
        else:
            self._config.output.default_editor = "davinci"

    def _update_settings_ui(self) -> None:
        """設定UIを現在の設定で更新"""
        self._window["-THRESHOLD-DB-"].update(self._config.silence.threshold_db)
        self._window["-MIN-SILENCE-MS-"].update(str(self._config.silence.min_duration_ms))
        self._window["-MODEL-NAME-"].update(self._config.filler.model_name)

        lang_display = next(
            (lang[0] for lang in LANGUAGES if lang[1] == self._config.filler.language),
            "日本語",
        )
        self._window["-LANGUAGE-"].update(lang_display)
        self._window["-DEVICE-"].update(self._config.filler.device)
        self._window["-MARGIN-BEFORE-"].update(str(self._config.margin.before_ms))
        self._window["-MARGIN-AFTER-"].update(str(self._config.margin.after_ms))
        self._window["-FPS-"].update(str(self._config.fps))
        self._window["-MIN-KEEP-MS-"].update(str(self._config.min_keep_duration_ms))

    def _set_processing_ui(self, processing: bool) -> None:
        """処理中のUI状態を設定"""
        self._window[EVENT_START].update(visible=not processing)
        self._window[EVENT_CANCEL].update(visible=processing)
        self._window["-PROGRESS-BAR-"].update(visible=processing, current_count=0)

        # 入力要素を無効化/有効化
        self._window["-VIDEO-PATH-"].update(disabled=processing)
        self._window["-EDITOR-FCP-"].update(disabled=processing)
        self._window["-EDITOR-DAVINCI-"].update(disabled=processing)

    def _update_results_tab(self, result: AudioProcessingResult) -> None:
        """結果タブを更新"""
        summary = result.summary

        # サマリー更新
        self._window["-TOTAL-DURATION-"].update(
            format_time(result.total_duration_ms)
        )

        cut_ms = int(summary.get("total_cut_ms", 0))
        self._window["-CUT-DURATION-"].update(format_time(cut_ms))

        cut_ratio = summary.get("cut_ratio", 0)
        self._window["-CUT-RATIO-"].update(f"{cut_ratio:.1f}%")

        self._window["-SILENCE-COUNT-"].update(str(len(result.silence_segments)))
        self._window["-FILLER-COUNT-"].update(str(len(result.filler_segments)))
        self._window["-KEEP-COUNT-"].update(str(len(result.keep_segments)))

        # セグメントテーブル更新
        table_data = []
        all_segments = (
            [(s, "SILENCE") for s in result.silence_segments]
            + [(s, "FILLER") for s in result.filler_segments]
            + [(s, "KEEP") for s in result.keep_segments]
        )
        # 開始時間でソート
        all_segments.sort(key=lambda x: x[0].start_ms)

        for i, (seg, seg_type) in enumerate(all_segments, 1):
            type_name = SEGMENT_TYPE_NAMES.get(seg_type, seg_type)
            table_data.append([
                i,
                type_name,
                format_time(seg.start_ms),
                format_time(seg.end_ms),
                format_time(seg.duration_ms),
            ])

        self._window["-SEGMENT-TABLE-"].update(values=table_data)
