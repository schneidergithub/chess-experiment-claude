"""Test script for local pipeline verification."""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.build_video import build_video
from src.metadata import generate_metadata
from src.puzzle_model import normalize_puzzle
from src.render_board import render_frames


def load_config():
    """Load configuration."""
    config_path = Path("config/app.json")
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def test_pipeline_with_sample_data():
    """Test the pipeline with sample puzzle data."""
    print("Testing pipeline with sample data...")

    # Load sample puzzle data
    sample_data_path = Path("test_data/sample_puzzle.json")
    with open(sample_data_path, encoding="utf-8") as f:
        raw_puzzle_data = json.load(f)

    # Set up paths
    run_date = datetime.now().strftime("%Y-%m-%d")
    artifacts_base = Path("artifacts")
    run_dir = artifacts_base / run_date
    frames_dir = run_dir / "frames"
    puzzle_json_path = run_dir / "puzzle.json"
    metadata_path = run_dir / "metadata.json"
    video_path = run_dir / "video.mp4"

    # Create directories
    run_dir.mkdir(parents=True, exist_ok=True)

    # Load config
    config = load_config()

    # Step 1: Save raw puzzle data
    print("Step 1: Saving puzzle data...")
    with open(puzzle_json_path, "w", encoding="utf-8") as f:
        json.dump(raw_puzzle_data, f, indent=2)
    print(f"  ✓ Saved to {puzzle_json_path}")

    # Step 2: Normalize puzzle data
    print("Step 2: Normalizing puzzle data...")
    puzzle_data = normalize_puzzle(raw_puzzle_data)
    print(f"  ✓ Puzzle ID: {puzzle_data.puzzle_id}")
    print(f"  ✓ Rating: {puzzle_data.rating}")
    print(f"  ✓ Side to move: {puzzle_data.side_to_move}")
    print(f"  ✓ Solution moves: {len(puzzle_data.solution)}")

    # Step 3: Render frames
    print("Step 3: Rendering frames...")
    frame_paths = render_frames(puzzle_data, frames_dir, config)
    print(f"  ✓ Rendered {len(frame_paths)} frames to {frames_dir}")

    # Step 4: Build video
    print("Step 4: Building video...")
    build_video(frames_dir, video_path, config)
    print(f"  ✓ Video created at {video_path}")

    # Step 5: Generate metadata
    print("Step 5: Generating metadata...")
    generate_metadata(puzzle_data, run_date, metadata_path, video_path, len(frame_paths))
    print(f"  ✓ Metadata saved to {metadata_path}")

    # Verify artifacts
    print("\nVerifying artifacts:")
    artifacts = [
        ("puzzle.json", puzzle_json_path),
        ("metadata.json", metadata_path),
        ("video.mp4", video_path),
        ("frames directory", frames_dir),
    ]

    all_exist = True
    for name, path in artifacts:
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name}: {path}")
        if not exists:
            all_exist = False

    # Check frame count
    if frames_dir.exists():
        frame_files = list(frames_dir.glob("frame_*.png"))
        print(f"  ✓ Frame count: {len(frame_files)}")

    if all_exist:
        print("\n✅ All tests passed! Pipeline works correctly.")
        return 0
    else:
        print("\n❌ Some artifacts are missing.")
        return 1


if __name__ == "__main__":
    sys.exit(test_pipeline_with_sample_data())
