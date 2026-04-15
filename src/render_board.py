"""Render chess board frames for video generation."""

import io
import logging
from pathlib import Path
from typing import Any

import cairosvg
import chess
import chess.svg
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class BoardRenderer:
    """Render chess board positions to PNG frames."""

    def __init__(
        self,
        board_size: int,
        video_width: int,
        video_height: int,
        show_coordinates: bool = True,
    ):
        """
        Initialize board renderer.

        Args:
            board_size: Size of the chess board in pixels
            video_width: Width of the video frame
            video_height: Height of the video frame
            show_coordinates: Whether to show board coordinates
        """
        self.board_size = board_size
        self.video_width = video_width
        self.video_height = video_height
        self.show_coordinates = show_coordinates

    def render_position(
        self,
        board: chess.Board,
        last_move: chess.Move | None = None,
        arrows: list[tuple[chess.Square, chess.Square]] | None = None,
    ) -> Image.Image:
        """
        Render a chess position as a PIL Image.

        Args:
            board: Chess board position
            last_move: Last move to highlight
            arrows: List of arrows to draw (start_square, end_square)

        Returns:
            PIL Image of the rendered board
        """
        # Generate SVG using python-chess
        svg_data = chess.svg.board(
            board,
            size=self.board_size,
            lastmove=last_move,
            coordinates=self.show_coordinates,
            arrows=arrows or [],
        )

        # Convert SVG to PNG using cairosvg
        png_data = cairosvg.svg2png(
            bytestring=svg_data.encode("utf-8"),
            output_width=self.board_size,
            output_height=self.board_size,
        )

        # Load PNG into PIL Image
        board_img = Image.open(io.BytesIO(png_data))

        return board_img

    def create_frame_with_text(
        self,
        board_img: Image.Image,
        header_text: str = "",
        footer_text: str = "",
    ) -> Image.Image:
        """
        Create a video frame with board image and text overlay.

        Args:
            board_img: Chess board image
            header_text: Text to display above the board
            footer_text: Text to display below the board

        Returns:
            Complete video frame as PIL Image
        """
        # Create blank frame with white background
        frame = Image.new("RGB", (self.video_width, self.video_height), "white")

        # Calculate vertical centering
        # Reserve space for header (if present) and footer (if present)
        header_height = 100 if header_text else 0
        footer_height = 80 if footer_text else 0

        # Calculate board position (centered horizontally, vertically positioned)
        board_x = (self.video_width - self.board_size) // 2
        available_height = self.video_height - header_height - footer_height
        board_y = header_height + (available_height - self.board_size) // 2

        # Paste board onto frame
        frame.paste(board_img, (board_x, board_y))

        # Draw text if provided
        draw = ImageDraw.Draw(frame)

        if header_text:
            # Try to use a larger font, fallback to default if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Get text bounding box
            bbox = draw.textbbox((0, 0), header_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Center text horizontally, position near top
            text_x = (self.video_width - text_width) // 2
            text_y = (header_height - text_height) // 2

            draw.text((text_x, text_y), header_text, fill="black", font=font)

        if footer_text:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            except (OSError, IOError):
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), footer_text, font=font)
            text_width = bbox[2] - bbox[0]

            text_x = (self.video_width - text_width) // 2
            text_y = self.video_height - footer_height + 20

            draw.text((text_x, text_y), footer_text, fill="gray", font=font)

        return frame

    def render_intro_frame(
        self,
        board: chess.Board,
        puzzle_id: str,
        rating: int,
        themes: list[str],
    ) -> Image.Image:
        """
        Render intro frame showing puzzle info.

        Args:
            board: Initial chess position
            puzzle_id: Puzzle ID
            rating: Puzzle rating
            themes: Puzzle themes

        Returns:
            Intro frame as PIL Image
        """
        board_img = self.render_position(board)
        header = f"Lichess Daily Puzzle - Rating: {rating}"
        footer = f"Themes: {', '.join(themes[:3])}"
        return self.create_frame_with_text(board_img, header, footer)

    def render_solution_frame(
        self,
        board: chess.Board,
        move: chess.Move,
        move_number: int,
        total_moves: int,
    ) -> Image.Image:
        """
        Render a solution move frame.

        Args:
            board: Chess position after the move
            move: The move that was made
            move_number: Current move number in solution
            total_moves: Total number of moves in solution

        Returns:
            Solution frame as PIL Image
        """
        board_img = self.render_position(board, last_move=move)
        header = f"Solution: Move {move_number}/{total_moves}"
        footer = f"{move.uci()}"
        return self.create_frame_with_text(board_img, header, footer)

    def render_outro_frame(self, board: chess.Board) -> Image.Image:
        """
        Render outro frame.

        Args:
            board: Final chess position

        Returns:
            Outro frame as PIL Image
        """
        board_img = self.render_position(board)
        header = "Puzzle Complete!"
        return self.create_frame_with_text(board_img, header)


def render_frames(
    puzzle_data: Any,
    output_dir: Path,
    config: dict[str, Any],
) -> list[Path]:
    """
    Render all frames for the puzzle video.

    Args:
        puzzle_data: Normalized puzzle data
        output_dir: Directory to save frames
        config: Rendering configuration

    Returns:
        List of paths to rendered frames in order
    """
    logger.info("Starting frame rendering", extra={"step": "render"})

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize renderer
    renderer = BoardRenderer(
        board_size=config["render"]["board_size"],
        video_width=config["video"]["width"],
        video_height=config["video"]["height"],
        show_coordinates=config["render"]["show_coordinates"],
    )

    # Initialize board from FEN
    board = chess.Board(puzzle_data.fen)

    frame_paths = []
    frame_counter = 0

    # Render intro frames
    intro_duration = config["render"]["intro_duration_frames"]
    logger.info(f"Rendering {intro_duration} intro frames", extra={"step": "render"})
    intro_frame = renderer.render_intro_frame(
        board, puzzle_data.puzzle_id, puzzle_data.rating, puzzle_data.themes
    )
    for _ in range(intro_duration):
        frame_path = output_dir / f"frame_{frame_counter:05d}.png"
        intro_frame.save(frame_path)
        frame_paths.append(frame_path)
        frame_counter += 1

    # Render think time frames (showing initial position)
    think_time = config["render"]["think_time_frames"]
    logger.info(f"Rendering {think_time} think-time frames", extra={"step": "render"})
    think_frame = renderer.create_frame_with_text(
        renderer.render_position(board),
        "Your turn to find the best move!",
    )
    for _ in range(think_time):
        frame_path = output_dir / f"frame_{frame_counter:05d}.png"
        think_frame.save(frame_path)
        frame_paths.append(frame_path)
        frame_counter += 1

    # Render solution moves
    move_duration = config["render"]["move_duration_frames"]
    total_moves = len(puzzle_data.solution)
    logger.info(f"Rendering {total_moves} solution moves", extra={"step": "render"})

    for i, move_uci in enumerate(puzzle_data.solution, 1):
        try:
            move = chess.Move.from_uci(move_uci)
            if move not in board.legal_moves:
                logger.warning(
                    f"Illegal move in solution: {move_uci}",
                    extra={"step": "render", "move": move_uci, "fen": board.fen()}
                )
                # Try to continue anyway
            board.push(move)

            solution_frame = renderer.render_solution_frame(board, move, i, total_moves)

            for _ in range(move_duration):
                frame_path = output_dir / f"frame_{frame_counter:05d}.png"
                solution_frame.save(frame_path)
                frame_paths.append(frame_path)
                frame_counter += 1

        except ValueError as e:
            logger.error(
                f"Failed to parse move: {move_uci}",
                extra={"step": "render", "error_message": str(e)}
            )
            raise

    # Render outro frames
    outro_duration = config["render"]["outro_duration_frames"]
    logger.info(f"Rendering {outro_duration} outro frames", extra={"step": "render"})
    outro_frame = renderer.render_outro_frame(board)
    for _ in range(outro_duration):
        frame_path = output_dir / f"frame_{frame_counter:05d}.png"
        outro_frame.save(frame_path)
        frame_paths.append(frame_path)
        frame_counter += 1

    logger.info(
        f"Rendered {len(frame_paths)} total frames",
        extra={"step": "render", "frame_count": len(frame_paths)}
    )

    return frame_paths
