from typing import List

from config import FEED_RATE, PEN_DOWN_COMMAND, PEN_UP_COMMAND, TRAVEL_RATE
from geometry import Path, Paths


def format_point(point: tuple[float, float]) -> str:
    return f"X{point[0]:.4f} Y{point[1]:.4f}"


def generate_gcode(
    paths: Paths,
    feed_rate: int = FEED_RATE,
    travel_rate: int = TRAVEL_RATE,
    pen_up_command: str = PEN_UP_COMMAND,
    pen_down_command: str = PEN_DOWN_COMMAND,
) -> List[str]:
    """Create a G-code program for a series of pen plotter paths."""
    lines: List[str] = ["G21", "G90", "G17", f"F{feed_rate}"]
    active_pen_up = True

    for path in paths:
        if not path:
            continue

        start = path[0]
        lines.append(pen_up_command)
        lines.append(f"G0 {format_point(start)} F{travel_rate}")
        lines.append(pen_down_command)
        for point in path[1:]:
            lines.append(f"G1 {format_point(point)} F{feed_rate}")
        active_pen_up = False

    if not active_pen_up:
        lines.append(pen_up_command)

    lines.append("G0 X0 Y0")
    lines.append("M2")
    return lines


def save_gcode(
    paths: Paths,
    output_file: str,
    feed_rate: int = FEED_RATE,
    travel_rate: int = TRAVEL_RATE,
    pen_up_command: str = PEN_UP_COMMAND,
    pen_down_command: str = PEN_DOWN_COMMAND,
) -> None:
    """Write G-code to the target file."""
    lines = generate_gcode(paths, feed_rate, travel_rate, pen_up_command, pen_down_command)
    with open(output_file, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")
