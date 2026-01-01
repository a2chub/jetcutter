# DaVinci Resolve Exporter

## 概要

`DaVinciExporter` は、DaVinci Resolve Scripting APIを使用して、ジェットカット済みタイムラインを直接DaVinci Resolveに作成するエクスポーターです。

## 特徴

- **ライブ接続**: DaVinci Resolveアプリケーションと直接通信
- **自動タイムライン構築**: 保持区間（KEEP segments）から自動的にタイムラインを作成
- **エラーハンドリング**: 包括的なバリデーションとエラー報告
- **コンテキストマネージャー対応**: `with`文による自動接続管理

## 必要要件

### システム要件

- **DaVinci Resolve Studio** (有料版) - Scripting APIは無料版では利用不可
- 対応OS: macOS, Windows, Linux
- Python 3.10以上

### インストール

```bash
# jetDRパッケージのインストール
pip install -e .
```

## アーキテクチャ

### クラス構造

```
DaVinciExporter (LiveConnectionExporter)
├── _connection: DRConnection
├── _project: DRProject
├── _media_pool: DRMediaPool
└── _builder: TimelineBuilder
```

### 継承関係

```
BaseTimelineExporter (ABC)
└── LiveConnectionExporter (ABC)
    └── DaVinciExporter
```

## API リファレンス

### プロパティ

#### `name` (str)
エクスポーターの名前を返します。

```python
exporter = DaVinciExporter()
print(exporter.name)  # "DaVinci Resolve"
```

#### `file_extension` (str)
ファイル拡張子（ライブ接続のため空文字）。

```python
print(exporter.file_extension)  # ""
```

#### `is_connected` (bool)
DaVinci Resolveへの接続状態を返します。

```python
if exporter.is_connected:
    print("Connected to DaVinci Resolve")
```

### メソッド

#### `connect() -> bool`
DaVinci Resolveへの接続を確立します。

**戻り値**: 接続に成功した場合`True`、失敗した場合`False`

**前提条件**:
- DaVinci Resolve Studioが起動している
- プロジェクトが開かれている
- Scripting APIが有効

```python
exporter = DaVinciExporter()
if exporter.connect():
    print("Connected successfully")
else:
    print("Connection failed")
```

#### `disconnect() -> None`
DaVinci Resolveとの接続を切断します。

```python
exporter.disconnect()
```

#### `validate_config(config: ExportConfig) -> list[str]`
エクスポート設定を検証します。

**引数**:
- `config`: エクスポート設定

**戻り値**: 検証エラーのリスト（空の場合は問題なし）

```python
errors = exporter.validate_config(config)
if errors:
    for error in errors:
        print(f"Error: {error}")
```

#### `export(segments: list[Segment], config: ExportConfig) -> ExportResult`
セグメントをDaVinci Resolveタイムラインとしてエクスポートします。

**引数**:
- `segments`: エクスポートするセグメントのリスト
- `config`: エクスポート設定

**戻り値**: `ExportResult`オブジェクト

**動作**:
1. 設定を検証
2. 接続を確認（未接続の場合は自動接続）
3. KEEPタイプのセグメントのみを抽出
4. タイムラインを作成
5. 各セグメントをクリップとして配置

```python
result = exporter.export(segments, config)
if result.success:
    print(f"Success: {result.message}")
    print(f"Exported {result.details['segments_exported']} segments")
else:
    print(f"Failed: {result.message}")
```

#### `get_project_info() -> dict | None`
現在のプロジェクト情報を取得します。

**戻り値**: プロジェクト情報の辞書、または`None`（未接続時）

```python
info = exporter.get_project_info()
if info:
    print(f"Project: {info['name']}")
    print(f"FPS: {info['frame_rate']}")
    print(f"Resolution: {info['resolution']}")
```

#### `list_timelines() -> list[str]`
プロジェクト内の全タイムライン名を取得します。

**戻り値**: タイムライン名のリスト

```python
timelines = exporter.list_timelines()
for name in timelines:
    print(f"Timeline: {name}")
```

## 使用例

### 基本的な使い方

```python
from pathlib import Path
from jetdr.davinci.exporter import DaVinciExporter
from jetdr.editor.segment import Segment, SegmentType
from jetdr.exporters.base import ExportConfig

# エクスポーターインスタンスを作成
exporter = DaVinciExporter()

# 接続
if not exporter.connect():
    print("Failed to connect")
    exit(1)

try:
    # セグメントを定義
    segments = [
        Segment(start_ms=0, end_ms=5000, type=SegmentType.KEEP),
        Segment(start_ms=5000, end_ms=8000, type=SegmentType.SILENCE),
        Segment(start_ms=8000, end_ms=15000, type=SegmentType.KEEP),
    ]

    # 設定を作成
    config = ExportConfig(
        video_path=Path("video.mp4"),
        output_name="JetCut_Timeline",
        fps=29.97,
    )

    # エクスポート
    result = exporter.export(segments, config)
    print(result.message)

finally:
    # 切断
    exporter.disconnect()
```

### コンテキストマネージャーを使用

```python
with DaVinciExporter() as exporter:
    if not exporter.is_connected:
        print("Connection failed")
        return

    result = exporter.export(segments, config)
    print(result.message)
```

### ファクトリーパターンを使用

```python
from jetdr.exporters import create_exporter

# ファクトリーでエクスポーターを作成
exporter = create_exporter("davinci")

# 通常通り使用
if exporter.connect():
    result = exporter.export(segments, config)
    exporter.disconnect()
```

## エラーハンドリング

### 接続エラー

```python
from jetdr.davinci.connection import DaVinciConnectionError

try:
    exporter.connect()
except DaVinciConnectionError as e:
    print(f"Connection error: {e}")
```

### タイムライン作成エラー

```python
from jetdr.davinci.timeline_builder import TimelineCreationError

try:
    result = exporter.export(segments, config)
except TimelineCreationError as e:
    print(f"Timeline creation failed: {e}")
```

### 設定検証

```python
# エクスポート前に検証
errors = exporter.validate_config(config)
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
    # エラー処理
else:
    # エクスポート実行
    result = exporter.export(segments, config)
```

## ExportResult の詳細

### 成功時

```python
ExportResult(
    success=True,
    output_path=None,  # ライブ接続のためファイル出力なし
    message="Timeline 'JetCut_Timeline' created successfully in DaVinci Resolve",
    details={
        "timeline_name": "JetCut_Timeline",
        "timeline_info": {
            "name": "JetCut_Timeline",
            "start_frame": 0,
            "end_frame": 598,
            "track_count": {"video": 1, "audio": 1}
        },
        "segments_count": 3,
        "fps": 29.97,
        "project_name": "MyProject"
    }
)
```

### 失敗時

```python
ExportResult(
    success=False,
    message="Video file not found: /path/to/video.mp4",
    details={
        "errors": ["Video file not found: /path/to/video.mp4"]
    }
)
```

## 内部実装

### セグメントフィルタリング

エクスポート時、`SegmentType.KEEP`のセグメントのみがタイムラインに含まれます。

```python
# 内部処理
from jetdr.editor.segment import SegmentType
keep_segments = [seg for seg in segments if seg.type == SegmentType.KEEP]
```

### タイムライン構築フロー

1. **接続確認**: `is_connected`をチェック
2. **メディアインポート**: `DRMediaPool.import_media_single()`
3. **タイムライン作成**: `TimelineBuilder.create_timeline()`
4. **クリップ配置**: 各セグメントに対して`add_clip_with_in_out()`
5. **情報取得**: `get_timeline_info()`で結果を収集

## トラブルシューティング

### "Failed to connect to DaVinci Resolve"

**原因**:
- DaVinci Resolveが起動していない
- DaVinci Resolve Studio（有料版）ではない
- プロジェクトが開かれていない

**解決方法**:
1. DaVinci Resolve Studioを起動
2. プロジェクトを開く
3. 再度接続を試行

### "Scripting API not found"

**原因**:
- DaVinci Resolveが正しくインストールされていない
- Scripting APIモジュールが見つからない

**解決方法**:
- DaVinci Resolveを再インストール
- パスを確認:
  - macOS: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules`
  - Windows: `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules`
  - Linux: `/opt/resolve/Developer/Scripting/Modules`

### "No project is currently open"

**原因**:
- DaVinci Resolveでプロジェクトが開かれていない

**解決方法**:
- DaVinci Resolveで既存プロジェクトを開くか、新規作成

## ベストプラクティス

### 1. コンテキストマネージャーの使用

```python
# 推奨
with DaVinciExporter() as exporter:
    # 処理
    pass

# 非推奨（手動管理）
exporter = DaVinciExporter()
exporter.connect()
# 処理
exporter.disconnect()  # 忘れる可能性
```

### 2. 事前検証

```python
# エクスポート前に設定を検証
errors = exporter.validate_config(config)
if errors:
    # エラー処理
    return

result = exporter.export(segments, config)
```

### 3. エラーハンドリング

```python
try:
    result = exporter.export(segments, config)
    if result.success:
        # 成功処理
        pass
    else:
        # 失敗処理
        logger.error(result.message)
except Exception as e:
    # 例外処理
    logger.exception("Unexpected error")
```

### 4. ログの活用

```python
from jetdr.utils.logger import get_logger

logger = get_logger(__name__)

# エクスポーター内部で自動的にログ出力
exporter.export(segments, config)
# INFO: Creating timeline 'MyTimeline' from 3 segments
# INFO: Successfully created timeline: MyTimeline
```

## 関連クラス

- [`DRConnection`](./src/jetdr/davinci/connection.py): DaVinci Resolve接続管理
- [`DRProject`](./src/jetdr/davinci/project.py): プロジェクト操作
- [`DRMediaPool`](./src/jetdr/davinci/media_pool.py): メディアプール管理
- [`TimelineBuilder`](./src/jetdr/davinci/timeline_builder.py): タイムライン構築
- [`ExportConfig`](./src/jetdr/exporters/base.py): エクスポート設定
- [`ExportResult`](./src/jetdr/exporters/base.py): エクスポート結果

## 制限事項

1. **DaVinci Resolve Studio必須**: 無料版ではScripting APIが利用不可
2. **アプリケーション起動必須**: DaVinci Resolveが起動している必要がある
3. **プロジェクト必須**: プロジェクトが開かれている必要がある
4. **同期処理**: タイムライン作成は同期処理（大量セグメントで時間がかかる可能性）

## 今後の拡張

- [ ] レンダリング機能の追加（`export_timeline()`の活用）
- [ ] バッチエクスポート対応
- [ ] プログレスコールバック
- [ ] マルチトラック対応
- [ ] エフェクト適用機能
