# jetDR - 動画自動編集エージェント

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

動画内の無音区間・フィラー（「あー」「えっと」等）を自動検知し、DaVinci ResolveまたはFinal Cut Proでジェットカット済みタイムラインを生成するPythonツールです。

## 特徴

- 🎬 **無音区間の自動検知**: 音量ベースで無音区間をミリ秒単位で特定
- 🗣️ **フィラー検知**: faster-whisperによる高精度な音声認識でフィラー単語を検出
- ✂️ **スマートカットロジック**: マージン設定やフレームアライン対応
- 🎥 **マルチNLE対応**: DaVinci Resolve（Scripting API）とFinal Cut Pro（FCPXML）をサポート
- 📁 **バッチ処理**: フォルダ内の複数動画を一括処理

## システム要件

### ソフトウェア
- Python 3.10以上
- DaVinci Resolve Studio 18.0以上（外部スクリプティングに必須）
- ffmpeg（システムにインストール済み）

### ハードウェア（推奨）
- RAM: 16GB以上
- GPU: NVIDIA RTX 30xx以上（CUDAによる高速処理）
- ストレージ: SSD 100GB以上の空き容量

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/jetDR.git
cd jetDR

# 仮想環境を作成・有効化
uv venv
source .venv/bin/activate

# 依存ライブラリをインストール
uv pip install -e ".[dev]"
```

## クイックスタート

### 1. 設定ファイルの準備

```bash
# デフォルト設定ファイルを生成
jetdr config init
```

`config/settings.yaml`でパラメータを調整できます：

```yaml
silence:
  threshold_db: -40.0    # 無音判定しきい値（dB）
  min_duration_ms: 300   # 最小無音期間（ms）

filler:
  model_name: "large-v3" # Whisperモデル
  language: "ja"         # 言語

margin:
  before_ms: 100         # 開始前バッファ（ms）
  after_ms: 100          # 終了後バッファ（ms）

fps: 29.97
```

### 2. 動画を処理

```bash
# DaVinci Resolveを起動した状態で実行
jetdr process input.mp4
```

### 3. バッチ処理

```bash
jetdr batch ./videos --pattern "*.mp4"
```

## 使用方法

### DaVinci Resolve用 (jetdr)

```bash
# 単一動画を処理
jetdr process VIDEO_PATH [OPTIONS]

# 動画を解析（DRへの書き込みなし）
jetdr analyze VIDEO_PATH [--format json|table]

# バッチ処理
jetdr batch FOLDER_PATH [OPTIONS]

# 設定を表示
jetdr config show
```

### Final Cut Pro用 (jetfcp)

```bash
# 動画を処理してFCPXMLを生成
jetfcp export VIDEO_PATH [OPTIONS]

# 動画を解析（FCPXML出力なし）
jetfcp analyze VIDEO_PATH [--format json|table]

# FCPXMLファイルを検証
jetfcp validate FCPXML_PATH
```

#### オプション

```bash
# 出力ファイル名を指定
jetfcp export input.mp4 -o output.fcpxml

# タイムライン名を指定
jetfcp export input.mp4 -n "MyProject"

# 設定ファイルを指定
jetfcp export input.mp4 -c custom_settings.yaml

# 詳細ログを出力
jetfcp export input.mp4 -V
```

### Pythonから使用

```python
from jetdr.audio.extractor import AudioExtractor
from jetdr.audio.analyzer import SilenceAnalyzer
from jetdr.speech.transcriber import Transcriber
from jetdr.speech.filler_detector import FillerDetector
from jetdr.editor.merger import SegmentMerger
from jetdr.davinci.connection import DRConnection
from jetdr.davinci.timeline_builder import TimelineBuilder

# 音声抽出
extractor = AudioExtractor()
audio_path = extractor.extract(video_path)

# 無音検知
silence_analyzer = SilenceAnalyzer(threshold_db=-40.0)
silence_segments = silence_analyzer.detect_silence(audio_path)

# フィラー検知
transcriber = Transcriber(model_name="large-v3")
word_timestamps = transcriber.transcribe(audio_path)

filler_detector = FillerDetector.from_yaml("config/fillers.yaml")
filler_segments = filler_detector.detect(word_timestamps)

# 保持区間算出
merger = SegmentMerger(margin_before_ms=100, margin_after_ms=100)
keep_segments = merger.calculate_keep_segments(
    silence_segments=silence_segments,
    filler_segments=filler_segments,
    total_duration_ms=total_duration_ms
)

# DaVinci Resolveでタイムライン作成
with DRConnection() as conn:
    builder = TimelineBuilder(conn)
    builder.create_timeline_from_segments(
        video_path=video_path,
        segments=keep_segments,
        timeline_name="JetCut Timeline"
    )
```

## フィラー辞書のカスタマイズ

`config/fillers.yaml`を編集して、検出対象のフィラー単語を追加できます：

```yaml
fillers:
  - あー
  - えー
  - えっと
  - うーん
  - まあ
  - なんか
  # 自分の口癖を追加
  - とりあえず
  - 要するに
```

## ドキュメント

詳細なドキュメントは`docs/`にあります：

### 共通
- [システム要件定義書](docs/davinci_resolve_auto_editor/requirements.md)
- [アーキテクチャ設計書](docs/davinci_resolve_auto_editor/architecture.md)
- [APIリファレンス](docs/davinci_resolve_auto_editor/api_reference.md)

### Final Cut Pro
- [FCP統合ガイド](docs/davinci_resolve_auto_editor/fcp_integration.md)
- [FCPモジュール実装](docs/fcp_module_implementation.md)

### DaVinci Resolve
- [DaVinciエクスポーター](docs/davinci_exporter.md)
- [タスクリスト](docs/davinci_resolve_auto_editor/task.md)

### テスト
- テスト数: 63 (passing)
- カバレッジ: 38% (FCPモジュール: 91-97%)

## 制限事項

### DaVinci Resolve
- DaVinci Resolve無料版では外部スクリプティングが制限されるため、**Studio版が必須**です

### Final Cut Pro
- 生成されたFCPXMLをFinal Cut Proにインポートする必要があります
- FCPXML v1.10形式で出力（Final Cut Pro 10.4.9以降対応）

### 共通
- 複数話者の同時発話には対応していません（初期バージョン）
- 音声認識精度は音質・話者の明瞭さに依存します

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照してください。

## 貢献

Issue・Pull Requestを歓迎します。詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。
