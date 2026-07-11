from __future__ import annotations

import math
import re
from typing import List, Tuple

from lxml import etree
from svgpathtools import Arc, CubicBezier, Line, Path as SvgPath, QuadraticBezier, parse_path

from geometry import Path, Paths, remove_duplicate_points


def _parse_transform(transform: str) -> Tuple[float, float, float, float, float, float]:
    """Parse a simple SVG transform string into a 2D affine matrix."""
    if not transform:
        return 1.0, 0.0, 0.0, 1.0, 0.0, 0.0

    translate = re.search(r"translate\((-?\d*\.?\d+)(?:[,\s]+(-?\d*\.?\d+))?\)", transform)
    scale = re.search(r"scale\((-?\d*\.?\d+)(?:[,\s]+(-?\d*\.?\d+))?\)", transform)
    matrix = re.search(r"matrix\(([^)]+)\)", transform)

    if matrix:
        parts = [float(value) for value in re.split(r"[,\s]+", matrix.group(1).strip()) if value]
        if len(parts) == 6:
            return tuple(parts)

    sx = sy = 1.0
    tx = ty = 0.0
    if scale:
        sx = float(scale.group(1))
        sy = float(scale.group(2)) if scale.group(2) is not None else sx
    if translate:
        tx = float(translate.group(1))
        ty = float(translate.group(2)) if translate.group(2) is not None else 0.0

    return sx, 0.0, 0.0, sy, tx, ty


def _apply_transform(point: Tuple[float, float], matrix: Tuple[float, float, float, float, float, float]) -> Tuple[float, float]:
    x, y = point
    a, b, c, d, e, f = matrix
    return x * a + y * c + e, x * b + y * d + f


def _sample_segment(segment, max_segment_length: float = 1.0) -> List[Tuple[float, float]]:
    """Return flattened sample points for a single SVG segment."""
    length = segment.length(error=1e-3)
    steps = max(int(math.ceil(length / max_segment_length)), 1)
    points = [segment.point(t / steps) for t in range(steps + 1)]
    return [(float(point.real), float(point.imag)) for point in points]


def _path_to_points(d: str, transform_matrix: Tuple[float, float, float, float, float, float]) -> Path:
    svg_path = parse_path(d)
    points: Path = []
    for segment in svg_path:
        segment_points = _sample_segment(segment)
        if points and points[-1] == segment_points[0]:
            segment_points = segment_points[1:]
        points.extend(segment_points)

    return [_apply_transform(pt, transform_matrix) for pt in remove_duplicate_points(points)]


def _circle_to_path(cx: float, cy: float, r: float, steps: int = 64) -> Path:
    return [
        (
            cx + math.cos(angle) * r,
            cy + math.sin(angle) * r,
        )
        for angle in [2.0 * math.pi * i / steps for i in range(steps + 1)]
    ]


def _rect_to_path(x: float, y: float, width: float, height: float) -> Path:
    return [
        (x, y),
        (x + width, y),
        (x + width, y + height),
        (x, y + height),
        (x, y),
    ]


def _points_from_attribute(value: str) -> Path:
    coords = [float(token) for token in re.split(r"[\s,]+", value.strip()) if token]
    return [(coords[i], coords[i + 1]) for i in range(0, len(coords) - 1, 2)]


def read_svg(file_path: str) -> Paths:
    """Read SVG content and convert supported elements into a list of coordinate paths."""
    try:
        parser = etree.XMLParser(remove_comments=True)
        document = etree.parse(file_path, parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        raise ValueError(f"Cannot read SVG file '{file_path}': {exc}")

    root = document.getroot()
    paths: Paths = []
    namespace = root.nsmap.get(None, "http://www.w3.org/2000/svg")
    ns = f"{{{namespace}}}"

    for element in root.iter():
        transform_matrix = _parse_transform(element.get("transform", ""))
        tag = etree.QName(element).localname.lower()

        if tag == "path" and element.get("d"):
            points = _path_to_points(element.get("d"), transform_matrix)
            if len(points) >= 2:
                paths.append(points)
        elif tag == "line":
            x1 = float(element.get("x1", "0"))
            y1 = float(element.get("y1", "0"))
            x2 = float(element.get("x2", "0"))
            y2 = float(element.get("y2", "0"))
            path = [_apply_transform((x1, y1), transform_matrix), _apply_transform((x2, y2), transform_matrix)]
            paths.append(remove_duplicate_points(path))
        elif tag in ("polyline", "polygon") and element.get("points"):
            points = _points_from_attribute(element.get("points"))
            points = [_apply_transform(pt, transform_matrix) for pt in points]
            if tag == "polygon" and points and points[0] != points[-1]:
                points.append(points[0])
            paths.append(remove_duplicate_points(points))
        elif tag == "circle":
            cx = float(element.get("cx", "0"))
            cy = float(element.get("cy", "0"))
            r = float(element.get("r", "0"))
            circle_path = [_apply_transform(pt, transform_matrix) for pt in _circle_to_path(cx, cy, r)]
            paths.append(remove_duplicate_points(circle_path))
        elif tag == "rect":
            x = float(element.get("x", "0"))
            y = float(element.get("y", "0"))
            width = float(element.get("width", "0"))
            height = float(element.get("height", "0"))
            rect_path = [_apply_transform(pt, transform_matrix) for pt in _rect_to_path(x, y, width, height)]
            paths.append(remove_duplicate_points(rect_path))

    return [path for path in paths if len(path) >= 2]
