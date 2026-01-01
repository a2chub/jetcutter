"""
connection - DaVinci Resolve接続管理モジュール

DaVinci Resolve Scripting APIへの接続を管理する。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from jetdr.utils.logger import get_logger

logger = get_logger(__name__)


class DaVinciConnectionError(Exception):
    """DaVinci Resolve接続エラー"""

    pass


class DRConnection:
    """
    DaVinci Resolveへの接続を管理するクラス

    DaVinci Resolve Studio（有料版）のScripting APIを使用して
    プログラムからDRを制御する。
    """

    # DaVinci Resolve Scripting APIのパス（OS別）
    RESOLVE_SCRIPT_PATHS = {
        "darwin": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
        "win32": "C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules",
        "linux": "/opt/resolve/Developer/Scripting/Modules",
    }

    def __init__(self) -> None:
        self._resolve: Any = None
        self._fusion: Any = None
        self._project_manager: Any = None

    def _add_script_path(self) -> None:
        """Scripting APIのパスをPythonパスに追加"""
        platform = sys.platform
        script_path = self.RESOLVE_SCRIPT_PATHS.get(platform)

        if script_path is None:
            raise DaVinciConnectionError(f"Unsupported platform: {platform}")

        script_path = Path(script_path)
        if not script_path.exists():
            raise DaVinciConnectionError(
                f"DaVinci Resolve Scripting API not found at: {script_path}\n"
                "Please ensure DaVinci Resolve Studio is installed."
            )

        if str(script_path) not in sys.path:
            sys.path.append(str(script_path))
            logger.debug(f"Added script path: {script_path}")

    def connect(self) -> bool:
        """
        DaVinci Resolveに接続する

        Returns:
            接続に成功したかどうか

        Raises:
            DaVinciConnectionError: 接続に失敗した場合
        """
        if self._resolve is not None:
            logger.debug("Already connected to DaVinci Resolve")
            return True

        logger.info("Connecting to DaVinci Resolve...")

        try:
            self._add_script_path()
        except DaVinciConnectionError as e:
            # Scripting APIが見つからない場合は詳細な警告を出力
            logger.warning(
                "DaVinci Resolve Scripting API not found. "
                "Running in offline mode - timeline export to DaVinci will be SKIPPED.\n"
                f"  Reason: {e}\n"
                "  Hint: Install DaVinci Resolve Studio (free version does not support scripting)"
            )
            return False

        try:
            import DaVinciResolveScript as dvr

            self._resolve = dvr.scriptapp("Resolve")

            if self._resolve is None:
                raise DaVinciConnectionError(
                    "Failed to connect to DaVinci Resolve. "
                    "Please ensure DaVinci Resolve is running."
                )

            self._fusion = self._resolve.Fusion()
            self._project_manager = self._resolve.GetProjectManager()

            logger.info("Connected to DaVinci Resolve successfully")
            return True

        except ImportError as e:
            raise DaVinciConnectionError(
                f"Failed to import DaVinciResolveScript: {e}"
            ) from e
        except Exception as e:
            raise DaVinciConnectionError(f"Connection failed: {e}") from e

    def disconnect(self) -> None:
        """接続を解除する"""
        self._resolve = None
        self._fusion = None
        self._project_manager = None
        logger.info("Disconnected from DaVinci Resolve")

    @property
    def is_connected(self) -> bool:
        """接続中かどうか"""
        return self._resolve is not None

    @property
    def resolve(self) -> Any:
        """Resolveオブジェクト"""
        if not self.is_connected:
            raise DaVinciConnectionError("Not connected to DaVinci Resolve")
        return self._resolve

    @property
    def fusion(self) -> Any:
        """Fusionオブジェクト"""
        if not self.is_connected:
            raise DaVinciConnectionError("Not connected to DaVinci Resolve")
        return self._fusion

    @property
    def project_manager(self) -> Any:
        """ProjectManagerオブジェクト"""
        if not self.is_connected:
            raise DaVinciConnectionError("Not connected to DaVinci Resolve")
        return self._project_manager

    def get_current_project(self) -> Any:
        """現在のプロジェクトを取得"""
        return self.project_manager.GetCurrentProject()

    def get_version(self) -> str:
        """DaVinci Resolveのバージョンを取得"""
        if not self.is_connected:
            return "Not connected"
        try:
            return self.resolve.GetVersion()
        except Exception:
            return "Unknown"

    def __enter__(self) -> DRConnection:
        """コンテキストマネージャ: 接続"""
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        """コンテキストマネージャ: 切断"""
        self.disconnect()


# グローバル接続インスタンス
_global_connection: DRConnection | None = None


def get_connection() -> DRConnection:
    """グローバル接続インスタンスを取得"""
    global _global_connection
    if _global_connection is None:
        _global_connection = DRConnection()
    return _global_connection


def connect() -> bool:
    """グローバル接続でDRに接続"""
    return get_connection().connect()


def disconnect() -> None:
    """グローバル接続を解除"""
    if _global_connection is not None:
        _global_connection.disconnect()
