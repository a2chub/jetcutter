"""
threading - スレッドセーフなユーティリティ

メインスレッドでのUI更新を保証するためのユーティリティ。
PyObjCのperformSelectorOnMainThread_を使用。
"""

import threading
from collections.abc import Callable
from typing import Any

import objc
from Foundation import NSObject, NSThread


class MainThreadDispatcher(NSObject):
    """
    メインスレッドで関数を実行するためのディスパッチャ

    PyObjCのperformSelectorOnMainThread_を使用して、
    バックグラウンドスレッドからUIを安全に更新する。
    """

    def init(self):
        self = objc.super(MainThreadDispatcher, self).init()
        if self is None:
            return None
        self._callbacks: dict[int, Callable[[], Any]] = {}
        self._lock = threading.Lock()
        self._counter = 0
        return self

    def executeCallback_(self, callback_id):
        """メインスレッドで実行されるコールバックハンドラ (Objective-Cセレクタ)"""
        with self._lock:
            callback = self._callbacks.pop(callback_id, None)

        if callback is not None:
            try:
                callback()
            except Exception as e:
                from loguru import logger
                logger.error(f"Error in main thread callback: {e}")


# ディスパッチャのPythonラッパー関数（NSObject外で定義）
def _dispatch_callback(dispatcher: "MainThreadDispatcher", callback: Callable[[], Any]) -> None:
    """
    メインスレッドでコールバックを実行

    Args:
        dispatcher: MainThreadDispatcherインスタンス
        callback: 実行する関数（引数なし）
    """
    if is_main_thread():
        callback()
        return

    # Store callback to prevent GC
    with dispatcher._lock:
        callback_id = dispatcher._counter
        dispatcher._counter += 1
        dispatcher._callbacks[callback_id] = callback

    # Dispatch to main thread
    dispatcher.performSelectorOnMainThread_withObject_waitUntilDone_(
        b"executeCallback:",
        callback_id,
        False,
    )


# Global dispatcher instance
_dispatcher: MainThreadDispatcher | None = None


def get_dispatcher() -> MainThreadDispatcher:
    """グローバルディスパッチャを取得"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = MainThreadDispatcher.alloc().init()
    return _dispatcher


def dispatch_to_main_thread(func: Callable[[], Any]) -> None:
    """
    メインスレッドで関数を実行

    すでにメインスレッドにいる場合は即座に実行。
    バックグラウンドスレッドからの呼び出しの場合はディスパッチ。

    Args:
        func: 実行する関数
    """
    _dispatch_callback(get_dispatcher(), func)


def is_main_thread() -> bool:
    """現在メインスレッドかどうかを返す"""
    return NSThread.isMainThread()
