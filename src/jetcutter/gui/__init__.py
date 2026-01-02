"""
gui - JetCutter macOSネイティブGUIモジュール

PyObjC + AppKitを使用したmacOSネイティブGUI。
"""


def main() -> int:
    """GUIアプリケーションを起動（遅延インポート）"""
    from jetcutter.gui.app import main as _main
    return _main()


__all__ = ["main"]
