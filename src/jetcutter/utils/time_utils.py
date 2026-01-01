"""
time_utils - 時間変換ユーティリティ

ミリ秒、フレーム番号、タイムコード間の変換を提供。

使い分けガイドライン:
    - このモジュール（utils/time_utils）:
      アプリケーション全般の時間計算に使用。整数ベースの高速な計算。
      用途: 無音検知、フィラー検知、UI表示など

    - fcp/time_utils:
      Final Cut Pro XML出力専用。Fractionベースの精密な計算。
      用途: FCPXML生成時のみ（フレーム精度が必須）

一般的なルール:
    - 内部処理はミリ秒（int）で統一
    - FCPへのエクスポート時のみ fcp/time_utils を使用
"""

from __future__ import annotations

from dataclasses import dataclass


# 一般的なフレームレート定義
class FrameRates:
    """一般的なフレームレート定数"""

    FPS_23_976 = 23.976
    FPS_24 = 24.0
    FPS_25 = 25.0
    FPS_29_97 = 29.97
    FPS_30 = 30.0
    FPS_50 = 50.0
    FPS_59_94 = 59.94
    FPS_60 = 60.0


@dataclass
class Timecode:
    """SMPTEタイムコードを表すクラス"""

    hours: int
    minutes: int
    seconds: int
    frames: int
    fps: float

    def __str__(self) -> str:
        """HH:MM:SS:FF形式の文字列を返す"""
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}:{self.frames:02d}"

    def to_ms(self) -> int:
        """ミリ秒に変換"""
        total_frames = (
            self.hours * 3600 * self.fps
            + self.minutes * 60 * self.fps
            + self.seconds * self.fps
            + self.frames
        )
        return frames_to_ms(int(total_frames), self.fps)

    @classmethod
    def from_ms(cls, ms: int, fps: float) -> Timecode:
        """ミリ秒から生成"""
        total_frames = ms_to_frames(ms, fps)
        fps_int = int(round(fps))

        frames = total_frames % fps_int
        total_seconds = total_frames // fps_int
        seconds = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60

        return cls(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            frames=frames,
            fps=fps,
        )


def ms_to_frames(ms: int, fps: float) -> int:
    """
    ミリ秒をフレーム番号に変換する

    Args:
        ms: ミリ秒
        fps: フレームレート

    Returns:
        フレーム番号（0始まり）
    """
    return int(ms * fps / 1000)


def frames_to_ms(frames: int, fps: float) -> int:
    """
    フレーム番号をミリ秒に変換する

    Args:
        frames: フレーム番号
        fps: フレームレート

    Returns:
        ミリ秒
    """
    return int(frames * 1000 / fps)


def ms_to_timecode(ms: int, fps: float) -> str:
    """
    ミリ秒をSMPTEタイムコードに変換する

    Args:
        ms: ミリ秒
        fps: フレームレート

    Returns:
        タイムコード文字列（"HH:MM:SS:FF"形式）
    """
    return str(Timecode.from_ms(ms, fps))


def timecode_to_ms(timecode: str, fps: float) -> int:
    """
    SMPTEタイムコードをミリ秒に変換する

    Args:
        timecode: タイムコード文字列（"HH:MM:SS:FF"形式）
        fps: フレームレート

    Returns:
        ミリ秒

    Raises:
        ValueError: タイムコード形式が不正な場合
    """
    parts = timecode.split(":")
    if len(parts) != 4:
        raise ValueError(f"Invalid timecode format: {timecode}")

    try:
        hours, minutes, seconds, frames = map(int, parts)
    except ValueError as e:
        raise ValueError(f"Invalid timecode format: {timecode}") from e

    tc = Timecode(
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        frames=frames,
        fps=fps,
    )
    return tc.to_ms()


def align_ms_to_frame(ms: int, fps: float, mode: str = "round") -> int:
    """
    ミリ秒をフレーム境界にアラインする

    Args:
        ms: ミリ秒
        fps: フレームレート
        mode: アライン方法（"round", "floor", "ceil"）

    Returns:
        フレーム境界にアラインされたミリ秒
    """
    frame_duration_ms = 1000.0 / fps

    if mode == "floor":
        aligned_frame = int(ms / frame_duration_ms)
    elif mode == "ceil":
        aligned_frame = int((ms + frame_duration_ms - 1) / frame_duration_ms)
    else:  # round
        aligned_frame = round(ms / frame_duration_ms)

    return int(aligned_frame * frame_duration_ms)


def get_frame_duration_ms(fps: float) -> float:
    """
    1フレームあたりのミリ秒を取得する

    Args:
        fps: フレームレート

    Returns:
        1フレームあたりのミリ秒
    """
    return 1000.0 / fps


def format_duration(ms: int) -> str:
    """
    ミリ秒を読みやすい形式にフォーマットする

    Args:
        ms: ミリ秒

    Returns:
        フォーマットされた文字列（例: "1:23.456"）
    """
    total_seconds = ms / 1000
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60

    if minutes > 0:
        return f"{minutes}:{seconds:06.3f}"
    return f"{seconds:.3f}s"


def ms_to_seconds(ms: int) -> float:
    """ミリ秒を秒に変換"""
    return ms / 1000.0


def seconds_to_ms(seconds: float) -> int:
    """秒をミリ秒に変換"""
    return int(seconds * 1000)
