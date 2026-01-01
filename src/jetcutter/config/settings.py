"""
settings - 設定管理モジュール

Pydanticを使用したアプリケーション設定の管理。
YAML設定ファイルの読み込み・書き出しに対応。

環境変数による設定上書きをサポート:
    JETCUTTER_DEFAULT_EDITOR: デフォルトターゲットエディタ (davinci, fcp)
    JETCUTTER_DEVICE: デバイス設定 (auto, cuda, cpu)
    JETCUTTER_COMPUTE_TYPE: 計算精度 (auto, float16, int8)
    JETCUTTER_MODEL_NAME: Whisperモデル名
    JETCUTTER_LANGUAGE: 認識言語コード
    JETCUTTER_THRESHOLD_DB: 無音判定しきい値
    JETCUTTER_FPS: フレームレート
    JETCUTTER_LOG_LEVEL: ログレベル (DEBUG, INFO, WARNING, ERROR)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


def _get_env_str(key: str, default: str) -> str:
    """環境変数から文字列を取得"""
    return os.environ.get(key, default)


def _get_env_float(key: str, default: float) -> float:
    """環境変数から浮動小数点数を取得"""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _get_env_int(key: str, default: int) -> int:
    """環境変数から整数を取得"""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


class SilenceDetectionConfig(BaseModel):
    """無音検知設定"""

    threshold_db: float = Field(
        default_factory=lambda: _get_env_float("JETCUTTER_THRESHOLD_DB", -40.0),
        description="無音判定しきい値（dBFS）",
        ge=-100.0,
        le=0.0,
    )
    min_duration_ms: int = Field(
        default=300,
        description="最小無音期間（ミリ秒）",
        ge=0,
    )


class FillerDetectionConfig(BaseModel):
    """フィラー検知設定"""

    model_name: str = Field(
        default_factory=lambda: _get_env_str("JETCUTTER_MODEL_NAME", "large-v3"),
        description="Whisperモデル名（tiny, base, small, medium, large-v3等）",
    )
    language: str = Field(
        default_factory=lambda: _get_env_str("JETCUTTER_LANGUAGE", "ja"),
        description="認識対象言語コード",
    )
    device: str = Field(
        default_factory=lambda: _get_env_str("JETCUTTER_DEVICE", "auto"),
        description="使用デバイス（auto, cuda, cpu）",
    )
    compute_type: str = Field(
        default_factory=lambda: _get_env_str("JETCUTTER_COMPUTE_TYPE", "int8"),
        description="計算精度（auto, float16, int8等）",
    )


class MarginConfig(BaseModel):
    """カットマージン設定"""

    before_ms: int = Field(
        default=100,
        description="保持区間開始前のバッファ（ミリ秒）",
        ge=0,
    )
    after_ms: int = Field(
        default=100,
        description="保持区間終了後のバッファ（ミリ秒）",
        ge=0,
    )


class OutputConfig(BaseModel):
    """出力設定"""

    default_editor: str = Field(
        default_factory=lambda: _get_env_str("JETCUTTER_DEFAULT_EDITOR", "fcp"),
        description="デフォルトのターゲットエディタ (davinci, fcp)",
    )
    timeline_prefix: str = Field(
        default="JetCut_",
        description="タイムライン名のプレフィックス",
    )
    create_backup: bool = Field(
        default=True,
        description="処理前にバックアップを作成するか",
    )
    default_width: int = Field(
        default=1920,
        description="デフォルト出力幅（ピクセル）",
        gt=0,
    )
    default_height: int = Field(
        default=1080,
        description="デフォルト出力高さ（ピクセル）",
        gt=0,
    )


class AppConfig(BaseModel):
    """アプリケーション全体設定"""

    silence: SilenceDetectionConfig = Field(default_factory=SilenceDetectionConfig)
    filler: FillerDetectionConfig = Field(default_factory=FillerDetectionConfig)
    margin: MarginConfig = Field(default_factory=MarginConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    fps: float = Field(
        default_factory=lambda: _get_env_float("JETCUTTER_FPS", 29.97),
        description="デフォルトフレームレート",
        gt=0.0,
    )
    min_keep_duration_ms: int = Field(
        default=500,
        description="最小保持区間長（ミリ秒）",
        ge=0,
    )
    filler_words: list[str] = Field(
        default_factory=list,
        description="フィラー単語リスト",
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> AppConfig:
        """
        YAMLファイルから設定を読み込む

        Args:
            path: 設定ファイルのパス

        Returns:
            AppConfigインスタンス

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            yaml.YAMLError: YAML解析エラー
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.model_validate(data)

    def to_yaml(self, path: str | Path) -> None:
        """
        設定をYAMLファイルに書き出す

        Args:
            path: 出力ファイルのパス
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.model_dump()
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return self.model_dump()

    @classmethod
    def load_with_fillers(
        cls,
        config_path: str | Path,
        fillers_path: str | Path | None = None,
    ) -> AppConfig:
        """
        設定ファイルとフィラー辞書を読み込む

        Args:
            config_path: 設定ファイルのパス
            fillers_path: フィラー辞書ファイルのパス（省略時は設定ファイルと同じディレクトリのfillers.yaml）

        Returns:
            フィラー単語リストを含むAppConfigインスタンス
        """
        config = cls.from_yaml(config_path)

        if fillers_path is None:
            fillers_path = Path(config_path).parent / "fillers.yaml"

        if Path(fillers_path).exists():
            with Path(fillers_path).open("r", encoding="utf-8") as f:
                fillers_data = yaml.safe_load(f) or {}
                config.filler_words = fillers_data.get("fillers", [])

        return config


def load_filler_words(path: str | Path) -> list[str]:
    """
    フィラー辞書ファイルを読み込む

    Args:
        path: フィラー辞書ファイルのパス

    Returns:
        フィラー単語のリスト
    """
    path = Path(path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data.get("fillers", [])


# デフォルト設定のシングルトン
_default_config: AppConfig | None = None


def get_default_config() -> AppConfig:
    """デフォルト設定を取得"""
    global _default_config
    if _default_config is None:
        _default_config = AppConfig()
    return _default_config


def set_default_config(config: AppConfig) -> None:
    """デフォルト設定を設定"""
    global _default_config
    _default_config = config
