"""
core - UI非依存の処理ロジック

GUIとCLIで共有するコア処理機能を提供。
"""

from jetcutter.core.callbacks import ProgressCallback
from jetcutter.core.processor import AudioProcessingResult, process_audio

__all__ = [
    "ProgressCallback",
    "AudioProcessingResult",
    "process_audio",
]
