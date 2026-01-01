# Final Cut Pro 連携ガイド

## 概要

jetFCPは、jetDRのFinal Cut Pro対応版です。動画から無音区間とフィラー（「あー」「えっと」等）を自動検知し、FCPXML形式でジェットカット済みタイムラインを出力します。

---

## インストール

```bash
# uvで依存関係をインストール
uv pip install -e ".[dev]"

# jetfcpコマンドが使用可能に
jetfcp --help
```

---

## 使用方法

### 基本的な使用

```bash
# 動画を処理してFCPXMLを生成
jetfcp export input.mp4

# 出力: JetCut_input.fcpxml
```

### オプション

```bash
jetfcp export input.mp4 \
  --output /path/to/output.fcpxml \  # 出力パスを指定
  --name "MyTimeline" \               # タイムライン名
  --config config/settings.yaml \     # 設定ファイル
  --fillers config/fillers.yaml \     # フィラー辞書
  --verbose                           # 詳細ログ
```

### 解析のみ（FCPXML出力なし）

```bash
# テーブル形式で表示
jetfcp analyze input.mp4

# JSON形式で出力
jetfcp analyze input.mp4 --format json --output result.json
```

### FCPXMLの検証

```bash
jetfcp validate output.fcpxml
```

---

## Final Cut Pro へのインポート

1. **jetfcp export** でFCPXMLファイルを生成
2. Final Cut Proを起動
3. **ファイル** → **読み込む** → **XML...**
4. 生成された `.fcpxml` ファイルを選択
5. 新しいイベントにタイムラインがインポートされます

---

## 設定

`config/settings.yaml` の設定はjetDRと共通です：

```yaml
silence:
  threshold_db: -40.0      # 無音判定の閾値
  min_duration_ms: 300     # 最小無音長

filler:
  model_name: "large-v3"   # Whisperモデル
  language: "ja"           # 言語
  device: "auto"           # GPU自動検出

margin:
  before_ms: 100           # 発話前マージン
  after_ms: 100            # 発話後マージン

fps: 29.97                 # フレームレート
min_keep_duration_ms: 500  # 最小保持区間長
```

---

## FCPXML仕様

### バージョン

jetFCPは **FCPXML v1.10** を生成します。以下のバージョンのFinal Cut Proに対応：

- Final Cut Pro 10.4.9 以降
- Final Cut Pro for iPad

### 構造

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
    <resources>
        <format id="r1" frameDuration="1001/30000s" width="1920" height="1080"/>
        <asset id="r2" src="file:///path/to/video.mp4" format="r1"/>
    </resources>
    <library>
        <event name="JetCut_Video">
            <project name="JetCut_Video">
                <sequence format="r1">
                    <spine>
                        <asset-clip ref="r2" start="0s" duration="5s"/>
                        <asset-clip ref="r2" start="10s" duration="3s"/>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>
```

### 時間精度

FCPXML は有理数で時間を表現します。jetFCPは `fractions.Fraction` を使用して完全なフレーム精度を保証：

| フレームレート | フレーム時間 |
|---------------|-------------|
| 23.976 fps | 1001/24000s |
| 24 fps | 1/24s |
| 25 fps | 1/25s |
| 29.97 fps | 1001/30000s |
| 30 fps | 1/30s |
| 59.94 fps | 1001/60000s |
| 60 fps | 1/60s |

---

## DaVinci Resolve vs Final Cut Pro

| 項目 | jetdr (DaVinci) | jetfcp (FCP) |
|------|-----------------|--------------|
| 出力形式 | タイムライン直接作成 | FCPXMLファイル |
| 必要条件 | DaVinci Resolve Studio起動 | FCPインストールのみ |
| インポート | 自動（APIで作成） | 手動（XML読み込み） |
| ライセンス | Studio版必須 | 不要 |

---

## トラブルシューティング

### FCPXMLがインポートできない

1. **jetfcp validate** でファイルを検証
2. 動画ファイルのパスが正しいか確認
3. 動画ファイルがFCPからアクセス可能か確認

### フレームレートが合わない

`config/settings.yaml` の `fps` 設定を元動画に合わせてください：

```yaml
fps: 29.97  # NTSC
# fps: 25.0  # PAL
# fps: 24.0  # 映画
```

### メディアオフライン

FCPXMLは動画ファイルへの絶対パスを含みます。ファイルを移動した場合は、FCPの「メディアを再リンク」機能を使用してください。

---

## API使用例

```python
from jetdr.exporters.base import ExportConfig
from jetdr.fcp.exporter import FCPExporter
from jetdr.editor.segment import Segment, SegmentType

# セグメントを準備
segments = [
    Segment(start_ms=0, end_ms=5000, type=SegmentType.KEEP),
    Segment(start_ms=10000, end_ms=15000, type=SegmentType.KEEP),
]

# エクスポート設定
config = ExportConfig(
    video_path="/path/to/video.mp4",
    output_name="MyTimeline",
    fps=29.97,
)

# FCPXML生成
exporter = FCPExporter()
result = exporter.export(segments, config)

if result.success:
    print(f"Exported to: {result.output_path}")
```
