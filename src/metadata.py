"""Generate metadata for puzzle video run."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def generate_metadata(
    puzzle_data: Any,
    run_date: str,
    output_path: Path,
    video_path: Path,
    frame_count: int,
) -> dict[str, Any]:
    """
    Generate metadata for the video generation run.

    Args:
        puzzle_data: Normalized puzzle data
        run_date: Date of the run (YYYY-MM-DD)
        output_path: Path to save metadata JSON
        video_path: Path to the generated video
        frame_count: Number of frames rendered

    Returns:
        Metadata dictionary
    """
    logger.info("Generating metadata", extra={"step": "metadata"})

    metadata = {
        "run_date": run_date,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "puzzle": puzzle_data.to_dict(),
        "video": {
            "path": str(video_path),
            "frame_count": frame_count,
        },
        "milestone": 1,
    }

    # Save metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(
        "Metadata saved",
        extra={"step": "metadata", "path": str(output_path)}
    )

    return metadata
