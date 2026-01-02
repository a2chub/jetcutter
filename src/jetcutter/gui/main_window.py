"""
main_window - メインウィンドウコントローラ

3タブ構成のメインウィンドウを管理。
GUIStateオブザーバとして処理完了時に結果タブへ自動切り替え。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import objc
from AppKit import (
    NSBackingStoreBuffered,
    NSFont,
    NSTabView,
    NSTabViewItem,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSMakeRect, NSObject
from loguru import logger

from jetcutter.gui.tabs.process_tab import ProcessTabController
from jetcutter.gui.tabs.results_tab import ResultsTabController
from jetcutter.gui.tabs.settings_tab import SettingsTabController

if TYPE_CHECKING:
    from jetcutter.core.processor import AudioProcessingResult
    from jetcutter.gui.controllers.processing_controller import ProcessingController
    from jetcutter.gui.controllers.settings_controller import SettingsController
    from jetcutter.gui.models.gui_state import GUIState

# Window dimensions
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 550
MIN_WIDTH = 600
MIN_HEIGHT = 450


class MainWindowController(NSObject):
    """
    メインウィンドウコントローラ

    3タブ構成（処理、設定、結果）のウィンドウを管理。
    GUIStateObserverプロトコルを実装し、処理完了時に結果タブへ自動切り替え。
    """

    # Properties
    _window: NSWindow
    _tab_view: NSTabView
    _gui_state: GUIState
    _settings_controller: SettingsController
    _processing_controller: ProcessingController

    # Tab Controllers
    _process_tab: ProcessTabController
    _settings_tab: SettingsTabController
    _results_tab: ResultsTabController

    @property
    def window(self) -> NSWindow:
        """メインウィンドウを返す"""
        return self._window

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
        self = objc.super(MainWindowController, self).init()
        if self is None:
            return None

        logger.info("Initializing MainWindowController")

        self._gui_state = gui_state
        self._settings_controller = settings_controller
        self._processing_controller = processing_controller

        # Register as observer for result completion
        gui_state.add_observer(self)

        # Create window and tabs
        self._create_window()
        self._create_tabs()

        logger.info("MainWindowController initialized successfully")

        return self

    def dealloc(self):
        """デアロケーション時にオブザーバを解除"""
        if hasattr(self, "_gui_state"):
            self._gui_state.remove_observer(self)
        objc.super(MainWindowController, self).dealloc()

    def _create_window(self) -> None:
        """ウィンドウを作成"""
        logger.debug("Creating main window")

        # Window style mask
        style_mask = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskMiniaturizable
            | NSWindowStyleMaskResizable
        )

        # Create window
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(200, 200, WINDOW_WIDTH, WINDOW_HEIGHT),
            style_mask,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("JetCutter")
        self._window.setMinSize_((MIN_WIDTH, MIN_HEIGHT))

        logger.debug("Window created successfully")

    def _create_tabs(self) -> None:
        """タブビューとタブコントローラを作成"""
        logger.debug("Creating tab view")

        # Create tab view
        self._tab_view = NSTabView.alloc().initWithFrame_(
            NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT - 20)
        )
        self._tab_view.setFont_(NSFont.systemFontOfSize_(13))

        # Create tab controllers
        logger.debug("Creating process tab controller")
        self._process_tab = (
            ProcessTabController.alloc().initWithGUIState_settingsController_processingController_(
                self._gui_state, self._settings_controller, self._processing_controller
            )
        )

        logger.debug("Creating settings tab controller")
        self._settings_tab = (
            SettingsTabController.alloc().initWithSettingsController_(
                self._settings_controller
            )
        )

        logger.debug("Creating results tab controller")
        self._results_tab = ResultsTabController.alloc().initWithGUIState_(
            self._gui_state
        )

        # Add process tab
        process_tab_item = NSTabViewItem.alloc().initWithIdentifier_(
            self._process_tab.identifier
        )
        process_tab_item.setLabel_(self._process_tab.label)
        process_tab_item.setView_(self._process_tab.view)
        self._tab_view.addTabViewItem_(process_tab_item)

        # Add settings tab
        settings_tab_item = NSTabViewItem.alloc().initWithIdentifier_(
            self._settings_tab.identifier
        )
        settings_tab_item.setLabel_(self._settings_tab.label)
        settings_tab_item.setView_(self._settings_tab.view)
        self._tab_view.addTabViewItem_(settings_tab_item)

        # Add results tab
        results_tab_item = NSTabViewItem.alloc().initWithIdentifier_(
            self._results_tab.identifier
        )
        results_tab_item.setLabel_(self._results_tab.label)
        results_tab_item.setView_(self._results_tab.view)
        self._tab_view.addTabViewItem_(results_tab_item)

        # Add tab view to window
        self._window.contentView().addSubview_(self._tab_view)

        logger.debug("Tab view and controllers created successfully")

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
        # MainWindowControllerは処理状態の変化には反応しない
        # 各タブコントローラが個別に処理
        pass

    def on_result_available(self, result: AudioProcessingResult) -> None:
        """
        処理結果が利用可能になった時に呼ばれる（結果タブへ自動切り替え）

        Args:
            result: 処理結果
        """
        logger.info("Result available - switching to results tab")

        # 結果タブに切り替え
        results_tab_index = self._tab_view.indexOfTabViewItemWithIdentifier_(
            self._results_tab.identifier
        )
        if results_tab_index >= 0:
            self._tab_view.selectTabViewItemAtIndex_(results_tab_index)
            logger.debug(f"Switched to results tab (index={results_tab_index})")
        else:
            logger.warning("Results tab not found")

    def on_error(self, message: str) -> None:
        """
        エラーが発生した時に呼ばれる

        Args:
            message: エラーメッセージ
        """
        # エラーは各タブコントローラが個別に処理
        pass
