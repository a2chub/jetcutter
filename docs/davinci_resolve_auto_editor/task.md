# タスクリスト：DaVinci Resolve 自動編集エージェント

## 概要

このドキュメントは、jetDRプロジェクトの開発タスクを追跡するためのチェックリストです。

**最終更新**: 2025-12-31

---

## Phase 1: プロジェクト基盤構築

### 1.1 プロジェクト初期化
- [x] `pyproject.toml`の作成
- [x] 依存ライブラリの定義
- [x] 開発ツール設定（ruff, pytest, mypy）
- [x] `.gitignore`の作成
- [x] `README.md`の作成

### 1.2 パッケージ構造
- [x] `src/jetdr/`ディレクトリ構造の作成
- [x] `src/jetdr/__init__.py`の作成
- [x] `src/jetdr/main.py`（CLIエントリーポイント）の作成

### 1.3 設定管理
- [x] `src/jetdr/config/settings.py`の実装
- [x] `config/settings.yaml`の作成
- [x] `config/fillers.yaml`の作成
- [x] 設定バリデーションの実装

### 1.4 ユーティリティ
- [x] `src/jetdr/utils/logger.py`の実装
- [x] `src/jetdr/utils/time_utils.py`の実装
- [x] `src/jetdr/utils/file_utils.py`の実装

### 1.5 テスト基盤
- [x] `tests/conftest.py`の作成
- [x] テスト用フィクスチャの定義
- [ ] CIパイプラインの設定（オプション）

---

## Phase 2: 音声解析エンジン

### 2.1 音声抽出
- [x] `src/jetdr/audio/__init__.py`の作成
- [x] `src/jetdr/audio/extractor.py`の実装
  - [x] `AudioExtractor`クラスの実装
  - [x] ffmpeg-pythonを使用した音声抽出
  - [x] サンプルレート設定
  - [x] 一時ファイル管理
- [ ] 音声抽出のユニットテスト

### 2.2 無音検知
- [x] `src/jetdr/audio/analyzer.py`の実装
  - [x] `SilenceAnalyzer`クラスの実装
  - [x] pydubを使用した音量解析
  - [x] しきい値ベースの無音検出
  - [x] 最小無音期間フィルタリング
- [ ] 無音検知のユニットテスト

### 2.3 音声認識
- [x] `src/jetdr/speech/__init__.py`の作成
- [x] `src/jetdr/speech/transcriber.py`の実装
  - [x] `Transcriber`クラスの実装
  - [x] faster-whisperモデルのロード
  - [x] 単語レベルタイムスタンプの取得
  - [x] GPU/CPU自動選択
- [ ] 音声認識のユニットテスト

### 2.4 フィラー検知
- [x] `src/jetdr/speech/filler_detector.py`の実装
  - [x] `FillerDetector`クラスの実装
  - [x] フィラー辞書のロード
  - [x] 単語マッチング
- [ ] フィラー検知のユニットテスト

---

## Phase 3: カットロジック実装

### 3.1 データモデル
- [x] `src/jetdr/editor/__init__.py`の作成
- [x] `src/jetdr/editor/segment.py`の実装
  - [x] `SegmentType`列挙型の定義
  - [x] `Segment`データクラスの実装
  - [x] 区間操作メソッド（overlaps, merge等）

### 3.2 区間マージロジック
- [x] `src/jetdr/editor/merger.py`の実装
  - [x] `SegmentMerger`クラスの実装
  - [x] 重複区間のマージアルゴリズム
  - [x] 補集合（保持区間）算出アルゴリズム
  - [x] マージン適用ロジック
  - [x] フレーム境界アラインメント
- [x] マージロジックのユニットテスト
- [x] エッジケースのテスト（空リスト、全区間無音等）

### 3.3 タイムライン生成
- [x] タイムラインデータ機能（`TimelineBuilder`に統合済み）
  - [x] タイムライン情報取得機能
  - [x] JSON出力機能（`Segment.to_dict`経由）
- [x] タイムラインデータのユニットテスト

---

## Phase 4: DaVinci Resolve連携

### 4.1 接続管理
- [x] `src/jetdr/davinci/__init__.py`の作成
- [x] `src/jetdr/davinci/connection.py`の実装
  - [x] `DRConnection`クラスの実装
  - [x] Scripting API接続
  - [x] 接続状態管理
  - [x] エラーハンドリング

### 4.2 プロジェクト操作
- [x] `src/jetdr/davinci/project.py`の実装
  - [x] `DRProject`クラスの実装
  - [x] プロジェクト作成/取得
  - [x] プロジェクト設定管理

### 4.3 メディアプール操作
- [x] `src/jetdr/davinci/media_pool.py`の実装
  - [x] `DRMediaPool`クラスの実装
  - [x] メディアインポート
  - [x] ビン管理

### 4.4 タイムライン構築
- [x] `src/jetdr/davinci/timeline_builder.py`の実装
  - [x] `TimelineBuilder`クラスの実装
  - [x] タイムライン作成
  - [x] クリップ配置
  - [x] In/Outポイント設定
- [ ] DR連携の統合テスト（要DaVinci Resolve実機）

---

## Phase 5: 統合・最適化

### 5.1 CLI実装
- [x] `process`コマンドの完全実装
- [x] `analyze`コマンドの完全実装
- [x] `batch`コマンドの完全実装
- [x] 進捗表示（rich使用）
- [x] エラーメッセージの改善

### 5.2 統合テスト
- [ ] エンドツーエンドテストの作成
- [ ] 実際の動画ファイルを使用したテスト
- [ ] DaVinci Resolveとの統合テスト

### 5.3 パフォーマンス最適化
- [ ] GPU使用時の最適化確認
- [ ] 大容量ファイル処理の検証
- [ ] メモリ使用量の最適化

### 5.4 ドキュメント
- [x] APIリファレンスの作成（既存ドキュメント）
- [ ] ユーザーガイドの作成
- [ ] インストール手順の作成
- [ ] トラブルシューティングガイドの作成

---

## Phase 6: Final Cut Pro 対応

### 6.1 抽象エクスポーター基盤
- [x] `src/jetdr/exporters/__init__.py`の作成
- [x] `src/jetdr/exporters/base.py`の実装
  - [x] `BaseTimelineExporter`抽象クラス
  - [x] `FileExporter`抽象クラス（FCPXML等）
  - [x] `LiveConnectionExporter`抽象クラス（DaVinci等）
  - [x] `ExportConfig`データクラス
  - [x] `ExportResult`データクラス
- [x] `src/jetdr/exporters/factory.py`の実装
  - [x] `ExporterRegistry`クラス
  - [x] `create_exporter`ファクトリー関数

### 6.2 FCPモジュール
- [x] `src/jetdr/fcp/__init__.py`の作成
- [x] `src/jetdr/fcp/time_utils.py`の実装
  - [x] `FCPTime`データクラス（Fraction使用）
  - [x] フレーム精度の時間計算
  - [x] 標準フレームレート対応（23.976, 24, 25, 29.97, 30, 50, 59.94, 60 fps）
- [x] `src/jetdr/fcp/fcpxml_builder.py`の実装
  - [x] `FCPXMLBuilder`クラス
  - [x] FCPXML v1.10準拠のXML生成
  - [x] `validate_fcpxml`検証関数
- [x] `src/jetdr/fcp/exporter.py`の実装
  - [x] `FCPExporter`クラス（FileExporter継承）
  - [x] `create_fcp_exporter`ファクトリー関数

### 6.3 DaVinciエクスポーター
- [x] `src/jetdr/davinci/exporter.py`の実装
  - [x] `DaVinciExporter`クラス（LiveConnectionExporter継承）
  - [x] TimelineBuilderのラッパー実装

### 6.4 jetfcp CLI
- [x] `src/jetfcp/__init__.py`の作成
- [x] `src/jetfcp/main.py`の実装
  - [x] `export`コマンド
  - [x] `analyze`コマンド
  - [x] `validate`コマンド
- [x] `pyproject.toml`のエントリーポイント追加

### 6.5 ドキュメント
- [x] `docs/davinci_resolve_auto_editor/fcp_integration.md`の作成
- [x] FCP連携ガイドの作成

---

## 追加タスク（将来的な拡張）

### Agentic機能
- [ ] LLM連携インターフェースの設計
- [ ] 編集指示の自然言語解釈
- [ ] 自動テロップ生成機能

### 品質向上
- [ ] より高精度なフィラー検出
- [ ] 複数話者対応
- [ ] ノイズ除去機能

---

## 進捗サマリー

| フェーズ | 完了タスク | 総タスク | 進捗率 |
|----------|-----------|----------|--------|
| Phase 1  | 14        | 15       | 93%    |
| Phase 2  | 14        | 18       | 78%    |
| Phase 3  | 10        | 10       | 100%   |
| Phase 4  | 11        | 12       | 92%    |
| Phase 5  | 5         | 12       | 42%    |
| Phase 6  | 18        | 18       | 100%   |
| **合計** | **72**    | **85**   | **85%** |

### テストカバレッジ

| モジュール | カバレッジ | テスト数 |
|------------|-----------|---------|
| fcp/time_utils | 97% | 24 |
| fcp/exporter | 92% | 19 |
| fcp/fcpxml_builder | 91% | - |
| exporters/ | 76-90% | - |
| editor/segment | - | 20 |
| **合計** | **38%** | **63** |

---

## 実装済みファイル一覧

```
src/jetdr/
├── __init__.py              ✅
├── main.py                  ✅ (CLI: process, analyze, batch, config)
├── audio/
│   ├── __init__.py          ✅
│   ├── extractor.py         ✅ (AudioExtractor)
│   └── analyzer.py          ✅ (SilenceAnalyzer)
├── speech/
│   ├── __init__.py          ✅
│   ├── transcriber.py       ✅ (Transcriber, WordTimestamp)
│   └── filler_detector.py   ✅ (FillerDetector)
├── editor/
│   ├── __init__.py          ✅
│   ├── segment.py           ✅ (Segment, SegmentType)
│   └── merger.py            ✅ (SegmentMerger, quick_merge)
├── davinci/
│   ├── __init__.py          ✅
│   ├── connection.py        ✅ (DRConnection)
│   ├── project.py           ✅ (DRProject)
│   ├── media_pool.py        ✅ (DRMediaPool)
│   ├── timeline_builder.py  ✅ (TimelineBuilder)
│   └── exporter.py          ✅ (DaVinciExporter) [NEW]
├── exporters/               [NEW]
│   ├── __init__.py          ✅ (エクスポーター自動登録)
│   ├── base.py              ✅ (BaseTimelineExporter, FileExporter, etc.)
│   └── factory.py           ✅ (ExporterRegistry, create_exporter)
├── fcp/                     [NEW]
│   ├── __init__.py          ✅ (FCPモジュール公開API)
│   ├── time_utils.py        ✅ (FCPTime, Fraction時間計算)
│   ├── fcpxml_builder.py    ✅ (FCPXMLBuilder, FCPXML v1.10生成)
│   └── exporter.py          ✅ (FCPExporter)
├── config/
│   ├── __init__.py          ✅
│   └── settings.py          ✅ (AppConfig, SilenceDetectionConfig, etc.)
└── utils/
    ├── __init__.py          ✅
    ├── logger.py            ✅ (setup_logger, get_logger)
    ├── time_utils.py        ✅ (ms_to_frames, frames_to_ms, etc.)
    └── file_utils.py        ✅ (validate_input_file, list_video_files, etc.)

src/jetfcp/                  [NEW]
├── __init__.py              ✅
└── main.py                  ✅ (CLI: export, analyze, validate)

config/
├── settings.yaml            ✅
└── fillers.yaml             ✅

docs/
└── davinci_resolve_auto_editor/
    ├── task.md              ✅
    └── fcp_integration.md   ✅ [NEW]

tests/
├── __init__.py              ✅
├── conftest.py              ✅
├── test_segment.py          ✅ (20 tests passing)
└── test_fcp/                [NEW]
    ├── __init__.py          ✅
    ├── test_time_utils.py   ✅ (24 tests - FCPTime, frame duration)
    └── test_exporter.py     ✅ (19 tests - FCPExporter, registry)
```

---

## 残タスク優先度

### 高優先度
1. DaVinci Resolve実機での統合テスト
2. 実際の動画ファイルでのE2Eテスト

### 中優先度
3. 各モジュールのユニットテスト追加
4. README.mdの作成
5. インストール手順の作成

### 低優先度
6. CIパイプライン設定
7. パフォーマンス最適化
8. ユーザーガイド・トラブルシューティングガイド
