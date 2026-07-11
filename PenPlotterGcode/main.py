from __future__ import annotations

import argparse
import os
import sys

from dxf_reader import read_dxf
from gcode_writer import save_gcode
from geometry import Path, Paths
from gcode_transformer import get_page_size, transform_gcode_file
from optimizer import optimize_paths
from svg_reader import read_svg
from config import (
    AUTO_CENTER,
    AUTO_SCALE,
    PLOTTER_HEIGHT,
    PLOTTER_WIDTH,
    PRESERVE_ASPECT,
    SMOOTHING_ITERATIONS,
)


def _detect_file_type(input_path: str) -> str:
    extension = os.path.splitext(input_path)[1].lower()
    if extension == ".svg":
        return "svg"
    if extension == ".dxf":
        return "dxf"
    raise ValueError("Unsupported input format. Please use .svg or .dxf files.")


def _read_geometry(input_path: str) -> Paths:
    file_type = _detect_file_type(input_path)
    if file_type == "svg":
        return read_svg(input_path)
    return read_dxf(input_path)


def _validate_paths(paths: Paths) -> None:
    if not paths:
        raise ValueError("No valid geometry found in the input file.")
    if all(len(path) < 2 for path in paths):
        raise ValueError("Input file contains no drawable paths.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PenPlotterGcode SVG/DXF to G-code converter")
    parser.add_argument("input_file", help="Input SVG or DXF file")
    parser.add_argument("output_file", help="Output G-code file")
    parser.add_argument("--auto-scale", action="store_true", help="Scale artwork to fit a target work area")
    parser.add_argument("--scale-width", type=float, default=None, help="Target width for auto-scaling")
    parser.add_argument("--scale-height", type=float, default=None, help="Target height for auto-scaling")
    parser.add_argument("--auto-center", action="store_true", help="Center artwork at the origin")
    parser.add_argument("--smooth", type=int, default=None, help="Number of smoothing iterations")
    parser.add_argument("--transform-gcode", action="store_true", help="Transform an existing G-code file to fit a page size")
    parser.add_argument("--page-size", type=str, default="A4", help="Page size preset for G-code transform: A4, A3, A2")
    parser.add_argument("--page-width", type=float, default=None, help="Custom target width for G-code transform")
    parser.add_argument("--page-height", type=float, default=None, help="Custom target height for G-code transform")
    parser.add_argument("--landscape", action="store_true", help="Use landscape orientation for page-size transformation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.transform_gcode:
            if args.page_width is not None and args.page_height is not None:
                page_width = args.page_width
                page_height = args.page_height
            else:
                page_width, page_height = get_page_size(args.page_size, landscape=args.landscape)

            if page_width <= 0 or page_height <= 0:
                raise ValueError("Page width and height must be positive numbers.")

            transform_gcode_file(args.input_file, args.output_file, page_width, page_height)
            print(f"Transformed G-code saved to: {args.output_file}")
            return 0

        paths = _read_geometry(args.input_file)
        _validate_paths(paths)

        auto_scale = args.auto_scale or args.scale_width is not None or args.scale_height is not None or AUTO_SCALE
        target_width = args.scale_width if args.scale_width is not None else PLOTTER_WIDTH
        target_height = args.scale_height if args.scale_height is not None else PLOTTER_HEIGHT
        if auto_scale and (target_width <= 0 or target_height <= 0):
            raise ValueError("Scale width and height must be positive numbers.")

        auto_center = args.auto_center or AUTO_CENTER
        smoothing_iterations = args.smooth if args.smooth is not None else SMOOTHING_ITERATIONS

        optimized = optimize_paths(
            paths,
            auto_scale=auto_scale,
            target_width=target_width,
            target_height=target_height,
            preserve_aspect=PRESERVE_ASPECT,
            auto_center=auto_center,
            smoothing_iterations=smoothing_iterations,
        )
        save_gcode(optimized, args.output_file)
        print(f"Generated G-code: {args.output_file}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
