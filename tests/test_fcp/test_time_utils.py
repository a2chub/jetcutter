"""
Tests for FCP time utilities.
"""

from fractions import Fraction

import pytest

from jetcutter.fcp.time_utils import (
    FRAME_DURATIONS,
    FCPTime,
    format_frame_duration,
    get_frame_duration,
)


class TestGetFrameDuration:
    """Tests for get_frame_duration function."""

    def test_exact_fps_values(self) -> None:
        """Test exact FPS values return correct frame duration."""
        assert get_frame_duration(30.0) == Fraction(1, 30)
        assert get_frame_duration(24.0) == Fraction(1, 24)
        assert get_frame_duration(25.0) == Fraction(1, 25)
        assert get_frame_duration(60.0) == Fraction(1, 60)

    def test_drop_frame_rates(self) -> None:
        """Test drop-frame rates return correct NTSC fractions."""
        assert get_frame_duration(29.97) == Fraction(1001, 30000)
        assert get_frame_duration(23.976) == Fraction(1001, 24000)
        assert get_frame_duration(59.94) == Fraction(1001, 60000)

    def test_close_fps_rounds_to_standard(self) -> None:
        """Test FPS values close to standard rates are matched."""
        # 29.97 with slight variation
        assert get_frame_duration(29.975) == Fraction(1001, 30000)
        assert get_frame_duration(29.965) == Fraction(1001, 30000)

    def test_unsupported_fps_raises_error(self) -> None:
        """Test unsupported FPS raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported FPS"):
            get_frame_duration(15.0)

        with pytest.raises(ValueError, match="Unsupported FPS"):
            get_frame_duration(120.0)


class TestFCPTime:
    """Tests for FCPTime class."""

    def test_from_ms_30fps(self) -> None:
        """Test creating FCPTime from milliseconds at 30fps."""
        fcp_time = FCPTime.from_ms(1000, 30.0)
        assert fcp_time.value == Fraction(1, 1)
        assert fcp_time.frame_duration == Fraction(1, 30)

    def test_from_ms_2997fps(self) -> None:
        """Test creating FCPTime from milliseconds at 29.97fps."""
        fcp_time = FCPTime.from_ms(1000, 29.97)
        # 1 second at 29.97fps ≈ 30 frames
        assert fcp_time.frame_duration == Fraction(1001, 30000)

    def test_from_frames(self) -> None:
        """Test creating FCPTime from frame count."""
        fcp_time = FCPTime.from_frames(30, 30.0)
        assert fcp_time.value == Fraction(1, 1)

        fcp_time = FCPTime.from_frames(60, 30.0)
        assert fcp_time.value == Fraction(2, 1)

    def test_from_seconds(self) -> None:
        """Test creating FCPTime from seconds."""
        fcp_time = FCPTime.from_seconds(2.5, 30.0)
        # 2.5 seconds = 75 frames at 30fps
        assert fcp_time.to_frames() == 75

    def test_to_fcpxml_string_fraction(self) -> None:
        """Test FCPXML string format for fractional time."""
        fcp_time = FCPTime.from_frames(1, 29.97)
        assert fcp_time.to_fcpxml_string() == "1001/30000s"

    def test_to_fcpxml_string_whole_second(self) -> None:
        """Test FCPXML string format for whole seconds."""
        fcp_time = FCPTime.from_frames(30, 30.0)
        assert fcp_time.to_fcpxml_string() == "1s"

        fcp_time = FCPTime.from_frames(150, 30.0)
        assert fcp_time.to_fcpxml_string() == "5s"

    def test_to_seconds(self) -> None:
        """Test conversion to seconds."""
        fcp_time = FCPTime.from_frames(30, 30.0)
        assert fcp_time.to_seconds() == 1.0

    def test_to_frames(self) -> None:
        """Test conversion to frame count."""
        fcp_time = FCPTime.from_ms(2000, 30.0)
        assert fcp_time.to_frames() == 60

    def test_addition(self) -> None:
        """Test adding two FCPTime values."""
        time1 = FCPTime.from_frames(30, 30.0)
        time2 = FCPTime.from_frames(60, 30.0)
        result = time1 + time2
        assert result.to_frames() == 90

    def test_addition_different_fps_raises_error(self) -> None:
        """Test adding FCPTime with different FPS raises error."""
        time1 = FCPTime.from_frames(30, 30.0)
        time2 = FCPTime.from_frames(30, 24.0)
        with pytest.raises(ValueError, match="different frame durations"):
            _ = time1 + time2

    def test_subtraction(self) -> None:
        """Test subtracting two FCPTime values."""
        time1 = FCPTime.from_frames(90, 30.0)
        time2 = FCPTime.from_frames(30, 30.0)
        result = time1 - time2
        assert result.to_frames() == 60

    def test_subtraction_different_fps_raises_error(self) -> None:
        """Test subtracting FCPTime with different FPS raises error."""
        time1 = FCPTime.from_frames(30, 30.0)
        time2 = FCPTime.from_frames(30, 25.0)
        with pytest.raises(ValueError, match="different frame durations"):
            _ = time1 - time2

    def test_equality(self) -> None:
        """Test FCPTime equality comparison."""
        time1 = FCPTime.from_frames(30, 30.0)
        time2 = FCPTime.from_frames(30, 30.0)
        assert time1 == time2

    def test_equality_different_values(self) -> None:
        """Test FCPTime inequality for different values."""
        time1 = FCPTime.from_frames(30, 30.0)
        time2 = FCPTime.from_frames(60, 30.0)
        assert time1 != time2

    def test_comparison_operators(self) -> None:
        """Test FCPTime comparison operators."""
        time1 = FCPTime.from_frames(30, 30.0)
        time2 = FCPTime.from_frames(60, 30.0)

        assert time1 < time2
        assert time1 <= time2
        assert time2 > time1
        assert time2 >= time1
        assert time1 <= time1
        assert time1 >= time1

    def test_repr(self) -> None:
        """Test FCPTime string representation."""
        fcp_time = FCPTime.from_frames(30, 30.0)
        repr_str = repr(fcp_time)
        assert "FCPTime" in repr_str
        assert "1s" in repr_str


class TestFormatFrameDuration:
    """Tests for format_frame_duration function."""

    def test_format_30fps(self) -> None:
        """Test format for 30fps."""
        assert format_frame_duration(30.0) == "1/30s"

    def test_format_2997fps(self) -> None:
        """Test format for 29.97fps (NTSC)."""
        assert format_frame_duration(29.97) == "1001/30000s"

    def test_format_24fps(self) -> None:
        """Test format for 24fps."""
        assert format_frame_duration(24.0) == "1/24s"

    def test_format_5994fps(self) -> None:
        """Test format for 59.94fps."""
        assert format_frame_duration(59.94) == "1001/60000s"
