"""
cli - CLIユーティリティモジュール

main.pyから抽出した共通処理ロジックを提供。
"""

from __future__ import annotations

from jetcutter.cli.config_loader import load_app_config
from jetcutter.cli.processor import AudioProcessingResult, process_audio
from jetcutter.cli.summary import display_summary

__all__ = [
    "load_app_config",
    "process_audio",
    "AudioProcessingResult",
    "display_summary",
]
