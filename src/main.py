"""Main CLI orchestrator for chess puzzle video pipeline."""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.build_video import build_video
from src.fetch_puzzle import fetch_daily_puzzle
from src.metadata import generate_metadata
from src.puzzle_model import normalize_puzzle
from src.render_board import render_frames
from src.state_manager import StateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path = Path("config/app.json")) -> dict[str, Any]:
    """
    Load application configuration.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def smoke_test() -> int:
    """
    Run smoke test to verify dependencies.

    Returns:
        0 on success, 1 on failure
    """
    logger.info("Running smoke test")

    errors = []

    # Check required Python packages
    try:
        import requests
        logger.info(f"✓ requests {requests.__version__}")
    except ImportError as e:
        errors.append(f"✗ requests not found: {e}")

    try:
        import chess
        logger.info(f"✓ python-chess {chess.__version__}")
    except ImportError as e:
        errors.append(f"✗ python-chess not found: {e}")

    try:
        import PIL
        logger.info(f"✓ Pillow {PIL.__version__}")
    except ImportError as e:
        errors.append(f"✗ Pillow not found: {e}")

    try:
        import cairosvg
        logger.info(f"✓ cairosvg {cairosvg.__version__}")
    except ImportError as e:
        errors.append(f"✗ cairosvg not found: {e}")

    # Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            logger.info(f"✓ FFmpeg: {version_line}")
        else:
            errors.append("✗ FFmpeg found but returned error")
    except FileNotFoundError:
        errors.append("✗ FFmpeg not found in PATH")

    # Check config file
    try:
        config = load_config()
        logger.info("✓ Config file loaded")
    except Exception as e:
        errors.append(f"✗ Config file error: {e}")

    # Print results
    if errors:
        logger.error("Smoke test failed:")
        for error in errors:
            logger.error(f"  {error}")
        return 1
    else:
        logger.info("Smoke test passed - all dependencies available")
        return 0


def run_pipeline(skip_upload: bool = False, force: bool = False) -> int:
    """
    Run the full video generation pipeline.

    Args:
        skip_upload: Skip upload step (Milestone 1 only)
        force: Force rerun even if already complete

    Returns:
        0 on success, 1 on failure
    """
    logger.info("Starting pipeline run", extra={"skip_upload": skip_upload, "force": force})

    try:
        # Load configuration
        config = load_config()

        # Set up paths
        run_date = datetime.now().strftime("%Y-%m-%d")
        artifacts_base = Path(config["paths"]["artifacts_base"])
        run_dir = artifacts_base / run_date
        frames_dir = run_dir / "frames"
        state_dir = run_dir / ".state"

        # Initialize state manager
        state_manager = StateManager(state_dir)

        # Check if run is already complete
        if state_manager.is_run_complete() and not force:
            logger.info(f"Run already complete for {run_date}. Use --force to rerun.")
            return 0

        # Clear state if force flag is set
        if force and state_manager.is_run_complete():
            logger.info("Force flag set, clearing previous run state")
            state_manager.clear_state()

        # Step 1: Fetch puzzle
        puzzle_json_path = run_dir / "puzzle.json"
        if not state_manager.is_step_complete("fetch") or force:
            try:
                logger.info("Step 1: Fetching puzzle")
                raw_puzzle_data = fetch_daily_puzzle(
                    config["lichess"]["daily_puzzle_url"],
                    puzzle_json_path,
                )
                state_manager.mark_step_complete("fetch")
            except Exception as e:
                state_manager.save_error("fetch", e)
                raise
        else:
            logger.info("Step 1: Skipping fetch (already complete)")
            with open(puzzle_json_path, encoding="utf-8") as f:
                raw_puzzle_data = json.load(f)

        # Step 2: Normalize puzzle data
        if not state_manager.is_step_complete("normalize") or force:
            try:
                logger.info("Step 2: Normalizing puzzle data")
                puzzle_data = normalize_puzzle(raw_puzzle_data)
                state_manager.mark_step_complete("normalize")
            except Exception as e:
                state_manager.save_error("normalize", e)
                raise
        else:
            logger.info("Step 2: Skipping normalize (already complete)")
            puzzle_data = normalize_puzzle(raw_puzzle_data)

        # Step 3: Render frames
        if not state_manager.is_step_complete("render") or force:
            try:
                logger.info("Step 3: Rendering frames")
                frame_paths = render_frames(puzzle_data, frames_dir, config)
                state_manager.mark_step_complete("render")
            except Exception as e:
                state_manager.save_error("render", e)
                raise
        else:
            logger.info("Step 3: Skipping render (already complete)")
            frame_paths = sorted(frames_dir.glob("frame_*.png"))

        # Step 4: Build video
        video_path = run_dir / "video.mp4"
        if not state_manager.is_step_complete("video") or force:
            try:
                logger.info("Step 4: Building video")
                build_video(frames_dir, video_path, config)
                state_manager.mark_step_complete("video")
            except Exception as e:
                state_manager.save_error("video", e)
                raise
        else:
            logger.info("Step 4: Skipping video (already complete)")

        # Step 5: Generate metadata
        metadata_path = run_dir / "metadata.json"
        if not state_manager.is_step_complete("metadata") or force:
            try:
                logger.info("Step 5: Generating metadata")
                generate_metadata(
                    puzzle_data,
                    run_date,
                    metadata_path,
                    video_path,
                    len(frame_paths),
                )
                state_manager.mark_step_complete("metadata")
            except Exception as e:
                state_manager.save_error("metadata", e)
                raise
        else:
            logger.info("Step 5: Skipping metadata (already complete)")

        # Mark run complete
        state_manager.mark_run_complete()

        # Log completion
        logger.info("Pipeline completed successfully")
        logger.info(f"Artifacts saved to: {run_dir}")
        logger.info(f"  - puzzle.json: {puzzle_json_path}")
        logger.info(f"  - metadata.json: {metadata_path}")
        logger.info(f"  - video.mp4: {video_path}")
        logger.info(f"  - frames/: {len(frame_paths)} frames")

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Chess puzzle video generation pipeline (Milestone 1)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Smoke test command
    subparsers.add_parser("smoke-test", help="Verify dependencies")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run video generation pipeline")
    run_parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip upload step (Milestone 1 mode)",
    )
    run_parser.add_argument(
        "--force",
        action="store_true",
        help="Force rerun even if already complete",
    )

    args = parser.parse_args()

    if args.command == "smoke-test":
        return smoke_test()
    elif args.command == "run":
        return run_pipeline(skip_upload=args.skip_upload, force=args.force)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
