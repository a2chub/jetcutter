"""
tabs - タブビュー定義

各タブのUI要素を定義するモジュール。
"""

from jetcutter.gui_mock.tabs.process_tab import create_process_tab
from jetcutter.gui_mock.tabs.settings_tab import create_settings_tab
from jetcutter.gui_mock.tabs.results_tab import create_results_tab

__all__ = ["create_process_tab", "create_settings_tab", "create_results_tab"]
