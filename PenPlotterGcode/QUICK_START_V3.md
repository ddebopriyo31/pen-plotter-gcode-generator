# PenPlotter GUI v3.0 - Quick Start Guide

## 🚀 Launch the Application

```powershell
python gui.py
```

The application window will open with three tabs:

---

## 📖 Tab 1: Beginner Mode

**For simple, one-click conversions**

1. Click **"Browse"** under "Input File:" → Select your SVG or DXF file
2. Click **"Browse"** under "Output File:" → Choose where to save the G-code
3. (Optional) Adjust **Feed Rate** and **Travel Rate** if needed
4. (Optional) Customize **Pen Up/Down Commands** for your plotter
5. Click **"Generate G-code"**

✅ That's it! Your G-code file is ready to use.

---

## ⚙️ Tab 2: Advanced Mode

**For fine-tuned control over all parameters**

### Left Side: Conversion Settings
- Feed Rate, Travel Rate, Pen Commands (same as Beginner)
- **Optimization section:**
  - ✓ Auto-scale to fit plotter (set target width/height)
  - ✓ Auto-center at origin
  - Smoothing slider (0-10 iterations for curve smoothing)

### Right Side: Plotter Configuration
- Plotter Width/Height (configure your physical plotter size)
- **Path Optimization:**
  - ✓ Join adjacent paths
  - ✓ Optimize travel (nearest-neighbor ordering to reduce pen-up travel)
- **Page Size (for G-code Transform mode):**
  - Select preset (A4/A3/A2/A5) or custom dimensions
  - Landscape orientation toggle

---

## 💾 Tab 3: Profiles

**Save and reuse your favorite configurations**

### Save a Profile
1. Configure all settings in Advanced Mode
2. Go to **Profiles tab**
3. Click **"Save Current as Profile"**
4. Enter a name (e.g., "Fast Draft", "Fine Detail A4")
5. Click **"Save"**

### Load a Profile
1. Go to **Profiles tab**
2. Click on a profile name in the list
3. Click **"Load Profile"**
4. ✅ All settings restore automatically!

### Delete a Profile
1. Select profile from list
2. Click **"Delete Profile"**
3. Confirm deletion

**Profiles are stored in `.plotterprofiles/` directory (inside your project folder)**

---

## 👁️ Live Preview

As you load files, you'll see:

- **Geometry preview** in the canvas (shows your paths)
- **Live statistics:**
  - Number of paths and total points
  - Canvas size (mm)
  - Total line length
- **Interactive controls:**
  - Scroll wheel: zoom in/out
  - Click and drag: pan around the preview

---

## 🔄 Mode Indicator

The status line shows what mode you're in:

- **"Mode: Convert (SVG → G-code)"** — Loading SVG file
- **"Mode: Convert (DXF → G-code)"** — Loading DXF file  
- **"Mode: Transform (G-code → G-code)"** — Loading existing G-code (rescales it to fit a page size)

When in Transform mode, Beginner/Advanced tabs are disabled (only page size options appear).

---

## ✨ Feature Highlights

### 1. Automatic File Type Detection
- Load SVG, DXF, or G-code — the GUI figures out which mode to use
- UI updates automatically to show relevant options

### 2. Background Processing
- G-code generation runs in a background thread
- UI stays responsive with progress bar
- Status shows: "Reading geometry..." → "Optimizing..." → "Generating..." → ✓ Complete!

### 3. Error Handling
- Invalid files? Clear error messages explain what went wrong
- Missing files? Helpful prompts guide you
- Invalid parameters? Validation catches issues before processing

### 4. Full Feature Parity with CLI
Everything you can do on command line is available in the GUI:
```powershell
# This CLI command...
python main.py drawing.svg output.gcode --auto-scale --scale-width 150 --auto-center --smooth 2

# ...is replicated in GUI Advanced tab with:
# ✓ Auto-scale enabled, width=150, height=150
# ✓ Auto-center enabled
# ✓ Smoothing=2 iterations
```

---

## 🎯 Typical Workflows

### Quick Convert (Beginner Tab)
```
1. Load file
2. Generate
```
(2 clicks!)

### Optimized Conversion (Advanced Tab)
```
1. Load file (preview auto-updates)
2. Enable Auto-scale (set your plotter dimensions)
3. Enable Auto-center
4. Adjust smoothing if needed
5. Generate
```

### Batch Processing with Profiles (Profiles Tab)
```
1. Configure Advanced settings once
2. Save as profile "My Plotter Config"
3. Later: Load profile for new files
   → All settings restore instantly
```

### Transform Existing G-code (Auto-detected)
```
1. Load existing .gcode file
   → UI auto-switches to Transform mode
2. Select page size (A4, A3, custom...)
3. Optionally enable Landscape
4. Generate (scaled to fit new page)
```

---

## 🐛 Troubleshooting

### "No valid input file"
- Make sure the file path is correct
- File must be .svg, .dxf, or .gcode

### Preview shows but won't zoom
- Try scrolling in the preview area
- Click-drag to pan around
- Scroll wheel zooms (up=zoom in, down=zoom out)

### Profile doesn't load
- Check that the profile name exists in the list
- Profiles are stored in `.plotterprofiles/` directory
- Make sure you're in the Profiles tab

### G-code generation is slow
- Large files (1000+ paths) take longer
- The progress bar shows current stage
- Don't close the app while it's processing!

---

## 📊 Understanding the Statistics

In the Live Preview section, you see:

- **Paths**: Number of separate drawing paths/curves
- **Points**: Total vertices in all paths
- **Size**: Bounding box dimensions in millimeters
- **Length**: Total line length in millimeters (approximate draw time = length / feed_rate)

---

## 💡 Pro Tips

1. **Use profiles** for different plotting styles (fast draft vs. fine detail)
2. **Auto-scale + Auto-center** = "just make it fit" — great for most cases
3. **Smoothing** helps reduce jagged curves (especially from DXF arcs)
4. **Preview** before generating — catch issues early!
5. **Travel optimization** reduces pen-up distance significantly (saves time)

---

## 📚 More Information

- See `README.md` for feature list and installation
- See `V3_IMPLEMENTATION_SUMMARY.md` for technical details
- CLI still available: `python main.py --help`

---

**Happy plotting! 🖊️**
