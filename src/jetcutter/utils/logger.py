"""
logger - ログ設定モジュール

loguruを使用した構造化ログ出力の設定。
コンソールとファイルへの出力に対応。

環境変数:
    JETCUTTER_LOG_LEVEL: ログレベル（DEBUG, INFO, WARNING, ERROR）
    JETCUTTER_LOG_FORMAT: ログフォーマット（text, json）
    JETCUTTER_LOG_DIR: ログファイル出力ディレクトリ
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from loguru import logger


def _get_log_level_from_env() -> str:
    """環境変数からログレベルを取得"""
    level = os.environ.get("JETCUTTER_LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level not in valid_levels:
        return "INFO"
    return level


def _get_log_format_from_env() -> str:
    """環境変数からログフォーマットを取得"""
    fmt = os.environ.get("JETCUTTER_LOG_FORMAT", "text").lower()
    if fmt not in {"text", "json"}:
        return "text"
    return fmt


def _get_log_dir_from_env() -> Path | None:
    """環境変数からログディレクトリを取得"""
    log_dir = os.environ.get("JETCUTTER_LOG_DIR")
    if log_dir:
        return Path(log_dir)
    return None


# デフォルトのログ設定
DEFAULT_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

DEFAULT_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)


def _json_serializer(record: dict[str, Any]) -> str:
    """ログレコードをJSON形式にシリアライズする"""
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }
    # extra フィールドを追加
    if record.get("extra"):
        for key, value in record["extra"].items():
            if key not in subset:
                # Pathオブジェクトなどを文字列に変換
                if isinstance(value, Path):
                    subset[key] = str(value)
                elif hasattr(value, "__dict__"):
                    subset[key] = str(value)
                else:
                    subset[key] = value
    return json.dumps(subset, ensure_ascii=False, default=str)


def _json_sink(message: Any) -> None:
    """JSON形式でログを出力するシンク"""
    record = message.record
    sys.stderr.write(_json_serializer(record) + "\n")


def setup_logger(
    level: str = "INFO",
    log_dir: str | Path | None = None,
    console: bool = True,
    rotation: str = "1 day",
    retention: str = "7 days",
    json_format: bool = False,
) -> None:
    """
    ロガーをセットアップする

    Args:
        level: ログレベル（DEBUG, INFO, WARNING, ERROR）
        log_dir: ログファイルの出力ディレクトリ（Noneの場合はファイル出力なし）
        console: コンソール出力を有効にするか
        rotation: ログローテーション間隔
        retention: ログ保持期間
        json_format: JSON形式で出力するか
    """
    # 既存のハンドラを削除
    logger.remove()

    # コンソール出力
    if console:
        if json_format:
            logger.add(
                _json_sink,
                level=level,
                colorize=False,
            )
        else:
            logger.add(
                sys.stderr,
                format=DEFAULT_LOG_FORMAT,
                level=level,
                colorize=True,
            )

    # ファイル出力
    if log_dir is not None:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        if json_format:
            logger.add(
                log_path / "jetcutter_{time:YYYY-MM-DD}.jsonl",
                format="{message}",
                level="DEBUG",
                rotation=rotation,
                retention=retention,
                encoding="utf-8",
                serialize=True,
            )
        else:
            logger.add(
                log_path / "jetcutter_{time:YYYY-MM-DD}.log",
                format=DEFAULT_FILE_FORMAT,
                level="DEBUG",
                rotation=rotation,
                retention=retention,
                encoding="utf-8",
            )


def get_logger(name: str | None = None) -> Any:
    """
    ロガーインスタンスを取得する

    Args:
        name: ロガー名（モジュール名など）

    Returns:
        loguruのロガーインスタンス
    """
    if name:
        return logger.bind(name=name)
    return logger


def create_job_logger(job_id: str | None = None) -> Any:
    """
    ジョブID付きのロガーを作成する

    Args:
        job_id: ジョブID（省略時は自動生成）

    Returns:
        ジョブIDがバインドされたロガー
    """
    if job_id is None:
        job_id = str(uuid.uuid4())[:8]
    return logger.bind(job_id=job_id)


class LogContext:
    """
    ログコンテキストマネージャ

    処理の開始・終了をログに記録する。
    """

    def __init__(
        self,
        operation: str,
        job_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            operation: 操作名
            job_id: ジョブID（省略時は自動生成）
            **kwargs: 追加のコンテキスト情報
        """
        self.operation = operation
        self.job_id = job_id or str(uuid.uuid4())[:8]
        self.kwargs = kwargs
        self._logger = logger.bind(
            operation=operation,
            job_id=self.job_id,
            **kwargs,
        )

    def __enter__(self) -> LogContext:
        self._logger.info(f"Starting: {self.operation}")
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: Any,
    ) -> None:
        if exc_type is not None:
            self._logger.error(f"Failed: {self.operation} - {exc_val}")
        else:
            self._logger.info(f"Completed: {self.operation}")

    def log(self, level: str, message: str, **extra: Any) -> None:
        """コンテキスト付きでログを出力"""
        log_func = getattr(self._logger, level.lower())
        log_func(message, **extra)


def log_processing_stats(
    video_path: str | Path,
    duration_ms: int,
    silence_count: int,
    filler_count: int,
    keep_count: int,
    processing_time_sec: float,
    job_id: str | None = None,
) -> None:
    """
    処理統計をログに出力する

    Args:
        video_path: 処理した動画のパス
        duration_ms: 動画の長さ（ミリ秒）
        silence_count: 無音区間の数
        filler_count: フィラー区間の数
        keep_count: 保持区間の数
        processing_time_sec: 処理時間（秒）
        job_id: ジョブID（省略可）
    """
    duration_sec = duration_ms / 1000
    speed_ratio = duration_sec / processing_time_sec if processing_time_sec > 0 else 0

    # 構造化ログ用のコンテキスト
    log_context = {
        "video_path": str(video_path),
        "duration_sec": duration_sec,
        "silence_count": silence_count,
        "filler_count": filler_count,
        "keep_count": keep_count,
        "processing_time_sec": processing_time_sec,
        "speed_ratio": speed_ratio,
    }
    if job_id:
        log_context["job_id"] = job_id

    bound_logger = logger.bind(**log_context)
    bound_logger.info(
        f"Processing complete: {Path(video_path).name} | "
        f"Duration: {duration_sec:.1f}s | "
        f"Segments: silence={silence_count}, filler={filler_count}, keep={keep_count} | "
        f"Time: {processing_time_sec:.2f}s ({speed_ratio:.2f}x)"
    )


# デフォルトのセットアップ（環境変数で設定可能）
_default_log_dir = _get_log_dir_from_env()
_default_json_format = _get_log_format_from_env() == "json"
setup_logger(
    level=_get_log_level_from_env(),
    console=True,
    log_dir=_default_log_dir,
    json_format=_default_json_format,
)
