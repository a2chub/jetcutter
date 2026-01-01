"""
analyzer - 無音検知モジュール

pydubを使用して音声ファイルから無音区間を検出する。
"""

from __future__ import annotations

from pathlib import Path

from pydub import AudioSegment
from pydub.silence import detect_silence

from jetcutter.editor.segment import Segment, SegmentType
from jetcutter.utils.logger import get_logger

logger = get_logger(__name__)


class SilenceDetectionError(Exception):
    """無音検知エラー"""

    pass


class SilenceAnalyzer:
    """
    音声ファイルから無音区間を検出するクラス

    pydubを使用して音量ベースの無音検知を行う。
    """

    def __init__(
        self,
        threshold_db: float = -40.0,
        min_duration_ms: int = 300,
    ) -> None:
        """
        Args:
            threshold_db: 無音判定しきい値（dBFS）。この値以下を無音とみなす
            min_duration_ms: 最小無音期間（ミリ秒）。この長さ以上の無音のみ検出
        """
        self.threshold_db = threshold_db
        self.min_duration_ms = min_duration_ms

    def detect_silence(self, audio_path: str | Path) -> list[Segment]:
        """
        音声ファイルから無音区間を検出する

        Args:
            audio_path: 音声ファイルのパス

        Returns:
            無音区間のリスト（Segmentオブジェクト）

        Raises:
            SilenceDetectionError: 検出に失敗した場合
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise SilenceDetectionError(f"Audio file not found: {audio_path}")

        logger.info(f"Detecting silence in {audio_path.name}")
        logger.debug(f"Threshold: {self.threshold_db}dB, Min duration: {self.min_duration_ms}ms")

        try:
            audio = AudioSegment.from_file(str(audio_path))
        except Exception as e:
            raise SilenceDetectionError(f"Failed to load audio file: {e}") from e

        try:
            # pydubのdetect_silenceは[(start, end), ...]形式で返す
            silence_ranges = detect_silence(
                audio,
                min_silence_len=self.min_duration_ms,
                silence_thresh=self.threshold_db,
            )
        except Exception as e:
            raise SilenceDetectionError(f"Silence detection failed: {e}") from e

        segments = [
            Segment(
                start_ms=start,
                end_ms=end,
                type=SegmentType.SILENCE,
            )
            for start, end in silence_ranges
        ]

        logger.info(f"Found {len(segments)} silence segments")
        return segments

    def get_audio_duration_ms(self, audio_path: str | Path) -> int:
        """
        音声ファイルの長さをミリ秒で取得する

        Args:
            audio_path: 音声ファイルのパス

        Returns:
            音声の長さ（ミリ秒）
        """
        audio_path = Path(audio_path)

        try:
            audio = AudioSegment.from_file(str(audio_path))
            return len(audio)
        except Exception as e:
            raise SilenceDetectionError(f"Failed to get audio duration: {e}") from e

    def get_audio_stats(self, audio_path: str | Path) -> dict[str, float]:
        """
        音声ファイルの統計情報を取得する

        Args:
            audio_path: 音声ファイルのパス

        Returns:
            統計情報（dBFS, max_dBFS, duration_ms等）
        """
        audio_path = Path(audio_path)

        try:
            audio = AudioSegment.from_file(str(audio_path))
            return {
                "duration_ms": len(audio),
                "dBFS": audio.dBFS,
                "max_dBFS": audio.max_dBFS,
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "sample_width": audio.sample_width,
            }
        except Exception as e:
            raise SilenceDetectionError(f"Failed to get audio stats: {e}") from e

    def detect_non_silence(self, audio_path: str | Path) -> list[Segment]:
        """
        音声ファイルから有音区間を検出する（無音の補集合）

        Args:
            audio_path: 音声ファイルのパス

        Returns:
            有音区間のリスト（Segmentオブジェクト）
        """
        from pydub.silence import detect_nonsilent

        audio_path = Path(audio_path)

        try:
            audio = AudioSegment.from_file(str(audio_path))
        except Exception as e:
            raise SilenceDetectionError(f"Failed to load audio file: {e}") from e

        try:
            nonsilent_ranges = detect_nonsilent(
                audio,
                min_silence_len=self.min_duration_ms,
                silence_thresh=self.threshold_db,
            )
        except Exception as e:
            raise SilenceDetectionError(f"Non-silence detection failed: {e}") from e

        segments = [
            Segment(
                start_ms=start,
                end_ms=end,
                type=SegmentType.KEEP,
            )
            for start, end in nonsilent_ranges
        ]

        logger.info(f"Found {len(segments)} non-silence segments")
        return segments
