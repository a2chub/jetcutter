"""
filler_detector - フィラー検知モジュール

音声認識結果からフィラー単語（「あー」「えっと」等）を検出する。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from jetdr.editor.segment import Segment, SegmentType
from jetdr.utils.logger import get_logger

if TYPE_CHECKING:
    from jetdr.speech.transcriber import WordTimestamp

logger = get_logger(__name__)


# デフォルトのフィラー単語リスト（日本語）
DEFAULT_FILLER_WORDS = [
    "あー",
    "えー",
    "えっと",
    "うーん",
    "まあ",
    "なんか",
    "その",
    "あのー",
    "ええと",
    "あのね",
    "あー",
    "うん",
    "んー",
]


class FillerDetector:
    """
    フィラー単語を検出するクラス

    Whisperの文字起こし結果からフィラー単語を検出し、
    削除対象区間としてマークする。
    """

    def __init__(self, filler_words: list[str] | None = None) -> None:
        """
        Args:
            filler_words: 検出対象のフィラー単語リスト。省略時はデフォルトを使用
        """
        if filler_words is None:
            filler_words = DEFAULT_FILLER_WORDS.copy()

        # 正規化してセットに変換（高速な検索のため）
        self.filler_words = {self._normalize(w) for w in filler_words}
        logger.debug(f"Filler detector initialized with {len(self.filler_words)} words")

    @staticmethod
    def _normalize(word: str) -> str:
        """単語を正規化（小文字化、空白除去）"""
        return word.strip().lower()

    def detect(self, word_timestamps: list[WordTimestamp]) -> list[Segment]:
        """
        単語リストからフィラー区間を検出する

        Args:
            word_timestamps: 単語タイムスタンプのリスト

        Returns:
            フィラー区間のリスト（Segmentオブジェクト）
        """
        filler_segments: list[Segment] = []

        for word_ts in word_timestamps:
            normalized = self._normalize(word_ts.word)

            if normalized in self.filler_words:
                filler_segments.append(
                    Segment(
                        start_ms=word_ts.start_ms,
                        end_ms=word_ts.end_ms,
                        type=SegmentType.FILLER,
                        metadata={
                            "word": word_ts.word,
                            "confidence": word_ts.confidence,
                        },
                    )
                )

        logger.info(f"Detected {len(filler_segments)} filler segments")
        return filler_segments

    def detect_with_context(
        self,
        word_timestamps: list[WordTimestamp],
        context_words: int = 2,
    ) -> list[dict]:
        """
        フィラー単語を検出し、前後のコンテキストを含めて返す

        Args:
            word_timestamps: 単語タイムスタンプのリスト
            context_words: 前後に含める単語数

        Returns:
            フィラー情報のリスト（前後のコンテキスト付き）
        """
        results: list[dict] = []

        for i, word_ts in enumerate(word_timestamps):
            normalized = self._normalize(word_ts.word)

            if normalized in self.filler_words:
                # 前後のコンテキストを取得
                start_idx = max(0, i - context_words)
                end_idx = min(len(word_timestamps), i + context_words + 1)

                context_before = [w.word for w in word_timestamps[start_idx:i]]
                context_after = [w.word for w in word_timestamps[i + 1 : end_idx]]

                results.append(
                    {
                        "word": word_ts.word,
                        "start_ms": word_ts.start_ms,
                        "end_ms": word_ts.end_ms,
                        "confidence": word_ts.confidence,
                        "context_before": context_before,
                        "context_after": context_after,
                    }
                )

        return results

    def add_filler_word(self, word: str) -> None:
        """フィラー単語を追加"""
        self.filler_words.add(self._normalize(word))

    def remove_filler_word(self, word: str) -> None:
        """フィラー単語を削除"""
        self.filler_words.discard(self._normalize(word))

    def get_filler_words(self) -> list[str]:
        """フィラー単語リストを取得"""
        return sorted(self.filler_words)

    @classmethod
    def from_yaml(cls, path: str | Path) -> FillerDetector:
        """
        YAMLファイルからフィラー辞書を読み込んでインスタンスを作成する

        Args:
            path: フィラー辞書YAMLファイルのパス

        Returns:
            FillerDetectorインスタンス
        """
        path = Path(path)

        if not path.exists():
            logger.warning(f"Filler dictionary not found: {path}, using defaults")
            return cls()

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        filler_words = data.get("fillers", [])
        logger.info(f"Loaded {len(filler_words)} filler words from {path}")

        return cls(filler_words=filler_words)

    def to_yaml(self, path: str | Path) -> None:
        """
        フィラー辞書をYAMLファイルに書き出す

        Args:
            path: 出力ファイルのパス
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {"fillers": sorted(self.filler_words)}

        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"Saved {len(self.filler_words)} filler words to {path}")


def detect_fillers_from_audio(
    audio_path: str | Path,
    filler_words: list[str] | None = None,
    model_name: str = "large-v3",
) -> list[Segment]:
    """
    音声ファイルからフィラー区間を検出するユーティリティ関数

    Args:
        audio_path: 音声ファイルのパス
        filler_words: 検出対象のフィラー単語リスト
        model_name: Whisperモデル名

    Returns:
        フィラー区間のリスト
    """
    from jetdr.speech.transcriber import Transcriber

    transcriber = Transcriber(model_name=model_name)
    word_timestamps = transcriber.transcribe(audio_path)

    detector = FillerDetector(filler_words=filler_words)
    return detector.detect(word_timestamps)
