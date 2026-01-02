"""
gui_state - アプリケーション状態の中央管理

オブザーバパターンで状態変更を通知。
スレッドセーフなアクセスを保証。
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from jetcutter.gui.utils.threading import dispatch_to_main_thread, is_main_thread

if TYPE_CHECKING:
    from jetcutter.core.processor import AudioProcessingResult
    from jetcutter.gui.protocols import GUIStateObserver


@dataclass
class ProcessingState:
    """処理状態を表すデータクラス"""

    is_processing: bool = False
    current_stage: str = ""
    progress_percent: int = 0
    error_message: str | None = None


class GUIState:
    """
    アプリケーション状態の中央管理

    オブザーバパターンで状態変更を通知。
    スレッドセーフなアクセスを保証。
    ProgressReporterProtocolも実装し、ProcessingControllerと統合。

    Usage:
        state = GUIState()
        state.add_observer(my_controller)
        state.set_processing(True)  # Notifies all observers
    """

    def __init__(self) -> None:
        self._processing_state = ProcessingState()
        self._result: AudioProcessingResult | None = None
        self._observers: list[GUIStateObserver] = []
        # RLockを使用して再入可能なロックにする（デッドロック防止）
        self._lock = threading.RLock()
        self._is_cancelled = False

    @property
    def processing_state(self) -> ProcessingState:
        """現在の処理状態を返す"""
        with self._lock:
            return ProcessingState(
                is_processing=self._processing_state.is_processing,
                current_stage=self._processing_state.current_stage,
                progress_percent=self._processing_state.progress_percent,
                error_message=self._processing_state.error_message,
            )

    @property
    def result(self) -> AudioProcessingResult | None:
        """処理結果を返す"""
        with self._lock:
            return self._result

    def add_observer(self, observer: GUIStateObserver) -> None:
        """オブザーバを追加"""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def remove_observer(self, observer: GUIStateObserver) -> None:
        """オブザーバを削除"""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def set_processing(self, is_processing: bool) -> None:
        """処理中フラグを設定"""
        with self._lock:
            self._processing_state.is_processing = is_processing
            if not is_processing:
                self._processing_state.current_stage = ""
                self._processing_state.progress_percent = 0
            state = self.processing_state

        self._notify_processing_state_changed(state)

    def set_stage(self, stage: str, progress: int) -> None:
        """現在のステージと進捗を設定"""
        with self._lock:
            self._processing_state.current_stage = stage
            self._processing_state.progress_percent = max(0, min(100, progress))
            state = self.processing_state

        self._notify_processing_state_changed(state)

    def set_result(self, result: AudioProcessingResult) -> None:
        """処理結果を設定"""
        with self._lock:
            self._result = result

        self._notify_result_available(result)

    def set_error(self, message: str) -> None:
        """エラー状態を設定"""
        with self._lock:
            self._processing_state.error_message = message
            self._processing_state.is_processing = False

        self._notify_error(message)

    def clear_error(self) -> None:
        """エラー状態をクリア"""
        with self._lock:
            self._processing_state.error_message = None

    # ========== ProgressReporterProtocol Implementation ==========

    def report_stage(self, stage: str, progress: int) -> None:
        """
        ステージと進捗を報告（ProgressReporterProtocol）

        Args:
            stage: ステージ名
            progress: 進捗率（0-100）
        """
        self.set_processing(True)
        self.set_stage(stage, progress)

    def report_error(self, message: str) -> None:
        """
        エラーを報告（ProgressReporterProtocol）

        Args:
            message: エラーメッセージ
        """
        self.set_error(message)

    def report_complete(self, result: AudioProcessingResult) -> None:
        """
        処理完了を報告（ProgressReporterProtocol）

        Args:
            result: 処理結果
        """
        self.set_processing(False)
        self.set_result(result)

    def is_cancelled(self) -> bool:
        """
        キャンセルされたかどうかを返す（ProgressReporterProtocol）

        Returns:
            キャンセル状態
        """
        with self._lock:
            return self._is_cancelled

    def cancel(self) -> None:
        """キャンセルフラグを設定"""
        with self._lock:
            self._is_cancelled = True

    def reset_cancel(self) -> None:
        """キャンセルフラグをリセット"""
        with self._lock:
            self._is_cancelled = False

    # ========== Private Notification Methods ==========

    def _notify_processing_state_changed(self, state: ProcessingState) -> None:
        """オブザーバに処理状態変更を通知（メインスレッドで）"""
        with self._lock:
            observers = list(self._observers)

        def notify() -> None:
            for observer in observers:
                try:
                    observer.on_processing_state_changed(
                        state.is_processing, state.current_stage, state.progress_percent
                    )
                except Exception:
                    pass  # Ignore observer errors

        if is_main_thread():
            notify()
        else:
            dispatch_to_main_thread(notify)

    def _notify_result_available(self, result: AudioProcessingResult) -> None:
        """オブザーバに結果利用可能を通知（メインスレッドで）"""
        with self._lock:
            observers = list(self._observers)

        def notify() -> None:
            for observer in observers:
                try:
                    observer.on_result_available(result)
                except Exception:
                    pass

        if is_main_thread():
            notify()
        else:
            dispatch_to_main_thread(notify)

    def _notify_error(self, message: str) -> None:
        """オブザーバにエラーを通知（メインスレッドで）"""
        with self._lock:
            observers = list(self._observers)

        def notify() -> None:
            for observer in observers:
                try:
                    observer.on_error(message)
                except Exception:
                    pass

        if is_main_thread():
            notify()
        else:
            dispatch_to_main_thread(notify)
