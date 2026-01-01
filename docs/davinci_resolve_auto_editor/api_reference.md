# API リファレンス：DaVinci Resolve 自動編集エージェント

## 概要

本ドキュメントは、jetDRパッケージの主要なクラスと関数のAPIリファレンスです。

---

## 目次

1. [設定 (Config)](#config)
2. [音声処理 (Audio)](#audio)
3. [音声認識 (Speech)](#speech)
4. [編集ロジック (Editor)](#editor)
5. [DaVinci Resolve連携 (Davinci)](#davinci)
6. [ユーティリティ (Utils)](#utils)
7. [Exporters (エクスポーター)](#exporters)
8. [FCP (Final Cut Pro)](#fcp)
9. [CLI](#cli)

---

## Config

### `jetdr.config.settings`

#### `class AppConfig`

アプリケーション全体の設定を管理するPydanticモデル。

```python
from jetdr.config.settings import AppConfig

config = AppConfig.from_yaml("config/settings.yaml")
```

**属性:**

| 属性名    | 型                      | デフォルト | 説明                     |
|-----------|-------------------------|------------|--------------------------|
| `silence` | `SilenceDetectionConfig`| -          | 無音検知設定             |
| `filler`  | `FillerDetectionConfig` | -          | フィラー検知設定         |
| `margin`  | `MarginConfig`          | -          | カットマージン設定       |
| `fps`     | `float`                 | `29.97`    | フレームレート           |

**メソッド:**

```python
@classmethod
def from_yaml(cls, path: str | Path) -> AppConfig:
    """YAMLファイルから設定を読み込む"""
    
def to_yaml(self, path: str | Path) -> None:
    """設定をYAMLファイルに書き出す"""
```

---

#### `class SilenceDetectionConfig`

無音検知の設定。

| 属性名            | 型      | デフォルト | 説明                     |
|-------------------|---------|------------|--------------------------|
| `threshold_db`    | `float` | `-40.0`    | 無音判定しきい値（dB）   |
| `min_duration_ms` | `int`   | `300`      | 最小無音期間（ミリ秒）   |

---

#### `class FillerDetectionConfig`

フィラー検知の設定。

| 属性名         | 型            | デフォルト   | 説明                   |
|----------------|---------------|--------------|------------------------|
| `model_name`   | `str`         | `"large-v3"` | Whisperモデル名        |
| `language`     | `str`         | `"ja"`       | 言語コード             |
| `filler_words` | `List[str]`   | `[]`         | フィラー単語リスト     |

---

#### `class MarginConfig`

カットマージンの設定。

| 属性名      | 型    | デフォルト | 説明                       |
|-------------|-------|------------|----------------------------|
| `before_ms` | `int` | `100`      | 開始前バッファ（ミリ秒）   |
| `after_ms`  | `int` | `100`      | 終了後バッファ（ミリ秒）   |

---

## Audio

### `jetdr.audio.extractor`

#### `class AudioExtractor`

動画ファイルから音声を抽出するクラス。

```python
from jetdr.audio.extractor import AudioExtractor

extractor = AudioExtractor(sample_rate=16000)
audio_path = extractor.extract(video_path)
```

**コンストラクタ:**

```python
def __init__(self, sample_rate: int = 16000):
    """
    Args:
        sample_rate: 出力音声のサンプルレート（Hz）
    """
```

**メソッド:**

```python
def extract(
    self, 
    video_path: Path, 
    output_path: Optional[Path] = None
) -> Path:
    """
    動画から音声を抽出する
    
    Args:
        video_path: 入力動画ファイルのパス
        output_path: 出力音声ファイルのパス（省略時は一時ファイル）
        
    Returns:
        抽出された音声ファイルのパス
        
    Raises:
        AudioExtractionError: 抽出に失敗した場合
    """
```

---

### `jetdr.audio.analyzer`

#### `class SilenceAnalyzer`

音声ファイルから無音区間を検出するクラス。

```python
from jetdr.audio.analyzer import SilenceAnalyzer

analyzer = SilenceAnalyzer(threshold_db=-40.0, min_duration_ms=300)
silence_segments = analyzer.detect_silence(audio_path)
```

**コンストラクタ:**

```python
def __init__(
    self,
    threshold_db: float = -40.0,
    min_duration_ms: int = 300
):
    """
    Args:
        threshold_db: 無音判定しきい値（dBFS）
        min_duration_ms: 最小無音期間（ミリ秒）
    """
```

**メソッド:**

```python
def detect_silence(self, audio_path: Path) -> List[Segment]:
    """
    音声ファイルから無音区間を検出する
    
    Args:
        audio_path: 音声ファイルのパス
        
    Returns:
        無音区間のリスト（Segmentオブジェクト）
        
    Raises:
        SilenceDetectionError: 検出に失敗した場合
    """

def get_audio_duration_ms(self, audio_path: Path) -> int:
    """
    音声ファイルの長さをミリ秒で取得する
    
    Args:
        audio_path: 音声ファイルのパス
        
    Returns:
        音声の長さ（ミリ秒）
    """
```

---

## Speech

### `jetdr.speech.transcriber`

#### `class Transcriber`

faster-whisperを使用した音声認識クラス。

```python
from jetdr.speech.transcriber import Transcriber

transcriber = Transcriber(model_name="large-v3", language="ja")
word_timestamps = transcriber.transcribe(audio_path)
```

**コンストラクタ:**

```python
def __init__(
    self,
    model_name: str = "large-v3",
    device: str = "auto",
    compute_type: str = "auto",
    language: str = "ja"
):
    """
    Args:
        model_name: Whisperモデル名（tiny, base, small, medium, large-v3等）
        device: 使用デバイス（"auto", "cuda", "cpu"）
        compute_type: 計算精度（"auto", "float16", "int8"等）
        language: 認識対象言語コード
    """
```

**メソッド:**

```python
def transcribe(self, audio_path: Path) -> List[WordTimestamp]:
    """
    音声を文字起こしし、単語タイムスタンプを返す
    
    Args:
        audio_path: 音声ファイルのパス
        
    Returns:
        WordTimestampオブジェクトのリスト
        
    Raises:
        TranscriptionError: 文字起こしに失敗した場合
    """
```

#### `class WordTimestamp`

単語とそのタイムスタンプを保持するデータクラス。

```python
@dataclass
class WordTimestamp:
    word: str          # 単語テキスト
    start_ms: int      # 開始時間（ミリ秒）
    end_ms: int        # 終了時間（ミリ秒）
    confidence: float  # 認識確信度（0.0-1.0）
```

---

### `jetdr.speech.filler_detector`

#### `class FillerDetector`

フィラー単語を検出するクラス。

```python
from jetdr.speech.filler_detector import FillerDetector

detector = FillerDetector(filler_words=["えー", "あー", "えっと"])
filler_segments = detector.detect(word_timestamps)
```

**コンストラクタ:**

```python
def __init__(self, filler_words: List[str]):
    """
    Args:
        filler_words: 検出対象のフィラー単語リスト
    """
```

**メソッド:**

```python
def detect(self, word_timestamps: List[WordTimestamp]) -> List[Segment]:
    """
    単語リストからフィラー区間を検出する
    
    Args:
        word_timestamps: 単語タイムスタンプのリスト
        
    Returns:
        フィラー区間のリスト（Segmentオブジェクト）
    """

@classmethod
def from_yaml(cls, path: Path) -> FillerDetector:
    """
    YAMLファイルからフィラー辞書を読み込んでインスタンスを作成する
    
    Args:
        path: フィラー辞書YAMLファイルのパス
        
    Returns:
        FillerDetectorインスタンス
    """
```

---

## Editor

### `jetdr.editor.segment`

#### `class SegmentType`

区間の種類を表す列挙型。

```python
from enum import Enum

class SegmentType(Enum):
    SILENCE = "silence"  # 無音区間
    FILLER = "filler"    # フィラー区間
    KEEP = "keep"        # 保持区間
    CUT = "cut"          # 削除区間
```

---

#### `class Segment`

時間区間を表すデータクラス。

```python
from jetdr.editor.segment import Segment, SegmentType

segment = Segment(
    start_ms=1000,
    end_ms=2500,
    type=SegmentType.KEEP
)
```

**属性:**

| 属性名     | 型                     | 説明                      |
|------------|------------------------|---------------------------|
| `start_ms` | `int`                  | 開始時間（ミリ秒）        |
| `end_ms`   | `int`                  | 終了時間（ミリ秒）        |
| `type`     | `SegmentType`          | 区間の種類                |
| `metadata` | `Optional[dict]`       | 追加情報（検出単語など）  |

**プロパティ:**

```python
@property
def duration_ms(self) -> int:
    """区間の長さ（ミリ秒）"""
```

**メソッド:**

```python
def overlaps(self, other: Segment) -> bool:
    """他の区間と重複するかチェック"""

def merge(self, other: Segment) -> Segment:
    """他の区間とマージして新しいSegmentを返す"""

def apply_margin(
    self, 
    before_ms: int, 
    after_ms: int, 
    max_duration_ms: int
) -> Segment:
    """マージンを適用した新しいSegmentを返す"""

def align_to_frame(self, fps: float) -> Segment:
    """フレーム境界にアラインした新しいSegmentを返す"""
```

---

### `jetdr.editor.merger`

#### `class SegmentMerger`

区間のマージと保持区間算出を行うクラス。

```python
from jetdr.editor.merger import SegmentMerger

merger = SegmentMerger(
    margin_before_ms=100,
    margin_after_ms=100,
    min_keep_duration_ms=500,
    fps=29.97
)

keep_segments = merger.calculate_keep_segments(
    silence_segments=silence_segments,
    filler_segments=filler_segments,
    total_duration_ms=total_duration_ms
)
```

**コンストラクタ:**

```python
def __init__(
    self,
    margin_before_ms: int = 100,
    margin_after_ms: int = 100,
    min_keep_duration_ms: int = 500,
    fps: float = 29.97
):
    """
    Args:
        margin_before_ms: 保持区間開始前のバッファ（ミリ秒）
        margin_after_ms: 保持区間終了後のバッファ（ミリ秒）
        min_keep_duration_ms: 最小保持区間長（ミリ秒）
        fps: フレームレート
    """
```

**メソッド:**

```python
def calculate_keep_segments(
    self,
    silence_segments: List[Segment],
    filler_segments: List[Segment],
    total_duration_ms: int
) -> List[Segment]:
    """
    保持区間を計算する
    
    Args:
        silence_segments: 無音区間リスト
        filler_segments: フィラー区間リスト
        total_duration_ms: 動画の総時間（ミリ秒）
        
    Returns:
        保持区間のリスト
    """

def merge_overlapping(self, segments: List[Segment]) -> List[Segment]:
    """
    重複・隣接する区間をマージする
    
    Args:
        segments: マージ対象の区間リスト
        
    Returns:
        マージ後の区間リスト
    """
```

---

## Davinci

### `jetdr.davinci.connection`

#### `class DRConnection`

DaVinci Resolveへの接続を管理するクラス。

```python
from jetdr.davinci.connection import DRConnection

with DRConnection() as conn:
    if conn.is_connected:
        # DRと連携した処理
        pass
```

**メソッド:**

```python
def connect(self) -> bool:
    """
    DaVinci Resolveに接続する
    
    Returns:
        接続に成功したかどうか
        
    Raises:
        DaVinciConnectionError: 接続に失敗した場合
    """

def disconnect(self) -> None:
    """接続を解除する"""

@property
def is_connected(self) -> bool:
    """接続中かどうか"""

@property
def resolve(self) -> Any:
    """Resolveオブジェクト"""

def __enter__(self) -> DRConnection:
    """コンテキストマネージャ: 接続"""

def __exit__(self, *args) -> None:
    """コンテキストマネージャ: 切断"""
```

---

### `jetdr.davinci.timeline_builder`

#### `class TimelineBuilder`

DaVinci Resolveでタイムラインを構築するクラス。

```python
from jetdr.davinci.timeline_builder import TimelineBuilder
from jetdr.davinci.connection import DRConnection

with DRConnection() as conn:
    builder = TimelineBuilder(conn)
    builder.create_timeline_from_segments(
        video_path=video_path,
        segments=keep_segments,
        timeline_name="JetCut Timeline"
    )
```

**コンストラクタ:**

```python
def __init__(self, connection: DRConnection):
    """
    Args:
        connection: DRConnectionインスタンス
    """
```

**メソッド:**

```python
def create_timeline_from_segments(
    self,
    video_path: Path,
    segments: List[Segment],
    timeline_name: str,
    fps: Optional[float] = None
) -> bool:
    """
    保持区間からタイムラインを作成する
    
    Args:
        video_path: 元動画ファイルのパス
        segments: 保持区間リスト
        timeline_name: タイムライン名
        fps: フレームレート（省略時は動画から取得）
        
    Returns:
        成功したかどうか
        
    Raises:
        TimelineCreationError: タイムライン作成に失敗した場合
    """

def import_media(self, video_path: Path) -> MediaPoolItem:
    """
    メディアプールに動画をインポートする
    
    Args:
        video_path: 動画ファイルのパス
        
    Returns:
        インポートされたMediaPoolItem
    """
```

---

## Utils

### `jetdr.utils.time_utils`

時間変換ユーティリティ関数群。

```python
from jetdr.utils.time_utils import (
    ms_to_frames,
    frames_to_ms,
    ms_to_timecode,
    align_ms_to_frame
)
```

**関数:**

```python
def ms_to_frames(ms: int, fps: float) -> int:
    """
    ミリ秒をフレーム番号に変換する
    
    Args:
        ms: ミリ秒
        fps: フレームレート
        
    Returns:
        フレーム番号（0始まり）
    """

def frames_to_ms(frames: int, fps: float) -> int:
    """
    フレーム番号をミリ秒に変換する
    
    Args:
        frames: フレーム番号
        fps: フレームレート
        
    Returns:
        ミリ秒
    """

def ms_to_timecode(ms: int, fps: float) -> str:
    """
    ミリ秒をSMPTEタイムコードに変換する
    
    Args:
        ms: ミリ秒
        fps: フレームレート
        
    Returns:
        タイムコード文字列（"HH:MM:SS:FF"形式）
    """

def align_ms_to_frame(ms: int, fps: float) -> int:
    """
    ミリ秒をフレーム境界にアラインする

    Args:
        ms: ミリ秒
        fps: フレームレート

    Returns:
        フレーム境界にアラインされたミリ秒
    """
```

---

## Exporters

### `jetdr.exporters.base`

エクスポーターの抽象基底クラスとデータモデルを提供する。

#### `class ExportConfig`

エクスポート設定を保持するデータクラス。

```python
from jetdr.exporters.base import ExportConfig
from pathlib import Path

config = ExportConfig(
    video_path=Path("/path/to/video.mp4"),
    output_name="edited_video",
    fps=29.97,
    width=1920,
    height=1080,
    metadata={"project_name": "My Project"}
)
```

**属性:**

| 属性名        | 型                    | デフォルト | 説明                     |
|---------------|----------------------|------------|--------------------------|
| `video_path`  | `Path`               | 必須       | 入力動画ファイルパス     |
| `output_name` | `str`                | 必須       | 出力ファイル/タイムライン名 |
| `fps`         | `float`              | `29.97`    | フレームレート           |
| `width`       | `Optional[int]`      | `None`     | 動画幅（ピクセル）       |
| `height`      | `Optional[int]`      | `None`     | 動画高さ（ピクセル）     |
| `metadata`    | `Optional[dict]`     | `None`     | 追加メタデータ           |

---

#### `class ExportResult`

エクスポート結果を保持するデータクラス。

```python
from jetdr.exporters.base import ExportResult

result = ExportResult(
    success=True,
    output_path=Path("/path/to/output.fcpxml"),
    message="Export completed successfully",
    details={"keep_segments": 5, "total_duration_ms": 30000}
)
```

**属性:**

| 属性名        | 型                    | 説明                     |
|---------------|-----------------------|--------------------------|
| `success`     | `bool`                | 成功したかどうか         |
| `output_path` | `Optional[Path]`      | 出力ファイルパス         |
| `message`     | `str`                 | 結果メッセージ           |
| `details`     | `Optional[dict]`      | 詳細情報                 |

---

#### `class BaseTimelineExporter`

すべてのエクスポーターの抽象基底クラス。

```python
from abc import ABC, abstractmethod
from jetdr.exporters.base import BaseTimelineExporter

class MyExporter(BaseTimelineExporter):
    @property
    def name(self) -> str:
        return "My Exporter"

    def validate_config(self, config: ExportConfig) -> tuple[bool, str]:
        # バリデーションロジック
        return True, ""

    def export(self, segments: list[Segment], config: ExportConfig) -> ExportResult:
        # エクスポートロジック
        pass
```

**プロパティ:**

| プロパティ | 型    | 説明               |
|------------|-------|-------------------|
| `name`     | `str` | エクスポーター名   |

**メソッド:**

```python
@abstractmethod
def validate_config(self, config: ExportConfig) -> tuple[bool, str]:
    """設定を検証する"""

@abstractmethod
def export(self, segments: list[Segment], config: ExportConfig) -> ExportResult:
    """セグメントをエクスポートする"""
```

---

#### `class FileExporter`

ファイル出力型エクスポーターの抽象基底クラス（FCPXML, EDL等）。

```python
from jetdr.exporters.base import FileExporter
```

**プロパティ:**

| プロパティ        | 型    | 説明                   |
|-------------------|-------|------------------------|
| `file_extension`  | `str` | ファイル拡張子（例: `.fcpxml`） |

**メソッド:**

```python
@abstractmethod
def export_to_string(self, segments: list[Segment], config: ExportConfig) -> str:
    """文字列としてエクスポート"""

def get_default_output_path(self, config: ExportConfig) -> Path:
    """デフォルト出力パスを取得"""
```

---

#### `class LiveConnectionExporter`

ライブ接続型エクスポーターの抽象基底クラス（DaVinci Resolve等）。

```python
from jetdr.exporters.base import LiveConnectionExporter
```

**プロパティ:**

| プロパティ      | 型     | 説明                   |
|-----------------|--------|------------------------|
| `is_connected`  | `bool` | 接続中かどうか         |

**メソッド:**

```python
@abstractmethod
def connect(self) -> bool:
    """アプリケーションに接続"""

@abstractmethod
def disconnect(self) -> None:
    """接続を解除"""

def __enter__(self) -> LiveConnectionExporter:
    """コンテキストマネージャ: 接続"""

def __exit__(self, *args) -> None:
    """コンテキストマネージャ: 切断"""
```

---

### `jetdr.exporters.factory`

#### `class ExporterRegistry`

エクスポーターを登録・管理するレジストリ。

```python
from jetdr.exporters.factory import ExporterRegistry

# 利用可能なエクスポーター一覧
available = ExporterRegistry.list_available()  # ['davinci', 'fcp']

# エクスポーター取得
exporter = ExporterRegistry.get("fcp")

# 新しいエクスポーター登録
ExporterRegistry.register("my_exporter", MyExporterClass)
```

**クラスメソッド:**

```python
@classmethod
def register(cls, name: str, exporter_class: type[BaseTimelineExporter]) -> None:
    """エクスポータークラスを登録"""

@classmethod
def get(cls, name: str) -> BaseTimelineExporter:
    """名前でエクスポーターインスタンスを取得"""

@classmethod
def list_available(cls) -> list[str]:
    """利用可能なエクスポーター名一覧を取得"""
```

---

#### `create_exporter()`

ファクトリー関数でエクスポーターを作成。

```python
from jetdr.exporters.factory import create_exporter

# DaVinci Resolveエクスポーター
davinci_exporter = create_exporter("davinci")

# FCPエクスポーター
fcp_exporter = create_exporter("fcp")
```

---

## FCP

### `jetdr.fcp.time_utils`

FCPXML用のフレーム精度時間計算ユーティリティ。

#### `class FCPTime`

フレーム精度の時間表現データクラス。

```python
from jetdr.fcp import FCPTime

# ミリ秒から作成
fcp_time = FCPTime.from_ms(1000, 29.97)
print(fcp_time.to_fcpxml_string())  # "1001/30s"

# フレーム数から作成
fcp_time = FCPTime.from_frames(30, 29.97)

# 秒数から作成
fcp_time = FCPTime.from_seconds(1.0, 29.97)
```

**属性:**

| 属性名          | 型         | 説明                        |
|-----------------|------------|----------------------------|
| `value`         | `Fraction` | 時間値（秒、分数で保持）    |
| `frame_duration`| `Fraction` | 1フレームの長さ（秒）       |

**クラスメソッド:**

```python
@classmethod
def from_ms(cls, ms: int, fps: float) -> FCPTime:
    """ミリ秒から作成"""

@classmethod
def from_frames(cls, frames: int, fps: float) -> FCPTime:
    """フレーム数から作成"""

@classmethod
def from_seconds(cls, seconds: float, fps: float) -> FCPTime:
    """秒数から作成"""
```

**メソッド:**

```python
def to_fcpxml_string(self) -> str:
    """FCPXML形式の文字列に変換（例: '1001/30000s'）"""

def to_seconds(self) -> float:
    """秒数に変換"""

def to_frames(self) -> int:
    """フレーム数に変換"""
```

**演算子:**

- `+`, `-`: 時間の加算・減算
- `==`, `<`, `<=`, `>`, `>=`: 比較演算

---

#### 関数

```python
from jetdr.fcp import get_frame_duration, format_frame_duration

# フレーム期間を取得（Fraction型）
frame_dur = get_frame_duration(29.97)  # Fraction(1001, 30000)

# FCPXML文字列形式で取得
formatted = format_frame_duration(29.97)  # "1001/30000s"
```

---

### `jetdr.fcp.fcpxml_builder`

#### `class FCPXMLBuilder`

FCPXML v1.10ドキュメントを構築するクラス。

```python
from pathlib import Path
from jetdr.fcp import FCPXMLBuilder
from jetdr.exporters.base import ExportConfig

config = ExportConfig(
    video_path=Path("/path/to/video.mp4"),
    output_name="project",
    fps=29.97,
    width=1920,
    height=1080,
)

builder = FCPXMLBuilder(config)

# XMLを文字列として取得
xml_string = builder.to_string(segments, indent=True)

# ファイルに書き出し
output_path = builder.write(segments, Path("/output/project.fcpxml"))
```

**メソッド:**

```python
def build(self, segments: list[Segment]) -> ET.Element:
    """FCPXML ElementTreeを構築"""

def to_string(self, segments: list[Segment], indent: bool = True) -> str:
    """XML文字列に変換"""

def write(self, segments: list[Segment], output_path: Path) -> Path:
    """ファイルに書き出し"""
```

---

#### `validate_fcpxml()`

FCPXML文字列の妥当性を検証。

```python
from jetdr.fcp import validate_fcpxml

is_valid, error_msg = validate_fcpxml(xml_string)
if not is_valid:
    print(f"Validation error: {error_msg}")
```

---

### `jetdr.fcp.exporter`

#### `class FCPExporter`

Final Cut Pro FCPXML形式でエクスポートするクラス。

```python
from pathlib import Path
from jetdr.fcp import FCPExporter
from jetdr.exporters.base import ExportConfig
from jetdr.editor.segment import Segment, SegmentType

# セグメント準備
segments = [
    Segment(start_ms=0, end_ms=1000, type=SegmentType.KEEP),
    Segment(start_ms=2000, end_ms=3500, type=SegmentType.KEEP),
]

# エクスポート設定
config = ExportConfig(
    video_path=Path("/path/to/video.mp4"),
    output_name="edited_video",
    fps=29.97,
    width=1920,
    height=1080,
)

# エクスポート実行
exporter = FCPExporter()
result = exporter.export(segments, config)

if result.success:
    print(f"Exported to: {result.output_path}")
```

**プロパティ:**

| プロパティ       | 型    | 値                   |
|------------------|-------|---------------------|
| `name`           | `str` | `"Final Cut Pro"`   |
| `file_extension` | `str` | `".fcpxml"`         |

**メソッド:**

```python
def validate_config(self, config: ExportConfig) -> tuple[bool, str]:
    """設定の妥当性を検証"""

def export(self, segments: list[Segment], config: ExportConfig) -> ExportResult:
    """FCPXMLファイルにエクスポート"""

def export_to_string(self, segments: list[Segment], config: ExportConfig) -> str:
    """XML文字列としてエクスポート（テスト用）"""

def get_default_output_path(self, config: ExportConfig) -> Path:
    """デフォルト出力パスを生成"""
```

---

#### `create_fcp_exporter()`

FCPExporterインスタンスを作成するファクトリー関数。

```python
from jetdr.fcp import create_fcp_exporter

exporter = create_fcp_exporter()
```

---

## CLI

### jetdr (DaVinci Resolve用)

```bash
# 単一動画を処理
jetdr process VIDEO_PATH [--output-name NAME] [--config CONFIG_PATH] [--target davinci|fcp]

# 動画を解析して区間を表示
jetdr analyze VIDEO_PATH [--format json|table]

# フォルダ内の全動画を一括処理
jetdr batch FOLDER_PATH [--config CONFIG_PATH]

# 設定を表示
jetdr config show

# デフォルト設定ファイルを生成
jetdr config init [--output PATH]
```

### jetfcp (Final Cut Pro用)

```bash
# 動画を処理してFCPXMLを生成
jetfcp export VIDEO_PATH [--output FILE] [--name NAME] [--config CONFIG_PATH]

# 動画を解析して区間を表示（FCPXML出力なし）
jetfcp analyze VIDEO_PATH [--format json|table]

# FCPXMLファイルを検証
jetfcp validate FCPXML_PATH
```

### コマンド詳細

#### `jetdr process`

動画を処理し、DaVinci Resolveにジェットカット済みタイムラインを生成する。

```bash
jetdr process input.mp4 --output-name "編集済みタイムライン" --config config/settings.yaml
```

**引数:**

| 引数         | 必須 | 説明                         |
|--------------|------|------------------------------|
| `VIDEO_PATH` | ✓    | 処理対象の動画ファイルパス   |

**オプション:**

| オプション        | デフォルト            | 説明                     |
|-------------------|----------------------|--------------------------|
| `--output-name`   | 動画ファイル名        | 出力タイムライン名       |
| `--config`, `-c`  | `config/settings.yaml`| 設定ファイルパス         |
| `--dry-run`       | `False`              | DRへの書き込みをスキップ |
| `--verbose`, `-v` | `False`              | 詳細出力を有効化         |

---

#### `jetdr analyze`

動画を解析し、無音区間とフィラー区間を表示する。

```bash
jetdr analyze input.mp4 --format json
```

**引数:**

| 引数         | 必須 | 説明                       |
|--------------|------|----------------------------|
| `VIDEO_PATH` | ✓    | 解析対象の動画ファイルパス |

**オプション:**

| オプション   | デフォルト | 説明                       |
|--------------|------------|----------------------------|
| `--format`   | `table`    | 出力形式（`json`または`table`）|
| `--output`   | なし       | 結果をファイルに出力       |

---

#### `jetdr batch`

フォルダ内の全動画を一括処理する。

```bash
jetdr batch ./videos --config config/settings.yaml
```

**引数:**

| 引数          | 必須 | 説明                       |
|---------------|------|----------------------------|
| `FOLDER_PATH` | ✓    | 動画フォルダパス           |

**オプション:**

| オプション       | デフォルト  | 説明                     |
|------------------|-------------|--------------------------|
| `--config`, `-c` | `config/settings.yaml` | 設定ファイルパス |
| `--pattern`      | `*.mp4`     | ファイルパターン         |
| `--recursive`    | `False`     | サブフォルダも処理       |

---

#### `jetfcp export`

動画を処理し、FCPXMLファイルを生成する。

```bash
jetfcp export input.mp4 --output edited.fcpxml --name "編集済みタイムライン"
```

**引数:**

| 引数         | 必須 | 説明                         |
|--------------|------|------------------------------|
| `VIDEO_PATH` | ✓    | 処理対象の動画ファイルパス   |

**オプション:**

| オプション        | デフォルト            | 説明                     |
|-------------------|----------------------|--------------------------|
| `--output`, `-o`  | 動画名.fcpxml        | 出力FCPXMLファイルパス   |
| `--name`, `-n`    | 動画ファイル名       | タイムライン名           |
| `--config`, `-c`  | `config/settings.yaml`| 設定ファイルパス        |
| `--verbose`, `-V` | `False`              | 詳細出力を有効化         |

---

#### `jetfcp analyze`

動画を解析し、無音区間とフィラー区間を表示する。

```bash
jetfcp analyze input.mp4 --format json
```

**引数:**

| 引数         | 必須 | 説明                       |
|--------------|------|----------------------------|
| `VIDEO_PATH` | ✓    | 解析対象の動画ファイルパス |

**オプション:**

| オプション   | デフォルト | 説明                           |
|--------------|------------|--------------------------------|
| `--format`   | `table`    | 出力形式（`json`または`table`）|
| `--output`   | なし       | 結果をファイルに出力           |

---

#### `jetfcp validate`

FCPXMLファイルの妥当性を検証する。

```bash
jetfcp validate output.fcpxml
```

**引数:**

| 引数          | 必須 | 説明                       |
|---------------|------|----------------------------|
| `FCPXML_PATH` | ✓    | 検証対象のFCPXMLファイルパス |

**出力例:**

```
✓ XML構造: 有効
✓ FCPXML version: 1.10
✓ リソース: 2個
✓ アセットクリップ: 5個
```

---

## 例外クラス

```python
from jetdr.exceptions import (
    JetDRError,
    AudioExtractionError,
    SilenceDetectionError,
    TranscriptionError,
    DaVinciConnectionError,
    TimelineCreationError
)
```

| 例外クラス              | 説明                              |
|-------------------------|-----------------------------------|
| `JetDRError`            | 基底例外クラス                    |
| `AudioExtractionError`  | 音声抽出に失敗した場合            |
| `SilenceDetectionError` | 無音検知に失敗した場合            |
| `TranscriptionError`    | 音声認識に失敗した場合            |
| `DaVinciConnectionError`| DaVinci Resolve接続に失敗した場合 |
| `TimelineCreationError` | タイムライン作成に失敗した場合    |
