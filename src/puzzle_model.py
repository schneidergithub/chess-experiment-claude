"""Normalize puzzle data from Lichess API response."""

import logging
from typing import Any

import chess

logger = logging.getLogger(__name__)


class PuzzleData:
    """Normalized puzzle data."""

    def __init__(
        self,
        puzzle_id: str,
        rating: int,
        themes: list[str],
        solution: list[str],
        fen: str,
        side_to_move: str,
        last_move: str | None = None,
        initial_ply: int | None = None,
        game_perf: str | None = None,
    ):
        self.puzzle_id = puzzle_id
        self.rating = rating
        self.themes = themes
        self.solution = solution
        self.fen = fen
        self.side_to_move = side_to_move
        self.last_move = last_move
        self.initial_ply = initial_ply
        self.game_perf = game_perf

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "puzzle_id": self.puzzle_id,
            "rating": self.rating,
            "themes": self.themes,
            "solution": self.solution,
            "fen": self.fen,
            "side_to_move": self.side_to_move,
            "last_move": self.last_move,
            "initial_ply": self.initial_ply,
            "game_perf": self.game_perf,
        }


def normalize_puzzle(raw_data: dict[str, Any]) -> PuzzleData:
    """
    Normalize raw Lichess puzzle data.

    Args:
        raw_data: Raw JSON response from Lichess API

    Returns:
        Normalized PuzzleData object

    Raises:
        KeyError: If required fields are missing
        ValueError: If FEN cannot be parsed
    """
    logger.info("Normalizing puzzle data", extra={"step": "normalize"})

    # Extract puzzle section (required)
    puzzle_section = raw_data["puzzle"]

    # Get FEN with fallback order: puzzle.fen -> raw.fen -> game.fen
    fen = None
    if "fen" in puzzle_section:
        fen = puzzle_section["fen"]
    elif "raw" in raw_data and "fen" in raw_data["raw"]:
        fen = raw_data["raw"]["fen"]
    elif "game" in raw_data and "fen" in raw_data["game"]:
        fen = raw_data["game"]["fen"]

    if not fen:
        raise ValueError("No FEN found in puzzle data")

    # Derive side to move from FEN
    try:
        board = chess.Board(fen)
        side_to_move = "white" if board.turn == chess.WHITE else "black"
    except Exception as e:
        logger.error(
            "Failed to parse FEN",
            extra={"step": "normalize", "fen": fen, "error_message": str(e)}
        )
        raise ValueError(f"Invalid FEN: {fen}") from e

    # Handle game.perf which can be string or object
    game_perf = None
    if "game" in raw_data:
        perf = raw_data["game"].get("perf")
        if isinstance(perf, dict):
            game_perf = perf.get("name") or perf.get("key")
        elif isinstance(perf, str):
            game_perf = perf

    puzzle_data = PuzzleData(
        puzzle_id=puzzle_section["id"],
        rating=puzzle_section["rating"],
        themes=puzzle_section.get("themes", []),
        solution=puzzle_section["solution"],
        fen=fen,
        side_to_move=side_to_move,
        last_move=puzzle_section.get("lastMove"),
        initial_ply=puzzle_section.get("initialPly"),
        game_perf=game_perf,
    )

    logger.info(
        "Puzzle normalized",
        extra={
            "step": "normalize",
            "puzzle_id": puzzle_data.puzzle_id,
            "side_to_move": puzzle_data.side_to_move,
        }
    )

    return puzzle_data
