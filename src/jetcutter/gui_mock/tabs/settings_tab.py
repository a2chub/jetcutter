"""
settings_tab - 設定タブ

無音検知、フィラー検知、マージン、一般設定のUI要素を配置。
Apple Human Interface Guidelines準拠。
"""

from AppKit import (
    NSView,
    NSTextField,
    NSButton,
    NSSlider,
    NSPopUpButton,
    NSFont,
    NSColor,
    NSBezelStyleRounded,
    NSBox,
    NSBoxSeparator,
)
from Foundation import NSMakeRect

# Apple HIG準拠の定数
MARGIN = 20
SECTION_SPACING = 24
ITEM_SPACING = 8
ROW_HEIGHT = 26
LABEL_WIDTH = 130
FIELD_WIDTH = 80
BUTTON_HEIGHT = 32


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
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 17))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setFont_(NSFont.systemFontOfSize_(13))
    label.setTextColor_(NSColor.labelColor())
    return label


def create_value_label(text: str, x: float, y: float, width: float) -> NSTextField:
    """値表示用ラベルを作成（右寄せ可能）"""
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 17))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setFont_(NSFont.monospacedDigitSystemFontOfSize_weight_(13, 0.0))
    label.setTextColor_(NSColor.secondaryLabelColor())
    return label


def create_text_field(x: float, y: float, width: float, value: str = "") -> NSTextField:
    """テキスト入力フィールドを作成"""
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 22))
    field.setStringValue_(value)
    field.setFont_(NSFont.systemFontOfSize_(13))
    return field


def create_button(title: str, x: float, y: float, width: float = 120, primary: bool = False) -> NSButton:
    """ボタンを作成"""
    button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, width, BUTTON_HEIGHT))
    button.setTitle_(title)
    button.setBezelStyle_(NSBezelStyleRounded)
    button.setFont_(NSFont.systemFontOfSize_(13))
    if primary:
        button.setKeyEquivalent_("\r")
    return button


def create_separator(x: float, y: float, width: float) -> NSBox:
    """区切り線を作成"""
    separator = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, width, 1))
    separator.setBoxType_(NSBoxSeparator)
    return separator


def create_popup(items: list, x: float, y: float, width: float, selected: int = 0) -> NSPopUpButton:
    """ポップアップボタン（ドロップダウン）を作成"""
    popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(x, y, width, 26), False)
    popup.removeAllItems()
    for item in items:
        popup.addItemWithTitle_(item)
    popup.selectItemAtIndex_(selected)
    return popup


def create_slider(x: float, y: float, width: float, min_val: float, max_val: float, value: float) -> NSSlider:
    """スライダーを作成"""
    slider = NSSlider.alloc().initWithFrame_(NSMakeRect(x, y, width, 20))
    slider.setMinValue_(min_val)
    slider.setMaxValue_(max_val)
    slider.setDoubleValue_(value)
    slider.setContinuous_(True)
    return slider


def create_settings_tab(width: float, height: float) -> NSView:
    """設定タブを作成"""
    view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

    content_width = width - MARGIN * 2
    y = height - MARGIN - 10
    field_x = MARGIN + LABEL_WIDTH + 8

    # ========== 無音検知セクション ==========
    section_label = create_section_label("無音検知", MARGIN, y, 200)
    view.addSubview_(section_label)

    # しきい値
    y -= ITEM_SPACING + ROW_HEIGHT
    threshold_label = create_label("しきい値 (dB):", MARGIN, y + 2, LABEL_WIDTH)
    view.addSubview_(threshold_label)

    threshold_slider = create_slider(field_x, y, 180, -80, 0, -40)
    view.addSubview_(threshold_slider)

    threshold_value = create_value_label("-40 dB", field_x + 190, y + 2, 60)
    view.addSubview_(threshold_value)

    # 最小無音時間
    y -= ITEM_SPACING + ROW_HEIGHT
    min_silence_label = create_label("最小無音時間:", MARGIN, y + 2, LABEL_WIDTH)
    view.addSubview_(min_silence_label)

    min_silence_field = create_text_field(field_x, y, FIELD_WIDTH, "300")
    view.addSubview_(min_silence_field)

    ms_label = create_label("ms", field_x + FIELD_WIDTH + 8, y + 2, 30)
    view.addSubview_(ms_label)

    # 区切り線
    y -= SECTION_SPACING
    separator1 = create_separator(MARGIN, y, content_width)
    view.addSubview_(separator1)

    # ========== フィラー検知セクション ==========
    y -= SECTION_SPACING
    filler_label = create_section_label("フィラー検知", MARGIN, y, 200)
    view.addSubview_(filler_label)

    # モデル
    y -= ITEM_SPACING + ROW_HEIGHT
    model_label = create_label("Whisperモデル:", MARGIN, y + 2, LABEL_WIDTH)
    view.addSubview_(model_label)

    model_popup = create_popup(
        ["tiny", "base", "small", "medium", "large-v3"],
        field_x, y, 140, 4
    )
    view.addSubview_(model_popup)

    # 言語
    y -= ITEM_SPACING + ROW_HEIGHT
    lang_label = create_label("言語:", MARGIN, y + 2, LABEL_WIDTH)
    view.addSubview_(lang_label)

    lang_popup = create_popup(
        ["日本語", "English", "中文", "한국어"],
        field_x, y, 140, 0
    )
    view.addSubview_(lang_popup)

    # デバイス
    y -= ITEM_SPACING + ROW_HEIGHT
    device_label = create_label("演算デバイス:", MARGIN, y + 2, LABEL_WIDTH)
    view.addSubview_(device_label)

    device_popup = create_popup(["自動", "CUDA (GPU)", "CPU"], field_x, y, 140, 0)
    view.addSubview_(device_popup)

    # 区切り線
    y -= SECTION_SPACING
    separator2 = create_separator(MARGIN, y, content_width)
    view.addSubview_(separator2)

    # ========== マージンセクション ==========
    y -= SECTION_SPACING
    margin_section_label = create_section_label("セグメントマージン", MARGIN, y, 200)
    view.addSubview_(margin_section_label)

    # マージン行
    y -= ITEM_SPACING + ROW_HEIGHT
    before_label = create_label("前:", MARGIN, y + 2, 30)
    view.addSubview_(before_label)

    before_field = create_text_field(MARGIN + 35, y, 60, "100")
    view.addSubview_(before_field)

    ms1_label = create_label("ms", MARGIN + 100, y + 2, 30)
    view.addSubview_(ms1_label)

    after_label = create_label("後:", MARGIN + 160, y + 2, 30)
    view.addSubview_(after_label)

    after_field = create_text_field(MARGIN + 195, y, 60, "100")
    view.addSubview_(after_field)

    ms2_label = create_label("ms", MARGIN + 260, y + 2, 30)
    view.addSubview_(ms2_label)

    # 区切り線
    y -= SECTION_SPACING
    separator3 = create_separator(MARGIN, y, content_width)
    view.addSubview_(separator3)

    # ========== 一般セクション ==========
    y -= SECTION_SPACING
    general_label = create_section_label("一般", MARGIN, y, 200)
    view.addSubview_(general_label)

    # FPSと最小保持時間
    y -= ITEM_SPACING + ROW_HEIGHT
    fps_label = create_label("FPS:", MARGIN, y + 2, 40)
    view.addSubview_(fps_label)

    fps_field = create_text_field(MARGIN + 45, y, 70, "29.97")
    view.addSubview_(fps_field)

    min_keep_label = create_label("最小保持時間:", MARGIN + 160, y + 2, 100)
    view.addSubview_(min_keep_label)

    min_keep_field = create_text_field(MARGIN + 265, y, 60, "500")
    view.addSubview_(min_keep_field)

    ms3_label = create_label("ms", MARGIN + 330, y + 2, 30)
    view.addSubview_(ms3_label)

    # ========== アクションボタン ==========
    button_y = MARGIN
    button_width = 130

    # デフォルトに戻す（左寄り）
    default_btn = create_button("デフォルトに戻す", MARGIN, button_y, button_width)
    view.addSubview_(default_btn)

    # 設定を保存（右寄り、プライマリ）
    save_btn = create_button("設定を保存", width - MARGIN - button_width, button_y, button_width, primary=True)
    view.addSubview_(save_btn)

    return view
