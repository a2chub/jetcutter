"""
results_tab - 結果タブ

処理結果のサマリーとセグメント一覧を表示。
Apple Human Interface Guidelines準拠。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import objc
from AppKit import (
    NSBezelBorder,
    NSBox,
    NSBoxSeparator,
    NSColor,
    NSFont,
    NSScrollView,
    NSTableColumn,
    NSTableView,
    NSTextField,
    NSView,
    NSViewHeightSizable,
    NSViewWidthSizable,
)
from Foundation import NSMakeRect, NSObject

if TYPE_CHECKING:
    from jetcutter.core.processor import AudioProcessingResult
    from jetcutter.editor.segment import Segment
    from jetcutter.gui.state import GUIState

from jetcutter.gui.constants import SEGMENT_TYPE_NAMES

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


class SegmentTableDataSource(NSObject):
    """セグメントテーブルのデータソース"""

    def init(self):
        self = objc.super(SegmentTableDataSource, self).init()
        if self is None:
            return None
        self._data = []  # list of (segment, type_label)
        return self

    def setData_(self, data):
        """データを設定

        Args:
            data: list of (Segment, str) tuples
        """
        self._data = list(data)

    def numberOfRowsInTableView_(self, tableView):
        """テーブルの行数を返す"""
        return len(self._data)

    def tableView_objectValueForTableColumn_row_(self, tableView, column, row):
        """指定された行・列の値を返す"""
        if row >= len(self._data):
            return None

        segment, type_label = self._data[row]
        col_id = column.identifier()

        if col_id == "#":
            return str(row + 1)
        elif col_id == "種別":
            return type_label
        elif col_id == "開始":
            return self._format_time(segment.start_ms)
        elif col_id == "終了":
            return self._format_time(segment.end_ms)
        elif col_id == "長さ":
            return self._format_time(segment.duration_ms)
        return None

    @staticmethod
    def _format_time(ms: int) -> str:
        """ミリ秒を MM:SS.SS 形式に変換"""
        total_seconds = ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:05.2f}"


class ResultsTabController(NSObject):
    """結果タブコントローラ"""

    def initWithGUIState_(self, gui_state: GUIState):
        """初期化

        Args:
            gui_state: GUIの状態管理オブジェクト
        """
        self = objc.super(ResultsTabController, self).init()
        if self is None:
            return None

        self._gui_state = gui_state
        self._segments = []

        # UI要素への参照（後で作成）
        self._total_field = None
        self._cut_field = None
        self._ratio_field = None
        self._silence_field = None
        self._filler_field = None
        self._keep_field = None
        self._proc_time_field = None
        self._table_view = None
        self._data_source = None

        # ビューを作成
        self._view = self._create_view()

        # オブザーバとして登録
        gui_state.add_observer(self)

        return self

    @property
    def view(self) -> NSView:
        """タブのルートビューを返す"""
        return self._view

    @property
    def identifier(self) -> str:
        """タブの識別子"""
        return "results"

    @property
    def label(self) -> str:
        """タブのラベル"""
        return "結果"

    def view_will_appear(self) -> None:
        """タブが表示される直前に呼ばれる"""
        pass

    def view_did_appear(self) -> None:
        """タブが表示された直後に呼ばれる"""
        pass

    # GUIStateObserver protocol
    def on_processing_state_changed(
        self, is_processing: bool, stage: str, progress: int
    ) -> None:
        """処理状態が変化した時に呼ばれる"""
        pass

    def on_result_available(self, result: AudioProcessingResult) -> None:
        """処理結果が利用可能になった時に呼ばれる"""
        self._update_summary(result)
        self._update_segment_table(result)

    def on_error(self, message: str) -> None:
        """エラーが発生した時に呼ばれる"""
        pass

    def _create_view(self) -> NSView:
        """結果タブのビューを作成"""
        width = 700
        height = 550
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        # 自動リサイズマスクを設定（タブ切り替え時のイベント処理に必要）
        view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

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
        self._total_field = create_readonly_field(col1_x + label_w, y - 2, field_w, "--")
        view.addSubview_(self._total_field)

        cut_label = create_label("削減時間:", col2_x, y, label_w)
        view.addSubview_(cut_label)
        self._cut_field = create_readonly_field(col2_x + label_w, y - 2, field_w, "--")
        view.addSubview_(self._cut_field)

        ratio_label = create_label("削減率:", col3_x, y, label_w)
        view.addSubview_(ratio_label)
        self._ratio_field = create_readonly_field(col3_x + label_w, y - 2, 60, "--")
        view.addSubview_(self._ratio_field)

        # 行2: 無音区間、フィラー、保持区間
        y -= ROW_HEIGHT + ITEM_SPACING
        silence_label = create_label("無音区間:", col1_x, y, label_w)
        view.addSubview_(silence_label)
        self._silence_field = create_readonly_field(col1_x + label_w, y - 2, 50, "--")
        view.addSubview_(self._silence_field)

        filler_label = create_label("フィラー:", col2_x, y, label_w)
        view.addSubview_(filler_label)
        self._filler_field = create_readonly_field(col2_x + label_w, y - 2, 50, "--")
        view.addSubview_(self._filler_field)

        keep_label = create_label("保持区間:", col3_x, y, label_w)
        view.addSubview_(keep_label)
        self._keep_field = create_readonly_field(col3_x + label_w, y - 2, 50, "--")
        view.addSubview_(self._keep_field)

        # 行3: 処理時間
        y -= ROW_HEIGHT + ITEM_SPACING
        proc_time_label = create_label("処理時間:", col1_x, y, label_w)
        view.addSubview_(proc_time_label)
        self._proc_time_field = create_readonly_field(col1_x + label_w, y - 2, field_w, "--")
        view.addSubview_(self._proc_time_field)

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

        self._table_view = NSTableView.alloc().initWithFrame_(
            NSMakeRect(0, 0, content_width - 20, table_height)
        )
        self._table_view.setUsesAlternatingRowBackgroundColors_(True)
        self._table_view.setGridStyleMask_(1)  # Horizontal grid
        self._table_view.setRowHeight_(22)

        # カラム定義
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
            self._table_view.addTableColumn_(column)

        # データソース設定（強参照を保持してGC防止）
        self._data_source = SegmentTableDataSource.alloc().init()
        self._table_view.setDataSource_(self._data_source)

        scroll_view.setDocumentView_(self._table_view)
        view.addSubview_(scroll_view)

        return view

    def _update_summary(self, result: AudioProcessingResult) -> None:
        """サマリー情報を更新

        Args:
            result: 処理結果
        """
        # 総時間
        total_ms = result.total_duration_ms
        self._total_field.setStringValue_(self._format_time(total_ms))

        # 削減時間と削減率
        cut_ms = sum(
            s.duration_ms for s in result.silence_segments + result.filler_segments
        )
        self._cut_field.setStringValue_(self._format_time(cut_ms))

        ratio = (cut_ms / total_ms * 100) if total_ms > 0 else 0
        self._ratio_field.setStringValue_(f"{ratio:.1f}%")

        # セグメント数
        self._silence_field.setStringValue_(str(len(result.silence_segments)))
        self._filler_field.setStringValue_(str(len(result.filler_segments)))
        self._keep_field.setStringValue_(str(len(result.keep_segments)))

        # 処理時間（GUIStateから取得、存在する場合のみ）
        if hasattr(self._gui_state, "processing_time_sec"):
            processing_time_sec = self._gui_state.processing_time_sec
            if processing_time_sec is not None:
                minutes = int(processing_time_sec // 60)
                seconds = processing_time_sec % 60
                processing_time_str = f"{minutes:02d}:{seconds:05.2f}"
                self._proc_time_field.setStringValue_(processing_time_str)
        # 処理時間が追跡されていない場合は "--" のままにする

    def _update_segment_table(self, result: AudioProcessingResult) -> None:
        """セグメントテーブルを更新

        Args:
            result: 処理結果
        """
        # すべてのセグメントを種別ラベル付きで収集
        segments: list[tuple[Segment, str]] = []

        for s in result.silence_segments:
            segments.append((s, SEGMENT_TYPE_NAMES["SILENCE"]))
        for s in result.filler_segments:
            segments.append((s, SEGMENT_TYPE_NAMES["FILLER"]))
        for s in result.keep_segments:
            segments.append((s, SEGMENT_TYPE_NAMES["KEEP"]))

        # 開始時間でソート
        segments.sort(key=lambda x: x[0].start_ms)

        # データソースを更新
        self._data_source.setData_(segments)

        # テーブルをリロード
        self._table_view.reloadData()

    @staticmethod
    def _format_time(ms: int) -> str:
        """ミリ秒を MM:SS.SS 形式に変換"""
        total_seconds = ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:05.2f}"
