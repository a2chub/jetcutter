"""
JetCutter - macOS GUI Application Entry Point

Briefcaseでパッケージ化された場合のエントリポイント。
"""

import multiprocessing
import os
import sys


def run():
    """アプリケーションを起動"""
    # macOSパッケージ化アプリでのマルチプロセス対応
    multiprocessing.freeze_support()

    # マルチスレッド数を制限（ctranslate2/faster-whisper対策）
    # これらの環境変数が設定されていないと、内部でマルチプロセスが起動される
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")

    # macOSでは fork を使用
    # spawn はアプリ全体を再実行するため、新しいウィンドウが起動してしまう
    # fork はメモリをコピーするだけなので、アプリは再起動されない
    if sys.platform == "darwin":
        try:
            multiprocessing.set_start_method("fork")
        except RuntimeError:
            pass  # 既に設定済みの場合はスキップ

    from jetcutter.gui.app import main

    main()


if __name__ == "__main__":
    run()
