import re
from typing import List, Tuple, Union


def get_page_size(page_size: Union[str, Tuple[float, float]], landscape: bool = False) -> Tuple[float, float]:
    """Return width and height in millimeters for a named page size."""
    if isinstance(page_size, str):
        size_key = page_size.strip().upper()
        page_sizes = {
            "A2": (420.0, 594.0),
            "A3": (297.0, 420.0),
            "A4": (210.0, 297.0),
            "A5": (148.0, 210.0),
        }
        if size_key not in page_sizes:
            raise ValueError(f"Unsupported page size: {page_size}")
        width, height = page_sizes[size_key]
    else:
        if len(page_size) != 2:
            raise ValueError("page_size tuple must contain exactly two values")
        width, height = float(page_size[0]), float(page_size[1])

    if landscape:
        width, height = height, width

    return width, height


def parse_gcode_file(input_path: str) -> List[str]:
    """Read a G-code file and return its raw lines."""
    with open(input_path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def transform_gcode_line(
    line: str,
    scale_x: float,
    scale_y: float,
    offset_x: float,
    offset_y: float,
) -> str:
    """Scale X/Y coordinates in a single G-code line."""
    def replace_coordinate(match: re.Match) -> str:
        code = match.group(1)
        value = float(match.group(2))
        if code == "X":
            transformed = value * scale_x + offset_x
        else:
            transformed = value * scale_y + offset_y
        return f"{code}{transformed:.4f}"

    return re.sub(
        r"\b([XY])\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
        replace_coordinate,
        line,
    )


def transform_gcode_lines(
    lines: List[str],
    target_width: float,
    target_height: float,
    preserve_aspect: bool = True,
) -> List[str]:
    """Scale and center all X/Y coordinates to fit the target page size."""
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for line in lines:
        for match in re.finditer(r"\b([XY])\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line):
            code = match.group(1)
            value = float(match.group(2))
            if code == "X":
                min_x = min(min_x, value)
                max_x = max(max_x, value)
            else:
                min_y = min(min_y, value)
                max_y = max(max_y, value)

    if min_x == float("inf") or min_y == float("inf"):
        return list(lines)

    width = max_x - min_x
    height = max_y - min_y
    if width == 0 or height == 0:
        scale_x = scale_y = 1.0
    else:
        scale_x = target_width / width
        scale_y = target_height / height
        if preserve_aspect:
            scale = min(scale_x, scale_y)
            scale_x = scale_y = scale

    scaled_width = width * scale_x
    scaled_height = height * scale_y
    offset_x = (target_width - scaled_width) / 2.0 - min_x * scale_x
    offset_y = (target_height - scaled_height) / 2.0 - min_y * scale_y

    return [
        transform_gcode_line(line, scale_x, scale_y, offset_x, offset_y)
        for line in lines
    ]


def transform_gcode_file(
    input_path: str,
    output_path: str,
    target_width: float,
    target_height: float,
    preserve_aspect: bool = True,
) -> None:
    """Read a G-code file, transform its coordinates, and write the result."""
    lines = parse_gcode_file(input_path)
    transformed = transform_gcode_lines(lines, target_width, target_height, preserve_aspect)
    with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(transformed))
        handle.write("\n")
