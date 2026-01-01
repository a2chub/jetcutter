"""
file_utils - ファイル操作ユーティリティ

ファイル存在確認、一時ファイル管理、パス操作などを提供。
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

# サポートする動画形式
SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".m4v",
    ".wmv",
    ".flv",
}

# サポートする音声形式
SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".aac",
    ".m4a",
    ".flac",
    ".ogg",
}


def is_video_file(path: str | Path) -> bool:
    """
    動画ファイルかどうかを判定する

    Args:
        path: ファイルパス

    Returns:
        動画ファイルの場合True
    """
    return Path(path).suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS


def is_audio_file(path: str | Path) -> bool:
    """
    音声ファイルかどうかを判定する

    Args:
        path: ファイルパス

    Returns:
        音声ファイルの場合True
    """
    return Path(path).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def ensure_directory(path: str | Path) -> Path:
    """
    ディレクトリが存在することを保証する（なければ作成）

    Args:
        path: ディレクトリパス

    Returns:
        作成または確認されたPathオブジェクト
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(
    input_path: str | Path,
    suffix: str = "_edited",
    output_dir: str | Path | None = None,
) -> Path:
    """
    出力ファイルパスを生成する

    Args:
        input_path: 入力ファイルパス
        suffix: ファイル名に追加するサフィックス
        output_dir: 出力ディレクトリ（Noneの場合は入力と同じディレクトリ）

    Returns:
        出力ファイルのPath
    """
    input_path = Path(input_path)
    stem = input_path.stem
    ext = input_path.suffix

    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        ensure_directory(output_dir)

    return output_dir / f"{stem}{suffix}{ext}"


@contextmanager
def temporary_file(
    suffix: str = "",
    prefix: str = "jetdr_",
    delete: bool = True,
) -> Generator[Path, None, None]:
    """
    一時ファイルのコンテキストマネージャ

    Args:
        suffix: ファイル拡張子
        prefix: ファイル名プレフィックス
        delete: コンテキスト終了時に削除するか

    Yields:
        一時ファイルのPath
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    temp_path = Path(path)

    try:
        # ファイルディスクリプタを閉じる（Windowsで必要）
        import os

        os.close(fd)
        yield temp_path
    finally:
        if delete and temp_path.exists():
            temp_path.unlink()


@contextmanager
def temporary_directory(
    prefix: str = "jetdr_",
    delete: bool = True,
) -> Generator[Path, None, None]:
    """
    一時ディレクトリのコンテキストマネージャ

    Args:
        prefix: ディレクトリ名プレフィックス
        delete: コンテキスト終了時に削除するか

    Yields:
        一時ディレクトリのPath
    """
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))

    try:
        yield temp_dir
    finally:
        if delete and temp_dir.exists():
            shutil.rmtree(temp_dir)


def list_video_files(
    directory: str | Path,
    recursive: bool = False,
) -> list[Path]:
    """
    ディレクトリ内の動画ファイルを列挙する

    Args:
        directory: 検索ディレクトリ
        recursive: サブディレクトリも検索するか

    Returns:
        動画ファイルのPathリスト
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []

    videos: list[Path] = []

    if recursive:
        for ext in SUPPORTED_VIDEO_EXTENSIONS:
            videos.extend(directory.rglob(f"*{ext}"))
    else:
        for ext in SUPPORTED_VIDEO_EXTENSIONS:
            videos.extend(directory.glob(f"*{ext}"))

    return sorted(videos)


def get_file_size_mb(path: str | Path) -> float:
    """
    ファイルサイズをMBで取得する

    Args:
        path: ファイルパス

    Returns:
        ファイルサイズ（MB）
    """
    path = Path(path)
    if not path.exists():
        return 0.0
    return path.stat().st_size / (1024 * 1024)


def validate_input_file(path: str | Path) -> Path:
    """
    入力ファイルを検証する

    Args:
        path: ファイルパス

    Returns:
        検証済みのPath

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: サポートされていないファイル形式の場合
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    if not is_video_file(path) and not is_audio_file(path):
        raise ValueError(
            f"Unsupported file format: {path.suffix}. "
            f"Supported video: {SUPPORTED_VIDEO_EXTENSIONS}, "
            f"Supported audio: {SUPPORTED_AUDIO_EXTENSIONS}"
        )

    return path


def safe_copy(src: str | Path, dst: str | Path) -> Path:
    """
    ファイルを安全にコピーする

    Args:
        src: コピー元
        dst: コピー先

    Returns:
        コピー先のPath
    """
    src = Path(src)
    dst = Path(dst)

    ensure_directory(dst.parent)
    shutil.copy2(src, dst)

    return dst
