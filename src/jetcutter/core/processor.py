"""
processor - 音声処理パイプライン（コア実装）

UI非依存の音声抽出、無音検知、フィラー検知の統合処理。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jetcutter.config.settings import AppConfig
from jetcutter.core.callbacks import NullProgressCallback, ProgressCallback
from jetcutter.editor.segment import Segment


@dataclass
class AudioProcessingResult:
    """音声処理の結果"""

    silence_segments: list[Segment]
    filler_segments: list[Segment]
    keep_segments: list[Segment]
    total_duration_ms: int
    audio_path: Path
    summary: dict[str, int | float] = field(default_factory=dict)


class ProcessingCancelledError(Exception):
    """処理がキャンセルされた場合の例外"""

    pass


def process_audio(
    video_path: Path,
    config: AppConfig,
    callback: ProgressCallback | None = None,
    cleanup_files: list[Path] | None = None,
) -> AudioProcessingResult:
    """
    動画から音声を抽出し、無音・フィラー検知を実行する

    Args:
        video_path: 動画ファイルパス
        config: アプリケーション設定
        callback: 進捗通知用コールバック（省略時はNullProgressCallback）
        cleanup_files: クリーンアップ対象ファイルリスト

    Returns:
        AudioProcessingResult - 処理結果

    Raises:
        AudioExtractionError: 音声抽出に失敗
        SilenceDetectionError: 無音検知に失敗
        TranscriptionError: 文字起こしに失敗
        ProcessingCancelledError: 処理がキャンセルされた
    """
    from jetcutter.audio.analyzer import SilenceAnalyzer
    from jetcutter.audio.extractor import AudioExtractor
    from jetcutter.editor.merger import SegmentMerger
    from jetcutter.speech.filler_detector import FillerDetector
    from jetcutter.speech.transcriber import Transcriber

    if callback is None:
        callback = NullProgressCallback()

    def check_cancelled() -> None:
        """キャンセルチェック"""
        if callback.is_cancelled():
            raise ProcessingCancelledError("Processing was cancelled by user")

    # 1. 音声抽出
    stage = "Extracting audio..."
    callback.on_stage_start(stage)
    check_cancelled()

    extractor = AudioExtractor()
    audio_path = extractor.extract(video_path)
    if cleanup_files is not None:
        cleanup_files.append(audio_path)
    callback.on_stage_complete(stage)

    # 音声の長さを取得
    analyzer = SilenceAnalyzer(
        threshold_db=config.silence.threshold_db,
        min_duration_ms=config.silence.min_duration_ms,
    )
    total_duration_ms = analyzer.get_audio_duration_ms(audio_path)

    # 2. 無音検知
    stage = "Detecting silence..."
    callback.on_stage_start(stage)
    check_cancelled()

    silence_segments = analyzer.detect_silence(audio_path)
    callback.on_stage_complete(stage)

    # 3. フィラー検知
    stage = "Detecting fillers..."
    callback.on_stage_start(stage)
    check_cancelled()

    transcriber = Transcriber(
        model_name=config.filler.model_name,
        device=config.filler.device,
        compute_type=config.filler.compute_type,
        language=config.filler.language,
    )
    word_timestamps = transcriber.transcribe(audio_path)

    filler_words = config.filler_words or []
    detector = FillerDetector(filler_words=filler_words if filler_words else None)
    filler_segments = detector.detect(word_timestamps)
    callback.on_stage_complete(stage)

    # 4. 保持区間算出
    stage = "Calculating keep segments..."
    callback.on_stage_start(stage)
    check_cancelled()

    merger = SegmentMerger(
        margin_before_ms=config.margin.before_ms,
        margin_after_ms=config.margin.after_ms,
        min_keep_duration_ms=config.min_keep_duration_ms,
        fps=config.fps,
    )
    keep_segments = merger.calculate_keep_segments(
        silence_segments,
        filler_segments,
        total_duration_ms,
    )
    callback.on_stage_complete(stage)

    # サマリー計算
    summary = merger.get_cut_summary(
        silence_segments,
        filler_segments,
        keep_segments,
        total_duration_ms,
    )

    return AudioProcessingResult(
        silence_segments=silence_segments,
        filler_segments=filler_segments,
        keep_segments=keep_segments,
        total_duration_ms=total_duration_ms,
        audio_path=audio_path,
        summary=summary,
    )
