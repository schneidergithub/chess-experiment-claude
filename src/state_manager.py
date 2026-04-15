"""Manage pipeline run state and step markers."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StateManager:
    """Manage pipeline execution state."""

    def __init__(self, state_dir: Path):
        """
        Initialize state manager.

        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def mark_step_complete(self, step_name: str) -> None:
        """
        Mark a pipeline step as complete.

        Args:
            step_name: Name of the step
        """
        marker_path = self.state_dir / f"{step_name}.complete"
        marker_path.touch()
        logger.debug(f"Marked step '{step_name}' complete", extra={"step": step_name})

    def is_step_complete(self, step_name: str) -> bool:
        """
        Check if a pipeline step is complete.

        Args:
            step_name: Name of the step

        Returns:
            True if step is complete, False otherwise
        """
        marker_path = self.state_dir / f"{step_name}.complete"
        return marker_path.exists()

    def mark_run_complete(self) -> None:
        """Mark the entire run as complete."""
        marker_path = self.state_dir / "run.complete"
        marker_path.touch()
        logger.info("Run marked complete", extra={"step": "state"})

    def is_run_complete(self) -> bool:
        """
        Check if the run is complete.

        Returns:
            True if run is complete, False otherwise
        """
        marker_path = self.state_dir / "run.complete"
        return marker_path.exists()

    def clear_state(self) -> None:
        """Clear all state markers for a fresh run."""
        logger.info("Clearing run state", extra={"step": "state"})
        for marker_file in self.state_dir.glob("*.complete"):
            marker_file.unlink()

    def save_error(self, step_name: str, error: Exception) -> None:
        """
        Save error information for a failed step.

        Args:
            step_name: Name of the step that failed
            error: Exception that occurred
        """
        error_path = self.state_dir / f"{step_name}.error"
        error_data = {
            "step": step_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        with open(error_path, "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2)

        logger.error(
            f"Error in step '{step_name}'",
            extra={"step": step_name, "error_message": str(error)}
        )
