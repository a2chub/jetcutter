"""
pytest 共通設定・フィクスチャ

テスト全体で共有するフィクスチャと設定を定義。
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from jetcutter.config.settings import AppConfig
from jetcutter.editor.segment import Segment, SegmentType


# テストデータディレクトリ
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture
def sample_config() -> AppConfig:
    """サンプル設定を返すフィクスチャ"""
    return AppConfig(
        fps=29.97,
        min_keep_duration_ms=500,
        filler_words=["あー", "えー", "えっと"],
    )


@pytest.fixture
def sample_silence_segments() -> list[Segment]:
    """サンプル無音区間リストを返すフィクスチャ"""
    return [
        Segment(start_ms=0, end_ms=1000, type=SegmentType.SILENCE),
        Segment(start_ms=3000, end_ms=4000, type=SegmentType.SILENCE),
        Segment(start_ms=7000, end_ms=8000, type=SegmentType.SILENCE),
    ]


@pytest.fixture
def sample_filler_segments() -> list[Segment]:
    """サンプルフィラー区間リストを返すフィクスチャ"""
    return [
        Segment(
            start_ms=2000,
            end_ms=2300,
            type=SegmentType.FILLER,
            metadata={"word": "えっと"},
        ),
        Segment(
            start_ms=5000,
            end_ms=5500,
            type=SegmentType.FILLER,
            metadata={"word": "あー"},
        ),
    ]


@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """一時ディレクトリを返すフィクスチャ"""
    yield tmp_path


@pytest.fixture
def sample_config_yaml(tmp_path: Path) -> Path:
    """サンプル設定YAMLファイルを作成するフィクスチャ"""
    config_path = tmp_path / "settings.yaml"
    config_content = """
silence:
  threshold_db: -40.0
  min_duration_ms: 300

filler:
  model_name: "tiny"
  language: "ja"

margin:
  before_ms: 100
  after_ms: 100

fps: 29.97
min_keep_duration_ms: 500
"""
    config_path.write_text(config_content, encoding="utf-8")
    return config_path


@pytest.fixture
def sample_fillers_yaml(tmp_path: Path) -> Path:
    """サンプルフィラー辞書YAMLファイルを作成するフィクスチャ"""
    fillers_path = tmp_path / "fillers.yaml"
    fillers_content = """
fillers:
  - あー
  - えー
  - えっと
"""
    fillers_path.write_text(fillers_content, encoding="utf-8")
    return fillers_path


# テストデータディレクトリがなければ作成
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
