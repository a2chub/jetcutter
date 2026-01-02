"""
main - JetCutter CLIエントリーポイント

Typerを使用したコマンドラインインターフェース。
"""

from __future__ import annotations

import atexit
import signal
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from jetcutter import __version__

app = typer.Typer(
    name="jetcutter",
    help="動画自動ジェットカット編集ツール - 無音区間・フィラー自動検知・削除",
    add_completion=False,
)

console = Console()

# グローバルなクリーンアップ対象ファイルリスト
_cleanup_files: list[Path] = []
_shutdown_requested = False


def _cleanup_temp_files() -> None:
    """一時ファイルをクリーンアップする"""
    for path in _cleanup_files:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass  # ファイル削除に失敗しても無視
    _cleanup_files.clear()


def _signal_handler(signum: int, frame: object) -> None:
    """シグナルハンドラ: Graceful Shutdownを処理"""
    global _shutdown_requested
    _shutdown_requested = True
    signal_name = signal.Signals(signum).name
    console.print(f"\n[yellow]Received {signal_name}, cleaning up...[/yellow]")
    _cleanup_temp_files()
    raise typer.Exit(130)  # 128 + signal number (SIGINT=2)


# シグナルハンドラを登録
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# プログラム終了時にもクリーンアップ
atexit.register(_cleanup_temp_files)


@contextmanager
def track_temp_file(path: Path) -> Generator[Path, None, None]:
    """一時ファイルをトラッキングし、終了時にクリーンアップする"""
    _cleanup_files.append(path)
    try:
        yield path
    finally:
        if path in _cleanup_files:
            _cleanup_files.remove(path)
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass


def version_callback(value: bool) -> None:
    """バージョン表示"""
    if value:
        console.print(f"JetCutter version {__version__}")
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
    """JetCutter - 動画自動ジェットカット編集ツール"""
    pass


@app.command()
def process(
    video_path: Path = typer.Argument(..., help="処理対象の動画ファイルパス"),
    output_name: str | None = typer.Option(
        None,
        "--output-name",
        "-o",
        help="出力タイムライン名",
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="ターゲットエディタ (davinci, fcp)。未指定時は設定ファイルのdefault_editorを使用",
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="エクスポート処理をスキップ（解析のみ）",
    ),
    output_path: Path | None = typer.Option(
        None,
        "--output-path",
        "-O",
        help="出力ファイルパス（ファイル出力型エクスポーター用）",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="詳細出力を有効化",
    ),
) -> None:
    """
    動画を処理してジェットカット済みタイムラインを生成する
    """
    from jetcutter.audio.analyzer import SilenceDetectionError
    from jetcutter.audio.extractor import AudioExtractionError
    from jetcutter.cli.config_loader import load_app_config
    from jetcutter.cli.processor import process_audio
    from jetcutter.cli.summary import display_summary
    from jetcutter.davinci.connection import DaVinciConnectionError
    from jetcutter.exceptions import ExportError
    from jetcutter.exporters import (
        ExportConfig,
        LiveConnectionExporter,
        create_exporter,
    )
    from jetcutter.speech.transcriber import TranscriptionError
    from jetcutter.utils.file_utils import validate_input_file
    from jetcutter.utils.logger import get_logger, setup_logger

    # ログ設定
    setup_logger(level="DEBUG" if verbose else "INFO")

    # 入力ファイル検証
    try:
        video_path = validate_input_file(video_path)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    # 設定読み込み
    config = load_app_config(config_path, fillers_path)

    # ターゲットエディタの決定（CLIオプション優先、未指定時は設定ファイルのデフォルト）
    effective_target = target if target is not None else config.output.default_editor

    # 出力名の設定
    if output_name is None:
        output_name = f"JetCut_{video_path.stem}"

    console.print(f"\n[bold]Processing:[/bold] {video_path.name}")
    console.print(f"[bold]Target:[/bold] {effective_target}")
    console.print(f"[bold]Output Name:[/bold] {output_name}\n")

    start_time = time.time()
    audio_path: Path | None = None

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 音声処理パイプライン
            result = process_audio(
                video_path=video_path,
                config=config,
                progress=progress,
                cleanup_files=_cleanup_files,
            )
            audio_path = result.audio_path

            # エクスポート（dry-runでなければ）
            if not dry_run:
                task = progress.add_task(f"Exporting to {effective_target}...", total=None)
                try:
                    exporter = create_exporter(effective_target)

                    export_config = ExportConfig(
                        video_path=video_path,
                        output_name=output_name,
                        fps=config.fps,
                        metadata={"output_path": str(output_path)} if output_path else {}
                    )

                    export_result = None

                    if isinstance(exporter, LiveConnectionExporter):
                        with exporter:
                            if exporter.is_connected:
                                export_result = exporter.export(
                                    result.keep_segments, export_config
                                )
                            else:
                                console.print(
                                    f"[red]Error:[/red] Could not connect to {effective_target}"
                                )
                                console.print(
                                    "  Hint: Ensure DaVinci Resolve Studio is running"
                                )
                                console.print(
                                    "  Note: Free version does not support external scripting"
                                )
                                raise typer.Exit(1) from None
                    else:
                        export_result = exporter.export(
                            result.keep_segments, export_config
                        )

                    if export_result:
                        if export_result.success:
                            console.print(
                                f"[green]Export success:[/green] {export_result.message}"
                            )
                            if export_result.output_path:
                                console.print(f"Output file: {export_result.output_path}")
                        else:
                            console.print(
                                f"[red]Export failed:[/red] {export_result.message}"
                            )

                except DaVinciConnectionError as e:
                    console.print(f"[red]Error:[/red] DaVinci connection failed: {e}")
                    console.print(
                        "  Hint: Ensure DaVinci Resolve Studio is running"
                    )
                    raise typer.Exit(1) from None
                except (AudioExtractionError, SilenceDetectionError, TranscriptionError) as e:
                    console.print(f"[red]Error:[/red] Processing failed: {e}")
                    raise typer.Exit(1) from None
                except ExportError as e:
                    console.print(f"[red]Error:[/red] Export failed: {e}")
                    raise typer.Exit(1) from None
                except KeyError:
                    console.print(f"[red]Error:[/red] Unknown exporter target: {effective_target}")
                    console.print("  Available targets: davinci, fcp")
                    raise typer.Exit(1) from None
                except Exception as e:
                    logger = get_logger(__name__)
                    logger.exception(f"Unexpected error during export: {e}")
                    console.print(f"[red]Error:[/red] Unexpected error: {e}")
                    console.print("  Check logs for details")
                    raise typer.Exit(1) from None
                progress.update(task, completed=True)

        # 処理時間
        processing_time = time.time() - start_time

        # 結果表示
        display_summary(
            summary=result.summary,
            processing_time=processing_time,
            video_path=video_path,
            silence_count=len(result.silence_segments),
            filler_count=len(result.filler_segments),
            keep_count=len(result.keep_segments),
        )

    finally:
        # 一時ファイルのクリーンアップ
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
    動画を解析して無音・フィラー区間を表示する
    """
    from jetcutter.audio.analyzer import SilenceAnalyzer
    from jetcutter.audio.extractor import AudioExtractor
    from jetcutter.cli.config_loader import load_app_config
    from jetcutter.cli.summary import display_analysis_table
    from jetcutter.speech.filler_detector import FillerDetector
    from jetcutter.speech.transcriber import Transcriber
    from jetcutter.utils.file_utils import validate_input_file

    # 入力ファイル検証
    try:
        video_path = validate_input_file(video_path)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    # 設定読み込み
    config = load_app_config(config_path)

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
            display_analysis_table(total_duration_ms, silence_segments, filler_segments)

    finally:
        # クリーンアップ
        if audio_path is not None:
            if audio_path in _cleanup_files:
                _cleanup_files.remove(audio_path)
            if audio_path.exists() and audio_path.suffix == ".wav":
                try:
                    audio_path.unlink()
                except OSError:
                    pass


@app.command()
def batch(
    folder_path: Path = typer.Argument(..., help="動画フォルダパス"),
    config_path: Path = typer.Option(
        Path("config/settings.yaml"),
        "--config",
        "-c",
        help="設定ファイルパス",
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="ターゲットエディタ (davinci, fcp)。未指定時は設定ファイルのdefault_editorを使用",
    ),
    pattern: str = typer.Option(
        "*.mp4",
        "--pattern",
        "-p",
        help="ファイルパターン",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="サブフォルダも処理",
    ),
) -> None:
    """
    フォルダ内の全動画を一括処理する
    """
    from jetcutter.utils.file_utils import list_video_files

    if not folder_path.is_dir():
        console.print(f"[red]Error:[/red] Not a directory: {folder_path}")
        raise typer.Exit(1) from None

    videos = list_video_files(folder_path, recursive=recursive)

    if not videos:
        console.print(f"[yellow]No video files found in:[/yellow] {folder_path}")
        raise typer.Exit(0)

    console.print(f"\n[bold]Found {len(videos)} video(s) to process[/bold]\n")

    for i, video in enumerate(videos, 1):
        console.print(f"\n[bold][{i}/{len(videos)}][/bold] Processing: {video.name}")

        try:
            process(
                video_path=video,
                output_name=f"JetCut_{video.stem}",
                target=target,
                config_path=config_path,
                dry_run=False,
                verbose=False,
            )
        except typer.Exit:
            console.print(f"[yellow]Skipping {video.name} due to error[/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]Unexpected error processing {video.name}:[/red] {e}")
            continue

    console.print("\n[bold green]Batch processing complete![/bold green]")


@app.command()
def config(
    action: str = typer.Argument(..., help="アクション（show, init）"),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="出力パス（initの場合）",
    ),
) -> None:
    """
    設定の表示・生成
    """
    from jetcutter.config.settings import AppConfig

    if action == "show":
        config_path = Path("config/settings.yaml")
        if config_path.exists():
            cfg = AppConfig.from_yaml(config_path)
            console.print("\n[bold]Current Configuration:[/bold]\n")
            console.print(cfg.model_dump_json(indent=2))
        else:
            console.print("[yellow]No config file found. Showing defaults:[/yellow]\n")
            cfg = AppConfig()
            console.print(cfg.model_dump_json(indent=2))

    elif action == "init":
        output_path = output or Path("config/settings.yaml")
        cfg = AppConfig()
        cfg.to_yaml(output_path)
        console.print(f"[green]Config file created:[/green] {output_path}")

    else:
        console.print(f"[red]Unknown action:[/red] {action}")
        console.print("Available actions: show, init")
        raise typer.Exit(1) from None


@app.command()
def check() -> None:
    """
    システム依存関係をチェックする（ヘルスチェック）
    """
    import shutil
    import subprocess

    from jetcutter.davinci.connection import DRConnection

    console.print("\n[bold]System Health Check[/bold]\n")
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

    # 2. ffprobe チェック
    console.print("[dim]Checking ffprobe...[/dim]", end=" ")
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        console.print("[green]OK[/green]")
    else:
        console.print("[yellow]Warning:[/yellow] ffprobe not found")

    # 3. DaVinci Resolve チェック
    console.print("[dim]Checking DaVinci Resolve...[/dim]", end=" ")
    try:
        conn = DRConnection()
        if conn.connect():
            version = conn.get_version()
            console.print(f"[green]OK[/green] (version {version})")
            conn.disconnect()
        else:
            console.print("[yellow]Not running[/yellow]")
            console.print("  Hint: Start DaVinci Resolve Studio if you want to export to DR")
    except Exception as e:
        console.print(f"[yellow]Not available:[/yellow] {e}")
        console.print("  Hint: DaVinci Resolve Studio is required for DR export")

    # 4. Whisper モデル確認
    console.print("[dim]Checking faster-whisper...[/dim]", end=" ")
    try:
        import faster_whisper  # noqa: F401

        console.print("[green]OK[/green]")
    except ImportError:
        console.print("[red]NOT FOUND[/red]")
        console.print("  Hint: pip install faster-whisper")
        all_ok = False

    # 5. Python パッケージ確認
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


@app.command()
def gui() -> None:
    """
    GUIアプリを起動する（macOS専用）
    """
    try:
        from jetcutter.gui.app import main as gui_main

        console.print("[dim]Starting JetCutter GUI...[/dim]")
        gui_main()
    except ImportError as e:
        console.print(f"[red]GUI module not available:[/red] {e}")
        console.print("\n[yellow]Hint:[/yellow] GUI requires PySimpleGUI4 package")
        console.print("  Install with: pip install PySimpleGUI4")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Failed to start GUI:[/red] {e}")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
