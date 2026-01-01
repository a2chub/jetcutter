"""
config_loader - 設定読み込みユーティリティ

CLIコマンド間で共通の設定読み込みロジックを提供。
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from jetdr.config.settings import AppConfig

console = Console()


def load_app_config(
    config_path: Path | None = None,
    fillers_path: Path | None = None,
    silent: bool = False,
) -> AppConfig:
    """
    設定ファイルを読み込み、なければデフォルトを返す

    Args:
        config_path: 設定ファイルパス（省略時はデフォルトパス）
        fillers_path: フィラー辞書ファイルパス
        silent: 警告メッセージを抑制するか

    Returns:
        AppConfigインスタンス

    Raises:
        SystemExit: 設定ファイルの読み込みに失敗した場合
    """
    if config_path is None:
        config_path = Path("config/settings.yaml")

    try:
        if config_path.exists():
            return AppConfig.load_with_fillers(config_path, fillers_path)
        else:
            if not silent:
                console.print(
                    f"[yellow]Warning:[/yellow] Config not found: {config_path}, using defaults"
                )
            return AppConfig()
    except Exception as e:
        console.print(f"[red]Error loading config:[/red] {e}")
        import typer

        raise typer.Exit(1) from None
