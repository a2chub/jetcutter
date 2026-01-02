"""
settings_tab - 設定タブコントローラ

無音検知、フィラー検知、マージン、一般設定のUI要素を配置し、
SettingsControllerと連携して設定の読み込み・保存を実装。
Apple Human Interface Guidelines準拠。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import objc
from AppKit import (
    NSAlert,
    NSBezelStyleRounded,
    NSBox,
    NSBoxSeparator,
    NSButton,
    NSColor,
    NSFont,
    NSPopUpButton,
    NSSlider,
    NSTextField,
    NSView,
)
from Foundation import NSMakeRect, NSObject

from jetcutter.gui.constants import (
    DEFAULT_DEVICE,
    DEFAULT_LANGUAGE,
    DEVICES,
    LANGUAGES,
    WHISPER_MODELS,
)

if TYPE_CHECKING:
    from jetcutter.config.settings import AppConfig
    from jetcutter.gui.controllers.settings_controller import SettingsController

# Apple HIG準拠の定数
MARGIN = 20
SECTION_SPACING = 24
ITEM_SPACING = 8
ROW_HEIGHT = 26
LABEL_WIDTH = 130
FIELD_WIDTH = 80
BUTTON_HEIGHT = 32


class SettingsTabController(NSObject):
    """設定タブコントローラ"""

    def initWithSettingsController_(self, settings_controller: SettingsController) -> SettingsTabController:
        """
        初期化

        Args:
            settings_controller: 設定管理コントローラ

        Returns:
            初期化されたインスタンス
        """
        self = objc.super(SettingsTabController, self).init()
        if self is None:
            return None

        self._settings_controller = settings_controller

        # UI要素への参照を保持
        self._threshold_slider: NSSlider | None = None
        self._threshold_value_label: NSTextField | None = None
        self._min_silence_field: NSTextField | None = None
        self._model_popup: NSPopUpButton | None = None
        self._lang_popup: NSPopUpButton | None = None
        self._device_popup: NSPopUpButton | None = None
        self._before_field: NSTextField | None = None
        self._after_field: NSTextField | None = None
        self._fps_field: NSTextField | None = None
        self._min_keep_field: NSTextField | None = None

        # ビューを作成
        self._view = self._create_view()

        # 設定を読み込んでUIに反映
        self.bind_config(settings_controller.config)

        return self

    def view(self) -> NSView:
        """ビューを返す"""
        return self._view

    def _create_view(self) -> NSView:
        """設定タブのビューを作成"""
        # ビューのサイズは親のタブビューで決定されるため、仮のサイズで作成
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 500))

        content_width = 700 - MARGIN * 2
        y = 500 - MARGIN - 10
        field_x = MARGIN + LABEL_WIDTH + 8

        # ========== 無音検知セクション ==========
        section_label = self._create_section_label("無音検知", MARGIN, y, 200)
        view.addSubview_(section_label)

        # しきい値
        y -= ITEM_SPACING + ROW_HEIGHT
        threshold_label = self._create_label("しきい値 (dB):", MARGIN, y + 2, LABEL_WIDTH)
        view.addSubview_(threshold_label)

        self._threshold_slider = self._create_slider(field_x, y, 180, -80, 0, -40)
        self._threshold_slider.setTarget_(self)
        self._threshold_slider.setAction_("handleThresholdSlider:")
        view.addSubview_(self._threshold_slider)

        self._threshold_value_label = self._create_value_label("-40 dB", field_x + 190, y + 2, 60)
        view.addSubview_(self._threshold_value_label)

        # 最小無音時間
        y -= ITEM_SPACING + ROW_HEIGHT
        min_silence_label = self._create_label("最小無音時間:", MARGIN, y + 2, LABEL_WIDTH)
        view.addSubview_(min_silence_label)

        self._min_silence_field = self._create_text_field(field_x, y, FIELD_WIDTH, "300")
        view.addSubview_(self._min_silence_field)

        ms_label = self._create_label("ms", field_x + FIELD_WIDTH + 8, y + 2, 30)
        view.addSubview_(ms_label)

        # 区切り線
        y -= SECTION_SPACING
        separator1 = self._create_separator(MARGIN, y, content_width)
        view.addSubview_(separator1)

        # ========== フィラー検知セクション ==========
        y -= SECTION_SPACING
        filler_label = self._create_section_label("フィラー検知", MARGIN, y, 200)
        view.addSubview_(filler_label)

        # モデル
        y -= ITEM_SPACING + ROW_HEIGHT
        model_label = self._create_label("Whisperモデル:", MARGIN, y + 2, LABEL_WIDTH)
        view.addSubview_(model_label)

        self._model_popup = self._create_popup(WHISPER_MODELS, field_x, y, 140, 4)
        view.addSubview_(self._model_popup)

        # 言語
        y -= ITEM_SPACING + ROW_HEIGHT
        lang_label = self._create_label("言語:", MARGIN, y + 2, LABEL_WIDTH)
        view.addSubview_(lang_label)

        lang_options = list(LANGUAGES.keys())
        self._lang_popup = self._create_popup(lang_options, field_x, y, 140, 0)
        view.addSubview_(self._lang_popup)

        # デバイス
        y -= ITEM_SPACING + ROW_HEIGHT
        device_label = self._create_label("演算デバイス:", MARGIN, y + 2, LABEL_WIDTH)
        view.addSubview_(device_label)

        device_options = list(DEVICES.keys())
        self._device_popup = self._create_popup(device_options, field_x, y, 140, 0)
        view.addSubview_(self._device_popup)

        # 区切り線
        y -= SECTION_SPACING
        separator2 = self._create_separator(MARGIN, y, content_width)
        view.addSubview_(separator2)

        # ========== マージンセクション ==========
        y -= SECTION_SPACING
        margin_section_label = self._create_section_label("セグメントマージン", MARGIN, y, 200)
        view.addSubview_(margin_section_label)

        # マージン行
        y -= ITEM_SPACING + ROW_HEIGHT
        before_label = self._create_label("前:", MARGIN, y + 2, 30)
        view.addSubview_(before_label)

        self._before_field = self._create_text_field(MARGIN + 35, y, 60, "100")
        view.addSubview_(self._before_field)

        ms1_label = self._create_label("ms", MARGIN + 100, y + 2, 30)
        view.addSubview_(ms1_label)

        after_label = self._create_label("後:", MARGIN + 160, y + 2, 30)
        view.addSubview_(after_label)

        self._after_field = self._create_text_field(MARGIN + 195, y, 60, "100")
        view.addSubview_(self._after_field)

        ms2_label = self._create_label("ms", MARGIN + 260, y + 2, 30)
        view.addSubview_(ms2_label)

        # 区切り線
        y -= SECTION_SPACING
        separator3 = self._create_separator(MARGIN, y, content_width)
        view.addSubview_(separator3)

        # ========== 一般セクション ==========
        y -= SECTION_SPACING
        general_label = self._create_section_label("一般", MARGIN, y, 200)
        view.addSubview_(general_label)

        # FPSと最小保持時間
        y -= ITEM_SPACING + ROW_HEIGHT
        fps_label = self._create_label("FPS:", MARGIN, y + 2, 40)
        view.addSubview_(fps_label)

        self._fps_field = self._create_text_field(MARGIN + 45, y, 70, "29.97")
        view.addSubview_(self._fps_field)

        min_keep_label = self._create_label("最小保持時間:", MARGIN + 160, y + 2, 100)
        view.addSubview_(min_keep_label)

        self._min_keep_field = self._create_text_field(MARGIN + 265, y, 60, "500")
        view.addSubview_(self._min_keep_field)

        ms3_label = self._create_label("ms", MARGIN + 330, y + 2, 30)
        view.addSubview_(ms3_label)

        # ========== アクションボタン ==========
        button_y = MARGIN
        button_width = 130

        # デフォルトに戻す（左寄り）
        default_btn = self._create_button("デフォルトに戻す", MARGIN, button_y, button_width)
        default_btn.setTarget_(self)
        default_btn.setAction_("handleResetDefaults:")
        view.addSubview_(default_btn)

        # 設定を保存（右寄り、プライマリ）
        save_btn = self._create_button("設定を保存", 700 - MARGIN - button_width, button_y, button_width, primary=True)
        save_btn.setTarget_(self)
        save_btn.setAction_("handleSaveSettings:")
        view.addSubview_(save_btn)

        return view

    # ========== アクションハンドラ ==========

    @objc.python_method
    def handleThresholdSlider_(self, sender: NSSlider) -> None:
        """しきい値スライダーのハンドラ"""
        value = sender.doubleValue()
        self._threshold_value_label.setStringValue_(f"{int(value)} dB")

    @objc.python_method
    def handleSaveSettings_(self, sender: NSButton) -> None:
        """設定を保存ボタンのハンドラ"""
        try:
            # UIから値を読み取り
            values = self.read_values()

            # SettingsControllerに反映
            self._settings_controller.update(**values)

            # ファイルに保存
            if self._settings_controller.save():
                self._show_success_alert(
                    "設定を保存しました",
                    f"設定ファイル: {self._settings_controller.config_path}"
                )
            else:
                self._show_error_alert("設定の保存に失敗しました")

        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to save settings: {e}")
            self._show_error_alert(f"設定の保存中にエラーが発生しました:\n{e}")

    @objc.python_method
    def handleResetDefaults_(self, sender: NSButton) -> None:
        """デフォルトに戻すボタンのハンドラ"""
        config = self._settings_controller.reset_to_defaults()
        self.bind_config(config)
        self._show_success_alert("デフォルト設定に戻しました", "")

    # ========== 設定バインディング ==========

    @objc.python_method
    def bind_config(self, config: AppConfig) -> None:
        """
        設定をUIに反映

        Args:
            config: 設定オブジェクト
        """
        # 無音検知
        self._threshold_slider.setDoubleValue_(config.silence.threshold_db)
        self._threshold_value_label.setStringValue_(f"{int(config.silence.threshold_db)} dB")
        self._min_silence_field.setStringValue_(str(config.silence.min_duration_ms))

        # フィラー検知
        # モデル選択
        model_index = self._model_popup.indexOfItemWithTitle_(config.filler.model_name)
        if model_index >= 0:
            self._model_popup.selectItemAtIndex_(model_index)

        # 言語選択（言語コードから表示名に変換）
        lang_display = self._get_language_display(config.filler.language)
        lang_index = self._lang_popup.indexOfItemWithTitle_(lang_display)
        if lang_index >= 0:
            self._lang_popup.selectItemAtIndex_(lang_index)

        # デバイス選択（デバイスコードから表示名に変換）
        device_display = self._get_device_display(config.filler.device)
        device_index = self._device_popup.indexOfItemWithTitle_(device_display)
        if device_index >= 0:
            self._device_popup.selectItemAtIndex_(device_index)

        # マージン
        self._before_field.setStringValue_(str(config.margin.before_ms))
        self._after_field.setStringValue_(str(config.margin.after_ms))

        # 一般
        self._fps_field.setStringValue_(str(config.fps))
        self._min_keep_field.setStringValue_(str(config.min_keep_duration_ms))

    @objc.python_method
    def read_values(self) -> dict:
        """
        UIから値を読み取る

        Returns:
            設定値の辞書
        """
        # 言語とデバイスは表示名からコードに変換
        lang_display = self._lang_popup.titleOfSelectedItem()
        lang_code = LANGUAGES.get(lang_display, "ja")

        device_display = self._device_popup.titleOfSelectedItem()
        device_code = DEVICES.get(device_display, "auto")

        return {
            # 無音検知
            "threshold_db": self._threshold_slider.doubleValue(),
            "min_duration_ms": int(self._min_silence_field.stringValue()),

            # フィラー検知
            "model_name": self._model_popup.titleOfSelectedItem(),
            "language": lang_code,
            "device": device_code,

            # マージン
            "before_ms": int(self._before_field.stringValue()),
            "after_ms": int(self._after_field.stringValue()),

            # 一般
            "fps": float(self._fps_field.stringValue()),
            "min_keep_duration_ms": int(self._min_keep_field.stringValue()),
        }

    # ========== ヘルパーメソッド ==========

    @objc.python_method
    def _get_language_display(self, lang_code: str) -> str:
        """言語コードから表示名を取得"""
        for display, code in LANGUAGES.items():
            if code == lang_code:
                return display
        return DEFAULT_LANGUAGE

    @objc.python_method
    def _get_device_display(self, device_code: str) -> str:
        """デバイスコードから表示名を取得"""
        for display, code in DEVICES.items():
            if code == device_code:
                return display
        return DEFAULT_DEVICE

    @objc.python_method
    def _show_success_alert(self, message: str, info: str = "") -> None:
        """成功アラートを表示"""
        alert = NSAlert.alloc().init()
        alert.setMessageText_(message)
        alert.setInformativeText_(info)
        alert.addButtonWithTitle_("OK")
        alert.runModal()

    @objc.python_method
    def _show_error_alert(self, message: str) -> None:
        """エラーアラートを表示"""
        alert = NSAlert.alloc().init()
        alert.setMessageText_("エラー")
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_("OK")
        alert.runModal()

    # ========== UI要素作成ヘルパー ==========

    @objc.python_method
    def _create_section_label(self, text: str, x: float, y: float, width: float) -> NSTextField:
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

    @objc.python_method
    def _create_label(self, text: str, x: float, y: float, width: float) -> NSTextField:
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

    @objc.python_method
    def _create_value_label(self, text: str, x: float, y: float, width: float) -> NSTextField:
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

    @objc.python_method
    def _create_text_field(self, x: float, y: float, width: float, value: str = "") -> NSTextField:
        """テキスト入力フィールドを作成"""
        field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 22))
        field.setStringValue_(value)
        field.setFont_(NSFont.systemFontOfSize_(13))
        return field

    @objc.python_method
    def _create_button(self, title: str, x: float, y: float, width: float = 120, primary: bool = False) -> NSButton:
        """ボタンを作成"""
        button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, width, BUTTON_HEIGHT))
        button.setTitle_(title)
        button.setBezelStyle_(NSBezelStyleRounded)
        button.setFont_(NSFont.systemFontOfSize_(13))
        if primary:
            button.setKeyEquivalent_("\r")
        return button

    @objc.python_method
    def _create_separator(self, x: float, y: float, width: float) -> NSBox:
        """区切り線を作成"""
        separator = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, width, 1))
        separator.setBoxType_(NSBoxSeparator)
        return separator

    @objc.python_method
    def _create_popup(self, items: list, x: float, y: float, width: float, selected: int = 0) -> NSPopUpButton:
        """ポップアップボタン（ドロップダウン）を作成"""
        popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(x, y, width, 26), False)
        popup.removeAllItems()
        for item in items:
            popup.addItemWithTitle_(item)
        if 0 <= selected < len(items):
            popup.selectItemAtIndex_(selected)
        return popup

    @objc.python_method
    def _create_slider(self, x: float, y: float, width: float, min_val: float, max_val: float, value: float) -> NSSlider:
        """スライダーを作成"""
        slider = NSSlider.alloc().initWithFrame_(NSMakeRect(x, y, width, 20))
        slider.setMinValue_(min_val)
        slider.setMaxValue_(max_val)
        slider.setDoubleValue_(value)
        slider.setContinuous_(True)
        return slider
