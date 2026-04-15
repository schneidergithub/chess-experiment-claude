"""Fetch daily puzzle from Lichess API."""

import json
import logging
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


def fetch_daily_puzzle(url: str, output_path: Path) -> dict[str, Any]:
    """
    Fetch the daily puzzle from Lichess API.

    Args:
        url: Lichess daily puzzle API URL
        output_path: Path to save raw puzzle JSON

    Returns:
        Parsed JSON response as dictionary

    Raises:
        requests.HTTPError: If the response status is not 200
        ValueError: If the response is not valid JSON
    """
    logger.info("Fetching daily puzzle", extra={"step": "fetch", "url": url})

    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        logger.error(
            "Failed to fetch puzzle",
            extra={
                "step": "fetch",
                "status_code": response.status_code,
                "url": url
            }
        )
        response.raise_for_status()

    try:
        puzzle_data = response.json()
    except json.JSONDecodeError as e:
        logger.error(
            "Invalid JSON response from Lichess API",
            extra={"step": "fetch", "error_message": str(e)}
        )
        raise ValueError(f"Invalid JSON response: {e}") from e

    # Save raw puzzle JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(puzzle_data, f, indent=2, ensure_ascii=False)

    logger.info(
        "Puzzle fetched and saved",
        extra={"step": "fetch", "path": str(output_path)}
    )

    return puzzle_data
