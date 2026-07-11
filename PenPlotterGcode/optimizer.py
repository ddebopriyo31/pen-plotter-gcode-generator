from typing import List, Tuple

from geometry import (
    Path,
    Paths,
    center_geometry,
    distance,
    join_connected_paths,
    remove_duplicate_points,
    scale_to_fit,
    smooth_paths,
)


def optimize_paths(
    paths: Paths,
    tolerance: float = 1e-3,
    auto_scale: bool = False,
    target_width: float | None = None,
    target_height: float | None = None,
    preserve_aspect: bool = True,
    auto_center: bool = False,
    smoothing_iterations: int = 0,
) -> Paths:
    """Clean, optionally scale/center, and optimize a list of paths for pen plotting."""
    cleaned = [remove_duplicate_points(path, tolerance) for path in paths if len(path) >= 2]
    cleaned = [path for path in cleaned if len(path) >= 2]

    if auto_scale and target_width is not None and target_height is not None:
        cleaned = scale_to_fit(cleaned, target_width, target_height, preserve_aspect)

    if auto_center:
        cleaned = center_geometry(cleaned, 0.0, 0.0)

    joined = join_connected_paths(cleaned, tolerance)
    ordered = nearest_neighbor(joined)
    if smoothing_iterations > 0:
        ordered = smooth_paths(ordered, smoothing_iterations)

    return ordered


def nearest_neighbor(paths: Paths, start_point: Tuple[float, float] = (0.0, 0.0)) -> Paths:
    """Order paths using a greedy nearest-neighbor strategy."""
    if not paths:
        return []

    remaining = list(paths)
    ordered: Paths = []
    current_point = start_point

    while remaining:
        best_index = 0
        best_distance = float("inf")
        best_reversed = False

        for index, path in enumerate(remaining):
            forward_distance = distance(current_point, path[0])
            reverse_distance = distance(current_point, path[-1])

            if forward_distance < best_distance:
                best_distance = forward_distance
                best_index = index
                best_reversed = False

            if reverse_distance < best_distance:
                best_distance = reverse_distance
                best_index = index
                best_reversed = True

        next_path = remaining.pop(best_index)
        if best_reversed:
            next_path = list(reversed(next_path))

        ordered.append(next_path)
        current_point = ordered[-1][-1]

    return ordered


def optimize_travel_distance(paths: Paths) -> Paths:
    """Optimize the order of travel to reduce non-drawing movement."""
    return nearest_neighbor(paths)


def reverse_path_if_better(path: Path) -> Path:
    """Reverse a path if it reduces distance to the next connection point."""
    return list(reversed(path)) if len(path) > 1 else path
