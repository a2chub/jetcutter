"""
settings_tab - 設定タブ

無音検知、フィラー検知、マージン、一般設定のUI要素を配置。
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


def create_text_field(x: float, y: float, width: float, value: str = "") -> NSTextField:
    """テキスト入力フィールドを作成"""
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 22))
    field.setStringValue_(value)
    field.setFont_(NSFont.systemFontOfSize_(13))
    return field


def create_button(title: str, x: float, y: float, width: float = 120) -> NSButton:
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

    y = height - 40
    margin = 20
    content_width = width - margin * 2
    label_width = 140

    # 無音検知セクション
    section_label = create_label("無音検知", margin, y, 200, bold=True)
    view.addSubview_(section_label)

    y -= 30
    threshold_label = create_label("しきい値 (dB):", margin, y, label_width)
    view.addSubview_(threshold_label)

    threshold_slider = create_slider(margin + label_width, y, 200, -80, 0, -40)
    view.addSubview_(threshold_slider)

    threshold_value = create_label("-40 dB", margin + label_width + 210, y, 60)
    view.addSubview_(threshold_value)

    y -= 30
    min_silence_label = create_label("最小無音時間 (ms):", margin, y, label_width)
    view.addSubview_(min_silence_label)

    min_silence_field = create_text_field(margin + label_width, y, 80, "300")
    view.addSubview_(min_silence_field)

    # 区切り線
    y -= 25
    separator1 = create_separator(margin, y, content_width)
    view.addSubview_(separator1)

    # フィラー検知セクション
    y -= 30
    filler_label = create_label("フィラー検知", margin, y, 200, bold=True)
    view.addSubview_(filler_label)

    y -= 30
    model_label = create_label("モデル:", margin, y, label_width)
    view.addSubview_(model_label)

    model_popup = create_popup(["tiny", "base", "small", "medium", "large-v3"], margin + label_width, y, 150, 4)
    view.addSubview_(model_popup)

    y -= 30
    lang_label = create_label("言語:", margin, y, label_width)
    view.addSubview_(lang_label)

    lang_popup = create_popup(["日本語", "英語", "中国語", "韓国語"], margin + label_width, y, 150, 0)
    view.addSubview_(lang_popup)

    y -= 30
    device_label = create_label("デバイス:", margin, y, label_width)
    view.addSubview_(device_label)

    device_popup = create_popup(["auto", "cuda", "cpu"], margin + label_width, y, 150, 0)
    view.addSubview_(device_popup)

    # 区切り線
    y -= 25
    separator2 = create_separator(margin, y, content_width)
    view.addSubview_(separator2)

    # マージンセクション
    y -= 30
    margin_section_label = create_label("マージン", margin, y, 200, bold=True)
    view.addSubview_(margin_section_label)

    y -= 30
    before_label = create_label("前マージン (ms):", margin, y, label_width)
    view.addSubview_(before_label)

    before_field = create_text_field(margin + label_width, y, 80, "100")
    view.addSubview_(before_field)

    after_label = create_label("後マージン (ms):", margin + label_width + 100, y, label_width)
    view.addSubview_(after_label)

    after_field = create_text_field(margin + label_width * 2 + 100, y, 80, "100")
    view.addSubview_(after_field)

    # 区切り線
    y -= 25
    separator3 = create_separator(margin, y, content_width)
    view.addSubview_(separator3)

    # 一般セクション
    y -= 30
    general_label = create_label("一般", margin, y, 200, bold=True)
    view.addSubview_(general_label)

    y -= 30
    fps_label = create_label("FPS:", margin, y, label_width)
    view.addSubview_(fps_label)

    fps_field = create_text_field(margin + label_width, y, 80, "29.97")
    view.addSubview_(fps_field)

    min_keep_label = create_label("最小保持時間 (ms):", margin + label_width + 100, y, label_width)
    view.addSubview_(min_keep_label)

    min_keep_field = create_text_field(margin + label_width * 2 + 100, y, 80, "500")
    view.addSubview_(min_keep_field)

    # ボタン（下部中央）
    button_y = 30
    default_btn = create_button("デフォルトに戻す", width / 2 - 140, button_y)
    view.addSubview_(default_btn)

    save_btn = create_button("設定を保存", width / 2 + 20, button_y)
    view.addSubview_(save_btn)

    return view
