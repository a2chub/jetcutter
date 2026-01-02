"""
app - JetCutter macOSネイティブGUI アプリケーション

PyObjC + AppKitを使用したmacOSネイティブUIアプリケーション。
"""

from __future__ import annotations

import os
import shutil
import sys

import objc
from AppKit import (
    NSAlert,
    NSApplication,
    NSApplicationActivationPolicyRegular,
    NSBackingStoreBuffered,
    NSMenu,
    NSMenuItem,
    NSTabView,
    NSTabViewItem,
    NSViewHeightSizable,
    NSViewWidthSizable,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSMakeRect, NSObject
from loguru import logger

from jetcutter.gui.constants import (
    TAB_LABELS,
    TAB_PROCESS,
    TAB_RESULTS,
    TAB_SETTINGS,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from jetcutter.gui.controllers.processing_controller import ProcessingController
from jetcutter.gui.controllers.settings_controller import SettingsController
from jetcutter.gui.models.gui_state import GUIState
from jetcutter.gui.tabs import (
    ProcessTabController,
    ResultsTabController,
    SettingsTabController,
)


def check_ffmpeg() -> bool:
    """
    ffmpegがインストールされているか確認

    BriefcaseでバンドルされたアプリはシステムのPATHにアクセスできないため、
    よくあるインストールパスを直接チェックする。

    Returns:
        ffmpegが利用可能ならTrue
    """
    # よくあるffmpegのインストールパス
    common_paths = [
        "/opt/homebrew/bin",  # Homebrew (Apple Silicon)
        "/usr/local/bin",  # Homebrew (Intel) / manual install
        "/usr/bin",  # System
        "/opt/local/bin",  # MacPorts
    ]

    # 現在のPATHに追加
    current_path = os.environ.get("PATH", "")
    additional_paths = [p for p in common_paths if p not in current_path]
    if additional_paths:
        os.environ["PATH"] = current_path + ":" + ":".join(additional_paths)
        logger.debug(f"Extended PATH with: {additional_paths}")

    # ffmpegを検索
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        logger.info(f"Found ffmpeg at: {ffmpeg_path}")
        return True

    # 直接パスをチェック
    for base_path in common_paths:
        ffmpeg_full = os.path.join(base_path, "ffmpeg")
        if os.path.isfile(ffmpeg_full) and os.access(ffmpeg_full, os.X_OK):
            logger.info(f"Found ffmpeg at: {ffmpeg_full}")
            return True

    return False


def show_ffmpeg_error() -> None:
    """ffmpeg未インストールエラーを表示"""
    alert = NSAlert.alloc().init()
    alert.setMessageText_("ffmpegが見つかりません")
    alert.setInformativeText_(
        "JetCutterを使用するには、ffmpegのインストールが必要です。\n\n"
        "Homebrewでインストール:\n"
        "  brew install ffmpeg\n\n"
        "または公式サイトからダウンロード:\n"
        "  https://ffmpeg.org/download.html"
    )
    alert.addButtonWithTitle_("終了")
    alert.runModal()


def create_menu_bar() -> NSMenu:
    """
    メニューバーを作成

    Returns:
        設定済みのNSMenu
    """
    # メインメニュー
    main_menu = NSMenu.alloc().init()

    # アプリケーションメニュー
    app_menu_item = NSMenuItem.alloc().init()
    main_menu.addItem_(app_menu_item)

    app_menu = NSMenu.alloc().init()
    app_menu_item.setSubmenu_(app_menu)

    # About メニュー項目
    about_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        f"About {WINDOW_TITLE}", "showAboutPanel:", ""
    )
    app_menu.addItem_(about_item)

    # セパレータ
    app_menu.addItem_(NSMenuItem.separatorItem())

    # Quit メニュー項目
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        f"Quit {WINDOW_TITLE}", "terminate:", "q"
    )
    app_menu.addItem_(quit_item)

    return main_menu


class JetCutterAppDelegate(NSObject):
    """
    アプリケーションデリゲート

    アプリケーションライフサイクルイベントを処理。
    """

    def init(self):
        """初期化"""
        self = objc.super(JetCutterAppDelegate, self).init()
        if self is None:
            return None

        self.window = None
        self.gui_state = None
        self.settings_controller = None
        self.processing_controller = None
        # タブコントローラへの参照を保持（GC防止）
        self.process_tab = None
        self.settings_tab = None
        self.results_tab = None
        self.tab_view = None
        self.tab_items = []  # NSTabViewItemの参照も保持

        return self

    def applicationDidFinishLaunching_(self, notification) -> None:
        """
        アプリケーション起動完了時

        GUIStateとコントローラーを初期化し、メインウィンドウを表示。
        """
        logger.info("Application launching...")

        try:
            # ffmpegチェック
            if not check_ffmpeg():
                logger.error("ffmpeg not found")
                show_ffmpeg_error()
                NSApplication.sharedApplication().terminate_(None)
                return

            # ========== 共有状態とコントローラの初期化 ==========

            # GUIState: 中央状態管理（Observer + ProgressReporter）
            self.gui_state = GUIState()

            # SettingsController: 設定の読み込み・保存
            self.settings_controller = SettingsController()

            # ProcessingController: バックグラウンド処理
            # gui_stateをProgressReporterとして使用
            self.processing_controller = ProcessingController(reporter=self.gui_state)

            # ========== タブコントローラの作成 ==========
            # 参照を保持してGC防止（重要！）

            # ProcessTabController: 処理タブ
            self.process_tab = ProcessTabController.alloc().initWithGUIState_settingsController_processingController_(
                self.gui_state,
                self.settings_controller,
                self.processing_controller,
            )

            # SettingsTabController: 設定タブ
            self.settings_tab = SettingsTabController.alloc().initWithSettingsController_(
                self.settings_controller
            )

            # ResultsTabController: 結果タブ
            self.results_tab = ResultsTabController.alloc().initWithGUIState_(self.gui_state)

            # ========== NSTabViewの構築 ==========

            # タブビューを作成
            self.tab_view = NSTabView.alloc().initWithFrame_(
                NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
            )
            # 自動リサイズマスクを設定（ウィンドウサイズに追従）
            self.tab_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

            # ProcessTabを追加
            process_tab_item = NSTabViewItem.alloc().initWithIdentifier_(TAB_PROCESS)
            process_tab_item.setLabel_(TAB_LABELS[TAB_PROCESS])
            process_tab_item.setView_(self.process_tab.view)
            self.tab_view.addTabViewItem_(process_tab_item)
            self.tab_items.append(process_tab_item)  # 参照保持

            # SettingsTabを追加
            settings_tab_item = NSTabViewItem.alloc().initWithIdentifier_(TAB_SETTINGS)
            settings_tab_item.setLabel_(TAB_LABELS[TAB_SETTINGS])
            settings_tab_item.setView_(self.settings_tab.view)
            self.tab_view.addTabViewItem_(settings_tab_item)
            self.tab_items.append(settings_tab_item)  # 参照保持

            # ResultsTabを追加
            results_tab_item = NSTabViewItem.alloc().initWithIdentifier_(TAB_RESULTS)
            results_tab_item.setLabel_(TAB_LABELS[TAB_RESULTS])
            results_tab_item.setView_(self.results_tab.view)
            self.tab_view.addTabViewItem_(results_tab_item)
            self.tab_items.append(results_tab_item)  # 参照保持

            # ========== ウィンドウの作成 ==========

            style_mask = (
                NSWindowStyleMaskTitled
                | NSWindowStyleMaskClosable
                | NSWindowStyleMaskMiniaturizable
                | NSWindowStyleMaskResizable
            )

            self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                NSMakeRect(200, 200, WINDOW_WIDTH, WINDOW_HEIGHT),
                style_mask,
                NSBackingStoreBuffered,
                False,
            )
            self.window.setTitle_(WINDOW_TITLE)
            self.window.setContentView_(self.tab_view)
            self.window.setMinSize_((WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT))

            # ウィンドウを中央に配置して表示
            self.window.center()
            self.window.makeKeyAndOrderFront_(None)

            logger.info("Main window created and displayed")

        except Exception as e:
            logger.exception(f"Failed to create main window: {e}")
            import traceback

            traceback.print_exc()

            # エラーダイアログを表示
            alert = NSAlert.alloc().init()
            alert.setMessageText_("起動エラー")
            alert.setInformativeText_(f"アプリケーションの起動に失敗しました:\n\n{e}")
            alert.addButtonWithTitle_("終了")
            alert.runModal()

            NSApplication.sharedApplication().terminate_(None)

    def applicationShouldTerminateAfterLastWindowClosed_(self, sender) -> bool:
        """
        最後のウィンドウが閉じられたら終了

        Returns:
            常にTrue
        """
        return True

    @objc.IBAction
    def showAboutPanel_(self, sender) -> None:
        """
        Aboutダイアログを表示

        アプリケーションのバージョン情報とライセンス情報を表示。
        """
        from jetcutter import __version__

        about_text = f"""JetCutter v{__version__}

DaVinci Resolve / Final Cut Pro 向け
自動編集エージェント

無音区間・フィラー自動検知・削除ツール

Copyright (c) 2024 JetCutter Contributors
Licensed under MIT License

https://github.com/a2chub/jetcutter"""

        alert = NSAlert.alloc().init()
        alert.setMessageText_(f"About {WINDOW_TITLE}")
        alert.setInformativeText_(about_text)
        alert.addButtonWithTitle_("OK")
        alert.runModal()


def main() -> int:
    """
    macOSネイティブGUIアプリケーションのメインエントリポイント

    Returns:
        終了コード
    """
    try:
        logger.info(f"Starting {WINDOW_TITLE}...")

        # アプリケーション初期化
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

        # メニューバー設定
        menu_bar = create_menu_bar()
        app.setMainMenu_(menu_bar)

        # デリゲート設定
        delegate = JetCutterAppDelegate.alloc().init()
        app.setDelegate_(delegate)

        # アプリケーションをアクティブに（フォアグラウンドに）
        app.activateIgnoringOtherApps_(True)

        # イベントループ開始
        logger.info("Starting event loop...")
        app.run()

        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
