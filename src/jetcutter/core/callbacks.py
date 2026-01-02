"""
callbacks - プログレスコールバックプロトコル

UI非依存のプログレス報告インターフェースを定義。
CLIはRich、GUIはPyObjC/AppKit用のアダプタを実装する。
"""

from __future__ import annotations

from typing import Protocol


class ProgressCallback(Protocol):
    """
    プログレスコールバックプロトコル

    処理の進捗を報告するためのインターフェース。
    CLIとGUIで異なる実装を提供可能。
    """

    def on_stage_start(self, stage: str) -> None:
        """
        処理ステージの開始を通知

        Args:
            stage: ステージ名（例: "Extracting audio...", "Detecting silence..."）
        """
        ...

    def on_stage_complete(self, stage: str) -> None:
        """
        処理ステージの完了を通知

        Args:
            stage: 完了したステージ名
        """
        ...

    def is_cancelled(self) -> bool:
        """
        処理のキャンセルが要求されているかを確認

        Returns:
            キャンセル要求があればTrue
        """
        ...


class NullProgressCallback:
    """
    何もしないプログレスコールバック実装

    プログレス表示が不要な場合に使用。
    """

    def on_stage_start(self, stage: str) -> None:
        """ステージ開始（何もしない）"""
        pass

    def on_stage_complete(self, stage: str) -> None:
        """ステージ完了（何もしない）"""
        pass

    def is_cancelled(self) -> bool:
        """キャンセルチェック（常にFalse）"""
        return False
