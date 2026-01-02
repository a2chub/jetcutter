"""
process_tab - 処理タブ

動画ファイル選択、出力モード、進捗表示のUI要素を配置。
"""

from AppKit import (
    NSView,
    NSTextField,
    NSButton,
    NSSegmentedControl,
    NSProgressIndicator,
    NSFont,
    NSColor,
    NSBezelStyleRounded,
    NSProgressIndicatorStyleBar,
    NSSegmentStyleRounded,
    NSTextFieldCell,
    NSBox,
    NSBoxSeparator,
)
from Foundation import NSMakeRect


def create_label(text: str, x: float, y: float, width: float, bold: bool = False) -> NSTextField:
    """ラベルを作成"""
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 20))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    if bold:
        label.setFont_(NSFont.boldSystemFontOfSize_(13))
    else:
        label.setFont_(NSFont.systemFontOfSize_(13))
    return label


def create_text_field(x: float, y: float, width: float, placeholder: str = "") -> NSTextField:
    """テキスト入力フィールドを作成"""
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 22))
    field.setPlaceholderString_(placeholder)
    field.setFont_(NSFont.systemFontOfSize_(13))
    return field


def create_button(title: str, x: float, y: float, width: float = 80) -> NSButton:
    """ボタンを作成"""
    button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, width, 32))
    button.setTitle_(title)
    button.setBezelStyle_(NSBezelStyleRounded)
    button.setFont_(NSFont.systemFontOfSize_(13))
    return button


def create_separator(x: float, y: float, width: float) -> NSBox:
    """区切り線を作成"""
    separator = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, width, 1))
    separator.setBoxType_(NSBoxSeparator)
    return separator


def create_process_tab(width: float, height: float) -> NSView:
    """処理タブを作成"""
    view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

    y = height - 40
    margin = 20
    content_width = width - margin * 2

    # 動画ファイルセクション
    label = create_label("動画ファイル", margin, y, 200, bold=True)
    view.addSubview_(label)

    y -= 30
    file_field = create_text_field(margin, y, content_width - 90, "動画ファイルを選択...")
    view.addSubview_(file_field)

    browse_btn = create_button("参照...", width - margin - 80, y - 5)
    view.addSubview_(browse_btn)

    y -= 20
    hint_label = create_label("対応形式: .mp4, .mov, .avi, .mkv, .webm", margin, y, 300)
    hint_label.setTextColor_(NSColor.secondaryLabelColor())
    hint_label.setFont_(NSFont.systemFontOfSize_(11))
    view.addSubview_(hint_label)

    # 区切り線
    y -= 20
    separator1 = create_separator(margin, y, content_width)
    view.addSubview_(separator1)

    # 出力モードセクション
    y -= 30
    mode_label = create_label("出力モード", margin, y, 200, bold=True)
    view.addSubview_(mode_label)

    y -= 35
    segment = NSSegmentedControl.alloc().initWithFrame_(NSMakeRect(margin, y, 200, 24))
    segment.setSegmentCount_(2)
    segment.setLabel_forSegment_("FCPX", 0)
    segment.setLabel_forSegment_("DR", 1)
    segment.setWidth_forSegment_(95, 0)
    segment.setWidth_forSegment_(95, 1)
    segment.setSelectedSegment_(0)
    segment.setSegmentStyle_(NSSegmentStyleRounded)
    view.addSubview_(segment)

    # 区切り線
    y -= 25
    separator2 = create_separator(margin, y, content_width)
    view.addSubview_(separator2)

    # 出力設定セクション
    y -= 30
    output_label = create_label("出力設定", margin, y, 200, bold=True)
    view.addSubview_(output_label)

    y -= 30
    timeline_label = create_label("タイムライン名:", margin, y, 100)
    view.addSubview_(timeline_label)

    timeline_field = create_text_field(margin + 110, y, 200, "JetCut_")
    timeline_field.setStringValue_("JetCut_")
    view.addSubview_(timeline_field)

    y -= 30
    output_path_label = create_label("出力先 (FCP):", margin, y, 100)
    view.addSubview_(output_path_label)

    output_field = create_text_field(margin + 110, y, content_width - 200, "出力先を選択...")
    view.addSubview_(output_field)

    output_browse_btn = create_button("参照...", width - margin - 80, y - 5)
    view.addSubview_(output_browse_btn)

    # 区切り線
    y -= 30
    separator3 = create_separator(margin, y, content_width)
    view.addSubview_(separator3)

    # プログレスバー
    y -= 35
    progress = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(margin, y, content_width, 20))
    progress.setStyle_(NSProgressIndicatorStyleBar)
    progress.setIndeterminate_(False)
    progress.setMinValue_(0)
    progress.setMaxValue_(100)
    progress.setDoubleValue_(35)  # ダミー値
    view.addSubview_(progress)

    # ステータステキスト
    y -= 25
    status_label = create_label("フィラー検知中...", margin, y, content_width)
    status_label.setTextColor_(NSColor.secondaryLabelColor())
    view.addSubview_(status_label)

    # ボタン（下部中央）
    button_y = 30
    start_btn = create_button("処理開始", width / 2 - 90, button_y, 100)
    view.addSubview_(start_btn)

    cancel_btn = create_button("キャンセル", width / 2 + 10, button_y, 100)
    view.addSubview_(cancel_btn)

    return view
