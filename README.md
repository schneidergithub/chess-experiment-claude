# Chess Puzzle Video Generator - Milestone 1

Generate chess puzzle videos from Lichess daily puzzles. This is **Milestone 1** - local video generation only, no YouTube upload functionality.

## Features

- Fetch daily puzzle from Lichess API
- Normalize puzzle data (FEN, solution moves, themes)
- Render chess board frames with move animations
- Generate silent MP4 video (1920x1080, 30fps)
- Save structured metadata and artifacts

## Requirements

- Python 3.11+
- FFmpeg (for video generation)

## Installation

1. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install package with dependencies:
```bash
pip install -e .[dev]
```

3. Verify installation:
```bash
python -m src.main smoke-test
```

## Usage

### Verify Dependencies
```bash
python -m src.main smoke-test
```

This checks for:
- Python packages (requests, python-chess, Pillow, cairosvg)
- FFmpeg availability
- Configuration file

### Generate Video

```bash
python -m src.main run --skip-upload
```

This will:
1. Fetch the daily puzzle from Lichess
2. Normalize puzzle data
3. Render board frames
4. Build MP4 video
5. Generate metadata

### Force Regeneration

To regenerate a video even if it already exists:
```bash
python -m src.main run --skip-upload --force
```

## Output Structure

Artifacts are saved to `artifacts/YYYY-MM-DD/`:

```
artifacts/2026-04-15/
├── puzzle.json          # Raw puzzle data from Lichess
├── metadata.json        # Run metadata and puzzle info
├── video.mp4            # Generated video (1920x1080, 30fps)
├── frames/              # Individual PNG frames
│   ├── frame_00000.png
│   ├── frame_00001.png
│   └── ...
└── .state/              # Run state markers (internal)
```

## Configuration

Edit `config/app.json` to customize:

- **Video settings**: Resolution, FPS, codec
- **Render settings**: Board size, frame durations
- **Paths**: Artifacts directory, FFmpeg path

## Milestone 1 Scope

This implementation includes **only** local video generation:

✅ Included:
- Lichess API integration
- Board rendering with python-chess
- Video generation with FFmpeg
- Local artifact storage

❌ Not included (future milestones):
- YouTube API integration
- OAuth authentication
- Upload automation
- Scheduling

## Testing

A test script is provided to verify the pipeline with sample data:

```bash
python test_pipeline.py
```

This tests all pipeline stages with a sample puzzle and verifies artifacts are created correctly.

## Project Structure

```
.
├── config/
│   └── app.json              # Application configuration
├── src/
│   ├── __init__.py
│   ├── main.py               # CLI orchestrator
│   ├── fetch_puzzle.py       # Lichess API client
│   ├── puzzle_model.py       # Data normalization
│   ├── render_board.py       # Board frame rendering
│   ├── build_video.py        # FFmpeg video builder
│   ├── metadata.py           # Metadata generation
│   └── state_manager.py      # Run state tracking
├── test_data/
│   └── sample_puzzle.json    # Sample puzzle for testing
├── test_pipeline.py          # Pipeline test script
├── pyproject.toml            # Package configuration
└── README.md                 # This file
```

## License

This project is for educational and personal use.
