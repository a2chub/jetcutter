"""
results_tab - 結果タブ

処理結果のサマリーとセグメント一覧を表示。
Apple Human Interface Guidelines準拠。
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

# Apple HIG準拠の定数
MARGIN = 20
SECTION_SPACING = 20
ITEM_SPACING = 8
ROW_HEIGHT = 26


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
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 17))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setFont_(NSFont.systemFontOfSize_(13))
    label.setTextColor_(NSColor.labelColor())
    return label


def create_readonly_field(x: float, y: float, width: float, value: str = "") -> NSTextField:
    """読み取り専用フィールドを作成"""
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 22))
    field.setStringValue_(value)
    field.setEditable_(False)
    field.setSelectable_(True)
    field.setFont_(NSFont.monospacedDigitSystemFontOfSize_weight_(13, 0.0))
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

    content_width = width - MARGIN * 2
    y = height - MARGIN - 10

    # ========== 処理結果セクション ==========
    section_label = create_section_label("処理結果", MARGIN, y, 200)
    view.addSubview_(section_label)

    # 区切り線
    y -= 12
    separator1 = create_separator(MARGIN, y, content_width)
    view.addSubview_(separator1)

    # サマリーレイアウト: 3列構成
    y -= SECTION_SPACING + 4

    # 列の位置を計算
    col_width = content_width // 3
    col1_x = MARGIN
    col2_x = MARGIN + col_width
    col3_x = MARGIN + col_width * 2

    label_w = 70
    field_w = 80

    # 行1: 総時間、削減時間、削減率
    total_label = create_label("総時間:", col1_x, y, label_w)
    view.addSubview_(total_label)
    total_field = create_readonly_field(col1_x + label_w, y - 2, field_w, "00:12.52")
    view.addSubview_(total_field)

    cut_label = create_label("削減時間:", col2_x, y, label_w)
    view.addSubview_(cut_label)
    cut_field = create_readonly_field(col2_x + label_w, y - 2, field_w, "00:01.40")
    view.addSubview_(cut_field)

    ratio_label = create_label("削減率:", col3_x, y, label_w)
    view.addSubview_(ratio_label)
    ratio_field = create_readonly_field(col3_x + label_w, y - 2, 60, "11.2%")
    view.addSubview_(ratio_field)

    # 行2: 無音区間、フィラー、保持区間
    y -= ROW_HEIGHT + ITEM_SPACING
    silence_label = create_label("無音区間:", col1_x, y, label_w)
    view.addSubview_(silence_label)
    silence_field = create_readonly_field(col1_x + label_w, y - 2, 50, "3")
    view.addSubview_(silence_field)

    filler_label = create_label("フィラー:", col2_x, y, label_w)
    view.addSubview_(filler_label)
    filler_field = create_readonly_field(col2_x + label_w, y - 2, 50, "2")
    view.addSubview_(filler_field)

    keep_label = create_label("保持区間:", col3_x, y, label_w)
    view.addSubview_(keep_label)
    keep_field = create_readonly_field(col3_x + label_w, y - 2, 50, "4")
    view.addSubview_(keep_field)

    # 行3: 処理時間
    y -= ROW_HEIGHT + ITEM_SPACING
    proc_time_label = create_label("処理時間:", col1_x, y, label_w)
    view.addSubview_(proc_time_label)
    proc_time_field = create_readonly_field(col1_x + label_w, y - 2, field_w, "00:22.35")
    view.addSubview_(proc_time_field)

    # 区切り線
    y -= SECTION_SPACING
    separator2 = create_separator(MARGIN, y, content_width)
    view.addSubview_(separator2)

    # ========== 検出セグメントセクション ==========
    y -= SECTION_SPACING
    segment_label = create_section_label("検出セグメント", MARGIN, y, 200)
    view.addSubview_(segment_label)

    # テーブルビュー
    y -= 8
    table_height = y - MARGIN

    scroll_view = NSScrollView.alloc().initWithFrame_(
        NSMakeRect(MARGIN, MARGIN, content_width, table_height)
    )
    scroll_view.setBorderType_(NSBezelBorder)
    scroll_view.setHasVerticalScroller_(True)
    scroll_view.setHasHorizontalScroller_(False)

    table_view = NSTableView.alloc().initWithFrame_(
        NSMakeRect(0, 0, content_width - 20, table_height)
    )
    table_view.setUsesAlternatingRowBackgroundColors_(True)
    table_view.setGridStyleMask_(1)  # Horizontal grid
    table_view.setRowHeight_(22)

    # カラム定義（幅を調整してバランスを改善）
    columns = [
        ("#", 35),
        ("種別", 70),
        ("開始", 90),
        ("終了", 90),
        ("長さ", 90),
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
    global _data_source_ref
    _data_source_ref = data_source

    return view


# データソース参照を保持するグローバル変数
_data_source_ref = None
