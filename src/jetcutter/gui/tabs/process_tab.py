"""
process_tab - 処理タブコントローラ

動画ファイル選択、出力モード、進捗表示を担当。
Apple Human Interface Guidelines準拠のUI。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import objc
from AppKit import (
    NSBezelStyleRounded,
    NSBox,
    NSBoxSeparator,
    NSButton,
    NSColor,
    NSFont,
    NSOpenPanel,
    NSProgressIndicator,
    NSProgressIndicatorStyleBar,
    NSSegmentedControl,
    NSSegmentStyleRounded,
    NSTextField,
    NSView,
)
from Foundation import NSMakeRect, NSObject
from loguru import logger

from jetcutter.gui.constants import (
    EDITOR_DAVINCI,
    EDITOR_FCP,
    STAGE_NAMES,
    VIDEO_EXTENSIONS,
)

if TYPE_CHECKING:
    from jetcutter.core.processor import AudioProcessingResult
    from jetcutter.gui.controllers.processing_controller import ProcessingController
    from jetcutter.gui.controllers.settings_controller import SettingsController
    from jetcutter.gui.models.gui_state import GUIState

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


def create_button(
    title: str, x: float, y: float, width: float = 90, primary: bool = False
) -> NSButton:
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


class ProcessTabController(NSObject):
    """
    処理タブコントローラ

    動画選択、出力設定、処理実行、進捗表示を担当。
    GUIStateObserverプロトコルを実装し、処理状態の変更を受け取る。
    """

    # Properties
    _gui_state: GUIState
    _settings_controller: SettingsController
    _processing_controller: ProcessingController
    _view: NSView

    # UI Elements
    _file_field: NSTextField
    _output_field: NSTextField
    _timeline_field: NSTextField
    _segment_control: NSSegmentedControl
    _progress_bar: NSProgressIndicator
    _status_label: NSTextField
    _start_button: NSButton
    _cancel_button: NSButton

    # State
    _is_processing: bool

    @property
    def view(self) -> NSView:
        """タブのルートビューを返す"""
        return self._view

    @property
    def identifier(self) -> str:
        """タブの識別子"""
        return "process"

    @property
    def label(self) -> str:
        """タブのラベル"""
        return "処理"

    def initWithGUIState_settingsController_processingController_(
        self,
        gui_state: GUIState,
        settings_controller: SettingsController,
        processing_controller: ProcessingController,
    ):
        """
        初期化

        Args:
            gui_state: GUIState instance
            settings_controller: SettingsController instance
            processing_controller: ProcessingController instance
        """
        self = objc.super(ProcessTabController, self).init()
        if self is None:
            return None

        self._gui_state = gui_state
        self._settings_controller = settings_controller
        self._processing_controller = processing_controller
        self._is_processing = False

        # Register as observer
        gui_state.add_observer(self)

        # Create view
        self._create_view()

        return self

    def dealloc(self):
        """デアロケーション時にオブザーバを解除"""
        if hasattr(self, "_gui_state"):
            self._gui_state.remove_observer(self)
        objc.super(ProcessTabController, self).dealloc()

    def _create_view(self):
        """ビューを作成（gui_mockのレイアウトを踏襲）"""
        width = 660.0
        height = 510.0
        self._view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

        content_width = width - MARGIN * 2
        y = height - MARGIN - 10

        # ========== 動画ファイルセクション ==========
        label = create_section_label("動画ファイル", MARGIN, y, 200)
        self._view.addSubview_(label)

        y -= ITEM_SPACING + FIELD_HEIGHT
        field_width = content_width - 100
        self._file_field = create_text_field(MARGIN, y, field_width, "動画ファイルを選択してください")
        self._view.addSubview_(self._file_field)

        browse_btn = create_button("選択...", MARGIN + field_width + 8, y - 5, 84)
        browse_btn.setTarget_(self)
        browse_btn.setAction_(b"handleBrowseVideo:")
        self._view.addSubview_(browse_btn)

        y -= ITEM_SPACING
        hint_label = create_hint_label("対応形式: MP4, MOV, AVI, MKV, WebM", MARGIN, y, 300)
        self._view.addSubview_(hint_label)

        # 区切り線
        y -= SECTION_SPACING
        separator1 = create_separator(MARGIN, y, content_width)
        self._view.addSubview_(separator1)

        # ========== 出力モードセクション ==========
        y -= SECTION_SPACING
        mode_label = create_section_label("出力モード", MARGIN, y, 200)
        self._view.addSubview_(mode_label)

        y -= ITEM_SPACING + 24
        self._segment_control = NSSegmentedControl.alloc().initWithFrame_(
            NSMakeRect(MARGIN, y, 240, 24)
        )
        self._segment_control.setSegmentCount_(2)
        self._segment_control.setLabel_forSegment_("Final Cut Pro", 0)
        self._segment_control.setLabel_forSegment_("DaVinci Resolve", 1)
        self._segment_control.setWidth_forSegment_(115, 0)
        self._segment_control.setWidth_forSegment_(115, 1)

        # Set default based on config
        config = self._settings_controller.config
        default_segment = 0 if config.output.default_editor == EDITOR_FCP else 1
        self._segment_control.setSelectedSegment_(default_segment)
        self._segment_control.setSegmentStyle_(NSSegmentStyleRounded)
        self._view.addSubview_(self._segment_control)

        # 区切り線
        y -= SECTION_SPACING
        separator2 = create_separator(MARGIN, y, content_width)
        self._view.addSubview_(separator2)

        # ========== 出力設定セクション ==========
        y -= SECTION_SPACING
        output_label = create_section_label("出力設定", MARGIN, y, 200)
        self._view.addSubview_(output_label)

        # タイムライン名
        y -= ITEM_SPACING + FIELD_HEIGHT
        timeline_label = create_label("タイムライン名:", MARGIN, y + 2, LABEL_WIDTH)
        self._view.addSubview_(timeline_label)

        self._timeline_field = create_text_field(MARGIN + LABEL_WIDTH + 8, y, 200, "")
        self._timeline_field.setStringValue_(config.output.timeline_prefix)
        self._view.addSubview_(self._timeline_field)

        # 出力先
        y -= ITEM_SPACING + FIELD_HEIGHT
        output_path_label = create_label("出力先:", MARGIN, y + 2, LABEL_WIDTH)
        self._view.addSubview_(output_path_label)

        output_field_width = content_width - LABEL_WIDTH - 100
        self._output_field = create_text_field(
            MARGIN + LABEL_WIDTH + 8, y, output_field_width, "出力先を選択してください"
        )
        self._view.addSubview_(self._output_field)

        output_browse_btn = create_button(
            "選択...", MARGIN + LABEL_WIDTH + output_field_width + 16, y - 5, 84
        )
        output_browse_btn.setTarget_(self)
        output_browse_btn.setAction_(b"handleBrowseOutput:")
        self._view.addSubview_(output_browse_btn)

        # ========== 進捗セクション ==========
        y -= SECTION_SPACING * 1.5

        # プログレスバー
        self._progress_bar = NSProgressIndicator.alloc().initWithFrame_(
            NSMakeRect(MARGIN, y, content_width, 4)
        )
        self._progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self._progress_bar.setIndeterminate_(False)
        self._progress_bar.setMinValue_(0)
        self._progress_bar.setMaxValue_(100)
        self._progress_bar.setDoubleValue_(0)
        self._view.addSubview_(self._progress_bar)

        # ステータステキスト
        y -= ITEM_SPACING + 4
        self._status_label = create_hint_label("", MARGIN, y, content_width)
        self._view.addSubview_(self._status_label)

        # ========== アクションボタン ==========
        button_y = MARGIN
        button_width = 100

        # キャンセルボタン（左寄り）
        self._cancel_button = create_button("キャンセル", MARGIN, button_y, button_width)
        self._cancel_button.setTarget_(self)
        self._cancel_button.setAction_(b"handleCancel:")
        self._cancel_button.setHidden_(True)  # Initially hidden
        self._view.addSubview_(self._cancel_button)

        # 処理開始ボタン（右寄り、プライマリ）
        self._start_button = create_button(
            "処理開始", width - MARGIN - button_width, button_y, button_width, primary=True
        )
        self._start_button.setTarget_(self)
        self._start_button.setAction_(b"handleStart:")
        self._view.addSubview_(self._start_button)

    # ========== Button Actions ==========

    def handleBrowseVideo_(self, sender):
        """動画ファイル選択ダイアログ"""
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(False)
        panel.setAllowedFileTypes_(VIDEO_EXTENSIONS)
        panel.setTitle_("動画ファイルを選択")
        panel.setPrompt_("選択")

        if panel.runModal() == 1:  # NSOKButton
            file_path = Path(panel.URLs()[0].path())
            self._file_field.setStringValue_(str(file_path))
            logger.info(f"Selected video: {file_path}")

    def handleBrowseOutput_(self, sender):
        """出力先フォルダ選択ダイアログ"""
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(False)
        panel.setCanChooseDirectories_(True)
        panel.setAllowsMultipleSelection_(False)
        panel.setTitle_("出力先フォルダを選択")
        panel.setPrompt_("選択")

        if panel.runModal() == 1:  # NSOKButton
            folder_path = Path(panel.URLs()[0].path())
            self._output_field.setStringValue_(str(folder_path))
            logger.info(f"Selected output folder: {folder_path}")

    def handleStart_(self, sender):
        """処理開始"""
        # Validate input
        video_path_str = self._file_field.stringValue()
        if not video_path_str:
            self._show_error_alert("動画ファイルを選択してください")
            return

        video_path = Path(video_path_str)
        if not video_path.exists():
            self._show_error_alert(f"ファイルが見つかりません:\n{video_path}")
            return

        # Get output path
        output_path_str = self._output_field.stringValue()
        output_path = Path(output_path_str) if output_path_str else None

        # Determine editor
        selected_segment = self._segment_control.selectedSegment()
        editor = EDITOR_FCP if selected_segment == 0 else EDITOR_DAVINCI

        # Update timeline prefix in config
        timeline_prefix = self._timeline_field.stringValue()
        if timeline_prefix:
            self._settings_controller.update(timeline_prefix=timeline_prefix)

        # Start processing
        logger.info(f"Starting processing: {video_path}, editor={editor}")
        config = self._settings_controller.config
        self._processing_controller.start(
            video_path=video_path,
            config=config,
            output_path=output_path,
            editor=editor,
        )

    def handleCancel_(self, sender):
        """処理キャンセル"""
        logger.info("Cancel button clicked")
        self._processing_controller.cancel()
        self._status_label.setStringValue_("キャンセル中...")

    # ========== GUIStateObserver Protocol ==========

    def on_processing_state_changed(
        self, is_processing: bool, stage: str, progress: int
    ) -> None:
        """
        処理状態が変化した時に呼ばれる

        Args:
            is_processing: 処理中かどうか
            stage: 現在のステージ
            progress: 進捗率（0-100）
        """
        self._is_processing = is_processing

        # Update progress bar
        self._progress_bar.setDoubleValue_(float(progress))

        # Update status text
        if is_processing and stage:
            stage_name = STAGE_NAMES.get(stage, stage)
            self._status_label.setStringValue_(f"{stage_name} ({progress}%)")
        elif not is_processing:
            self._status_label.setStringValue_("")
            self._progress_bar.setDoubleValue_(0.0)

        # Toggle button visibility
        self._start_button.setHidden_(is_processing)
        self._cancel_button.setHidden_(not is_processing)

        logger.debug(f"Processing state: {is_processing}, stage={stage}, progress={progress}")

    def on_result_available(self, result: AudioProcessingResult) -> None:
        """
        処理完了時に呼ばれる

        Args:
            result: 処理結果
        """
        logger.info("Processing completed successfully")
        self._status_label.setStringValue_("処理完了")

        # Show success alert
        self._show_info_alert(
            "処理が完了しました",
            "セグメントの検出とエクスポートが完了しました。\n結果タブで詳細を確認できます。",
        )

    def on_error(self, message: str) -> None:
        """
        エラー発生時に呼ばれる

        Args:
            message: エラーメッセージ
        """
        logger.error(f"Processing error: {message}")
        self._status_label.setStringValue_("エラー")

        # Show error alert
        self._show_error_alert(f"処理中にエラーが発生しました:\n\n{message}")

    # ========== Tab Lifecycle ==========

    def view_will_appear(self) -> None:
        """タブが表示される直前に呼ばれる"""
        pass

    def view_did_appear(self) -> None:
        """タブが表示された直後に呼ばれる"""
        pass

    # ========== Helper Methods ==========

    def _show_error_alert(self, message: str):
        """エラーアラートを表示"""
        from AppKit import NSAlert, NSAlertStyleCritical

        alert = NSAlert.alloc().init()
        alert.setMessageText_("エラー")
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSAlertStyleCritical)
        alert.addButtonWithTitle_("OK")
        alert.runModal()

    def _show_info_alert(self, title: str, message: str):
        """情報アラートを表示"""
        from AppKit import NSAlert, NSAlertStyleInformational

        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSAlertStyleInformational)
        alert.addButtonWithTitle_("OK")
        alert.runModal()
