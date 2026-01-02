# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JetCutter is a Python tool that automatically detects silence and filler words (「あー」「えっと」etc.) in videos and generates jet-cut timelines for DaVinci Resolve and Final Cut Pro.

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
jetcutter gui                         # Launch macOS GUI application
jetcutter process input.mp4           # Process video → DaVinci Resolve
jetcutter analyze input.mp4           # Analyze without export
jetcutter export input.mp4 -o out.fcpxml  # Generate FCPXML
jetcutter validate output.fcpxml     # Validate FCPXML syntax
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
| `src/jetcutter/audio/` | Audio extraction and silence detection |
| `src/jetcutter/speech/` | Whisper transcription and filler matching |
| `src/jetcutter/editor/segment.py` | Core `Segment` dataclass (SILENCE, FILLER, KEEP, CUT types) |
| `src/jetcutter/editor/merger.py` | Segment merging with margin application |
| `src/jetcutter/exporters/` | Abstract base classes and factory pattern for exporters |
| `src/jetcutter/davinci/` | DaVinci Resolve API integration (requires Studio version) |
| `src/jetcutter/fcp/` | FCPXML v1.10 generation for Final Cut Pro |
| `src/jetcutter/gui/` | macOS GUI application with PySimpleGUI4 |
| `src/jetcutter/core/` | Core processing pipeline |

### Exporter Architecture (Plugin Pattern)
- `BaseTimelineExporter` → abstract base
- `FileExporter` → generates output files (FCPExporter)
- `LiveConnectionExporter` → connects to running application (DaVinciExporter)
- `ExporterRegistry` → plugin registration via `_register_exporters()` on import

### Configuration
- `config/settings.yaml` - Detection parameters (threshold_db, min_duration_ms, model_name)
- `config/fillers.yaml` - Filler words dictionary
- Settings managed via Pydantic v2 models in `src/jetcutter/config/settings.py`

## Code Style

- Python 3.10+ with strict type hints (mypy strict mode)
- Line length: 100 characters
- Docstrings use Args/Returns format
- Japanese comments preferred for business logic
- Import order: standard library → third-party → first-party (ruff isort)

## External Dependencies

- **ffmpeg**: Must be installed on system for audio extraction
- **DaVinci Resolve Studio 18+**: Required for `jetcutter process` (free version lacks scripting API)
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

## Best Practices & Lessons Learned

### FCPXML生成

1. **FCPXML 1.10 DTD準拠**
   - `asset`要素には`src`属性を直接設定不可 → `media-rep`子要素を使用
   - `format`要素には`name`属性が必須（例: `FFVideoFormat1080p60`）
   - 分数の分母はフレームデュレーションと一致させる

2. **タイムコード対応**
   - DJI等のカメラは00:00:00:00以外のタイムコードで記録する場合がある
   - ffprobeでタイムコードを取得し、`asset`と`asset-clip`の`start`属性に反映

3. **FPS自動検出**
   - 動画のFPSはffprobeで取得（設定値より優先）
   - 59.94fps等の高フレームレートに対応

### GUI開発

1. **PySimpleGUI4の制約**
   - `write_event_value`を使用してスレッド間通信
   - Tkinterウィジェットの直接操作が必要な場合あり
   - `disabled=True`でRadio/Inputが非表示になるバグあり → 無効化処理を避ける

2. **バックグラウンド処理**
   - 長時間処理は別スレッドで実行
   - `threading.Event`でキャンセル処理を実装

3. **UI設計**
   - 処理中もUI要素を表示維持（バリデーション済みなので操作は無視）
   - 処理時間は結果タブに`MM:SS.SS`形式で表示

## Project Status

**Current Status**: ✅ GUI + FCPXML機能完成

| 機能 | 状態 | テスト |
|------|------|--------|
| 無音検知 | ✅ 完成 | - |
| フィラー検知 | ✅ 完成 | - |
| FCPXML生成 | ✅ 完成 | 43テスト合格 (97%カバレッジ) |
| DaVinci連携 | ✅ 完成 | - |
| macOS GUI | ✅ 完成 | - |

**Latest Updates** (2026-01-02):
- ✅ FCPXML 1.10 DTD準拠修正
- ✅ DJIタイムコード対応
- ✅ 自動FPS検出
- ✅ `jetcutter gui` CLIコマンド追加
- ✅ GUI: 出力モード表記変更（FCPX/DR）
- ✅ GUI: 処理中のUI消失バグ修正
- ✅ GUI: 処理時間表示機能追加
