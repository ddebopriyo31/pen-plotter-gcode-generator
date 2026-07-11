"""PenPlotter GUI v3.0 - Full-featured tabbed interface with live preview."""

from __future__ import annotations

import os
import threading
from tkinter import Canvas, filedialog, messagebox, ttk
from typing import TYPE_CHECKING

import tkinter as tk

from config_manager import ConfigManager, PlotterConfig
from dxf_reader import read_dxf
from geometry import Paths
from gcode_transformer import get_page_size, transform_gcode_file
from gcode_writer import save_gcode
from gui_utils import DragDropHandler, PreviewCanvas, detect_file_type
from optimizer import optimize_paths
from svg_reader import read_svg

if TYPE_CHECKING:
    from pathlib import Path


class ResultDialog(tk.Toplevel):
    """Dialog showing conversion results and statistics."""

    def __init__(self, parent: tk.Widget, title: str, message: str, stats: dict | None = None) -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("500x400")
        self.resizable(False, False)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Message
        msg_label = ttk.Label(self, text=message, wraplength=450, justify=tk.LEFT)
        msg_label.pack(padx=20, pady=15)

        # Stats if provided
        if stats:
            stats_frame = ttk.LabelFrame(self, text="Conversion Statistics", padding=10)
            stats_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

            for key, value in stats.items():
                key_label = ttk.Label(stats_frame, text=f"{key}:", font=("TkDefaultFont", 10, "bold"))
                key_label.grid(row=len(stats_frame.winfo_children()) // 2, column=0, sticky="w", padx=5, pady=5)
                value_label = ttk.Label(stats_frame, text=str(value), font=("TkDefaultFont", 10))
                value_label.grid(row=len(stats_frame.winfo_children()) // 2 - 1, column=1, sticky="w", padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=15)
        ttk.Button(button_frame, text="OK", command=self.destroy).pack(side=tk.LEFT, padx=5)


class PenPlotterGuiV3(tk.Tk):
    """Main GUI application for PenPlotter G-code converter."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Pen Plotter G-code Converter v3.0")
        self.geometry("1000x700")
        self.minsize(800, 600)

        self.config_manager = ConfigManager()
        self._setup_styles()
        self._create_widgets()
        self._setup_drag_drop()

    def _setup_styles(self) -> None:
        """Configure application styles."""
        style = ttk.Style()
        style.theme_use("clam")

    def _create_widgets(self) -> None:
        """Create main UI structure."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # File I/O section
        self._create_file_section(main_frame)

        # Tabbed interface
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        self.beginner_frame = ttk.Frame(self.notebook)
        self.advanced_frame = ttk.Frame(self.notebook)
        self.presets_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.beginner_frame, text="Beginner Mode")
        self.notebook.add(self.advanced_frame, text="Advanced Mode")
        self.notebook.add(self.presets_frame, text="Profiles")

        self._create_beginner_tab()
        self._create_advanced_tab()
        self._create_presets_tab()

        # Preview and status section
        self._create_preview_section(main_frame)

        # Action buttons
        self._create_action_buttons(main_frame)

    def _create_file_section(self, parent: ttk.Frame) -> None:
        """Create file input/output section."""
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding=10)
        file_frame.pack(fill=tk.X, pady=5)
        file_frame.columnconfigure(1, weight=1)

        # Input file
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_entry = ttk.Entry(file_frame, width=50)
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.input_entry.bind("<FocusOut>", lambda _: self._on_input_changed())
        ttk.Button(file_frame, text="Browse", command=self._browse_input, width=12).grid(row=0, column=2, padx=5)

        # Output file
        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_entry = ttk.Entry(file_frame, width=50)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self._browse_output, width=12).grid(row=1, column=2, padx=5)

        # Mode indicator
        self.mode_label = ttk.Label(file_frame, text="Mode: Convert (SVG/DXF → G-code)", foreground="blue")
        self.mode_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)

    def _create_beginner_tab(self) -> None:
        """Create beginner-friendly tab with essential options."""
        frame = ttk.Frame(self.beginner_frame, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Quick Settings", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 15))

        # Feed rate
        rate_frame = ttk.Frame(frame)
        rate_frame.pack(fill=tk.X, pady=10)
        ttk.Label(rate_frame, text="Feed Rate (mm/min):", width=25).pack(side=tk.LEFT)
        self.beginner_feed_rate = tk.StringVar(value="2000")
        ttk.Spinbox(rate_frame, from_=100, to=10000, textvariable=self.beginner_feed_rate, width=15).pack(side=tk.LEFT, padx=10)

        # Travel rate
        travel_frame = ttk.Frame(frame)
        travel_frame.pack(fill=tk.X, pady=10)
        ttk.Label(travel_frame, text="Travel Rate (mm/min):", width=25).pack(side=tk.LEFT)
        self.beginner_travel_rate = tk.StringVar(value="5000")
        ttk.Spinbox(travel_frame, from_=100, to=20000, textvariable=self.beginner_travel_rate, width=15).pack(side=tk.LEFT, padx=10)

        # Pen commands
        pen_up_frame = ttk.Frame(frame)
        pen_up_frame.pack(fill=tk.X, pady=10)
        ttk.Label(pen_up_frame, text="Pen Up Command:", width=25).pack(side=tk.LEFT)
        self.beginner_pen_up = tk.StringVar(value="M3 S80")
        ttk.Entry(pen_up_frame, textvariable=self.beginner_pen_up, width=30).pack(side=tk.LEFT, padx=10)

        pen_down_frame = ttk.Frame(frame)
        pen_down_frame.pack(fill=tk.X, pady=10)
        ttk.Label(pen_down_frame, text="Pen Down Command:", width=25).pack(side=tk.LEFT)
        self.beginner_pen_down = tk.StringVar(value="M5 S10")
        ttk.Entry(pen_down_frame, textvariable=self.beginner_pen_down, width=30).pack(side=tk.LEFT, padx=10)

        # Hint
        ttk.Label(
            frame,
            text="💡 For advanced options like auto-scaling, smoothing, and optimization, switch to the Advanced tab.",
            foreground="gray",
            wraplength=500,
        ).pack(anchor="w", pady=(30, 0))

    def _create_advanced_tab(self) -> None:
        """Create advanced options tab with all parameters."""
        main_frame = ttk.Frame(self.advanced_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Two-column layout
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Left column: Conversion settings
        ttk.Label(left_frame, text="Conversion Settings", font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(0, 10))

        # Feed rate
        ttk.Label(left_frame, text="Feed Rate (mm/min):").pack(anchor="w", pady=(5, 0))
        self.adv_feed_rate = tk.StringVar(value="2000")
        ttk.Spinbox(left_frame, from_=100, to=10000, textvariable=self.adv_feed_rate, width=20).pack(anchor="w", pady=(0, 10))

        # Travel rate
        ttk.Label(left_frame, text="Travel Rate (mm/min):").pack(anchor="w", pady=(5, 0))
        self.adv_travel_rate = tk.StringVar(value="5000")
        ttk.Spinbox(left_frame, from_=100, to=20000, textvariable=self.adv_travel_rate, width=20).pack(anchor="w", pady=(0, 10))

        # Pen commands
        ttk.Label(left_frame, text="Pen Up Command:").pack(anchor="w", pady=(5, 0))
        self.adv_pen_up = tk.StringVar(value="M3 S80")
        ttk.Entry(left_frame, textvariable=self.adv_pen_up, width=30).pack(anchor="w", pady=(0, 10))

        ttk.Label(left_frame, text="Pen Down Command:").pack(anchor="w", pady=(5, 0))
        self.adv_pen_down = tk.StringVar(value="M5 S10")
        ttk.Entry(left_frame, textvariable=self.adv_pen_down, width=30).pack(anchor="w", pady=(0, 20))

        # Optimization settings
        ttk.Label(left_frame, text="Optimization", font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(10, 10))

        # Auto-scale
        self.adv_auto_scale = tk.BooleanVar(value=False)
        ttk.Checkbutton(left_frame, text="Auto-scale to fit plotter", variable=self.adv_auto_scale).pack(anchor="w", pady=5)

        # Auto-scale dimensions
        scale_frame = ttk.Frame(left_frame)
        scale_frame.pack(anchor="w", pady=5)
        ttk.Label(scale_frame, text="  Width (mm):").pack(side=tk.LEFT)
        self.adv_scale_width = tk.StringVar(value="200")
        ttk.Spinbox(scale_frame, from_=10, to=500, textvariable=self.adv_scale_width, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(scale_frame, text="Height (mm):").pack(side=tk.LEFT, padx=10)
        self.adv_scale_height = tk.StringVar(value="200")
        ttk.Spinbox(scale_frame, from_=10, to=500, textvariable=self.adv_scale_height, width=12).pack(side=tk.LEFT, padx=5)

        # Auto-center
        self.adv_auto_center = tk.BooleanVar(value=False)
        ttk.Checkbutton(left_frame, text="Auto-center at origin", variable=self.adv_auto_center).pack(anchor="w", pady=5)

        # Smoothing
        ttk.Label(left_frame, text="Path Smoothing Iterations:").pack(anchor="w", pady=(10, 0))
        self.adv_smoothing = tk.IntVar(value=0)
        smoothing_frame = ttk.Frame(left_frame)
        smoothing_frame.pack(anchor="w", pady=5)
        ttk.Scale(smoothing_frame, from_=0, to=10, variable=self.adv_smoothing, orient=tk.HORIZONTAL, length=200).pack(
            side=tk.LEFT
        )
        self.smoothing_label = ttk.Label(smoothing_frame, text="0", width=3)
        self.smoothing_label.pack(side=tk.LEFT, padx=10)
        self.adv_smoothing.trace("w", lambda *_: self.smoothing_label.config(text=str(self.adv_smoothing.get())))

        # Right column: Plotter configuration
        ttk.Label(right_frame, text="Plotter Configuration", font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(0, 10))

        # Plotter dimensions
        ttk.Label(right_frame, text="Plotter Width (mm):").pack(anchor="w", pady=(5, 0))
        self.adv_plotter_width = tk.StringVar(value="200")
        ttk.Spinbox(right_frame, from_=10, to=1000, textvariable=self.adv_plotter_width, width=20).pack(anchor="w", pady=(0, 10))

        ttk.Label(right_frame, text="Plotter Height (mm):").pack(anchor="w", pady=(5, 0))
        self.adv_plotter_height = tk.StringVar(value="200")
        ttk.Spinbox(right_frame, from_=10, to=1000, textvariable=self.adv_plotter_height, width=20).pack(anchor="w", pady=(0, 20))

        # Path optimization
        ttk.Label(right_frame, text="Path Optimization", font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(10, 10))

        self.adv_path_join = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Join adjacent paths", variable=self.adv_path_join).pack(anchor="w", pady=5)

        self.adv_optimize_travel = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Optimize travel (nearest-neighbor)", variable=self.adv_optimize_travel).pack(anchor="w", pady=5)

        # Page size for G-code transform
        ttk.Label(right_frame, text="Page Size (for G-code transform):", font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(20, 10))

        ttk.Label(right_frame, text="Preset:").pack(anchor="w", pady=(5, 0))
        self.adv_page_size = tk.StringVar(value="A4")
        ttk.Combobox(right_frame, textvariable=self.adv_page_size, values=["A4", "A3", "A2", "A5", "Custom"], width=18, state="readonly").pack(
            anchor="w", pady=(0, 10)
        )

        ttk.Label(right_frame, text="Custom Width (mm):").pack(anchor="w", pady=(5, 0))
        self.adv_page_width = tk.StringVar(value="")
        ttk.Entry(right_frame, textvariable=self.adv_page_width, width=30).pack(anchor="w", pady=(0, 5))

        ttk.Label(right_frame, text="Custom Height (mm):").pack(anchor="w", pady=(5, 0))
        self.adv_page_height = tk.StringVar(value="")
        ttk.Entry(right_frame, textvariable=self.adv_page_height, width=30).pack(anchor="w", pady=(0, 10))

        self.adv_landscape = tk.BooleanVar(value=False)
        ttk.Checkbutton(right_frame, text="Landscape orientation", variable=self.adv_landscape).pack(anchor="w", pady=5)

    def _create_presets_tab(self) -> None:
        """Create profile management tab."""
        frame = ttk.Frame(self.presets_frame, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Profile list
        ttk.Label(frame, text="Saved Profiles", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 10))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.profile_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.profile_listbox.yview)

        self._refresh_profile_list()

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Load Profile", command=self._load_selected_profile, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Current as Profile", command=self._save_current_profile, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Profile", command=self._delete_selected_profile, width=20).pack(side=tk.LEFT, padx=5)

    def _create_preview_section(self, parent: ttk.Frame) -> None:
        """Create live preview canvas and stats."""
        preview_frame = ttk.LabelFrame(parent, text="Live Preview & Statistics", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        preview_frame.columnconfigure(0, weight=1)

        # Canvas
        self.preview_canvas = Canvas(preview_frame, bg="#f8f8f8", height=250, highlightthickness=1, highlightbackground="#cccccc")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=5)

        self.preview = PreviewCanvas(self.preview_canvas, width=400, height=250)

        # Stats
        stats_frame = ttk.Frame(preview_frame)
        stats_frame.pack(fill=tk.X, pady=5)

        self.stats_label = ttk.Label(
            stats_frame,
            text="Load a file to see preview • Paths: - | Points: - | Size: - x - mm | Length: - mm",
            foreground="gray",
        )
        self.stats_label.pack(anchor="w")

    def _create_action_buttons(self, parent: ttk.Frame) -> None:
        """Create main action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)

        self.convert_button = ttk.Button(
            button_frame, text="Generate G-code", command=self._on_generate_clicked, width=20
        )
        self.convert_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear", command=self._on_clear_clicked, width=20).pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(button_frame, variable=self.progress_var, maximum=100, length=300)
        self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        self.status_label = ttk.Label(button_frame, text="Ready", foreground="green", width=30)
        self.status_label.pack(side=tk.LEFT, padx=5)

    def _setup_drag_drop(self) -> None:
        """Setup drag-and-drop support if available."""
        # Note: tkinterdnd2 needs to be installed for this to work
        pass  # Drag-drop setup would go here

    def _browse_input(self) -> None:
        """Browse for input file."""
        filetypes = [("All Supported", "*.svg *.dxf *.gcode"), ("SVG files", "*.svg"), ("DXF files", "*.dxf"), ("G-code files", "*.gcode"), ("All files", "*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)
            self._on_input_changed()

    def _browse_output(self) -> None:
        """Browse for output file."""
        path = filedialog.asksaveasfilename(defaultextension=".gcode", filetypes=[("G-code files", "*.gcode"), ("All files", "*")])
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def _on_input_changed(self) -> None:
        """Handle input file change - update mode and preview."""
        input_file = self.input_entry.get().strip()
        if not input_file or not os.path.isfile(input_file):
            self.mode_label.config(text="Mode: (no valid input file)")
            return

        try:
            file_type = detect_file_type(input_file)
            if file_type == "gcode":
                self.mode_label.config(text="Mode: Transform (G-code → G-code)", foreground="orange")
                self.notebook.tab(0, state="disabled")
                self.notebook.tab(1, state="disabled")
            else:
                self.mode_label.config(text=f"Mode: Convert ({file_type.upper()} → G-code)", foreground="blue")
                self.notebook.tab(0, state="normal")
                self.notebook.tab(1, state="normal")

            # Load preview
            self._load_preview(input_file)
        except ValueError:
            self.mode_label.config(text="Mode: (unsupported file type)", foreground="red")

    def _load_preview(self, input_file: str) -> None:
        """Load and display geometry preview."""
        try:
            file_type = detect_file_type(input_file)
            if file_type == "svg":
                paths = read_svg(input_file)
            elif file_type == "dxf":
                paths = read_dxf(input_file)
            else:
                self.preview.set_paths(Paths())
                return

            self.preview.set_paths(paths)
            stats = self.preview.get_stats()
            self.stats_label.config(
                text=f"Paths: {stats['path_count']} | Points: {stats['point_count']} | Size: {stats['width']} x {stats['height']} mm | Length: {stats['total_length']} mm"
            )
        except Exception as e:
            self.stats_label.config(text=f"Error loading preview: {str(e)[:100]}", foreground="red")

    def _on_generate_clicked(self) -> None:
        """Handle generate button click."""
        input_file = self.input_entry.get().strip()
        output_file = self.output_entry.get().strip()

        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Error", "Please select a valid input file.")
            return

        if not output_file:
            messagebox.showerror("Error", "Please specify an output file path.")
            return

        # Run conversion in background thread
        thread = threading.Thread(target=self._do_conversion, args=(input_file, output_file), daemon=True)
        thread.start()

    def _do_conversion(self, input_file: str, output_file: str) -> None:
        """Perform the actual conversion."""
        try:
            self.status_label.config(text="Processing...", foreground="blue")
            self.progress_var.set(0)
            self.convert_button.config(state="disabled")

            file_type = detect_file_type(input_file)

            if file_type == "gcode":
                # Transform mode
                self.status_label.config(text="Transforming G-code...", foreground="blue")
                self.progress_var.set(30)

                width_text = self.adv_page_width.get().strip()
                height_text = self.adv_page_height.get().strip()

                if width_text and height_text:
                    page_width, page_height = float(width_text), float(height_text)
                else:
                    page_width, page_height = get_page_size(self.adv_page_size.get(), landscape=self.adv_landscape.get())

                self.progress_var.set(60)
                transform_gcode_file(input_file, output_file, page_width, page_height)
                self.progress_var.set(100)

                stats = {"Output File": output_file, "Input File": input_file}
            else:
                # Conversion mode
                self.status_label.config(text="Reading geometry...", foreground="blue")
                self.progress_var.set(20)

                if file_type == "svg":
                    paths = read_svg(input_file)
                else:
                    paths = read_dxf(input_file)

                self.status_label.config(text="Optimizing paths...", foreground="blue")
                self.progress_var.set(50)

                optimized = optimize_paths(
                    paths,
                    auto_scale=self.adv_auto_scale.get(),
                    scale_width=float(self.adv_scale_width.get()) if self.adv_auto_scale.get() else None,
                    scale_height=float(self.adv_scale_height.get()) if self.adv_auto_scale.get() else None,
                    auto_center=self.adv_auto_center.get(),
                    smoothing_iterations=self.adv_smoothing.get(),
                )

                self.status_label.config(text="Generating G-code...", foreground="blue")
                self.progress_var.set(80)

                save_gcode(
                    optimized,
                    output_file,
                    feed_rate=int(self.adv_feed_rate.get()),
                    travel_rate=int(self.adv_travel_rate.get()),
                    pen_up_command=self.adv_pen_up.get().strip(),
                    pen_down_command=self.adv_pen_down.get().strip(),
                )

                self.progress_var.set(100)

                # Get stats
                preview_stats = self.preview.get_stats()
                stats = {
                    "Input File": os.path.basename(input_file),
                    "Output File": os.path.basename(output_file),
                    "Paths": preview_stats["path_count"],
                    "Total Points": preview_stats["point_count"],
                    "Canvas Size": f"{preview_stats['width']} x {preview_stats['height']} mm",
                    "Total Length": f"{preview_stats['total_length']} mm",
                }

            self.status_label.config(text="✓ Complete!", foreground="green")
            messagebox.showinfo(
                "Success",
                f"G-code successfully generated!\n\nOutput: {output_file}",
            )

        except Exception as e:
            self.status_label.config(text="✗ Error", foreground="red")
            messagebox.showerror("Error", f"Conversion failed:\n\n{str(e)}")
        finally:
            self.convert_button.config(state="normal")

    def _on_clear_clicked(self) -> None:
        """Clear all fields."""
        self.input_entry.delete(0, tk.END)
        self.output_entry.delete(0, tk.END)
        self.preview.set_paths(Paths())
        self.stats_label.config(text="Load a file to see preview")
        self.progress_var.set(0)
        self.status_label.config(text="Ready", foreground="green")

    def _save_current_profile(self) -> None:
        """Save current settings as a profile."""
        # Create a simple dialog for profile name
        dialog = tk.Toplevel(self)
        dialog.title("Save Profile")
        dialog.geometry("300x100")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Profile Name:").pack(pady=10)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5, padx=10)

        def save_profile() -> None:
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Please enter a profile name.")
                return

            config = PlotterConfig(
                feed_rate=int(self.adv_feed_rate.get()),
                travel_rate=int(self.adv_travel_rate.get()),
                pen_up_command=self.adv_pen_up.get().strip(),
                pen_down_command=self.adv_pen_down.get().strip(),
                plotter_width=float(self.adv_plotter_width.get()),
                plotter_height=float(self.adv_plotter_height.get()),
                auto_scale=self.adv_auto_scale.get(),
                auto_center=self.adv_auto_center.get(),
                smoothing_iterations=self.adv_smoothing.get(),
            )

            try:
                self.config_manager.save_profile(name, config)
                messagebox.showinfo("Success", f"Profile '{name}' saved successfully!")
                self._refresh_profile_list()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save profile:\n{str(e)}")

        ttk.Button(dialog, text="Save", command=save_profile).pack(pady=10)

    def _load_selected_profile(self) -> None:
        """Load selected profile."""
        selection = self.profile_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a profile to load.")
            return

        profile_name = self.profile_listbox.get(selection[0])
        try:
            config = self.config_manager.load_profile(profile_name)
            self.adv_feed_rate.set(str(config.feed_rate))
            self.adv_travel_rate.set(str(config.travel_rate))
            self.adv_pen_up.set(config.pen_up_command)
            self.adv_pen_down.set(config.pen_down_command)
            self.adv_plotter_width.set(str(config.plotter_width))
            self.adv_plotter_height.set(str(config.plotter_height))
            self.adv_auto_scale.set(config.auto_scale)
            self.adv_auto_center.set(config.auto_center)
            self.adv_smoothing.set(config.smoothing_iterations)

            # Also update beginner tab
            self.beginner_feed_rate.set(str(config.feed_rate))
            self.beginner_travel_rate.set(str(config.travel_rate))
            self.beginner_pen_up.set(config.pen_up_command)
            self.beginner_pen_down.set(config.pen_down_command)

            messagebox.showinfo("Success", f"Profile '{profile_name}' loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile:\n{str(e)}")

    def _delete_selected_profile(self) -> None:
        """Delete selected profile."""
        selection = self.profile_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a profile to delete.")
            return

        profile_name = self.profile_listbox.get(selection[0])
        if messagebox.askyesno("Confirm", f"Delete profile '{profile_name}'?"):
            try:
                self.config_manager.delete_profile(profile_name)
                messagebox.showinfo("Success", f"Profile '{profile_name}' deleted.")
                self._refresh_profile_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete profile:\n{str(e)}")

    def _refresh_profile_list(self) -> None:
        """Refresh the profile listbox."""
        self.profile_listbox.delete(0, tk.END)
        for profile_name in self.config_manager.list_profiles():
            self.profile_listbox.insert(tk.END, profile_name)


def main() -> None:
    """Launch the application."""
    app = PenPlotterGuiV3()
    app.mainloop()


if __name__ == "__main__":
    main()
