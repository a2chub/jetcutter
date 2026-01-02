"""
results_tab - 結果タブ

処理結果のサマリーとセグメント一覧を表示。
"""

import objc
from AppKit import (
    NSView,
    NSTextField,
    NSFont,
    NSColor,
    NSBox,
    NSBoxSeparator,
    NSScrollView,
    NSTableView,
    NSTableColumn,
    NSBezelBorder,
)
from Foundation import NSMakeRect, NSObject


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


def create_readonly_field(x: float, y: float, width: float, value: str = "") -> NSTextField:
    """読み取り専用フィールドを作成"""
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 22))
    field.setStringValue_(value)
    field.setEditable_(False)
    field.setSelectable_(True)
    field.setFont_(NSFont.systemFontOfSize_(13))
    field.setBackgroundColor_(NSColor.controlBackgroundColor())
    return field


def create_separator(x: float, y: float, width: float) -> NSBox:
    """区切り線を作成"""
    separator = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, width, 1))
    separator.setBoxType_(NSBoxSeparator)
    return separator


class TableDataSource(NSObject):
    """テーブルデータソース"""

    def init(self):
        self = objc.super(TableDataSource, self).init()
        if self is None:
            return None
        # ダミーデータ
        self.data = [
            ["1", "保持", "00:00.00", "00:02.50", "00:02.50"],
            ["2", "無音", "00:02.50", "00:03.20", "00:00.70"],
            ["3", "保持", "00:03.20", "00:08.40", "00:05.20"],
            ["4", "フィラー", "00:08.40", "00:09.10", "00:00.70"],
            ["5", "保持", "00:09.10", "00:12.50", "00:03.40"],
        ]
        return self

    def numberOfRowsInTableView_(self, tableView):
        return len(self.data)

    def tableView_objectValueForTableColumn_row_(self, tableView, column, row):
        col_id = column.identifier()
        col_map = {"#": 0, "種別": 1, "開始": 2, "終了": 3, "長さ": 4}
        col_idx = col_map.get(col_id, 0)
        return self.data[row][col_idx]


def create_results_tab(width: float, height: float) -> NSView:
    """結果タブを作成"""
    view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

    y = height - 40
    margin = 20
    content_width = width - margin * 2

    # 処理結果セクション
    section_label = create_label("処理結果", margin, y, 200, bold=True)
    view.addSubview_(section_label)

    # 区切り線
    y -= 15
    separator1 = create_separator(margin, y, content_width)
    view.addSubview_(separator1)

    # サマリー行1
    y -= 35
    col1_x = margin
    col2_x = margin + 180
    col3_x = margin + 360

    total_label = create_label("総時間:", col1_x, y, 60)
    view.addSubview_(total_label)
    total_field = create_readonly_field(col1_x + 65, y, 80, "00:12.52")
    view.addSubview_(total_field)

    cut_label = create_label("削減時間:", col2_x, y, 70)
    view.addSubview_(cut_label)
    cut_field = create_readonly_field(col2_x + 75, y, 80, "00:01.40")
    view.addSubview_(cut_field)

    ratio_label = create_label("削減率:", col3_x, y, 60)
    view.addSubview_(ratio_label)
    ratio_field = create_readonly_field(col3_x + 65, y, 60, "11.2%")
    view.addSubview_(ratio_field)

    # サマリー行2
    y -= 30
    silence_label = create_label("無音区間:", col1_x, y, 70)
    view.addSubview_(silence_label)
    silence_field = create_readonly_field(col1_x + 75, y, 50, "3")
    view.addSubview_(silence_field)

    filler_label = create_label("フィラー:", col2_x, y, 60)
    view.addSubview_(filler_label)
    filler_field = create_readonly_field(col2_x + 65, y, 50, "2")
    view.addSubview_(filler_field)

    keep_label = create_label("保持区間:", col3_x, y, 70)
    view.addSubview_(keep_label)
    keep_field = create_readonly_field(col3_x + 75, y, 50, "4")
    view.addSubview_(keep_field)

    # サマリー行3（処理時間）
    y -= 30
    proc_time_label = create_label("処理時間:", col1_x, y, 70)
    view.addSubview_(proc_time_label)
    proc_time_field = create_readonly_field(col1_x + 75, y, 80, "00:22.35")
    view.addSubview_(proc_time_field)

    # 区切り線
    y -= 20
    separator2 = create_separator(margin, y, content_width)
    view.addSubview_(separator2)

    # セグメント一覧セクション
    y -= 30
    segment_label = create_label("検出セグメント", margin, y, 200, bold=True)
    view.addSubview_(segment_label)

    # テーブルビュー
    y -= 10
    table_height = y - 20

    scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(margin, 20, content_width, table_height))
    scroll_view.setBorderType_(NSBezelBorder)
    scroll_view.setHasVerticalScroller_(True)
    scroll_view.setHasHorizontalScroller_(False)

    table_view = NSTableView.alloc().initWithFrame_(NSMakeRect(0, 0, content_width - 20, table_height))
    table_view.setUsesAlternatingRowBackgroundColors_(True)
    table_view.setGridStyleMask_(1)  # Horizontal grid

    # カラム定義
    columns = [
        ("#", 40),
        ("種別", 80),
        ("開始", 100),
        ("終了", 100),
        ("長さ", 100),
    ]

    for col_id, col_width in columns:
        column = NSTableColumn.alloc().initWithIdentifier_(col_id)
        column.setWidth_(col_width)
        column.headerCell().setStringValue_(col_id)
        table_view.addTableColumn_(column)

    # データソース設定
    data_source = TableDataSource.alloc().init()
    table_view.setDataSource_(data_source)

    scroll_view.setDocumentView_(table_view)
    view.addSubview_(scroll_view)

    # データソースを保持（ガベージコレクション防止）
    view._data_source = data_source

    return view
