from __future__ import annotations

import math
from typing import Iterable, List, Tuple

import numpy as np

Point = Tuple[float, float]
Path = List[Point]
Paths = List[Path]


def remove_duplicate_points(path: Path, tolerance: float = 1e-6) -> Path:
    """Return a copy of path with consecutive duplicate points removed."""
    if not path:
        return []

    cleaned: Path = [path[0]]
    for point in path[1:]:
        if distance(cleaned[-1], point) > tolerance:
            cleaned.append(point)
    return cleaned


def distance(a: Point, b: Point) -> float:
    """Return Euclidean distance between two points."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def join_connected_paths(paths: Paths, tolerance: float = 1e-3) -> Paths:
    """Join paths that share endpoints within the given tolerance."""
    result = [remove_duplicate_points(path, tolerance) for path in paths if len(path) >= 2]
    merged = True

    while merged:
        merged = False
        for i, path_a in enumerate(result):
            if not path_a:
                continue
            a_start, a_end = path_a[0], path_a[-1]

            for j, path_b in enumerate(result):
                if i == j or not path_b:
                    continue
                b_start, b_end = path_b[0], path_b[-1]

                if distance(a_end, b_start) <= tolerance:
                    result[i] = path_a + path_b
                    del result[j]
                    merged = True
                    break
                if distance(a_end, b_end) <= tolerance:
                    result[i] = path_a + list(reversed(path_b))
                    del result[j]
                    merged = True
                    break
                if distance(a_start, b_end) <= tolerance:
                    result[i] = path_b + path_a
                    del result[j]
                    merged = True
                    break
                if distance(a_start, b_start) <= tolerance:
                    result[i] = list(reversed(path_b)) + path_a
                    del result[j]
                    merged = True
                    break

            if merged:
                break

    return [remove_duplicate_points(path, tolerance) for path in result if len(path) >= 2]


def calculate_bounds(paths: Paths) -> Tuple[float, float, float, float]:
    """Calculate the bounding box for a collection of paths."""
    all_points = [point for path in paths for point in path]
    if not all_points:
        return 0.0, 0.0, 0.0, 0.0

    xs = np.array([p[0] for p in all_points], dtype=float)
    ys = np.array([p[1] for p in all_points], dtype=float)
    return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())


def scale_geometry(paths: Paths, scale_x: float, scale_y: float) -> Paths:
    """Scale geometry by X and Y factors."""
    return [[(x * scale_x, y * scale_y) for x, y in path] for path in paths]


def center_geometry(paths: Paths, center_x: float = 0.0, center_y: float = 0.0) -> Paths:
    """Translate geometry so its center is at the requested coordinates."""
    min_x, min_y, max_x, max_y = calculate_bounds(paths)
    width = max_x - min_x
    height = max_y - min_y
    if width == 0 and height == 0:
        return paths

    offset_x = center_x - (min_x + width / 2.0)
    offset_y = center_y - (min_y + height / 2.0)
    return [[(x + offset_x, y + offset_y) for x, y in path] for path in paths]


def scale_to_fit(
    paths: Paths,
    target_width: float,
    target_height: float,
    preserve_aspect: bool = True,
) -> Paths:
    """Scale geometry to fit the requested target dimensions."""
    min_x, min_y, max_x, max_y = calculate_bounds(paths)
    width = max_x - min_x
    height = max_y - min_y
    if width == 0 or height == 0:
        return paths

    scale_x = target_width / width
    scale_y = target_height / height
    if preserve_aspect:
        scale = min(scale_x, scale_y)
        scale_x = scale_y = scale

    return scale_geometry(paths, scale_x, scale_y)


def smooth_path(path: Path, iterations: int = 1) -> Path:
    """Smooth a single path using a simple moving average."""
    if iterations <= 0 or len(path) < 3:
        return path

    result = path[:]
    closed = result[0] == result[-1]

    for _ in range(iterations):
        if closed:
            points = result[:-1]
            smoothed: Path = []
            count = len(points)
            if count < 3:
                break
            for index in range(count):
                prev_point = points[index - 1]
                current_point = points[index]
                next_point = points[(index + 1) % count]
                smoothed.append(
                    (
                        (prev_point[0] + current_point[0] + next_point[0]) / 3.0,
                        (prev_point[1] + current_point[1] + next_point[1]) / 3.0,
                    )
                )
            smoothed.append(smoothed[0])
            result = smoothed
        else:
            smoothed: Path = [result[0]]
            for index in range(1, len(result) - 1):
                prev_point = result[index - 1]
                current_point = result[index]
                next_point = result[index + 1]
                smoothed.append(
                    (
                        (prev_point[0] + current_point[0] + next_point[0]) / 3.0,
                        (prev_point[1] + current_point[1] + next_point[1]) / 3.0,
                    )
                )
            smoothed.append(result[-1])
            result = smoothed

    return result


def smooth_paths(paths: Paths, iterations: int = 1) -> Paths:
    """Apply smoothing to a list of paths."""
    if iterations <= 0:
        return paths
    return [smooth_path(path, iterations) for path in paths]
