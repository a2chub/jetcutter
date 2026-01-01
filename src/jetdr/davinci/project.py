"""
project - DaVinci Resolveプロジェクト操作モジュール

プロジェクトの作成、取得、設定管理を行う。
"""

from __future__ import annotations

from typing import Any

from jetdr.davinci.connection import DaVinciConnectionError, DRConnection
from jetdr.utils.logger import get_logger

logger = get_logger(__name__)


class DRProject:
    """
    DaVinci Resolveプロジェクトを操作するクラス
    """

    def __init__(self, connection: DRConnection) -> None:
        """
        Args:
            connection: DRConnectionインスタンス
        """
        self.connection = connection
        self._project: Any = None

    @property
    def project(self) -> Any:
        """現在のプロジェクト"""
        if self._project is None:
            self._project = self.connection.get_current_project()
        return self._project

    def get_current_project(self) -> Any:
        """現在のプロジェクトを取得"""
        self._project = self.connection.get_current_project()
        if self._project is None:
            raise DaVinciConnectionError("No project is currently open")
        return self._project

    def create_project(self, name: str) -> Any:
        """
        新しいプロジェクトを作成

        Args:
            name: プロジェクト名

        Returns:
            作成されたプロジェクト
        """
        pm = self.connection.project_manager
        project = pm.CreateProject(name)

        if project is None:
            raise DaVinciConnectionError(f"Failed to create project: {name}")

        self._project = project
        logger.info(f"Created project: {name}")
        return project

    def load_project(self, name: str) -> Any:
        """
        プロジェクトを読み込む

        Args:
            name: プロジェクト名

        Returns:
            読み込まれたプロジェクト
        """
        pm = self.connection.project_manager
        project = pm.LoadProject(name)

        if project is None:
            raise DaVinciConnectionError(f"Failed to load project: {name}")

        self._project = project
        logger.info(f"Loaded project: {name}")
        return project

    def save_project(self) -> bool:
        """プロジェクトを保存"""
        pm = self.connection.project_manager
        result = pm.SaveProject()
        if result:
            logger.info("Project saved")
        else:
            logger.warning("Failed to save project")
        return result

    def get_project_name(self) -> str:
        """プロジェクト名を取得"""
        return self.project.GetName()

    def get_project_settings(self) -> dict:
        """プロジェクト設定を取得"""
        return {
            "name": self.project.GetName(),
            "timeline_count": self.project.GetTimelineCount(),
            "frame_rate": self.get_frame_rate(),
            "resolution": self.get_resolution(),
        }

    def get_frame_rate(self) -> float:
        """プロジェクトのフレームレートを取得"""
        try:
            setting = self.project.GetSetting("timelineFrameRate")
            return float(setting) if setting else 29.97
        except Exception:
            return 29.97

    def get_resolution(self) -> tuple[int, int]:
        """プロジェクトの解像度を取得"""
        try:
            width = int(self.project.GetSetting("timelineResolutionWidth") or 1920)
            height = int(self.project.GetSetting("timelineResolutionHeight") or 1080)
            return (width, height)
        except Exception:
            return (1920, 1080)

    def set_frame_rate(self, fps: float) -> bool:
        """プロジェクトのフレームレートを設定"""
        return self.project.SetSetting("timelineFrameRate", str(fps))

    def set_resolution(self, width: int, height: int) -> bool:
        """プロジェクトの解像度を設定"""
        result1 = self.project.SetSetting("timelineResolutionWidth", str(width))
        result2 = self.project.SetSetting("timelineResolutionHeight", str(height))
        return result1 and result2

    def list_projects(self) -> list[str]:
        """利用可能なプロジェクト一覧を取得"""
        pm = self.connection.project_manager
        return pm.GetProjectListInCurrentFolder() or []

    def close_project(self) -> bool:
        """現在のプロジェクトを閉じる"""
        pm = self.connection.project_manager
        result = pm.CloseProject(self.project)
        if result:
            self._project = None
            logger.info("Project closed")
        return result
