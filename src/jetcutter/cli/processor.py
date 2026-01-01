"""
processor - 音声処理パイプライン

音声抽出、無音検知、フィラー検知の統合処理を提供。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from jetcutter.config.settings import AppConfig
from jetcutter.editor.segment import Segment

console = Console()


@dataclass
class AudioProcessingResult:
    """音声処理の結果"""

    silence_segments: list[Segment]
    filler_segments: list[Segment]
    keep_segments: list[Segment]
    total_duration_ms: int
    audio_path: Path
    summary: dict[str, int | float] = field(default_factory=dict)


def process_audio(
    video_path: Path,
    config: AppConfig,
    progress: Progress | None = None,
    cleanup_files: list[Path] | None = None,
) -> AudioProcessingResult:
    """
    動画から音声を抽出し、無音・フィラー検知を実行する

    Args:
        video_path: 動画ファイルパス
        config: アプリケーション設定
        progress: 進捗表示用Progressインスタンス（省略時は内部で作成）
        cleanup_files: クリーンアップ対象ファイルリスト

    Returns:
        AudioProcessingResult - 処理結果

    Raises:
        AudioExtractionError: 音声抽出に失敗
        SilenceDetectionError: 無音検知に失敗
        TranscriptionError: 文字起こしに失敗
    """
    from jetcutter.audio.analyzer import SilenceAnalyzer
    from jetcutter.audio.extractor import AudioExtractor
    from jetcutter.editor.merger import SegmentMerger
    from jetcutter.speech.filler_detector import FillerDetector
    from jetcutter.speech.transcriber import Transcriber

    def _process_with_progress(prog: Progress) -> AudioProcessingResult:
        # 1. 音声抽出
        task = prog.add_task("Extracting audio...", total=None)
        extractor = AudioExtractor()
        audio_path = extractor.extract(video_path)
        if cleanup_files is not None:
            cleanup_files.append(audio_path)
        prog.update(task, completed=True)

        # 音声の長さを取得
        analyzer = SilenceAnalyzer(
            threshold_db=config.silence.threshold_db,
            min_duration_ms=config.silence.min_duration_ms,
        )
        total_duration_ms = analyzer.get_audio_duration_ms(audio_path)

        # 2. 無音検知
        task = prog.add_task("Detecting silence...", total=None)
        silence_segments = analyzer.detect_silence(audio_path)
        prog.update(task, completed=True)

        # 3. フィラー検知
        task = prog.add_task("Detecting fillers...", total=None)
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
        prog.update(task, completed=True)

        # 4. 保持区間算出
        task = prog.add_task("Calculating keep segments...", total=None)
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
        prog.update(task, completed=True)

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

    if progress is not None:
        return _process_with_progress(progress)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as prog:
            return _process_with_progress(prog)
