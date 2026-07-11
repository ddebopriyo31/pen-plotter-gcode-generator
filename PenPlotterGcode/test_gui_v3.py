"""Test suite for GUI v3.0 components."""

from config_manager import ConfigManager, PlotterConfig
from gui_utils import detect_file_type, PreviewCanvas
from geometry import Point, Path, Paths
import tkinter as tk


def test_config_manager():
    """Test ConfigManager functionality."""
    print("\n=== Testing ConfigManager ===")
    
    # Test 1: Initialize
    cm = ConfigManager()
    print("[✓] ConfigManager initialized")
    
    # Test 2: Save profile
    config = PlotterConfig(
        feed_rate=3000,
        travel_rate=6000,
        auto_scale=True,
        smoothing_iterations=3,
        pen_up_command="M3 S90",
        pen_down_command="M5 S5",
    )
    cm.save_profile("TestProfile", config)
    print("[✓] Profile saved")
    
    # Test 3: Load profile
    loaded = cm.load_profile("TestProfile")
    assert loaded.feed_rate == 3000
    assert loaded.smoothing_iterations == 3
    assert loaded.pen_up_command == "M3 S90"
    print("[✓] Profile loaded and verified")
    
    # Test 4: List profiles
    profiles = cm.list_profiles()
    assert "TestProfile" in profiles
    print(f"[✓] Listed {len(profiles)} profile(s)")
    
    # Test 5: Delete profile
    cm.delete_profile("TestProfile")
    profiles = cm.list_profiles()
    assert "TestProfile" not in profiles
    print("[✓] Profile deleted")


def test_gui_utils():
    """Test gui_utils functionality."""
    print("\n=== Testing GUI Utils ===")
    
    # Test 1: File type detection
    assert detect_file_type("test.svg") == "svg"
    assert detect_file_type("test.dxf") == "dxf"
    assert detect_file_type("test.gcode") == "gcode"
    print("[✓] File type detection works")
    
    # Test 2: Invalid file type
    try:
        detect_file_type("test.txt")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("[✓] Invalid file type raises error")
    
    # Test 3: PreviewCanvas initialization
    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root)
    preview = PreviewCanvas(canvas, width=400, height=300)
    print("[✓] PreviewCanvas initialized")
    
    # Test 4: Set geometry (using proper type aliases as lists/tuples)
    path1: Path = [(0, 0), (10, 10), (20, 0)]
    path2: Path = [(25, 5), (35, 15), (40, 5)]
    paths: Paths = [path1, path2]
    preview.set_paths(paths)
    print("[✓] Geometry set in preview")
    
    # Test 5: Get statistics
    stats = preview.get_stats()
    assert stats["path_count"] == 2
    assert stats["point_count"] == 6
    assert stats["width"] > 0
    assert stats["height"] > 0
    print(f"[✓] Statistics: {stats['path_count']} paths, {stats['point_count']} points, {stats['width']:.1f}x{stats['height']:.1f}mm, {stats['total_length']:.1f}mm")
    
    # Test 6: Bounds calculation
    min_x, min_y, max_x, max_y = preview.get_bounds()
    assert min_x == 0
    assert max_x == 40
    print(f"[✓] Bounds: ({min_x}, {min_y}) to ({max_x}, {max_y})")
    
    # Test 7: Empty paths
    preview.set_paths([])
    stats = preview.get_stats()
    assert stats["path_count"] == 0
    print("[✓] Empty paths handled correctly")
    
    root.destroy()


def test_gui_imports():
    """Test that GUI imports work."""
    print("\n=== Testing GUI Imports ===")
    
    try:
        import gui
        print("[✓] GUI module imports successfully")
    except Exception as e:
        print(f"[✗] GUI import failed: {e}")
        raise


if __name__ == "__main__":
    print("=" * 50)
    print("PenPlotter GUI v3.0 Test Suite")
    print("=" * 50)
    
    try:
        test_config_manager()
        test_gui_utils()
        test_gui_imports()
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
