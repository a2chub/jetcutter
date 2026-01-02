"""
process_tab - 処理タブ

動画ファイル選択、出力モード、進捗表示のUI要素を配置。
Apple Human Interface Guidelines準拠。
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
    NSBox,
    NSBoxSeparator,
    NSControlStateValueOn,
)
from Foundation import NSMakeRect

# Apple HIG準拠の定数
MARGIN = 20
SECTION_SPACING = 24
ITEM_SPACING = 12
LABEL_HEIGHT = 17
FIELD_HEIGHT = 22
BUTTON_HEIGHT = 32
LABEL_WIDTH = 100


def create_section_label(text: str, x: float, y: float, width: float) -> NSTextField:
    """セクション見出しラベルを作成（太字・大きめ）"""
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 17))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setFont_(NSFont.boldSystemFontOfSize_(13))
    label.setTextColor_(NSColor.labelColor())
    return label


def create_label(text: str, x: float, y: float, width: float) -> NSTextField:
    """通常ラベルを作成"""
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, LABEL_HEIGHT))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setFont_(NSFont.systemFontOfSize_(13))
    label.setTextColor_(NSColor.labelColor())
    return label


def create_hint_label(text: str, x: float, y: float, width: float) -> NSTextField:
    """ヒントラベルを作成（小さめ・グレー）"""
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 14))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setFont_(NSFont.systemFontOfSize_(11))
    label.setTextColor_(NSColor.secondaryLabelColor())
    return label


def create_text_field(x: float, y: float, width: float, placeholder: str = "") -> NSTextField:
    """テキスト入力フィールドを作成"""
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, FIELD_HEIGHT))
    field.setPlaceholderString_(placeholder)
    field.setFont_(NSFont.systemFontOfSize_(13))
    return field


def create_button(title: str, x: float, y: float, width: float = 90, primary: bool = False) -> NSButton:
    """ボタンを作成"""
    button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, width, BUTTON_HEIGHT))
    button.setTitle_(title)
    button.setBezelStyle_(NSBezelStyleRounded)
    button.setFont_(NSFont.systemFontOfSize_(13))
    if primary:
        button.setKeyEquivalent_("\r")  # Enterキーで実行
    return button


def create_separator(x: float, y: float, width: float) -> NSBox:
    """区切り線を作成"""
    separator = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, width, 1))
    separator.setBoxType_(NSBoxSeparator)
    return separator


def create_process_tab(width: float, height: float) -> NSView:
    """処理タブを作成"""
    view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

    content_width = width - MARGIN * 2
    y = height - MARGIN - 10

    # ========== 動画ファイルセクション ==========
    label = create_section_label("動画ファイル", MARGIN, y, 200)
    view.addSubview_(label)

    y -= ITEM_SPACING + FIELD_HEIGHT
    field_width = content_width - 100
    file_field = create_text_field(MARGIN, y, field_width, "動画ファイルを選択してください")
    view.addSubview_(file_field)

    browse_btn = create_button("選択...", MARGIN + field_width + 8, y - 5, 84)
    view.addSubview_(browse_btn)

    y -= ITEM_SPACING
    hint_label = create_hint_label("対応形式: MP4, MOV, AVI, MKV, WebM", MARGIN, y, 300)
    view.addSubview_(hint_label)

    # 区切り線
    y -= SECTION_SPACING
    separator1 = create_separator(MARGIN, y, content_width)
    view.addSubview_(separator1)

    # ========== 出力モードセクション ==========
    y -= SECTION_SPACING
    mode_label = create_section_label("出力モード", MARGIN, y, 200)
    view.addSubview_(mode_label)

    y -= ITEM_SPACING + 24
    segment = NSSegmentedControl.alloc().initWithFrame_(NSMakeRect(MARGIN, y, 240, 24))
    segment.setSegmentCount_(2)
    segment.setLabel_forSegment_("Final Cut Pro", 0)
    segment.setLabel_forSegment_("DaVinci Resolve", 1)
    segment.setWidth_forSegment_(115, 0)
    segment.setWidth_forSegment_(115, 1)
    segment.setSelectedSegment_(0)
    segment.setSegmentStyle_(NSSegmentStyleRounded)
    view.addSubview_(segment)

    # 区切り線
    y -= SECTION_SPACING
    separator2 = create_separator(MARGIN, y, content_width)
    view.addSubview_(separator2)

    # ========== 出力設定セクション ==========
    y -= SECTION_SPACING
    output_label = create_section_label("出力設定", MARGIN, y, 200)
    view.addSubview_(output_label)

    # タイムライン名
    y -= ITEM_SPACING + FIELD_HEIGHT
    timeline_label = create_label("タイムライン名:", MARGIN, y + 2, LABEL_WIDTH)
    view.addSubview_(timeline_label)

    timeline_field = create_text_field(MARGIN + LABEL_WIDTH + 8, y, 200, "")
    timeline_field.setStringValue_("JetCut_")
    view.addSubview_(timeline_field)

    # 出力先
    y -= ITEM_SPACING + FIELD_HEIGHT
    output_path_label = create_label("出力先:", MARGIN, y + 2, LABEL_WIDTH)
    view.addSubview_(output_path_label)

    output_field_width = content_width - LABEL_WIDTH - 100
    output_field = create_text_field(MARGIN + LABEL_WIDTH + 8, y, output_field_width, "出力先を選択してください")
    view.addSubview_(output_field)

    output_browse_btn = create_button("選択...", MARGIN + LABEL_WIDTH + output_field_width + 16, y - 5, 84)
    view.addSubview_(output_browse_btn)

    # ========== 進捗セクション ==========
    y -= SECTION_SPACING * 1.5

    # プログレスバー
    progress = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(MARGIN, y, content_width, 4))
    progress.setStyle_(NSProgressIndicatorStyleBar)
    progress.setIndeterminate_(False)
    progress.setMinValue_(0)
    progress.setMaxValue_(100)
    progress.setDoubleValue_(35)
    view.addSubview_(progress)

    # ステータステキスト
    y -= ITEM_SPACING + 4
    status_label = create_hint_label("フィラー検知中... (35%)", MARGIN, y, content_width)
    view.addSubview_(status_label)

    # ========== アクションボタン ==========
    button_y = MARGIN
    button_width = 100

    # キャンセルボタン（左寄り）
    cancel_btn = create_button("キャンセル", MARGIN, button_y, button_width)
    view.addSubview_(cancel_btn)

    # 処理開始ボタン（右寄り、プライマリ）
    start_btn = create_button("処理開始", width - MARGIN - button_width, button_y, button_width, primary=True)
    view.addSubview_(start_btn)

    return view
