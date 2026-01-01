"""
speech - 音声認識モジュール

音声認識（faster-whisper）、フィラー検知を担当。
"""

from jetdr.speech.filler_detector import FillerDetector
from jetdr.speech.transcriber import Transcriber, TranscriptionError, WordTimestamp

__all__ = [
    "Transcriber",
    "TranscriptionError",
    "WordTimestamp",
    "FillerDetector",
]
