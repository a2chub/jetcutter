"""
protocols - GUIコンポーネントのインターフェース定義

PyObjC + AppKitベースのネイティブGUI用プロトコル。
"""

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from AppKit import NSView

    from jetcutter.config.settings import AppConfig
    from jetcutter.core.processor import AudioProcessingResult


class TabControllerProtocol(Protocol):
    """タブコントローラの共通インターフェース"""

    @property
    def view(self) -> "NSView":
        """タブのルートビューを返す"""
        ...

    @property
    def identifier(self) -> str:
        """タブの識別子（例: "process", "settings", "results"）"""
        ...

    @property
    def label(self) -> str:
        """タブのラベル（例: "処理", "設定", "結果"）"""
        ...

    def view_will_appear(self) -> None:
        """タブが表示される直前に呼ばれる"""
        ...

    def view_did_appear(self) -> None:
        """タブが表示された直後に呼ばれる"""
        ...


class ProgressReporterProtocol(Protocol):
    """スレッドセーフな進捗通知インターフェース"""

    def report_stage(self, stage: str, progress: int) -> None:
        """ステージと進捗を報告（0-100）"""
        ...

    def report_error(self, message: str) -> None:
        """エラーを報告"""
        ...

    def report_complete(self, result: "AudioProcessingResult") -> None:
        """処理完了を報告"""
        ...

    def is_cancelled(self) -> bool:
        """キャンセルされたかどうかを返す"""
        ...


class GUIStateObserver(Protocol):
    """状態変更の通知を受け取るオブザーバ"""

    def on_processing_state_changed(
        self, is_processing: bool, stage: str, progress: int
    ) -> None:
        """処理状態が変化した時に呼ばれる"""
        ...

    def on_result_available(self, result: "AudioProcessingResult") -> None:
        """処理結果が利用可能になった時に呼ばれる"""
        ...

    def on_error(self, message: str) -> None:
        """エラーが発生した時に呼ばれる"""
        ...


class SettingsBindingProtocol(Protocol):
    """設定の双方向バインディング"""

    def bind_config(self, config: "AppConfig") -> None:
        """設定をUIにバインド"""
        ...

    def read_values(self) -> dict[str, Any]:
        """UIから値を読み取る"""
        ...

    def set_enabled(self, enabled: bool) -> None:
        """UIの有効/無効を設定"""
        ...
