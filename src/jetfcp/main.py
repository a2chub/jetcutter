"""
jetfcp - Final Cut Pro 自動編集ツール CLI

jetDRのFinal Cut Pro版。FCPXML形式でタイムラインを出力。
"""

from __future__ import annotations

import atexit
import signal
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from jetdr import __version__

app = typer.Typer(
    name="jetfcp",
    help="Final Cut Pro 自動編集ツール - 無音区間・フィラー自動検知・FCPXML出力",
    add_completion=False,
)

console = Console()

# グローバルなクリーンアップ対象ファイルリスト
_cleanup_files: list[Path] = []


def _cleanup_temp_files() -> None:
    """一時ファイルをクリーンアップする"""
    for path in _cleanup_files:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
    _cleanup_files.clear()


def _signal_handler(signum: int, frame: object) -> None:
    """シグナルハンドラ: Graceful Shutdownを処理"""
    signal_name = signal.Signals(signum).name
    console.print(f"\n[yellow]Received {signal_name}, cleaning up...[/yellow]")
    _cleanup_temp_files()
    raise typer.Exit(130)


# シグナルハンドラを登録
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# プログラム終了時にもクリーンアップ
atexit.register(_cleanup_temp_files)


def version_callback(value: bool) -> None:
    """バージョン表示"""
    if value:
        console.print(f"jetFCP version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="バージョンを表示",
    ),
) -> None:
    """jetFCP - Final Cut Pro 自動編集ツール"""
    pass


@app.command()
def export(
    video_path: Path = typer.Argument(..., help="処理対象の動画ファイルパス"),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="出力FCPXMLファイルパス",
    ),
    output_name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="タイムライン名（出力ファイル名）",
    ),
    config_path: Path = typer.Option(
        Path("config/settings.yaml"),
        "--config",
        "-c",
        help="設定ファイルパス",
    ),
    fillers_path: Path | None = typer.Option(
        None,
        "--fillers",
        "-f",
        help="フィラー辞書ファイルパス",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="詳細出力を有効化",
    ),
) -> None:
    """
    動画を処理してFCPXMLファイルを生成する
    """
    from jetdr.audio.analyzer import SilenceAnalyzer
    from jetdr.audio.extractor import AudioExtractor
    from jetdr.config.settings import AppConfig
    from jetdr.editor.merger import SegmentMerger
    from jetdr.exporters.base import ExportConfig
    from jetdr.fcp.exporter import FCPExporter
    from jetdr.speech.filler_detector import FillerDetector
    from jetdr.speech.transcriber import Transcriber
    from jetdr.utils.file_utils import validate_input_file
    from jetdr.utils.logger import setup_logger

    # ログ設定
    setup_logger(level="DEBUG" if verbose else "INFO")

    # 入力ファイル検証
    try:
        video_path = validate_input_file(video_path)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    # 設定読み込み
    try:
        if config_path.exists():
            config = AppConfig.load_with_fillers(config_path, fillers_path)
        else:
            console.print(
                f"[yellow]Warning:[/yellow] Config not found: {config_path}, using defaults"
            )
            config = AppConfig()
    except Exception as e:
        console.print(f"[red]Error loading config:[/red] {e}")
        raise typer.Exit(1) from None

    # 出力名の設定
    if output_name is None:
        output_name = f"JetCut_{video_path.stem}"

    console.print(f"\n[bold]Processing:[/bold] {video_path.name}")
    console.print(f"[bold]Output:[/bold] {output_name}.fcpxml\n")

    start_time = time.time()
    audio_path: Path | None = None

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 1. 音声抽出
            task = progress.add_task("Extracting audio...", total=None)
            extractor = AudioExtractor()
            audio_path = extractor.extract(video_path)
            _cleanup_files.append(audio_path)
            progress.update(task, completed=True)

            # 2. 無音検知
            task = progress.add_task("Detecting silence...", total=None)
            analyzer = SilenceAnalyzer(
                threshold_db=config.silence.threshold_db,
                min_duration_ms=config.silence.min_duration_ms,
            )
            silence_segments = analyzer.detect_silence(audio_path)
            total_duration_ms = analyzer.get_audio_duration_ms(audio_path)
            progress.update(task, completed=True)

            # 3. フィラー検知
            task = progress.add_task("Detecting fillers...", total=None)
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
            progress.update(task, completed=True)

            # 4. 保持区間算出
            task = progress.add_task("Calculating keep segments...", total=None)
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
            progress.update(task, completed=True)

            # 5. FCPXML生成
            task = progress.add_task("Generating FCPXML...", total=None)

            export_config = ExportConfig(
                video_path=video_path,
                output_name=output_name,
                fps=config.fps,
            )

            if output is not None:
                export_config.metadata["output_path"] = str(output)

            exporter = FCPExporter()
            result = exporter.export(keep_segments, export_config)

            progress.update(task, completed=True)

        # 処理時間
        processing_time = time.time() - start_time

        # 結果表示
        if result.success:
            summary = merger.get_cut_summary(
                silence_segments,
                filler_segments,
                keep_segments,
                total_duration_ms,
            )

            console.print("\n[bold green]Export Complete![/bold green]\n")
            console.print(f"[bold]Output:[/bold] {result.output_path}\n")

            table = Table(title="Processing Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Duration", f"{summary['total_duration_ms'] / 1000:.1f}s")
            table.add_row("Silence Segments", str(summary["silence_segments_count"]))
            table.add_row("Filler Segments", str(summary["filler_segments_count"]))
            table.add_row("Keep Segments", str(summary["keep_segments_count"]))
            table.add_row("Time Saved", f"{summary['cut_total_ms'] / 1000:.1f}s")
            table.add_row("Reduction", f"{summary['reduction_percent']:.1f}%")
            table.add_row("Processing Time", f"{processing_time:.1f}s")

            console.print(table)
        else:
            console.print(f"\n[red]Export Failed:[/red] {result.message}")
            raise typer.Exit(1) from None

    finally:
        # 一時ファイルのクリーンアップ（正常終了・エラー・中断時すべてで実行）
        if audio_path is not None:
            if audio_path in _cleanup_files:
                _cleanup_files.remove(audio_path)
            if audio_path.exists() and audio_path.suffix == ".wav":
                try:
                    audio_path.unlink()
                except OSError:
                    pass


@app.command()
def analyze(
    video_path: Path = typer.Argument(..., help="解析対象の動画ファイルパス"),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="出力形式（table または json）",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="結果をファイルに出力",
    ),
    config_path: Path = typer.Option(
        Path("config/settings.yaml"),
        "--config",
        "-c",
        help="設定ファイルパス",
    ),
) -> None:
    """
    動画を解析して無音・フィラー区間を表示する（FCPXML出力なし）
    """
    from jetdr.audio.analyzer import SilenceAnalyzer
    from jetdr.audio.extractor import AudioExtractor
    from jetdr.config.settings import AppConfig
    from jetdr.speech.filler_detector import FillerDetector
    from jetdr.speech.transcriber import Transcriber
    from jetdr.utils.file_utils import validate_input_file

    # 入力ファイル検証
    try:
        video_path = validate_input_file(video_path)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    # 設定読み込み
    config = AppConfig.from_yaml(config_path) if config_path.exists() else AppConfig()

    console.print(f"\n[bold]Analyzing:[/bold] {video_path.name}\n")

    audio_path: Path | None = None

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 音声抽出
            task = progress.add_task("Extracting audio...", total=None)
            extractor = AudioExtractor()
            audio_path = extractor.extract(video_path)
            _cleanup_files.append(audio_path)
            progress.update(task, completed=True)

            # 無音検知
            task = progress.add_task("Detecting silence...", total=None)
            analyzer = SilenceAnalyzer(
                threshold_db=config.silence.threshold_db,
                min_duration_ms=config.silence.min_duration_ms,
            )
            silence_segments = analyzer.detect_silence(audio_path)
            total_duration_ms = analyzer.get_audio_duration_ms(audio_path)
            progress.update(task, completed=True)

            # フィラー検知
            task = progress.add_task("Detecting fillers...", total=None)
            transcriber = Transcriber(
                model_name=config.filler.model_name,
                language=config.filler.language,
            )
            word_timestamps = transcriber.transcribe(audio_path)
            detector = FillerDetector()
            filler_segments = detector.detect(word_timestamps)
            progress.update(task, completed=True)

        # 結果の整形
        if format == "json":
            import json

            result = {
                "video_path": str(video_path),
                "total_duration_ms": total_duration_ms,
                "silence_segments": [s.to_dict() for s in silence_segments],
                "filler_segments": [s.to_dict() for s in filler_segments],
            }
            output_text = json.dumps(result, ensure_ascii=False, indent=2)

            if output:
                output.write_text(output_text, encoding="utf-8")
                console.print(f"[green]Results saved to:[/green] {output}")
            else:
                console.print(output_text)
        else:
            # テーブル表示
            console.print(f"\n[bold]Total Duration:[/bold] {total_duration_ms / 1000:.1f}s\n")

            # 無音区間
            table = Table(title=f"Silence Segments ({len(silence_segments)})")
            table.add_column("#", style="dim")
            table.add_column("Start", style="cyan")
            table.add_column("End", style="cyan")
            table.add_column("Duration", style="green")

            for i, seg in enumerate(silence_segments[:20], 1):
                table.add_row(
                    str(i),
                    f"{seg.start_ms / 1000:.2f}s",
                    f"{seg.end_ms / 1000:.2f}s",
                    f"{seg.duration_ms / 1000:.2f}s",
                )

            if len(silence_segments) > 20:
                table.add_row("...", "...", "...", f"+{len(silence_segments) - 20} more")

            console.print(table)

            # フィラー区間
            table = Table(title=f"Filler Segments ({len(filler_segments)})")
            table.add_column("#", style="dim")
            table.add_column("Word", style="yellow")
            table.add_column("Start", style="cyan")
            table.add_column("End", style="cyan")

            for i, seg in enumerate(filler_segments[:20], 1):
                table.add_row(
                    str(i),
                    seg.metadata.get("word", ""),
                    f"{seg.start_ms / 1000:.2f}s",
                    f"{seg.end_ms / 1000:.2f}s",
                )

            if len(filler_segments) > 20:
                table.add_row("...", "...", "...", f"+{len(filler_segments) - 20} more")

            console.print(table)

    finally:
        # クリーンアップ（正常終了・エラー・中断時すべてで実行）
        if audio_path is not None:
            if audio_path in _cleanup_files:
                _cleanup_files.remove(audio_path)
            if audio_path.exists() and audio_path.suffix == ".wav":
                try:
                    audio_path.unlink()
                except OSError:
                    pass


@app.command()
def validate(
    fcpxml_path: Path = typer.Argument(..., help="検証するFCPXMLファイル"),
) -> None:
    """
    FCPXMLファイルを検証する
    """
    import xml.etree.ElementTree as ET

    if not fcpxml_path.exists():
        console.print(f"[red]Error:[/red] File not found: {fcpxml_path}")
        raise typer.Exit(1) from None

    try:
        tree = ET.parse(fcpxml_path)
        root = tree.getroot()

        if root.tag != "fcpxml":
            console.print("[red]Error:[/red] Not a valid FCPXML file")
            raise typer.Exit(1) from None

        version = root.get("version", "unknown")
        console.print(f"[green]Valid FCPXML[/green] version {version}")

        # Count elements
        resources = root.find("resources")
        assets = resources.findall("asset") if resources is not None else []
        formats = resources.findall("format") if resources is not None else []

        library = root.find("library")
        events = library.findall("event") if library is not None else []

        # Find clips in sequence
        clips = root.findall(".//asset-clip")

        console.print(f"  Formats: {len(formats)}")
        console.print(f"  Assets: {len(assets)}")
        console.print(f"  Events: {len(events)}")
        console.print(f"  Clips: {len(clips)}")

    except ET.ParseError as e:
        console.print(f"[red]XML Parse Error:[/red] {e}")
        raise typer.Exit(1) from None


@app.command()
def check() -> None:
    """
    システム依存関係をチェックする（ヘルスチェック）
    """
    import shutil
    import subprocess

    console.print("\n[bold]System Health Check (jetFCP)[/bold]\n")
    all_ok = True

    # 1. ffmpeg チェック
    console.print("[dim]Checking ffmpeg...[/dim]", end=" ")
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
            console.print(f"[green]OK[/green] ({version_line})")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] ffmpeg found but error: {e}")
            all_ok = False
    else:
        console.print("[red]NOT FOUND[/red]")
        console.print("  Hint: Install ffmpeg (brew install ffmpeg / apt install ffmpeg)")
        all_ok = False

    # 2. Whisper モデル確認
    console.print("[dim]Checking faster-whisper...[/dim]", end=" ")
    try:
        import faster_whisper  # noqa: F401

        console.print("[green]OK[/green]")
    except ImportError:
        console.print("[red]NOT FOUND[/red]")
        console.print("  Hint: pip install faster-whisper")
        all_ok = False

    # 3. Python パッケージ確認
    console.print("[dim]Checking Python packages...[/dim]", end=" ")
    missing_packages = []
    for pkg in ["pydub", "yaml", "pydantic", "typer", "rich", "loguru"]:
        try:
            if pkg == "yaml":
                __import__("yaml")
            else:
                __import__(pkg)
        except ImportError:
            missing_packages.append(pkg)

    if not missing_packages:
        console.print("[green]OK[/green]")
    else:
        console.print(f"[red]Missing:[/red] {', '.join(missing_packages)}")
        all_ok = False

    # 結果サマリー
    console.print()
    if all_ok:
        console.print("[bold green]All checks passed![/bold green]")
    else:
        console.print("[bold yellow]Some checks failed. See above for details.[/bold yellow]")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
