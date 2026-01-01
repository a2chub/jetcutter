# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

jetDR is a Python tool that automatically detects silence and filler words (「あー」「えっと」etc.) in videos and generates jet-cut timelines for DaVinci Resolve and Final Cut Pro.

## Development Commands

```bash
# Install with dev dependencies (uses uv package manager)
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run all tests with coverage
pytest

# Run a single test file
pytest tests/test_fcp/test_time_utils.py -v

# Run specific test
pytest tests/test_segment.py::test_segment_overlap -v

# Linting
ruff check src/

# Type checking
mypy src/

# Format check
ruff format src/ --check

# CLI commands
jetdr process input.mp4           # Process video → DaVinci Resolve
jetdr analyze input.mp4           # Analyze without export
jetfcp export input.mp4 -o out.fcpxml  # Generate FCPXML
jetfcp validate output.fcpxml     # Validate FCPXML syntax
```

## Architecture

### Processing Pipeline
```
Video → Audio Extraction (ffmpeg) → Silence Detection (pydub)
→ Filler Detection (faster-whisper) → Segment Merging → Export
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/jetdr/audio/` | Audio extraction and silence detection |
| `src/jetdr/speech/` | Whisper transcription and filler matching |
| `src/jetdr/editor/segment.py` | Core `Segment` dataclass (SILENCE, FILLER, KEEP, CUT types) |
| `src/jetdr/editor/merger.py` | Segment merging with margin application |
| `src/jetdr/exporters/` | Abstract base classes and factory pattern for exporters |
| `src/jetdr/davinci/` | DaVinci Resolve API integration (requires Studio version) |
| `src/jetdr/fcp/` | FCPXML v1.10 generation for Final Cut Pro |
| `src/jetfcp/` | Separate CLI for FCP-only workflow |

### Exporter Architecture (Plugin Pattern)
- `BaseTimelineExporter` → abstract base
- `FileExporter` → generates output files (FCPExporter)
- `LiveConnectionExporter` → connects to running application (DaVinciExporter)
- `ExporterRegistry` → plugin registration via `_register_exporters()` on import

### Configuration
- `config/settings.yaml` - Detection parameters (threshold_db, min_duration_ms, model_name)
- `config/fillers.yaml` - Filler words dictionary
- Settings managed via Pydantic v2 models in `src/jetdr/config/settings.py`

## Code Style

- Python 3.10+ with strict type hints (mypy strict mode)
- Line length: 100 characters
- Docstrings use Args/Returns format
- Japanese comments preferred for business logic
- Import order: standard library → third-party → first-party (ruff isort)

## External Dependencies

- **ffmpeg**: Must be installed on system for audio extraction
- **DaVinci Resolve Studio 18+**: Required for `jetdr process` (free version lacks scripting API)
- **faster-whisper**: Runs on CUDA if available, falls back to CPU

## Documentation

Core docs in `docs/davinci_resolve_auto_editor/`:
- `requirements.md` - System requirements
- `architecture.md` - Module relationships and design
- `api_reference.md` - Public API documentation
- `task.md` - Development task tracking

## Git Workflow

### ブランチ戦略
- **dev**: デフォルトブランチ（開発の統合先）
- **feature-xxx**: 機能追加用ブランチ

### 開発フロー
1. `dev`ブランチから`feature-xxx`ブランチを切り出す
2. 機能開発を行う
3. 完成後、`dev`ブランチにマージして戻す

### ブランチ命名規則
- 機能追加: `feature-<機能名>` (例: `feature-batch-export`)
- バグ修正: `fix-<issue番号または概要>` (例: `fix-silence-detection`)
- リファクタリング: `refactor-<対象>` (例: `refactor-cli-module`)

### コミットメッセージ
コンベンショナルコミット形式を使用:
- `feat:` - 新機能
- `fix:` - バグ修正
- `docs:` - ドキュメント
- `test:` - テスト
- `refactor:` - リファクタリング
- `chore:` - その他
