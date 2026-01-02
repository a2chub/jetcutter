"""
time_utils - Final Cut Pro time utilities

Frame-accurate time calculations using fractions.Fraction.
Handles conversion between milliseconds, frames, and FCPXML time format.

Note:
    このモジュールはFCPXML出力専用です。
    内部処理には utils/time_utils を使用してください。

    FCP XMLではフレーム境界への正確なアライメントが必要なため、
    Fractionを使用して丸め誤差を防いでいます。

See Also:
    jetcutter.utils.time_utils: アプリケーション全般の時間計算用
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import ClassVar

# Standard frame durations as exact fractions
FRAME_DURATIONS: dict[float, Fraction] = {
    23.976: Fraction(1001, 24000),
    24.0: Fraction(1, 24),
    25.0: Fraction(1, 25),
    29.97: Fraction(1001, 30000),
    30.0: Fraction(1, 30),
    50.0: Fraction(1, 50),
    59.94: Fraction(1001, 60000),
    60.0: Fraction(1, 60),
}


def get_frame_duration(fps: float) -> Fraction:
    """
    Get exact frame duration for given FPS.

    Args:
        fps: Frame rate (e.g., 29.97, 30.0)

    Returns:
        Frame duration as Fraction

    Raises:
        ValueError: If FPS is not supported
    """
    if fps in FRAME_DURATIONS:
        return FRAME_DURATIONS[fps]

    # Round to nearest standard FPS
    closest_fps = min(FRAME_DURATIONS.keys(), key=lambda x: abs(x - fps))
    if abs(closest_fps - fps) < 0.01:
        return FRAME_DURATIONS[closest_fps]

    raise ValueError(
        f"Unsupported FPS: {fps}. Supported rates: {sorted(FRAME_DURATIONS.keys())}"
    )


@dataclass
class FCPTime:
    """
    Represents a time value in FCPXML format.

    Uses Fraction for frame-accurate calculations.
    FCPXML time format: "numerator/denominator s" or "value s"

    Attributes:
        value: Time value in seconds as Fraction
        frame_duration: Duration of one frame as Fraction
    """

    value: Fraction
    frame_duration: Fraction

    # Tolerance for comparing fractions (1 microsecond)
    COMPARISON_TOLERANCE: ClassVar[float] = 1e-6

    def to_fcpxml_string(self) -> str:
        """
        Convert to FCPXML time string format.

        Returns:
            Time string like "1001/30000s" or "5s" for whole seconds

        Note:
            FCPXMLではframe durationの分母と一致させる必要がある場合があるため、
            frame_durationの分母を基準にして出力する。

        Examples:
            >>> fcp_time = FCPTime(Fraction(1001, 30000), Fraction(1001, 30000))
            >>> fcp_time.to_fcpxml_string()
            '1001/30000s'
            >>> fcp_time = FCPTime(Fraction(5, 1), Fraction(1, 30))
            >>> fcp_time.to_fcpxml_string()
            '5s'
        """
        # If value is 0, return "0s"
        if self.value == 0:
            return "0s"

        # If denominator is 1 (whole seconds), use simplified format
        if self.value.denominator == 1:
            return f"{self.value.numerator}s"

        # FCPXMLではframe durationの分母と一致させる
        # frame_duration = 1001/60000 の場合、分母は60000を使用
        target_denominator = self.frame_duration.denominator

        # 値を target_denominator 基準に変換
        # value = n/d -> n * (target_denominator/d) / target_denominator
        # ただしフレーム境界に揃っている場合は整数になる
        numerator = int(self.value * target_denominator)

        return f"{numerator}/{target_denominator}s"

    @classmethod
    def from_ms(cls, ms: int, fps: float) -> FCPTime:
        """
        Create FCPTime from milliseconds, aligned to frame boundaries.

        Args:
            ms: Time in milliseconds
            fps: Frame rate

        Returns:
            FCPTime instance aligned to nearest frame

        Examples:
            >>> fcp_time = FCPTime.from_ms(1000, 30.0)
            >>> fcp_time.value
            Fraction(1, 1)
        """
        frame_duration = get_frame_duration(fps)

        # Convert ms to seconds as Fraction
        seconds = Fraction(ms, 1000)

        # Round to nearest frame boundary
        frames = round(seconds / frame_duration)
        aligned_value = frames * frame_duration

        return cls(value=aligned_value, frame_duration=frame_duration)

    @classmethod
    def from_frames(cls, frames: int, fps: float) -> FCPTime:
        """
        Create FCPTime from frame count.

        Args:
            frames: Number of frames
            fps: Frame rate

        Returns:
            FCPTime instance

        Examples:
            >>> fcp_time = FCPTime.from_frames(30, 30.0)
            >>> fcp_time.value
            Fraction(1, 1)
        """
        frame_duration = get_frame_duration(fps)
        value = frames * frame_duration

        return cls(value=value, frame_duration=frame_duration)

    @classmethod
    def from_seconds(cls, seconds: float, fps: float) -> FCPTime:
        """
        Create FCPTime from seconds, aligned to frame boundaries.

        Args:
            seconds: Time in seconds
            fps: Frame rate

        Returns:
            FCPTime instance aligned to nearest frame
        """
        frame_duration = get_frame_duration(fps)

        # Convert to Fraction and round to frame boundary
        seconds_frac = Fraction(seconds).limit_denominator(1000000)
        frames = round(seconds_frac / frame_duration)
        aligned_value = frames * frame_duration

        return cls(value=aligned_value, frame_duration=frame_duration)

    def to_seconds(self) -> float:
        """
        Convert to seconds as float.

        Returns:
            Time in seconds
        """
        return float(self.value)

    def to_frames(self) -> int:
        """
        Convert to frame count.

        Returns:
            Number of frames (rounded)
        """
        return round(self.value / self.frame_duration)

    def __add__(self, other: FCPTime) -> FCPTime:
        """Add two FCPTime values."""
        if self.frame_duration != other.frame_duration:
            raise ValueError("Cannot add FCPTime values with different frame durations")

        return FCPTime(
            value=self.value + other.value, frame_duration=self.frame_duration
        )

    def __sub__(self, other: FCPTime) -> FCPTime:
        """Subtract two FCPTime values."""
        if self.frame_duration != other.frame_duration:
            raise ValueError(
                "Cannot subtract FCPTime values with different frame durations"
            )

        return FCPTime(
            value=self.value - other.value, frame_duration=self.frame_duration
        )

    def __eq__(self, other: object) -> bool:
        """Compare two FCPTime values for equality."""
        if not isinstance(other, FCPTime):
            return NotImplemented

        return (
            abs(float(self.value - other.value)) < self.COMPARISON_TOLERANCE
            and self.frame_duration == other.frame_duration
        )

    def __lt__(self, other: FCPTime) -> bool:
        """Compare if this time is less than another."""
        return self.value < other.value

    def __le__(self, other: FCPTime) -> bool:
        """Compare if this time is less than or equal to another."""
        return self.value <= other.value

    def __gt__(self, other: FCPTime) -> bool:
        """Compare if this time is greater than another."""
        return self.value > other.value

    def __ge__(self, other: FCPTime) -> bool:
        """Compare if this time is greater than or equal to another."""
        return self.value >= other.value

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"FCPTime({self.to_fcpxml_string()}, {float(self.value):.6f}s)"


def format_frame_duration(fps: float) -> str:
    """
    Get FCPXML-formatted frame duration string for given FPS.

    Args:
        fps: Frame rate

    Returns:
        Frame duration string (e.g., "1001/30000s")

    Examples:
        >>> format_frame_duration(29.97)
        '1001/30000s'
        >>> format_frame_duration(30.0)
        '1/30s'
    """
    frame_duration = get_frame_duration(fps)

    if frame_duration.denominator == 1:
        return f"{frame_duration.numerator}s"

    return f"{frame_duration.numerator}/{frame_duration.denominator}s"
