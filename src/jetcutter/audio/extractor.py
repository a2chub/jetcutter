"""
extractor - 音声抽出モジュール

ffmpeg-pythonを使用して動画ファイルから音声を抽出する。
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from jetcutter.utils.file_utils import ensure_directory, temporary_file, validate_input_file
from jetcutter.utils.logger import get_logger

logger = get_logger(__name__)


class AudioExtractionError(Exception):
    """音声抽出エラー"""

    pass


class AudioExtractor:
    """
    動画ファイルから音声を抽出するクラス

    ffmpegを使用してWAV形式で音声を抽出する。
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> None:
        """
        Args:
            sample_rate: 出力音声のサンプルレート（Hz）。Whisper用に16000推奨
            channels: 出力音声のチャンネル数。1（モノラル）推奨
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """ffmpegがインストールされているか確認"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
            )
        except FileNotFoundError as e:
            raise AudioExtractionError(
                "ffmpeg is not installed. Please install ffmpeg first."
            ) from e
        except subprocess.CalledProcessError as e:
            raise AudioExtractionError(f"ffmpeg check failed: {e}") from e

    def extract(
        self,
        video_path: str | Path,
        output_path: str | Path | None = None,
    ) -> Path:
        """
        動画から音声を抽出する

        Args:
            video_path: 入力動画ファイルのパス
            output_path: 出力音声ファイルのパス（省略時は入力と同じディレクトリに.wav）

        Returns:
            抽出された音声ファイルのパス

        Raises:
            AudioExtractionError: 抽出に失敗した場合
        """
        video_path = validate_input_file(video_path)

        if output_path is None:
            output_path = video_path.with_suffix(".wav")
        else:
            output_path = Path(output_path)
            ensure_directory(output_path.parent)

        logger.info(f"Extracting audio from {video_path.name}")

        try:
            self._run_ffmpeg(video_path, output_path)
        except subprocess.CalledProcessError as e:
            raise AudioExtractionError(
                f"Audio extraction failed: {e.stderr.decode() if e.stderr else str(e)}"
            ) from e

        if not output_path.exists():
            raise AudioExtractionError(f"Output file was not created: {output_path}")

        logger.info(f"Audio extracted to {output_path.name}")
        return output_path

    def _run_ffmpeg(self, input_path: Path, output_path: Path) -> None:
        """ffmpegを実行して音声を抽出"""
        cmd = [
            "ffmpeg",
            "-y",  # 上書き確認なし
            "-i",
            str(input_path),
            "-vn",  # 映像なし
            "-acodec",
            "pcm_s16le",  # 16bit PCM
            "-ar",
            str(self.sample_rate),
            "-ac",
            str(self.channels),
            str(output_path),
        ]

        logger.debug(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            check=True,
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                cmd,
                result.stdout,
                result.stderr,
            )

    def extract_to_temp(self, video_path: str | Path) -> Path:
        """
        動画から音声を抽出して一時ファイルに保存

        注意: 返されたPathは呼び出し側で削除する必要がある

        Args:
            video_path: 入力動画ファイルのパス

        Returns:
            一時音声ファイルのパス
        """
        video_path = validate_input_file(video_path)

        # 一時ファイルを作成（削除しない）
        with temporary_file(suffix=".wav", delete=False) as temp_path:
            return self.extract(video_path, temp_path)

    def get_audio_info(self, file_path: str | Path) -> dict[str, Any]:
        """
        音声/動画ファイルの情報を取得

        Args:
            file_path: ファイルパス

        Returns:
            ファイル情報の辞書（duration, sample_rate, channels等）
        """
        file_path = Path(file_path)

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            import json

            data = json.loads(result.stdout)

            # 音声ストリームを探す
            audio_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break

            format_info = data.get("format", {})

            return {
                "duration_ms": int(float(format_info.get("duration", 0)) * 1000),
                "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
                "channels": audio_stream.get("channels", 0) if audio_stream else 0,
                "codec": audio_stream.get("codec_name", "") if audio_stream else "",
                "bit_rate": int(format_info.get("bit_rate", 0)),
            }
        except (subprocess.CalledProcessError, KeyError, ValueError) as e:
            logger.warning(f"Failed to get audio info: {e}")
            return {}

    def get_video_info(self, file_path: str | Path) -> dict[str, Any]:
        """
        動画ファイルの情報を取得（FPS、解像度、タイムコード等）

        Args:
            file_path: ファイルパス

        Returns:
            ファイル情報の辞書（fps, width, height, duration_ms, timecode_start_ms等）
        """
        file_path = Path(file_path)

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            import json

            data = json.loads(result.stdout)

            # 動画ストリームを探す
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            format_info = data.get("format", {})

            # FPSを解析（例: "60000/1001" → 59.94）
            fps = 29.97  # デフォルト
            if video_stream:
                r_frame_rate = video_stream.get("r_frame_rate", "30/1")
                if "/" in r_frame_rate:
                    num, den = r_frame_rate.split("/")
                    if int(den) != 0:
                        fps = int(num) / int(den)
                else:
                    fps = float(r_frame_rate)

            # タイムコードを解析（例: "10:09:11;27" → ミリ秒）
            timecode_start_ms = 0
            timecode_str = None

            # format tagsからタイムコードを取得
            format_tags = format_info.get("tags", {})
            if "timecode" in format_tags:
                timecode_str = format_tags["timecode"]

            # または stream tagsから取得
            if not timecode_str and video_stream:
                stream_tags = video_stream.get("tags", {})
                if "timecode" in stream_tags:
                    timecode_str = stream_tags["timecode"]

            if timecode_str:
                timecode_start_ms = self._parse_timecode(timecode_str, fps)
                logger.debug(f"Parsed timecode '{timecode_str}' to {timecode_start_ms}ms")

            return {
                "fps": fps,
                "width": int(video_stream.get("width", 1920)) if video_stream else 1920,
                "height": int(video_stream.get("height", 1080)) if video_stream else 1080,
                "duration_ms": int(float(format_info.get("duration", 0)) * 1000),
                "codec": video_stream.get("codec_name", "") if video_stream else "",
                "timecode_start_ms": timecode_start_ms,
            }
        except (subprocess.CalledProcessError, KeyError, ValueError) as e:
            logger.warning(f"Failed to get video info: {e}")
            return {
                "fps": 29.97,
                "width": 1920,
                "height": 1080,
                "duration_ms": 0,
                "codec": "",
                "timecode_start_ms": 0,
            }

    def _parse_timecode(self, timecode: str, fps: float) -> int:
        """
        タイムコード文字列をミリ秒に変換

        Args:
            timecode: タイムコード文字列（例: "10:09:11;27" または "10:09:11:27"）
            fps: フレームレート

        Returns:
            ミリ秒単位の時間
        """
        import re

        # タイムコード形式: HH:MM:SS:FF または HH:MM:SS;FF（ドロップフレーム）
        match = re.match(r"(\d+):(\d+):(\d+)[:;](\d+)", timecode)
        if not match:
            return 0

        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        frames = int(match.group(4))

        # 時間をミリ秒に変換
        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000

        # フレームをミリ秒に変換
        frame_duration_ms = 1000.0 / fps
        total_ms += int(frames * frame_duration_ms)

        return total_ms
