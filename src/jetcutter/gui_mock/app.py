"""
app - macOSネイティブGUIモック アプリケーション

PyObjC + AppKitを使用したmacOSネイティブUIのモック。
見た目確認用で、機能は実装されていない。

使用方法:
    python -m jetcutter.gui_mock.app
"""

from AppKit import NSApplication, NSApp, NSApplicationActivationPolicyRegular
from Foundation import NSObject

from jetcutter.gui_mock.main_window import create_main_window


class AppDelegate(NSObject):
    """アプリケーションデリゲート"""

    def applicationDidFinishLaunching_(self, notification):
        """アプリケーション起動完了時"""
        # メインウィンドウを作成・表示
        self.window = create_main_window()
        self.window.makeKeyAndOrderFront_(None)

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

    # デリゲート設定
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)

    # アプリケーションをアクティブに
    app.activateIgnoringOtherApps_(True)

    # イベントループ開始
    app.run()


if __name__ == "__main__":
    main()
