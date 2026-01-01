"""
window - ウィンドウレイアウト定義

PySimpleGUI4を使用したウィンドウレイアウト。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import PySimpleGUI as sg

from jetcutter.config.settings import AppConfig
from jetcutter.gui.constants import (
    DEVICES,
    EVENT_BROWSE_OUTPUT,
    EVENT_BROWSE_VIDEO,
    EVENT_CANCEL,
    EVENT_LOAD_DEFAULTS,
    EVENT_SAVE_SETTINGS,
    EVENT_START,
    LANGUAGES,
    SEGMENT_TABLE_COL_WIDTHS,
    SEGMENT_TABLE_HEADINGS,
    VIDEO_FILE_TYPES,
    WHISPER_MODELS,
    WINDOW_SIZE,
    WINDOW_TITLE,
)

if TYPE_CHECKING:
    pass


def create_process_tab(config: AppConfig) -> list[list[sg.Element]]:
    """処理タブのレイアウトを作成"""
    default_editor = config.output.default_editor

    return [
        [sg.Text("動画ファイル", font=("", 12, "bold"))],
        [
            sg.Input(key="-VIDEO-PATH-", size=(55, 1), enable_events=True),
            sg.FileBrowse(
                "参照...",
                key=EVENT_BROWSE_VIDEO,
                file_types=VIDEO_FILE_TYPES,
            ),
        ],
        [sg.Text("対応形式: .mp4, .mov, .avi, .mkv, .webm", font=("", 9), text_color="gray")],
        [sg.HorizontalSeparator()],
        [sg.Text("エクスポート先", font=("", 12, "bold"))],
        [
            sg.Radio(
                "Final Cut Pro (.fcpxml)",
                "EDITOR",
                key="-EDITOR-FCP-",
                default=(default_editor == "fcp"),
            ),
        ],
        [
            sg.Radio(
                "DaVinci Resolve",
                "EDITOR",
                key="-EDITOR-DAVINCI-",
                default=(default_editor == "davinci"),
            ),
        ],
        [sg.HorizontalSeparator()],
        [sg.Text("出力設定", font=("", 12, "bold"))],
        [
            sg.Text("タイムライン名:"),
            sg.Input(
                default_text=config.output.timeline_prefix,
                key="-TIMELINE-PREFIX-",
                size=(30, 1),
            ),
        ],
        [
            sg.Text("出力先 (FCP):    "),
            sg.Input(key="-OUTPUT-PATH-", size=(40, 1)),
            sg.FolderBrowse("参照...", key=EVENT_BROWSE_OUTPUT),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.ProgressBar(
                100,
                orientation="h",
                size=(50, 20),
                key="-PROGRESS-BAR-",
                visible=False,
            ),
        ],
        [sg.Text("", key="-STATUS-TEXT-", size=(60, 1))],
        [sg.VPush()],
        [
            sg.Push(),
            sg.Button("処理開始", key=EVENT_START, size=(15, 1)),
            sg.Button("キャンセル", key=EVENT_CANCEL, size=(15, 1), visible=False),
            sg.Push(),
        ],
    ]


def create_settings_tab(config: AppConfig) -> list[list[sg.Element]]:
    """設定タブのレイアウトを作成"""
    # 言語の初期値を取得
    lang_display = [lang[0] for lang in LANGUAGES if lang[1] == config.filler.language]
    default_lang = lang_display[0] if lang_display else "日本語"

    return [
        # 無音検知設定
        [sg.Text("無音検知", font=("", 12, "bold"))],
        [
            sg.Text("しきい値 (dB):", size=(15, 1)),
            sg.Slider(
                range=(-80, 0),
                default_value=config.silence.threshold_db,
                resolution=1,
                orientation="h",
                size=(30, 15),
                key="-THRESHOLD-DB-",
            ),
        ],
        [
            sg.Text("最小無音時間 (ms):", size=(15, 1)),
            sg.Input(
                default_text=str(config.silence.min_duration_ms),
                key="-MIN-SILENCE-MS-",
                size=(10, 1),
            ),
        ],
        [sg.HorizontalSeparator()],
        # フィラー検知設定
        [sg.Text("フィラー検知", font=("", 12, "bold"))],
        [
            sg.Text("モデル:", size=(15, 1)),
            sg.Combo(
                WHISPER_MODELS,
                default_value=config.filler.model_name,
                key="-MODEL-NAME-",
                size=(15, 1),
                readonly=True,
            ),
        ],
        [
            sg.Text("言語:", size=(15, 1)),
            sg.Combo(
                [lang[0] for lang in LANGUAGES],
                default_value=default_lang,
                key="-LANGUAGE-",
                size=(15, 1),
                readonly=True,
            ),
        ],
        [
            sg.Text("デバイス:", size=(15, 1)),
            sg.Combo(
                DEVICES,
                default_value=config.filler.device,
                key="-DEVICE-",
                size=(15, 1),
                readonly=True,
            ),
        ],
        [sg.HorizontalSeparator()],
        # マージン設定
        [sg.Text("マージン", font=("", 12, "bold"))],
        [
            sg.Text("前マージン (ms):", size=(15, 1)),
            sg.Input(
                default_text=str(config.margin.before_ms),
                key="-MARGIN-BEFORE-",
                size=(10, 1),
            ),
            sg.Text("後マージン (ms):"),
            sg.Input(
                default_text=str(config.margin.after_ms),
                key="-MARGIN-AFTER-",
                size=(10, 1),
            ),
        ],
        [sg.HorizontalSeparator()],
        # 一般設定
        [sg.Text("一般", font=("", 12, "bold"))],
        [
            sg.Text("FPS:", size=(15, 1)),
            sg.Input(
                default_text=str(config.fps),
                key="-FPS-",
                size=(10, 1),
            ),
            sg.Text("最小保持時間 (ms):"),
            sg.Input(
                default_text=str(config.min_keep_duration_ms),
                key="-MIN-KEEP-MS-",
                size=(10, 1),
            ),
        ],
        [sg.VPush()],
        [
            sg.Push(),
            sg.Button("デフォルトに戻す", key=EVENT_LOAD_DEFAULTS, size=(15, 1)),
            sg.Button("設定を保存", key=EVENT_SAVE_SETTINGS, size=(15, 1)),
            sg.Push(),
        ],
    ]


def create_results_tab() -> list[list[sg.Element]]:
    """結果タブのレイアウトを作成"""
    return [
        [sg.Text("処理結果", font=("", 12, "bold"))],
        [sg.HorizontalSeparator()],
        # サマリー
        [
            sg.Frame(
                "サマリー",
                [
                    [
                        sg.Text("総時間:", size=(10, 1)),
                        sg.Text("--:--", key="-TOTAL-DURATION-", size=(10, 1)),
                        sg.Text("削減時間:", size=(10, 1)),
                        sg.Text("--:--", key="-CUT-DURATION-", size=(10, 1)),
                        sg.Text("削減率:", size=(8, 1)),
                        sg.Text("--%", key="-CUT-RATIO-", size=(8, 1)),
                    ],
                    [
                        sg.Text("無音区間:", size=(10, 1)),
                        sg.Text("0", key="-SILENCE-COUNT-", size=(10, 1)),
                        sg.Text("フィラー:", size=(10, 1)),
                        sg.Text("0", key="-FILLER-COUNT-", size=(10, 1)),
                        sg.Text("保持区間:", size=(8, 1)),
                        sg.Text("0", key="-KEEP-COUNT-", size=(8, 1)),
                    ],
                ],
                expand_x=True,
            )
        ],
        [sg.HorizontalSeparator()],
        # セグメント一覧
        [sg.Text("検出セグメント", font=("", 11, "bold"))],
        [
            sg.Table(
                values=[],
                headings=SEGMENT_TABLE_HEADINGS,
                col_widths=SEGMENT_TABLE_COL_WIDTHS,
                auto_size_columns=False,
                justification="left",
                num_rows=15,
                key="-SEGMENT-TABLE-",
                enable_events=True,
                expand_x=True,
                expand_y=True,
            )
        ],
    ]


def create_main_window(config: AppConfig) -> sg.Window:
    """メインウィンドウを作成"""
    sg.theme("SystemDefault")

    tab_group = sg.TabGroup(
        [
            [
                sg.Tab("処理", create_process_tab(config), key="-TAB-PROCESS-"),
                sg.Tab("設定", create_settings_tab(config), key="-TAB-SETTINGS-"),
                sg.Tab("結果", create_results_tab(), key="-TAB-RESULTS-"),
            ]
        ],
        key="-TAB-GROUP-",
        expand_x=True,
        expand_y=True,
    )

    layout = [
        [tab_group],
        [
            sg.Text("Ready", key="-FOOTER-STATUS-", size=(50, 1)),
            sg.Push(),
            sg.Text("v0.1.0", font=("", 9), text_color="gray"),
        ],
    ]

    return sg.Window(
        WINDOW_TITLE,
        layout,
        size=WINDOW_SIZE,
        finalize=True,
        resizable=True,
    )
