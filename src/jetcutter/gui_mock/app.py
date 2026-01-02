"""
app - macOSネイティブGUIモック アプリケーション

PyObjC + AppKitを使用したmacOSネイティブUIのモック。
見た目確認用で、機能は実装されていない。

使用方法:
    python -m jetcutter.gui_mock.app
"""

from AppKit import (
    NSApplication,
    NSApp,
    NSApplicationActivationPolicyRegular,
    NSMenu,
    NSMenuItem,
)
from Foundation import NSObject

from jetcutter.gui_mock.main_window import create_main_window


def create_menu_bar():
    """メニューバーを作成"""
    # メインメニュー
    main_menu = NSMenu.alloc().init()

    # アプリケーションメニュー
    app_menu_item = NSMenuItem.alloc().init()
    main_menu.addItem_(app_menu_item)

    app_menu = NSMenu.alloc().init()
    app_menu_item.setSubmenu_(app_menu)

    # Quit メニュー項目
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Quit JetCutter", "terminate:", "q"
    )
    app_menu.addItem_(quit_item)

    return main_menu


class AppDelegate(NSObject):
    """アプリケーションデリゲート"""

    def applicationDidFinishLaunching_(self, notification):
        """アプリケーション起動完了時"""
        print("Creating main window...")
        try:
            # メインウィンドウを作成・表示
            self.window = create_main_window()
            print(f"Window created: {self.window}")
            self.window.center()  # 画面中央に配置
            print("Window centered")
            self.window.setIsVisible_(True)
            self.window.makeKeyAndOrderFront_(None)
            self.window.orderFrontRegardless()
            print("Window should be visible now")
        except Exception as e:
            print(f"Error creating window: {e}")
            import traceback
            traceback.print_exc()

    def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
        """最後のウィンドウが閉じられたら終了"""
        return True


def main():
    """メインエントリーポイント"""
    print("Starting JetCutter Native GUI Mock...")
    print("This is a visual mockup only - no functionality implemented.")
    print()

    # アプリケーション初期化
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    # メニューバー設定
    menu_bar = create_menu_bar()
    app.setMainMenu_(menu_bar)

    # デリゲート設定
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)

    # アプリケーションをアクティブに（フォアグラウンドに）
    app.activateIgnoringOtherApps_(True)

    print("Starting event loop...")

    # イベントループ開始
    app.run()


if __name__ == "__main__":
    main()
