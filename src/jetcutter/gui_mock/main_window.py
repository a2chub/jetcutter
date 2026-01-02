"""
main_window - メインウィンドウ定義

3タブ構成のメインウィンドウを作成。
"""

from AppKit import (
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSBackingStoreBuffered,
    NSTabView,
    NSTabViewItem,
    NSFont,
)
from Foundation import NSMakeRect

from jetcutter.gui_mock.tabs import (
    create_process_tab,
    create_settings_tab,
    create_results_tab,
)


WINDOW_WIDTH = 700
WINDOW_HEIGHT = 550


def create_main_window() -> NSWindow:
    """メインウィンドウを作成"""
    # ウィンドウスタイル
    style_mask = (
        NSWindowStyleMaskTitled
        | NSWindowStyleMaskClosable
        | NSWindowStyleMaskMiniaturizable
        | NSWindowStyleMaskResizable
    )

    # ウィンドウ作成
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(200, 200, WINDOW_WIDTH, WINDOW_HEIGHT),
        style_mask,
        NSBackingStoreBuffered,
        False,
    )
    window.setTitle_("JetCutter")
    window.setMinSize_((600, 450))

    # タブビュー作成
    tab_view = NSTabView.alloc().initWithFrame_(
        NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT - 20)
    )
    tab_view.setFont_(NSFont.systemFontOfSize_(13))

    # タブコンテンツサイズ
    tab_content_width = WINDOW_WIDTH - 20
    tab_content_height = WINDOW_HEIGHT - 80

    # 処理タブ
    process_tab_item = NSTabViewItem.alloc().initWithIdentifier_("process")
    process_tab_item.setLabel_("処理")
    process_tab_item.setView_(create_process_tab(tab_content_width, tab_content_height))
    tab_view.addTabViewItem_(process_tab_item)

    # 設定タブ
    settings_tab_item = NSTabViewItem.alloc().initWithIdentifier_("settings")
    settings_tab_item.setLabel_("設定")
    settings_tab_item.setView_(create_settings_tab(tab_content_width, tab_content_height))
    tab_view.addTabViewItem_(settings_tab_item)

    # 結果タブ
    results_tab_item = NSTabViewItem.alloc().initWithIdentifier_("results")
    results_tab_item.setLabel_("結果")
    results_tab_item.setView_(create_results_tab(tab_content_width, tab_content_height))
    tab_view.addTabViewItem_(results_tab_item)

    # コンテンツビューに追加
    window.contentView().addSubview_(tab_view)

    return window
