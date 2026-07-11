"""Configuration manager for per-project overrides."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from config import (
    AUTO_CENTER,
    AUTO_SCALE,
    FEED_RATE,
    PEN_DOWN_COMMAND,
    PEN_UP_COMMAND,
    PLOTTER_HEIGHT,
    PLOTTER_WIDTH,
    PRESERVE_ASPECT,
    SMOOTHING_ITERATIONS,
    TRAVEL_RATE,
)


@dataclass
class PlotterConfig:
    """Dataclass representing plotter configuration."""

    feed_rate: int = FEED_RATE
    travel_rate: int = TRAVEL_RATE
    pen_up_command: str = PEN_UP_COMMAND
    pen_down_command: str = PEN_DOWN_COMMAND
    plotter_width: float = PLOTTER_WIDTH
    plotter_height: float = PLOTTER_HEIGHT
    auto_scale: bool = AUTO_SCALE
    auto_center: bool = AUTO_CENTER
    smoothing_iterations: int = SMOOTHING_ITERATIONS
    preserve_aspect: bool = PRESERVE_ASPECT

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PlotterConfig:
        """Create from dictionary, using defaults for missing keys."""
        defaults = asdict(PlotterConfig())
        defaults.update(data)
        return PlotterConfig(**defaults)

    @staticmethod
    def from_global() -> PlotterConfig:
        """Create from global config defaults."""
        return PlotterConfig()


class ConfigManager:
    """Manages global and per-project plotter configurations."""

    PROFILES_DIR = ".plotterprofiles"

    def __init__(self, project_dir: str = ".") -> None:
        """Initialize configuration manager.

        Args:
            project_dir: Root directory for the project (where profiles are stored)
        """
        self.project_dir = Path(project_dir)
        self.profiles_dir = self.project_dir / self.PROFILES_DIR
        self.current_config = PlotterConfig.from_global()
        self._ensure_profiles_dir()

    def _ensure_profiles_dir(self) -> None:
        """Create profiles directory if it doesn't exist."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def get_current(self) -> PlotterConfig:
        """Get current configuration."""
        return self.current_config

    def set_current(self, config: PlotterConfig) -> None:
        """Set current configuration."""
        self.current_config = config

    def save_profile(self, profile_name: str, config: PlotterConfig) -> str:
        """Save configuration as a named profile.

        Args:
            profile_name: Name of the profile (e.g., "Fast Draft")
            config: PlotterConfig to save

        Returns:
            Path to saved profile file
        """
        profile_path = self.profiles_dir / f"{profile_name}.json"
        with open(profile_path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        return str(profile_path)

    def load_profile(self, profile_name: str) -> PlotterConfig:
        """Load configuration from a named profile.

        Args:
            profile_name: Name of the profile (with or without .json extension)

        Returns:
            Loaded PlotterConfig

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        if not profile_name.endswith(".json"):
            profile_name += ".json"
        profile_path = self.profiles_dir / profile_name
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_path}")
        with open(profile_path) as f:
            data = json.load(f)
        return PlotterConfig.from_dict(data)

    def list_profiles(self) -> list[str]:
        """List all available profile names (without extension).

        Returns:
            List of profile names
        """
        if not self.profiles_dir.exists():
            return []
        profiles = [f.stem for f in self.profiles_dir.glob("*.json")]
        return sorted(profiles)

    def delete_profile(self, profile_name: str) -> None:
        """Delete a profile.

        Args:
            profile_name: Name of the profile (with or without .json extension)

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        if not profile_name.endswith(".json"):
            profile_name += ".json"
        profile_path = self.profiles_dir / profile_name
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_path}")
        profile_path.unlink()

    def export_profile(self, profile_name: str, export_path: str) -> None:
        """Export a profile to an external file.

        Args:
            profile_name: Name of the profile to export
            export_path: Where to save the exported profile

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        config = self.load_profile(profile_name)
        with open(export_path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)

    def import_profile(self, import_path: str, profile_name: str) -> str:
        """Import a profile from an external file.

        Args:
            import_path: Path to the profile file to import
            profile_name: Name to save the profile as

        Returns:
            Path to saved profile file

        Raises:
            FileNotFoundError: If import file doesn't exist
        """
        if not os.path.exists(import_path):
            raise FileNotFoundError(f"Import file not found: {import_path}")
        with open(import_path) as f:
            data = json.load(f)
        config = PlotterConfig.from_dict(data)
        return self.save_profile(profile_name, config)
