from __future__ import annotations

import math
from typing import List, Tuple

import ezdxf

from geometry import Path, Paths, remove_duplicate_points


def _sample_circle(cx: float, cy: float, radius: float, segments: int = 64) -> Path:
    return [
        (
            cx + math.cos(theta) * radius,
            cy + math.sin(theta) * radius,
        )
        for theta in [2.0 * math.pi * i / segments for i in range(segments + 1)]
    ]


def _sample_arc(cx: float, cy: float, radius: float, start_angle: float, end_angle: float, segments: int = 32) -> Path:
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    if end_rad < start_rad:
        end_rad += 2.0 * math.pi
    arc_length = end_rad - start_rad
    count = max(int(math.ceil(abs(arc_length) / (math.pi / 16))), 4)
    return [
        (
            cx + math.cos(start_rad + t * arc_length) * radius,
            cy + math.sin(start_rad + t * arc_length) * radius,
        )
        for t in [i / count for i in range(count + 1)]
    ]


def read_dxf(file_path: str) -> Paths:
    """Read DXF file and convert supported entities into coordinate paths."""
    try:
        document = ezdxf.readfile(file_path)
    except (IOError, ezdxf.DXFStructureError) as exc:
        raise ValueError(f"Cannot read DXF file '{file_path}': {exc}")

    msp = document.modelspace()
    paths: Paths = []

    for entity in msp:
        etype = entity.dxftype()
        if etype == "LINE":
            start = (float(entity.dxf.start.x), float(entity.dxf.start.y))
            end = (float(entity.dxf.end.x), float(entity.dxf.end.y))
            paths.append(remove_duplicate_points([start, end]))
        elif etype in {"POLYLINE", "LWPOLYLINE"}:
            points = [
                (float(point[0]), float(point[1]))
                for point in entity.get_points(closed=False)
            ]
            if entity.closed and points and points[0] != points[-1]:
                points.append(points[0])
            paths.append(remove_duplicate_points(points))
        elif etype == "CIRCLE":
            cx = float(entity.dxf.center.x)
            cy = float(entity.dxf.center.y)
            radius = float(entity.dxf.radius)
            paths.append(remove_duplicate_points(_sample_circle(cx, cy, radius)))
        elif etype == "ARC":
            cx = float(entity.dxf.center.x)
            cy = float(entity.dxf.center.y)
            radius = float(entity.dxf.radius)
            start_angle = float(entity.dxf.start_angle)
            end_angle = float(entity.dxf.end_angle)
            paths.append(remove_duplicate_points(_sample_arc(cx, cy, radius, start_angle, end_angle)))

    return [path for path in paths if len(path) >= 2]
