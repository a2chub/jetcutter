"""
settings_controller - 設定管理コントローラ

設定の読み込み、保存、検証を担当。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from jetcutter.config.settings import AppConfig


def get_config_path() -> Path:
    """
    設定ファイルパスを解決

    優先順位:
    1. ./config/settings.yaml (ローカル)
    2. パッケージ内の config/settings.yaml
    3. ~/.jetcutter/settings.yaml (ホーム)
    4. デフォルト: ./config/settings.yaml

    Returns:
        設定ファイルのパス
    """
    # ローカル config
    local_config = Path("config/settings.yaml")
    if local_config.exists():
        return local_config.resolve()

    # パッケージ内
    try:
        import jetcutter
        package_config = Path(jetcutter.__file__).parent.parent / "config" / "settings.yaml"
        if package_config.exists():
            return package_config.resolve()
    except Exception:
        pass

    # ホームディレクトリ
    home_config = Path.home() / ".jetcutter" / "settings.yaml"
    if home_config.exists():
        return home_config.resolve()

    # デフォルト
    return local_config.resolve()


def get_fillers_path() -> Path:
    """
    フィラーワード辞書パスを解決

    Returns:
        フィラー辞書ファイルのパス
    """
    # ローカル config
    local_fillers = Path("config/fillers.yaml")
    if local_fillers.exists():
        return local_fillers.resolve()

    # パッケージ内
    try:
        import jetcutter
        package_fillers = Path(jetcutter.__file__).parent.parent / "config" / "fillers.yaml"
        if package_fillers.exists():
            return package_fillers.resolve()
    except Exception:
        pass

    # デフォルト
    return local_fillers.resolve()


class SettingsController:
    """
    設定の読み込み・保存・検証
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Args:
            config_path: 設定ファイルパス（Noneでデフォルト位置）
        """
        self._config_path = config_path or get_config_path()
        self._fillers_path = get_fillers_path()
        self._config: AppConfig | None = None

    @property
    def config(self) -> AppConfig:
        """現在の設定を返す"""
        if self._config is None:
            self.load()
        return self._config  # type: ignore

    @property
    def config_path(self) -> Path:
        """設定ファイルパスを返す"""
        return self._config_path

    def load(self) -> AppConfig:
        """
        設定を読み込む

        Returns:
            読み込んだ設定
        """
        from jetcutter.config.settings import AppConfig

        try:
            self._config = AppConfig.load_with_fillers(
                config_path=self._config_path,
                fillers_path=self._fillers_path,
            )
            logger.info(f"Loaded config from {self._config_path}")
        except FileNotFoundError:
            logger.warning(f"Config not found at {self._config_path}, using defaults")
            self._config = AppConfig()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = AppConfig()

        return self._config

    def save(self) -> bool:
        """
        現在の設定を保存

        Returns:
            保存成功したかどうか
        """
        if self._config is None:
            logger.warning("No config to save")
            return False

        try:
            # Ensure directory exists
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            self._config.to_yaml(self._config_path)
            logger.info(f"Saved config to {self._config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def reset_to_defaults(self) -> AppConfig:
        """
        デフォルト設定に戻す

        Returns:
            デフォルト設定
        """
        from jetcutter.config.settings import AppConfig

        self._config = AppConfig()

        # Load filler words from file if available
        try:
            if self._fillers_path.exists():
                import yaml
                with open(self._fillers_path, encoding="utf-8") as f:
                    fillers_data = yaml.safe_load(f)
                    if fillers_data and "fillers" in fillers_data:
                        self._config.filler_words = fillers_data["fillers"]
        except Exception as e:
            logger.warning(f"Failed to load fillers: {e}")

        logger.info("Reset to default config")
        return self._config

    def update(self, **kwargs) -> None:
        """
        設定値を更新

        Args:
            **kwargs: 更新する設定値
        """
        if self._config is None:
            self.load()

        # Update silence config
        if "threshold_db" in kwargs:
            self._config.silence.threshold_db = float(kwargs["threshold_db"])
        if "min_duration_ms" in kwargs:
            self._config.silence.min_duration_ms = int(kwargs["min_duration_ms"])

        # Update filler config
        if "model_name" in kwargs:
            self._config.filler.model_name = str(kwargs["model_name"])
        if "language" in kwargs:
            self._config.filler.language = str(kwargs["language"])
        if "device" in kwargs:
            self._config.filler.device = str(kwargs["device"])

        # Update margin config
        if "before_ms" in kwargs:
            self._config.margin.before_ms = int(kwargs["before_ms"])
        if "after_ms" in kwargs:
            self._config.margin.after_ms = int(kwargs["after_ms"])

        # Update output config
        if "default_editor" in kwargs:
            self._config.output.default_editor = str(kwargs["default_editor"])
        if "timeline_prefix" in kwargs:
            self._config.output.timeline_prefix = str(kwargs["timeline_prefix"])

        # Update general config
        if "fps" in kwargs:
            self._config.fps = float(kwargs["fps"])
        if "min_keep_duration_ms" in kwargs:
            self._config.min_keep_duration_ms = int(kwargs["min_keep_duration_ms"])
