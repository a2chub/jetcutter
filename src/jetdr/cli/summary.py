"""
summary - 結果サマリー表示

処理結果のテーブル表示を提供。
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from jetdr.utils.logger import log_processing_stats

console = Console()


def display_summary(
    summary: dict[str, int | float],
    processing_time: float,
    video_path: Path | None = None,
    silence_count: int | None = None,
    filler_count: int | None = None,
    keep_count: int | None = None,
) -> None:
    """
    処理結果のサマリーを表示する

    Args:
        summary: get_cut_summary()からの結果辞書
        processing_time: 処理時間（秒）
        video_path: 動画ファイルパス（ログ記録用）
        silence_count: 無音区間数（ログ記録用、省略時はsummaryから取得）
        filler_count: フィラー区間数（ログ記録用、省略時はsummaryから取得）
        keep_count: 保持区間数（ログ記録用、省略時はsummaryから取得）
    """
    console.print("\n[bold green]Processing Complete![/bold green]\n")

    table = Table(title="Processing Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Duration", f"{summary['total_duration_ms'] / 1000:.1f}s")
    table.add_row("Silence Segments", str(summary['silence_segments_count']))
    table.add_row("Filler Segments", str(summary['filler_segments_count']))
    table.add_row("Keep Segments", str(summary['keep_segments_count']))
    table.add_row("Time Saved", f"{summary['cut_total_ms'] / 1000:.1f}s")
    table.add_row("Reduction", f"{summary['reduction_percent']:.1f}%")
    table.add_row("Processing Time", f"{processing_time:.1f}s")

    console.print(table)

    # ログ記録
    if video_path is not None:
        log_processing_stats(
            video_path,
            int(summary['total_duration_ms']),
            silence_count or int(summary['silence_segments_count']),
            filler_count or int(summary['filler_segments_count']),
            keep_count or int(summary['keep_segments_count']),
            processing_time,
        )


def display_analysis_table(
    total_duration_ms: int,
    silence_segments: list,
    filler_segments: list,
) -> None:
    """
    解析結果をテーブル表示する

    Args:
        total_duration_ms: 音声の総時間（ミリ秒）
        silence_segments: 無音区間リスト
        filler_segments: フィラー区間リスト
    """
    console.print(f"\n[bold]Total Duration:[/bold] {total_duration_ms / 1000:.1f}s\n")

    # 無音区間
    table = Table(title=f"Silence Segments ({len(silence_segments)})")
    table.add_column("#", style="dim")
    table.add_column("Start", style="cyan")
    table.add_column("End", style="cyan")
    table.add_column("Duration", style="green")

    for i, seg in enumerate(silence_segments[:20], 1):  # 最大20件
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
