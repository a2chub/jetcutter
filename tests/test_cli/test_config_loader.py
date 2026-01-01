"""Tests for cli.config_loader module."""

from pathlib import Path

import pytest
import typer
import yaml

from jetcutter.cli.config_loader import load_app_config
from jetcutter.config.settings import AppConfig


class TestLoadAppConfig:
    """Tests for load_app_config function."""

    def test_load_default_config_when_path_not_exists(self, tmp_path: Path) -> None:
        """Returns default config when config file doesn't exist."""
        config_path = tmp_path / "nonexistent.yaml"
        config = load_app_config(config_path, silent=True)

        assert isinstance(config, AppConfig)
        assert config.fps == pytest.approx(29.97, rel=0.01)

    def test_load_config_from_yaml(self, tmp_path: Path) -> None:
        """Successfully loads config from YAML file."""
        config_path = tmp_path / "settings.yaml"
        config_data = {
            "fps": 30.0,
            "silence": {"threshold_db": -35.0, "min_duration_ms": 500},
            "margin": {"before_ms": 200, "after_ms": 200},
        }
        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        config = load_app_config(config_path)

        assert config.fps == 30.0
        assert config.silence.threshold_db == -35.0
        assert config.silence.min_duration_ms == 500
        assert config.margin.before_ms == 200

    def test_load_config_with_fillers(self, tmp_path: Path) -> None:
        """Loads config with filler words from separate file."""
        config_path = tmp_path / "settings.yaml"
        fillers_path = tmp_path / "fillers.yaml"

        # Create main config
        config_data = {"fps": 25.0}
        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # Create fillers file
        fillers_data = {"fillers": ["えー", "あの", "その"]}
        with fillers_path.open("w", encoding="utf-8") as f:
            yaml.dump(fillers_data, f)

        config = load_app_config(config_path, fillers_path)

        assert config.fps == 25.0
        assert "えー" in config.filler_words
        assert "あの" in config.filler_words
        assert len(config.filler_words) == 3

    def test_load_config_uses_default_path(self) -> None:
        """Uses default path when config_path is None."""
        # This should not raise, just return defaults if file doesn't exist
        config = load_app_config(None, silent=True)
        assert isinstance(config, AppConfig)

    def test_load_invalid_yaml_raises_exit(self, tmp_path: Path) -> None:
        """Exits when YAML parsing fails."""
        from click.exceptions import Exit

        config_path = tmp_path / "invalid.yaml"
        config_path.write_text("invalid: yaml: content: [", encoding="utf-8")

        with pytest.raises(Exit):
            load_app_config(config_path)
