"""GUI utility functions for preview canvas, drag-drop, and file handling."""

from __future__ import annotations

import os
from tkinter import Canvas
from typing import TYPE_CHECKING, Callable

from geometry import Point, Paths

if TYPE_CHECKING:
    from tkinter import Tk


class PreviewCanvas:
    """Handles 2D preview rendering of geometry."""

    PADDING = 20
    BACKGROUND = "#f8f8f8"
    LINE_COLOR = "#333333"
    LINE_WIDTH = 1
    GRID_COLOR = "#e0e0e0"
    GRID_SIZE = 20

    def __init__(self, canvas: Canvas, width: int = 400, height: int = 300) -> None:
        """Initialize preview canvas.

        Args:
            canvas: Tkinter Canvas widget
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.canvas = canvas
        self.width = width
        self.height = height
        self.paths: Paths | None = None
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._setup_canvas()
        self._bind_events()

    def _setup_canvas(self) -> None:
        """Configure canvas appearance."""
        self.canvas.config(bg=self.BACKGROUND, highlightthickness=1, highlightbackground="#cccccc")
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        self.canvas.bind("<Button-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_move)

    def _bind_events(self) -> None:
        """Bind mouse events for zoom and pan."""
        self._pan_start_x = 0
        self._pan_start_y = 0

    def _on_mousewheel(self, event: object) -> str:
        """Handle mouse wheel for zoom."""
        if hasattr(event, "delta"):
            delta = event.delta
        else:
            delta = event.num if hasattr(event, "num") else 0  # type: ignore
        
        if delta > 0:
            self.zoom *= 1.1
        elif delta < 0:
            self.zoom /= 1.1
        self.zoom = max(0.1, min(10.0, self.zoom))
        self.redraw()
        return "break"

    def _on_pan_start(self, event: object) -> None:
        """Start panning."""
        self._pan_start_x = event.x if hasattr(event, "x") else 0  # type: ignore
        self._pan_start_y = event.y if hasattr(event, "y") else 0  # type: ignore

    def _on_pan_move(self, event: object) -> None:
        """Pan the canvas."""
        x = event.x if hasattr(event, "x") else 0  # type: ignore
        y = event.y if hasattr(event, "y") else 0  # type: ignore
        self.pan_x += (x - self._pan_start_x) / self.zoom
        self.pan_y += (y - self._pan_start_y) / self.zoom
        self._pan_start_x = x
        self._pan_start_y = y
        self.redraw()

    def set_paths(self, paths: Paths) -> None:
        """Set geometry to display and auto-fit to canvas.

        Args:
            paths: Paths to display
        """
        self.paths = paths
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._auto_fit()
        self.redraw()

    def _auto_fit(self) -> None:
        """Calculate zoom to fit paths in canvas."""
        if not self.paths or not any(len(path) > 0 for path in self.paths):
            return

        min_x = float("inf")
        max_x = float("-inf")
        min_y = float("inf")
        max_y = float("-inf")

        for path in self.paths:
            for point in path:
                min_x = min(min_x, point[0])
                max_x = max(max_x, point[0])
                min_y = min(min_y, point[1])
                max_y = max(max_y, point[1])

        if min_x == float("inf"):
            return

        width = max_x - min_x
        height = max_y - min_y
        if width < 0.01 or height < 0.01:
            return

        canvas_width = self.width - 2 * self.PADDING
        canvas_height = self.height - 2 * self.PADDING
        zoom_x = canvas_width / width if width > 0 else 1.0
        zoom_y = canvas_height / height if height > 0 else 1.0
        self.zoom = min(zoom_x, zoom_y) * 0.9  # 0.9 for padding

        self.pan_x = -(min_x + width / 2) * self.zoom + canvas_width / 2
        self.pan_y = -(min_y + height / 2) * self.zoom + canvas_height / 2

    def _world_to_canvas(self, point: Point) -> tuple[float, float]:
        """Convert world coordinates to canvas coordinates."""
        x = point[0] * self.zoom + self.pan_x + self.PADDING
        y = point[1] * self.zoom + self.pan_y + self.PADDING
        return x, y

    def redraw(self) -> None:
        """Redraw the canvas."""
        self.canvas.delete("all")
        self._draw_grid()
        if self.paths:
            self._draw_paths()

    def _draw_grid(self) -> None:
        """Draw optional grid background."""
        # Simple grid for reference
        for x in range(0, self.width, self.GRID_SIZE):
            self.canvas.create_line(x, 0, x, self.height, fill=self.GRID_COLOR, width=0)
        for y in range(0, self.height, self.GRID_SIZE):
            self.canvas.create_line(0, y, self.width, y, fill=self.GRID_COLOR, width=0)

    def _draw_paths(self) -> None:
        """Draw paths on canvas."""
        if not self.paths:
            return

        for path in self.paths:
            if len(path) < 2:
                continue
            for i in range(len(path) - 1):
                p1 = self._world_to_canvas(path[i])
                p2 = self._world_to_canvas(path[i + 1])
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=self.LINE_COLOR, width=self.LINE_WIDTH)

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get bounding box of paths in world coordinates.

        Returns:
            (min_x, min_y, max_x, max_y)
        """
        if not self.paths or not any(len(path) > 0 for path in self.paths):
            return 0, 0, 0, 0

        min_x = float("inf")
        max_x = float("-inf")
        min_y = float("inf")
        max_y = float("-inf")

        for path in self.paths:
            for point in path:
                min_x = min(min_x, point[0])
                max_x = max(max_x, point[0])
                min_y = min(min_y, point[1])
                max_y = max(max_y, point[1])

        if min_x == float("inf"):
            return 0, 0, 0, 0
        return min_x, min_y, max_x, max_y

    def get_stats(self) -> dict[str, float | int]:
        """Get statistics about current paths.

        Returns:
            Dictionary with stats (path_count, point_count, bounding_box dimensions, total_length)
        """
        if not self.paths:
            return {"path_count": 0, "point_count": 0, "width": 0, "height": 0, "total_length": 0}

        path_count = len(self.paths)
        point_count = sum(len(path) for path in self.paths)
        min_x, min_y, max_x, max_y = self.get_bounds()
        width = max_x - min_x
        height = max_y - min_y

        total_length = 0.0
        for path in self.paths:
            for i in range(len(path) - 1):
                p1 = path[i]
                p2 = path[i + 1]
                dist = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
                total_length += dist

        return {
            "path_count": path_count,
            "point_count": point_count,
            "width": round(width, 2),
            "height": round(height, 2),
            "total_length": round(total_length, 2),
        }


class DragDropHandler:
    """Handles drag-and-drop file operations."""

    SUPPORTED_EXTENSIONS = {".svg", ".dxf", ".gcode"}

    @staticmethod
    def register_drag_drop(
        widget: Tk, on_drop: Callable[[str], None], filetypes: set[str] | None = None
    ) -> None:
        """Register drag-drop handler on a widget.

        Args:
            widget: Tkinter widget
            on_drop: Callback function that receives file path
            filetypes: Set of supported extensions (e.g., {".svg", ".dxf"})
        """
        if filetypes is None:
            filetypes = DragDropHandler.SUPPORTED_EXTENSIONS

        def drop(event: object) -> None:
            # Handle drop event
            if hasattr(event, "data"):
                files = widget.tk.splitlist(event.data)  # type: ignore
                for file_path in files:
                    # Clean up file path (remove curly braces on Windows)
                    file_path = file_path.strip("{}")
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(file_path)[1].lower()
                        if ext in filetypes:
                            on_drop(file_path)
                            return

        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", drop)


def detect_file_type(file_path: str) -> str:
    """Detect file type from extension.

    Args:
        file_path: Path to file

    Returns:
        File type: "svg", "dxf", or "gcode"

    Raises:
        ValueError: If file type is not supported
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".svg":
        return "svg"
    if ext == ".dxf":
        return "dxf"
    if ext == ".gcode":
        return "gcode"
    raise ValueError(f"Unsupported file type: {ext}")


# tkinterdnd constants (will be imported if available)
try:
    from tkinterdnd2 import DND_FILES  # type: ignore

    HAS_DND = True
except ImportError:
    HAS_DND = False
    DND_FILES = None
