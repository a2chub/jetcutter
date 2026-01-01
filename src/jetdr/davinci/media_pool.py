"""
media_pool - DaVinci Resolveメディアプール操作モジュール

メディアのインポート、ビン管理を行う。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jetdr.davinci.connection import DaVinciConnectionError
from jetdr.davinci.project import DRProject
from jetdr.utils.logger import get_logger

logger = get_logger(__name__)


class DRMediaPool:
    """
    DaVinci Resolveのメディアプールを操作するクラス
    """

    def __init__(self, project: DRProject) -> None:
        """
        Args:
            project: DRProjectインスタンス
        """
        self.dr_project = project
        self._media_pool: Any = None

    @property
    def media_pool(self) -> Any:
        """MediaPoolオブジェクト"""
        if self._media_pool is None:
            self._media_pool = self.dr_project.project.GetMediaPool()
        return self._media_pool

    def get_root_folder(self) -> Any:
        """ルートフォルダを取得"""
        return self.media_pool.GetRootFolder()

    def get_current_folder(self) -> Any:
        """現在のフォルダを取得"""
        return self.media_pool.GetCurrentFolder()

    def set_current_folder(self, folder: Any) -> bool:
        """現在のフォルダを設定"""
        return self.media_pool.SetCurrentFolder(folder)

    def create_bin(self, name: str, parent: Any | None = None) -> Any:
        """
        新しいビン（フォルダ）を作成

        Args:
            name: ビン名
            parent: 親フォルダ（省略時はルート）

        Returns:
            作成されたビン
        """
        if parent is not None:
            self.set_current_folder(parent)

        folder = self.media_pool.AddSubFolder(self.get_current_folder(), name)

        if folder is None:
            # 既存のフォルダを探す
            current = self.get_current_folder()
            for sub in current.GetSubFolderList():
                if sub.GetName() == name:
                    folder = sub
                    break

        if folder is None:
            raise DaVinciConnectionError(f"Failed to create bin: {name}")

        logger.info(f"Created/found bin: {name}")
        return folder

    def import_media(self, file_paths: list[str | Path]) -> list[Any]:
        """
        メディアファイルをインポート

        Args:
            file_paths: インポートするファイルパスのリスト

        Returns:
            インポートされたMediaPoolItemのリスト
        """
        # パスを文字列に変換
        paths = [str(Path(p).resolve()) for p in file_paths]

        logger.info(f"Importing {len(paths)} media file(s)")

        items = self.media_pool.ImportMedia(paths)

        if items is None:
            raise DaVinciConnectionError("Failed to import media")

        logger.info(f"Imported {len(items)} media item(s)")
        return items

    def import_media_single(self, file_path: str | Path) -> Any:
        """
        単一のメディアファイルをインポート

        Args:
            file_path: インポートするファイルパス

        Returns:
            インポートされたMediaPoolItem
        """
        items = self.import_media([file_path])
        if not items:
            raise DaVinciConnectionError(f"Failed to import: {file_path}")
        return items[0]

    def find_media_by_name(self, name: str, folder: Any | None = None) -> Any | None:
        """
        名前でメディアを検索

        Args:
            name: メディア名
            folder: 検索フォルダ（省略時は現在のフォルダ）

        Returns:
            見つかったMediaPoolItem、なければNone
        """
        if folder is None:
            folder = self.get_current_folder()

        clips = folder.GetClipList()
        for clip in clips:
            if clip.GetName() == name:
                return clip

        return None

    def get_clip_info(self, clip: Any) -> dict:
        """
        クリップ情報を取得

        Args:
            clip: MediaPoolItem

        Returns:
            クリップ情報の辞書
        """
        return {
            "name": clip.GetName(),
            "clip_property": clip.GetClipProperty(),
            "duration": clip.GetClipProperty("Duration"),
            "fps": clip.GetClipProperty("FPS"),
            "resolution": clip.GetClipProperty("Resolution"),
        }

    def delete_clips(self, clips: list[Any]) -> bool:
        """
        クリップを削除

        Args:
            clips: 削除するMediaPoolItemのリスト

        Returns:
            成功したかどうか
        """
        return self.media_pool.DeleteClips(clips)

    def get_all_clips(self, folder: Any | None = None, recursive: bool = False) -> list[Any]:
        """
        フォルダ内の全クリップを取得

        Args:
            folder: 対象フォルダ（省略時はルート）
            recursive: サブフォルダも含めるか

        Returns:
            MediaPoolItemのリスト
        """
        if folder is None:
            folder = self.get_root_folder()

        clips = list(folder.GetClipList())

        if recursive:
            for sub in folder.GetSubFolderList():
                clips.extend(self.get_all_clips(sub, recursive=True))

        return clips
