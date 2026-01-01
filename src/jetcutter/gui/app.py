"""
app - JetCutter GUIアプリケーション メインエントリ

PySimpleGUI4を使用したmacOS GUIアプリケーション。
"""

from __future__ import annotations

import sys
from pathlib import Path


# ffmpegの存在確認
def check_ffmpeg() -> bool:
    """ffmpegがインストールされているか確認"""
    import shutil
    return shutil.which("ffmpeg") is not None


def get_config_path() -> Path:
    """設定ファイルパスを取得"""
    # 1. カレントディレクトリのconfig
    local_config = Path("config/settings.yaml")
    if local_config.exists():
        return local_config

    # 2. パッケージ内のconfig
    package_config = Path(__file__).parent.parent.parent.parent / "config" / "settings.yaml"
    if package_config.exists():
        return package_config

    # 3. ホームディレクトリ
    home_config = Path.home() / ".jetcutter" / "settings.yaml"
    if home_config.exists():
        return home_config

    # デフォルトはローカル
    return local_config


def load_config() -> tuple:
    """設定を読み込み"""
    from jetcutter.config.settings import AppConfig

    config_path = get_config_path()
    fillers_path = config_path.parent / "fillers.yaml"

    if config_path.exists():
        try:
            config = AppConfig.load_with_fillers(config_path, fillers_path)
        except Exception:
            config = AppConfig()
    else:
        config = AppConfig()

    return config, config_path


def main() -> int:
    """GUIアプリケーションのメインエントリ"""
    try:
        import PySimpleGUI4 as sg
    except ImportError:
        print("Error: PySimpleGUI4 is not installed.")
        print("Please install it with: pip install PySimpleGUI4")
        return 1

    # ffmpegチェック
    if not check_ffmpeg():
        sg.popup_error(
            "ffmpegがインストールされていません。\n\n"
            "Homebrewでインストール:\n"
            "  brew install ffmpeg\n\n"
            "または公式サイトからダウンロード:\n"
            "  https://ffmpeg.org/download.html",
            title="ffmpegが見つかりません",
        )
        return 1

    # 設定読み込み
    config, config_path = load_config()

    # ウィンドウ作成
    from jetcutter.gui.handlers import EventHandler
    from jetcutter.gui.window import create_main_window

    window = create_main_window(config)
    handler = EventHandler(window, config, config_path)

    # イベントループ
    try:
        while True:
            event, values = window.read(timeout=100)

            if event == sg.TIMEOUT_KEY:
                continue

            if not handler.handle(event, values):
                break

    except KeyboardInterrupt:
        pass
    finally:
        window.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
