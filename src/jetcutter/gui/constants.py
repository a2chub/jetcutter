"""
constants - GUI定数定義

ウィンドウサイズ、色、フォントなどのUI定数。
"""

# ウィンドウ設定
WINDOW_TITLE = "JetCutter"
WINDOW_SIZE = (700, 550)

# サポートする動画形式
VIDEO_EXTENSIONS = ("mp4", "MP4", "mov", "MOV", "avi", "AVI", "mkv", "MKV", "webm", "WEBM")
VIDEO_FILE_TYPES = (("Video Files", "*.mp4 *.MP4 *.mov *.MOV *.avi *.mkv *.webm"),)

# 処理ステージ名（日本語）
STAGE_NAMES = {
    "Extracting audio...": "音声を抽出中...",
    "Detecting silence...": "無音区間を検出中...",
    "Detecting fillers...": "フィラーを検出中...",
    "Calculating keep segments...": "保持区間を計算中...",
}

# プログレスパーセンテージ
STAGE_PROGRESS = {
    "Extracting audio...": 10,
    "Detecting silence...": 35,
    "Detecting fillers...": 80,
    "Calculating keep segments...": 95,
}

# Whisperモデル選択肢
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]

# 言語選択肢
LANGUAGES = [
    ("日本語", "ja"),
    ("英語", "en"),
    ("中国語", "zh"),
    ("韓国語", "ko"),
]

# デバイス選択肢
DEVICES = ["auto", "cuda", "cpu"]

# エディタ選択肢
EDITORS = [
    ("Final Cut Pro", "fcp"),
    ("DaVinci Resolve", "davinci"),
]

# セグメントタイプの日本語表示
SEGMENT_TYPE_NAMES = {
    "SILENCE": "無音",
    "FILLER": "フィラー",
    "KEEP": "保持",
    "CUT": "カット",
}

# テーブルヘッダー
SEGMENT_TABLE_HEADINGS = ["#", "種別", "開始", "終了", "長さ"]
SEGMENT_TABLE_COL_WIDTHS = [5, 10, 12, 12, 12]

# イベントキー
EVENT_BROWSE_VIDEO = "-BROWSE-VIDEO-"
EVENT_BROWSE_OUTPUT = "-BROWSE-OUTPUT-"
EVENT_START = "-START-"
EVENT_CANCEL = "-CANCEL-"
EVENT_SAVE_SETTINGS = "-SAVE-SETTINGS-"
EVENT_LOAD_DEFAULTS = "-LOAD-DEFAULTS-"
EVENT_STAGE = "-STAGE-"
EVENT_PROGRESS = "-PROGRESS-"
EVENT_COMPLETE = "-COMPLETE-"
EVENT_ERROR = "-ERROR-"
EVENT_CANCELLED = "-CANCELLED-"
