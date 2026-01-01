"""
audio - 音声処理モジュール

音声抽出（ffmpeg）、無音検知（pydub）を担当。
"""

from jetcutter.audio.analyzer import SilenceAnalyzer, SilenceDetectionError
from jetcutter.audio.extractor import AudioExtractionError, AudioExtractor

__all__ = [
    "AudioExtractor",
    "AudioExtractionError",
    "SilenceAnalyzer",
    "SilenceDetectionError",
]
