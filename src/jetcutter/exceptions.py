"""
exceptions - JetCutter共通例外モジュール

アプリケーション全体で使用する例外クラスを定義する。
エラーの分類とトラブルシューティングを容易にする。
"""

from __future__ import annotations


class JetCutterError(Exception):
    """JetCutterの基底例外クラス"""

    def __init__(self, message: str, hint: str | None = None) -> None:
        """
        Args:
            message: エラーメッセージ
            hint: トラブルシューティングのヒント
        """
        self.message = message
        self.hint = hint
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.hint:
            return f"{self.message}\n  Hint: {self.hint}"
        return self.message


class ConfigurationError(JetCutterError):
    """設定関連のエラー"""

    pass


class AudioProcessingError(JetCutterError):
    """音声処理関連のエラー（リトライ可能な場合あり）"""

    pass


class ExportError(JetCutterError):
    """エクスポート処理のエラー"""

    pass


class ConnectionError(JetCutterError):
    """外部接続のエラー（リトライ可能）"""

    pass


class ValidationError(JetCutterError):
    """入力検証のエラー"""

    pass
