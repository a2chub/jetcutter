"""
constants - GUI定数定義

ビジネスロジック定数とAppKit固有の定数を定義。
"""

# ========== ウィンドウ設定 ==========
WINDOW_TITLE = "JetCutter"
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 550
WINDOW_MIN_WIDTH = 600
WINDOW_MIN_HEIGHT = 450

# ========== 処理ステージ ==========
STAGE_NAMES = {
    "extract": "音声抽出中...",
    "silence": "無音検知中...",
    "transcribe": "文字起こし中...",
    "filler": "フィラー検知中...",
    "merge": "セグメント統合中...",
    "export": "エクスポート中...",
}

STAGE_PROGRESS = {
    "extract": 10,
    "silence": 30,
    "transcribe": 50,
    "filler": 70,
    "merge": 85,
    "export": 95,
}

# ========== エディタ選択 ==========
EDITOR_FCP = "fcp"
EDITOR_DAVINCI = "davinci"
EDITOR_LABELS = {
    EDITOR_FCP: "Final Cut Pro",
    EDITOR_DAVINCI: "DaVinci Resolve",
}

# ========== Whisperモデル ==========
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]
DEFAULT_MODEL = "large-v3"

# ========== 言語 ==========
LANGUAGES = {
    "日本語": "ja",
    "English": "en",
    "中文": "zh",
    "한국어": "ko",
}
DEFAULT_LANGUAGE = "日本語"

# ========== デバイス ==========
DEVICES = {
    "自動": "auto",
    "CUDA (GPU)": "cuda",
    "CPU": "cpu",
}
DEFAULT_DEVICE = "自動"

# ========== ファイルタイプ ==========
VIDEO_EXTENSIONS = ["mp4", "mov", "avi", "mkv", "webm", "m4v"]

# ========== セグメントタイプ表示 ==========
SEGMENT_TYPE_NAMES = {
    "SILENCE": "無音",
    "FILLER": "フィラー",
    "KEEP": "保持",
    "CUT": "カット",
}

# ========== テーブル設定 ==========
SEGMENT_TABLE_HEADINGS = ["#", "種別", "開始", "終了", "長さ"]

# ========== UI定数 (Apple HIG準拠) ==========
MARGIN = 20
SECTION_SPACING = 24
ITEM_SPACING = 8
ROW_HEIGHT = 26
LABEL_HEIGHT = 17
FIELD_HEIGHT = 22
BUTTON_HEIGHT = 32

# ========== タブ識別子 ==========
TAB_PROCESS = "process"
TAB_SETTINGS = "settings"
TAB_RESULTS = "results"

TAB_LABELS = {
    TAB_PROCESS: "処理",
    TAB_SETTINGS: "設定",
    TAB_RESULTS: "結果",
}
