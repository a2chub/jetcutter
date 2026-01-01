"""
transcriber - 音声認識モジュール

faster-whisperを使用して音声を文字起こしし、
単語レベルのタイムスタンプを取得する。

パフォーマンス:
    モデルはグローバルにキャッシュされ、バッチ処理時に再利用されます。
    明示的にアンロードするには clear_model_cache() を呼び出してください。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from jetcutter.utils.logger import get_logger

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = get_logger(__name__)

# グローバルモデルキャッシュ
_model_cache: dict[str, WhisperModel] = {}


def get_cached_model(
    model_name: str,
    device: str = "auto",
    compute_type: str = "int8",
) -> WhisperModel:
    """
    キャッシュされたWhisperモデルを取得する

    Args:
        model_name: モデル名
        device: デバイス
        compute_type: 計算精度

    Returns:
        WhisperModelインスタンス
    """
    cache_key = f"{model_name}:{device}:{compute_type}"

    if cache_key not in _model_cache:
        logger.info(f"Loading Whisper model: {model_name} (device={device}, compute_type={compute_type})")
        from faster_whisper import WhisperModel

        _model_cache[cache_key] = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )
        logger.info(f"Whisper model loaded and cached: {cache_key}")
    else:
        logger.debug(f"Using cached Whisper model: {cache_key}")

    return _model_cache[cache_key]


def clear_model_cache() -> None:
    """モデルキャッシュをクリアしてメモリを解放"""
    global _model_cache
    if _model_cache:
        logger.info(f"Clearing {len(_model_cache)} cached Whisper model(s)")
        _model_cache.clear()
    else:
        logger.debug("Model cache is already empty")


class TranscriptionError(Exception):
    """文字起こしエラー"""

    pass


@dataclass
class WordTimestamp:
    """単語とそのタイムスタンプを保持するデータクラス"""

    word: str
    start_ms: int
    end_ms: int
    confidence: float

    @property
    def duration_ms(self) -> int:
        """単語の長さ（ミリ秒）"""
        return self.end_ms - self.start_ms


class Transcriber:
    """
    faster-whisperを使用した音声認識クラス

    単語レベルのタイムスタンプを取得し、
    フィラー検知や字幕生成に使用できるデータを提供する。
    """

    def __init__(
        self,
        model_name: str = "large-v3",
        device: str = "auto",
        compute_type: str = "int8",
        language: str = "ja",
    ) -> None:
        """
        Args:
            model_name: Whisperモデル名（tiny, base, small, medium, large-v3等）
            device: 使用デバイス（"auto", "cuda", "cpu"）
            compute_type: 計算精度（"auto", "float16", "int8"等）
            language: 認識対象言語コード
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model: WhisperModel | None = None

    def _load_model(self) -> WhisperModel:
        """モデルを遅延ロードする（グローバルキャッシュを使用）"""
        if self._model is None:
            try:
                self._model = get_cached_model(
                    self.model_name,
                    self.device,
                    self.compute_type,
                )
            except Exception as e:
                raise TranscriptionError(f"Failed to load Whisper model: {e}") from e
        return self._model

    def transcribe(self, audio_path: str | Path) -> list[WordTimestamp]:
        """
        音声を文字起こしし、単語タイムスタンプを返す

        Args:
            audio_path: 音声ファイルのパス

        Returns:
            WordTimestampオブジェクトのリスト

        Raises:
            TranscriptionError: 文字起こしに失敗した場合
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        logger.info(f"Transcribing {audio_path.name}")

        model = self._load_model()

        try:
            segments, info = model.transcribe(
                str(audio_path),
                language=self.language,
                word_timestamps=True,
                vad_filter=True,  # Voice Activity Detection
            )

            logger.debug(f"Detected language: {info.language}, probability: {info.language_probability:.2f}")

            word_timestamps: list[WordTimestamp] = []

            for segment in segments:
                if segment.words:
                    for word in segment.words:
                        word_timestamps.append(
                            WordTimestamp(
                                word=word.word.strip(),
                                start_ms=int(word.start * 1000),
                                end_ms=int(word.end * 1000),
                                confidence=word.probability,
                            )
                        )

            logger.info(f"Transcribed {len(word_timestamps)} words")
            return word_timestamps

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e

    def transcribe_text(self, audio_path: str | Path) -> str:
        """
        音声を文字起こしし、テキストのみを返す

        Args:
            audio_path: 音声ファイルのパス

        Returns:
            文字起こしテキスト
        """
        words = self.transcribe(audio_path)
        return "".join(w.word for w in words)

    def transcribe_with_segments(
        self, audio_path: str | Path
    ) -> tuple[list[WordTimestamp], list[dict]]:
        """
        音声を文字起こしし、単語タイムスタンプとセグメント情報を返す

        Args:
            audio_path: 音声ファイルのパス

        Returns:
            (単語タイムスタンプのリスト, セグメント情報のリスト)
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        model = self._load_model()

        try:
            segments_iter, info = model.transcribe(
                str(audio_path),
                language=self.language,
                word_timestamps=True,
                vad_filter=True,
            )

            word_timestamps: list[WordTimestamp] = []
            segment_info: list[dict] = []

            for segment in segments_iter:
                segment_info.append(
                    {
                        "start_ms": int(segment.start * 1000),
                        "end_ms": int(segment.end * 1000),
                        "text": segment.text.strip(),
                    }
                )

                if segment.words:
                    for word in segment.words:
                        word_timestamps.append(
                            WordTimestamp(
                                word=word.word.strip(),
                                start_ms=int(word.start * 1000),
                                end_ms=int(word.end * 1000),
                                confidence=word.probability,
                            )
                        )

            return word_timestamps, segment_info

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e

    def unload_model(self) -> None:
        """
        インスタンスからモデル参照を解除する

        Note:
            モデルはグローバルキャッシュに保持されるため、
            完全にメモリを解放するには clear_model_cache() を
            呼び出してください。
        """
        if self._model is not None:
            self._model = None
            logger.debug("Model reference released from instance")
