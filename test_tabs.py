#!/usr/bin/env python3
"""NSTabView動作テスト - タブ切り替え問題の診断"""

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyRegular,
    NSBackingStoreBuffered,
    NSColor,
    NSFont,
    NSTabView,
    NSTabViewItem,
    NSTextField,
    NSView,
    NSViewHeightSizable,
    NSViewWidthSizable,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSMakeRect, NSObject
import objc


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        print("App launching...")

        # シンプルなタブビューを作成
        tab_view = NSTabView.alloc().initWithFrame_(NSMakeRect(0, 0, 500, 400))
        tab_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        # タブ1: 赤い背景
        tab1_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 480, 350))
        tab1_view.setWantsLayer_(True)
        tab1_view.layer().setBackgroundColor_(NSColor.redColor().CGColor())

        tab1_item = NSTabViewItem.alloc().initWithIdentifier_("tab1")
        tab1_item.setLabel_("タブ1")
        tab1_item.setView_(tab1_view)
        tab_view.addTabViewItem_(tab1_item)

        # タブ2: 緑の背景
        tab2_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 480, 350))
        tab2_view.setWantsLayer_(True)
        tab2_view.layer().setBackgroundColor_(NSColor.greenColor().CGColor())

        tab2_item = NSTabViewItem.alloc().initWithIdentifier_("tab2")
        tab2_item.setLabel_("タブ2")
        tab2_item.setView_(tab2_view)
        tab_view.addTabViewItem_(tab2_item)

        # タブ3: 青い背景
        tab3_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 480, 350))
        tab3_view.setWantsLayer_(True)
        tab3_view.layer().setBackgroundColor_(NSColor.blueColor().CGColor())

        tab3_item = NSTabViewItem.alloc().initWithIdentifier_("tab3")
        tab3_item.setLabel_("タブ3")
        tab3_item.setView_(tab3_view)
        tab_view.addTabViewItem_(tab3_item)

        # ウィンドウ作成
        style = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskMiniaturizable
            | NSWindowStyleMaskResizable
        )
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(200, 200, 500, 400),
            style,
            NSBackingStoreBuffered,
            False,
        )
        window.setTitle_("Tab Test")
        window.setContentView_(tab_view)
        window.center()
        window.makeKeyAndOrderFront_(None)

        # ウィンドウを保持
        self.window = window
        self.tab_view = tab_view

        print("Window displayed. Try clicking on tabs.")

    def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
        return True


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.activateIgnoringOtherApps_(True)

    print("Starting app...")
    app.run()


if __name__ == "__main__":
    main()
