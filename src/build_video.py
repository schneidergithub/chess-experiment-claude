"""Build video from frame sequence using FFmpeg."""

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def build_video(
    frames_dir: Path,
    output_path: Path,
    config: dict[str, Any],
) -> None:
    """
    Build MP4 video from frame sequence using FFmpeg.

    Args:
        frames_dir: Directory containing frame_*.png files
        output_path: Path for output video file
        config: Video configuration

    Raises:
        RuntimeError: If FFmpeg command fails
        FileNotFoundError: If FFmpeg is not found
    """
    logger.info("Building video with FFmpeg", extra={"step": "video"})

    # Get configuration
    fps = config["video"]["fps"]
    codec = config["video"]["codec"]
    pixel_format = config["video"]["pixel_format"]
    ffmpeg_cmd = config["paths"]["ffmpeg_command"]

    # Build FFmpeg command
    # Input: frame sequence from frames_dir
    # -framerate: input framerate
    # -i: input pattern
    # -c:v: video codec
    # -pix_fmt: pixel format for compatibility
    # -y: overwrite output file
    cmd = [
        ffmpeg_cmd,
        "-framerate", str(fps),
        "-pattern_type", "glob",
        "-i", str(frames_dir / "frame_*.png"),
        "-c:v", codec,
        "-pix_fmt", pixel_format,
        "-y",
        str(output_path),
    ]

    logger.info(
        "Running FFmpeg",
        extra={"step": "video", "command": " ".join(cmd)}
    )

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(
            "Video created successfully",
            extra={"step": "video", "path": str(output_path)}
        )
        if result.stdout:
            logger.debug("FFmpeg stdout", extra={"output": result.stdout})

    except FileNotFoundError as e:
        logger.error(
            "FFmpeg not found",
            extra={"step": "video", "command": ffmpeg_cmd}
        )
        raise FileNotFoundError(
            f"FFmpeg not found at '{ffmpeg_cmd}'. "
            "Please install FFmpeg or configure the path in config/app.json"
        ) from e

    except subprocess.CalledProcessError as e:
        logger.error(
            "FFmpeg failed",
            extra={
                "step": "video",
                "returncode": e.returncode,
                "stderr": e.stderr,
                "stdout": e.stdout,
            }
        )
        raise RuntimeError(f"FFmpeg failed with code {e.returncode}: {e.stderr}") from e
