# PenPlotterGcode v2.0

A modular Python SVG/DXF to GRBL-compatible G-code converter for CoreXY pen plotters.

## Features

- Reads SVG and DXF input files.
- Supports SVG `path`, `line`, `polyline`, `polygon`, `circle`, and `rect`.
- Supports DXF `LINE`, `POLYLINE`, `LWPOLYLINE`, `CIRCLE`, and `ARC`.
- Generates optimized pen plotter G-code with only XY moves and servo pen commands.
- Includes a simple Tkinter GUI skeleton for future expansion.

## Installation

1. Create a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Usage

### Command line

```powershell
python main.py drawing.svg drawing.gcode
python main.py example.dxf example.gcode
```

### Version 2.0 options

```powershell
python main.py drawing.svg drawing.gcode --auto-scale --scale-width 180 --scale-height 180 --auto-center --smooth 2
```

### G-code transformer

Transform existing G-code to fit a page size:

```powershell
python main.py input.gcode output.gcode --transform-gcode --page-size A4
```

Or use a custom width and height (millimeters):

```powershell
python main.py input.gcode output.gcode --transform-gcode --page-width 210 --page-height 297
```

Use landscape orientation with:

```powershell
python main.py input.gcode output.gcode --transform-gcode --page-size A3 --landscape
```

### GUI

```powershell
python gui.py
```

## Configuration

Global plotter settings are defined in `config.py`:

- `FEED_RATE` (default: 2000 mm/min)
- `TRAVEL_RATE` (default: 5000 mm/min)
- `PEN_UP_COMMAND` (default: "M3 S80")
- `PEN_DOWN_COMMAND` (default: "M5 S10")
- `UNITS` (default: "mm")
- `PLOTTER_WIDTH` (default: 200 mm)
- `PLOTTER_HEIGHT` (default: 200 mm)
- `AUTO_SCALE` (default: False)
- `AUTO_CENTER` (default: False)
- `SMOOTHING_ITERATIONS` (default: 0)

### Per-Project Profiles (v3.0)

Version 3.0 introduces profile management. Save custom configurations as profiles from the GUI:

```powershell
# Profiles are stored in .plotterprofiles/ directory as JSON files
# Load, save, and manage profiles from the GUI "Profiles" tab
```

## Project structure

- `main.py` — CLI entry point
- `gui.py` — GUI v3.0 with tabbed interface, live preview, and profile management
- `config_manager.py` — Per-project configuration profiles (new in v3.0)
- `gui_utils.py` — Preview canvas, drag-drop handlers, file utilities (new in v3.0)
- `svg_reader.py` — SVG parser and flattening
- `dxf_reader.py` — DXF entity conversion
- `optimizer.py` — path optimization functions
- `gcode_writer.py` — G-code generation
- `gcode_transformer.py` — G-code scaling and transformation
- `geometry.py` — reusable geometry utilities (Point, Path, Paths)

## Example files

- `example.svg`
- `example.dxf`
- `example.gcode`

## Version History

### Version 3.0 (Current)

**GUI Enhancements:**
- ✨ Dual-mode tabbed interface: Beginner mode (simple) + Advanced mode (all features)
- 🎨 Live 2D preview canvas with zoom and pan controls
- 📊 Real-time statistics (paths, points, canvas size, total line length)
- 💾 Profile management: Save, load, and delete conversion profiles
- ⚙️ Full parameter exposure: auto-scale, smoothing, plotter dimensions, path joining, travel optimization
- 📈 Progress indicator with status feedback
- 🎯 Automatic file type detection (SVG/DXF/G-code)
- 🔄 Responsive background processing (threading)

**New Modules:**
- `config_manager.py` — Per-project profile management with JSON storage
- `gui_utils.py` — Preview canvas rendering, file detection, drag-drop utilities

**Features:**
- Beginner Mode: Simplified interface for basic conversions
- Advanced Mode: Expose all CLI options (auto-scale, smoothing iterations, plotter dimensions, page size presets)
- Profiles: Save/load/manage plotter configurations
- Preview: See geometry before conversion

### Version 2.0

- Nearest neighbor path optimization
- Path smoothing with configurable iterations
- Auto-scaling to fit work area
- Auto-centering at origin
- G-code transformation (scale existing G-code)

### Version 1.0

- Basic SVG/DXF to G-code conversion
- Command-line interface
- Configurable plotter parameters

## Future Enhancements

- Drag-and-drop file input support
- PDF preview export before G-code generation
- Profile template packages for sharing
- Windows/macOS/Linux executable packaging
- Advanced layer support for multi-tool workflows
- Estimated draw time calculation
